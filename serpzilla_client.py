"""
Client for working with Serpzilla API
"""

import aiohttp
import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class SerpzillaClient:
    """Client for interacting with Serpzilla API"""

    BASE_URL = "https://app.serpzilla.com"
    USER_AGENT = "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; Serpzilla-mcp-client/1.0"

    def __init__(self, login: str, api_token: str):
        self.login = login
        self.api_token = api_token
        self.auth_ticket = None
        self.jwt_token = None
        self.session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            # Set default headers for the whole session
            default_headers = {
                "User-Agent": self.USER_AGENT,
                "Accept": "application/json",
            }
            self.session = aiohttp.ClientSession(headers=default_headers)
        return self.session

    async def authorize(self) -> Dict[str, Any]:
        """
        Two-step authorization in Serpzilla:
        1. Get AUTH_TICKET via /login
        2. Get JWT via /auth
        """
        try:
            session = await self._get_session()

            # Step 1: Get AUTH_TICKET
            logger.info(f"Authorizing user {self.login}")
            async with session.post(
                    f"{self.BASE_URL}/login",
                    json={"login": self.login, "apiToken": self.api_token},
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    }
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Error getting AUTH_TICKET: {error_text}")

                data = await response.json()
                # AUTH_TICKET is also set in cookies
                cookies = response.cookies
                if 'AUTH_TICKET' in cookies:
                    self.auth_ticket = cookies['AUTH_TICKET'].value
                elif 'authTicket' in data:
                    self.auth_ticket = data['authTicket']
                else:
                    raise Exception("Failed to get AUTH_TICKET")

                logger.info("AUTH_TICKET received successfully")

            # Step 2: Get JWT
            async with session.get(
                f"{self.BASE_URL}/auth",
                headers={
                    "Accept": "application/json",
                    "Cookie": f"AUTH_TICKET={self.auth_ticket}",
                }
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Error getting JWT: {error_text}")

                data = await response.json()
                self.jwt_token = data.get('token')
                if not self.jwt_token:
                    raise Exception("Failed to get JWT")

                logger.info("JWT received successfully")

            return {
                "success": True,
                "message": "Authorization successful"
            }

        except Exception as e:
            logger.error(f"Authorization error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Perform authorized request to API
        """
        if not self.auth_ticket or not self.jwt_token:
            await self.authorize()

        session = await self._get_session()

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.jwt_token}",
            "Cookie": f"AUTH_TICKET={self.auth_ticket}",
        }

        if data is not None:
            headers["Content-Type"] = "application/json"

        url = f"{self.BASE_URL}{endpoint}"

        log_headers = headers.copy()
        if 'Authorization' in log_headers:
            log_headers['Authorization'] = 'Bearer ***'
        if 'Cookie' in log_headers:
            log_headers['Cookie'] = 'AUTH_TICKET=***'
        log_entry = {
            "method": method,
            "url": url,
            "params": params,
            "data": data,
            "headers": log_headers
        }
        logger.info(f"API request: {json.dumps(log_entry, ensure_ascii=False)}")

        async with session.request(
            method=method,
            url=url,
            json=data,
            params=params,
            headers=headers
        ) as response:
            if response.status == 401:
                # Token expired, trying to re-authorize
                logger.info("Token expired, re-authorizing")
                await self.authorize()
                headers["Authorization"] = f"Bearer {self.jwt_token}"
                headers["Cookie"] = f"AUTH_TICKET={self.auth_ticket}"

                async with session.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=headers
                ) as retry_response:
                    return await retry_response.json()

            return await response.json()
        return None

    async def get_projects(self) -> Dict[str, Any]:
        """
        Get list of projects
        """
        # First get list of projects
        result = await self._make_request("GET", "/rest/Project")

        # If there are projects, get info for each
        if isinstance(result, dict) and result.get('projects'):
            projects = result['projects']
            for project in projects:
                project_id = project.get('id')
                if project_id:
                    # Get URLs and texts for project
                    urls = await self._make_request("GET", f"/rest/Url/list/projectId/{project_id}")
                    if isinstance(urls, dict):
                        project['urls'] = urls.get('urls', [])

        return result

    async def create_project(self, domain: str) -> Dict[str, Any]:
        """
        Create new project
        """
        return await self._make_request(
            "POST",
            "/rest/Project/addSimpleProjectAndContent",
            data={"domain": domain}
        )

    async def add_article(
        self,
        project_id: int,
        url: str,
        title: str,
        body: str,
        meta_title: str,
        meta_description: str = "",
        meta_keywords: str = "",
        is_comments_disabled: bool = False,
        limit_max_usages: int = 1
    ) -> Dict[str, Any]:
        """
        Create a new Guest Post article (Advertiser's Article)
        Returns articleId, urlId, urlHref
        """
        data = {
            "url": url,
            "title": title,
            "body": body,
            "metaTitle": meta_title,
            "metaDescription": meta_description,
            "metaKeywords": meta_keywords,
            "isCommentsDisabled": is_comments_disabled,
            "limitMaxUsages": limit_max_usages
        }
        return await self._make_request("POST", f"/rest/Content/add/article/projectId/{project_id}", data=data)

    async def get_project_content_list(
        self,
        project_id: Optional[int] = None,
        creation_source: Optional[int] = None,
        substring_text: Optional[str] = None,
        url_ids: Optional[List[int]] = None,
        content_type: Optional[int] = None,
        status: Optional[int] = None,
        content_status_ids: Optional[List[int]] = None,
        from_: Optional[int] = None,
        limit: Optional[int] = None,
        order_by: Optional[str] = None,
        order_direction: Optional[str] = None,
        async_url_id: Optional[int] = None,
        show_async_content_load: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Get a filtered list of content (texts, articles) for a project.
        """
        params = {}
        if project_id is not None:
            params["projectId"] = project_id
        if creation_source is not None:
            params["creationSource"] = creation_source

        data = {}
        if substring_text is not None:
            data["substringText"] = substring_text
        if url_ids is not None:
            data["urlIds"] = url_ids
        if content_type is not None:
            data["contentType"] = content_type
        if status is not None:
            data["status"] = status
        if content_status_ids is not None:
            data["contentStatusIds"] = content_status_ids
        if from_ is not None:
            data["from"] = from_
        if limit is not None:
            data["limit"] = limit
        if order_by is not None:
            data["orderBy"] = order_by
        if order_direction is not None:
            data["orderDirection"] = order_direction
        if async_url_id is not None:
            data["asyncUrlId"] = async_url_id
        if show_async_content_load is not None:
            data["showAsyncContentLoad"] = show_async_content_load

        return await self._make_request("POST", "/rest/Content/list/", data=data, params=params)

    async def search_sites(
        self,
        project_id: int,
        link_type: str,
        price_from: Optional[float] = None,
        price_to: Optional[float] = None,
        language: Optional[str] = None,
        majestic_cf_from: Optional[int] = None,
        majestic_cf_to: Optional[int] = None,
        majestic_tf_from: Optional[int] = None,
        majestic_tf_to: Optional[int] = None,
        moz_da_from: Optional[int] = None,
        moz_da_to: Optional[int] = None,
        moz_page_rank_from: Optional[int] = None,
        moz_page_rank_to: Optional[int] = None,
        moz_page_authority_from: Optional[int] = None,
        moz_page_authority_to: Optional[int] = None,
        moz_spam_score_from: Optional[int] = None,
        moz_spam_score_to: Optional[int] = None,
        external_links_to: Optional[int] = None,
        domain_level: Optional[int] = None,
        days_old_whois_from: Optional[int] = None,
        ahrefs_dr_from: Optional[int] = None,
        ahrefs_dr_to: Optional[int] = None,
        ahrefs_backlinks_from: Optional[int] = None,
        ahrefs_backlinks_to: Optional[int] = None,
        ahrefs_keywords_from: Optional[int] = None,
        ahrefs_keywords_to: Optional[int] = None,
        keywords: Optional[str] = None,
        avg_placement_time_from: Optional[int] = None,
        avg_placement_time_to: Optional[int] = None,
        placement_probability_from: Optional[int] = None,
        placement_probability_to: Optional[int] = None,
        pages_google_from: Optional[int] = None,
        pages_google_to: Optional[int] = None,
        semrush_as_from: Optional[int] = None,
        semrush_as_to: Optional[int] = None,
        semrush_domains_from: Optional[int] = None,
        semrush_domains_to: Optional[int] = None,
        traffic_semrush_from: Optional[int] = None,
        traffic_ahrefs_from: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Search donor sites by filters
        """
        # Build request parameters
        params = {
            "permanentLinkType": link_type,
            "projectId": project_id
        }

        data = {}
        # Base
        if price_from is not None:
            data["priceArticleFrom"] = price_from
        if price_to is not None:
            data["priceArticleTo"] = price_to

        if language is not None:
            data["siteLanguage"] = language

        # Majestic
        if majestic_cf_from is not None:
            data["majesticCfFrom"] = majestic_cf_from
        if majestic_cf_to is not None:
            data["majesticCfTo"] = majestic_cf_to
        if majestic_tf_from is not None:
            data["majesticTfFrom"] = majestic_tf_from
        if majestic_tf_to is not None:
            data["majesticTfTo"] = majestic_tf_to

        # Moz
        if moz_da_from is not None:
            data["mozDomainAuthorityFrom"] = moz_da_from
        if moz_da_to is not None:
            data["mozDomainAuthorityTo"] = moz_da_to
        if moz_page_rank_from is not None:
            data["mozPageRankFrom"] = moz_page_rank_from
        if moz_page_rank_to is not None:
            data["mozPageRankTo"] = moz_page_rank_to
        if moz_page_authority_from is not None:
            data["mozPageAuthorityFrom"] = moz_page_authority_from
        if moz_page_authority_to is not None:
            data["mozPageAuthorityTo"] = moz_page_authority_to
        if moz_spam_score_from is not None:
            data["mozSpamScoreFrom"] = moz_spam_score_from
        if moz_spam_score_to is not None:
            data["mozSpamScoreTo"] = moz_spam_score_to

        # Other
        if external_links_to is not None:
            data["externalLinksTo"] = external_links_to
        if domain_level is not None:
            data["domainLevel"] = domain_level
        if days_old_whois_from is not None:
            data["daysOldWhoisFrom"] = days_old_whois_from

        # Ahrefs
        if ahrefs_dr_from is not None:
            data["ahrefsDomainRatingFrom"] = ahrefs_dr_from
        if ahrefs_dr_to is not None:
            data["ahrefsDomainRatingTo"] = ahrefs_dr_to
        if ahrefs_backlinks_from is not None:
            data["ahrefsTotalBacklinksFrom"] = ahrefs_backlinks_from
        if ahrefs_backlinks_to is not None:
            data["ahrefsTotalBacklinksTo"] = ahrefs_backlinks_to
        if ahrefs_keywords_from is not None:
            data["ahrefsTotalKeywordsFrom"] = ahrefs_keywords_from
        if ahrefs_keywords_to is not None:
            data["ahrefsTotalKeywordsTo"] = ahrefs_keywords_to

        # Keywords
        if keywords is not None:
            data["keywords"] = keywords

        # Placement time and probability
        if avg_placement_time_from is not None:
            data["avgPlacementTimeFrom"] = avg_placement_time_from
        if avg_placement_time_to is not None:
            data["avgPlacementTimeTo"] = avg_placement_time_to
        if placement_probability_from is not None:
            data["placementProbabilityFrom"] = placement_probability_from
        if placement_probability_to is not None:
            data["placementProbabilityTo"] = placement_probability_to

        # Indexing in Google
        if pages_google_from is not None:
            data["nofPagesInGoogleFrom"] = pages_google_from
        if pages_google_to is not None:
            data["nofPagesInGoogleTo"] = pages_google_to

        # Semrush
        if semrush_as_from is not None:
            data["semrushAscoreFrom"] = semrush_as_from
        if semrush_as_to is not None:
            data["semrushAscoreTo"] = semrush_as_to
        if semrush_domains_from is not None:
            data["semrushDomainsNumFrom"] = semrush_domains_from
        if semrush_domains_to is not None:
            data["semrushDomainsNumTo"] = semrush_domains_to

        # Traffic
        if traffic_semrush_from is not None:
            data["trafficSemrushFrom"] = traffic_semrush_from
        if traffic_ahrefs_from is not None:
            data["trafficAhrefsFrom"] = traffic_ahrefs_from

        return await self._make_request(
            "POST",
            f"/rest/SearchPermanent/projectId/{project_id}",
            data=data,
            params=params
        )

    async def get_site_info(self, site_id: int) -> Dict[str, Any]:
        """
        Get full site card details for a given site ID.
        """
        return await self._make_request("GET", f"/rest/Site/{site_id}")

    async def purchase_placement(
        self,
        project_id: int,
        site_id: int,
        link_type: str,
        url_id: Optional[int] = None,
        text_id: Optional[int] = None,
        article_id: Optional[int] = None,
        search_history_id: Optional[str] = None,
        is_content_need_approval: bool = False
    ) -> Dict[str, Any]:
        """
        Purchase placement
        """
        # Determine linkTypeId based on placement type
        link_type_map = {
            "link": 20,      # In The News
            "news": 21,      # Advertiser’s Article
            "review": 22,    # Publisher’s Article
            "archive": 23    # In The Archive
        }

        link_type_id = link_type_map.get(link_type)
        if not link_type_id:
            raise ValueError(f"Unknown link type: {link_type}")

        # Build link for purchase
        link = {
            "siteId": site_id
        }

        if link_type == "news":
            if article_id:
                link["articleId"] = article_id
            if url_id:
                link["urlsTexts"] = [{"urlId": url_id}]
            else:
                raise ValueError("url_id is required for news placements")
        else:
            if url_id and text_id:
                link["urlsTexts"] = [{"urlId": url_id, "textId": text_id}]
            else:
                raise ValueError("url_id and text_id are required for this placement type")

        # Build request data
        data = {
            "links": [link],
            "settings": {
                "creditPeriod": 0,
                "isContentNeedApproval": is_content_need_approval,
                "nofPendingDays": 5,
                "warrantyPackage": 2,
                "discountWanted": [],
                "isLinkTextFinal": False,
                "isConfirmedMaxUsagesExceeding": True
            }
        }

        if search_history_id:
            data["settings"]["searchHistoryId"] = search_history_id

        return await self._make_request(
            "POST",
            f"/rest/Placement/permanent/create/projectId/{project_id}",
            data=data,
            params={"linkTypeId": link_type_id}
        )

    async def get_project_placements(self, project_id: int) -> Dict[str, Any]:
        """
        Get list of placements in project
        """
        return await self._make_request(
            "POST",
            f"/rest/Project/placements/links",
            params={"projectId": project_id}
        )

    async def perform_placement_action(self, action: str, placement_ids: List[int]) -> Dict[str, Any]:
        """
        Perform an action on a list of placements.
        Valid actions: force_billing_seo, approve_seo, approve_content_seo,
                       approve_from_arbitration_seo, cancel_from_on_placement_seo,
                       cancel_from_improve_seo, cancel_seo, terminate_seo,
                       cancel_order_change_links_seo, price_changing_action_accept_seo,
                       guarantee_wm, accept_order_change_links_wm,
                       price_changing_action_reject_wm, delete_draft_seo,
                       buy_from_buy_fail_seo, delete_from_buy_fail_seo.
        """
        data = {
            "action": action,
            "placementIds": placement_ids
        }
        return await self._make_request("PATCH", "/rest/Placement/action", data=data)

    async def get_user_info(self) -> Dict[str, Any]:
        """
        Get current user information including account balance
        """
        return await self._make_request("GET", "/rest/User/info")

    async def close(self):
        """Close session"""
        if self.session and not self.session.closed:
            await self.session.close()
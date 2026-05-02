#!/usr/bin/env python3
"""
MCP Server for Serpzilla API - purchasing article placements for SEO
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

from serpzilla_client import SerpzillaClient

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Getting credentials from environment variables
SERPZILLA_LOGIN = os.environ.get("SERPZILLA_LOGIN")
SERPZILLA_API_TOKEN = os.environ.get("SERPZILLA_API_TOKEN")

if not SERPZILLA_LOGIN or not SERPZILLA_API_TOKEN:
    logger.error("SERPZILLA_LOGIN and SERPZILLA_API_TOKEN must be set")
    raise ValueError("Missing required environment variables")

# Initializing client
client = SerpzillaClient(SERPZILLA_LOGIN, SERPZILLA_API_TOKEN)

# Creating MCP server
app = Server("serpzilla-mcp-server")


@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List of available MCP tools
    """
    return [
        types.Tool(
            name="authorize",
            description="Authorization in Serpzilla API using login and API token",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="list_projects",
            description="Get list of existing projects",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="create_project",
            description="Create a new project for domain promotion",
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Domain to promote (e.g., https://example.com/)"
                    }
                },
                "required": ["domain"]
            }
        ),
        types.Tool(
            name="search_sites",
            description="Search donor sites by given filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "Project ID"
                    },
                    "link_type": {
                        "type": "string",
                        "description": "Placement type: news, review, link, archive",
                        "enum": ["news", "review", "link", "archive"]
                    },
                    "price_from": {
                        "type": "number",
                        "description": "Minimum price"
                    },
                    "price_to": {
                        "type": "number",
                        "description": "Maximum price"
                    },
                    "language": {
                        "type": "string",
                        "description": "Site language"
                    },
                    "majestic_cf_from": {"type": "integer", "description": "Majestic Citation Flow from"},
                    "majestic_cf_to": {"type": "integer", "description": "Majestic Citation Flow to"},
                    "majestic_tf_from": {"type": "integer", "description": "Majestic Trust Flow from"},
                    "majestic_tf_to": {"type": "integer", "description": "Majestic Trust Flow to"},
                    "moz_da_from": {"type": "integer", "description": "Moz Domain Authority from"},
                    "moz_da_to": {"type": "integer", "description": "Moz Domain Authority to"},
                    "moz_page_rank_from": {"type": "integer", "description": "Moz Page Rank from"},
                    "moz_page_rank_to": {"type": "integer", "description": "Moz Page Rank to"},
                    "moz_page_authority_from": {"type": "integer", "description": "Moz Page Authority from"},
                    "moz_page_authority_to": {"type": "integer", "description": "Moz Page Authority to"},
                    "moz_spam_score_from": {"type": "integer", "description": "Moz Spam Score from"},
                    "moz_spam_score_to": {"type": "integer", "description": "Moz Spam Score to"},
                    "external_links_to": {"type": "integer",
                                          "description": "Maximum number of external links on donor"},
                    "domain_level": {"type": "integer",
                                     "description": "Domain level: 0 - all, 2 - only second level, 3 - only third",
                                     "enum": [0, 2, 3]},
                    "days_old_whois_from": {"type": "integer", "description": "Domain age in days from"},
                    "ahrefs_dr_from": {"type": "integer", "description": "Ahrefs DR from"},
                    "ahrefs_dr_to": {"type": "integer", "description": "Ahrefs DR to"},
                    "ahrefs_backlinks_from": {"type": "integer",
                                              "description": "Ahrefs total backlinks from"},
                    "ahrefs_backlinks_to": {"type": "integer", "description": "Ahrefs total backlinks to"},
                    "ahrefs_keywords_from": {"type": "integer", "description": "Ahrefs total keywords from"},
                    "ahrefs_keywords_to": {"type": "integer", "description": "Ahrefs total keywords to"},
                    "keywords": {"type": "string", "description": "Keywords separated by commas"},
                    "avg_placement_time_from": {"type": "integer",
                                                "description": "Minimum placement time in days"},
                    "avg_placement_time_to": {"type": "integer", "description": "Maximum placement time in days"},
                    "placement_probability_from": {"type": "integer",
                                                   "description": "Minimum placement probability percentage"},
                    "placement_probability_to": {"type": "integer",
                                                 "description": "Maximum placement probability percentage"},
                    "pages_google_from": {"type": "integer",
                                          "description": "Minimum number of pages in Google index"},
                    "pages_google_to": {"type": "integer",
                                        "description": "Maximum number of pages in Google index"},
                    "semrush_as_from": {"type": "integer", "description": "Semrush AS (Authority Score) from"},
                    "semrush_as_to": {"type": "integer", "description": "Semrush AS to"},
                    "semrush_domains_from": {"type": "integer", "description": "Semrush number of domains from"},
                    "semrush_domains_to": {"type": "integer", "description": "Semrush number of domains to"},
                    "traffic_semrush_from": {"type": "integer", "description": "Semrush traffic from"},
                    "traffic_ahrefs_from": {"type": "integer", "description": "Ahrefs traffic from"},
                },
                "required": ["project_id", "link_type"]
            }
        ),
        types.Tool(
            name="get_site_info",
            description="Get detailed information about a donor site (site card), including metrics, price, status, "
                        "languages, statistics, etc.",
            inputSchema={
                "type": "object",
                "properties": {
                    "site_id": {
                        "type": "integer",
                        "description": "Site ID"
                    }
                },
                "required": ["site_id"]
            }
        ),
        types.Tool(
            name="purchase_placement",
            description="Purchase placement on selected site",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "Project ID"
                    },
                    "site_id": {
                        "type": "integer",
                        "description": "Donor site ID"
                    },
                    "url_id": {
                        "type": "integer",
                        "description": "Promoted URL ID"
                    },
                    "text_id": {
                        "type": "integer",
                        "description": "Text ID (for link, review, archive)"
                    },
                    "article_id": {
                        "type": "integer",
                        "description": "Article ID (for news)"
                    },
                    "link_type": {
                        "type": "string",
                        "description": "Placement type",
                        "enum": ["news", "review", "link", "archive"]
                    },
                    "search_history_id": {
                        "type": "string",
                        "description": "Search history ID"
                    },
                    "is_content_need_approval": {
                        "type": "boolean",
                        "description": "Whether content approval is required",
                        "default": False
                    }
                },
                "required": ["project_id", "site_id", "link_type"]
            }
        ),
        types.Tool(
            name="add_article",
            description="Create a new Guest Post article (Advertiser's Article) for a project. "
                        "Returns articleId and urlId needed for purchase.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "integer", "description": "Project ID"},
                    "url": {"type": "string", "description": "Promoted URL (e.g., https://example.com)"},
                    "title": {"type": "string", "description": "Article title", "minLength": 2},
                    "body": {"type": "string", "description": "Article HTML text, must contain at least one link",
                             "maxLength": 64000},
                    "meta_title": {"type": "string", "description": "META Title of the article"},
                    "meta_description": {"type": "string", "description": "META Description", "default": ""},
                    "meta_keywords": {"type": "string", "description": "META Keywords", "default": ""},
                    "is_comments_disabled": {"type": "boolean", "description": "Disable comments", "default": False},
                    "limit_max_usages": {"type": "integer", "description": "Maximum usage limit", "default": 1}
                },
                "required": ["project_id", "url", "title", "body", "meta_title"]
            }
        ),
        types.Tool(
            name="get_project_content_list",
            description="Get a list of content (articles and texts) in a project with filtering, "
                        "sorting, and pagination. "
                        "Supports status, type, URL IDs, and search by substring.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "Project ID"
                    },
                    "creation_source": {
                        "type": "integer",
                        "description": "Source of content creation: 0 - user, 1 - system",
                        "enum": [0, 1]
                    },
                    "substring_text": {
                        "type": "string",
                        "description": "Search by substring in content text"
                    },
                    "url_ids": {
                        "type": "array",
                        "description": "Filter by URL IDs",
                        "items": {"type": "integer"}
                    },
                    "content_type": {
                        "type": "integer",
                        "description": "Content type: 1 - text, 3 - Guest Post",
                        "enum": [1, 3]
                    },
                    "status": {
                        "type": "integer",
                        "description": "Content status: 0-Draft, 1-Creating, 2-Creation error, 3-AI article error, "
                                       "5-Moderation, 6-Rejected, 7-AI article creation, 10-Active, 11-Changing, "
                                       "20-Archived, 30-Deleted",
                        "enum": [0, 1, 2, 3, 5, 6, 7, 10, 11, 20, 30]
                    },
                    "content_status_ids": {
                        "type": "array",
                        "description": "List of content status IDs",
                        "items": {
                            "type": "integer",
                            "description": "Content status: 0-Draft, 1-Creating, 2-Creation error, 3-AI article error, "
                                           "5-Moderation, 6-Rejected, 7-AI article creation, 10-Active, 11-Changing, "
                                           "20-Archived, 30-Deleted",
                            "enum": [0, 1, 2, 3, 5, 6, 7, 10, 11, 20, 30]
                        }
                    },
                    "from": {
                        "type": "integer",
                        "description": "First entry position (offset)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of records"
                    },
                    "order_by": {
                        "type": "string",
                        "description": "Sort field",
                        "enum": ["createdAt", "text"]
                    },
                    "order_direction": {
                        "type": "string",
                        "description": "Sort direction",
                        "enum": ["asc", "desc"]
                    },
                    "async_url_id": {
                        "type": "integer",
                        "description": "Async URL ID"
                    },
                    "show_async_content_load": {
                        "type": "boolean",
                        "description": "Show only contents in process of adding",
                        "default": False
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="get_project_placements",
            description="Get list of all placements in project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "Project ID"
                    }
                },
                "required": ["project_id"]
            }
        ),
        types.Tool(
            name="perform_placement_action",
            description="Perform an action on one or more placements (e.g., approve, cancel). "
                        "The list of allowed actions: force_billing_seo, approve_seo, approve_content_seo, "
                        "approve_from_arbitration_seo, cancel_from_on_placement_seo, cancel_from_improve_seo, "
                        "cancel_seo, terminate_seo, cancel_order_change_links_seo, price_changing_action_accept_seo, "
                        "guarantee_wm, accept_order_change_links_wm, price_changing_action_reject_wm, "
                        "delete_draft_seo, buy_from_buy_fail_seo, delete_from_buy_fail_seo.",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action to perform (see list)",
                        "enum": [
                            "force_billing_seo",
                            "approve_seo",
                            "approve_content_seo",
                            "approve_from_arbitration_seo",
                            "cancel_from_on_placement_seo",
                            "cancel_from_improve_seo",
                            "cancel_seo",
                            "terminate_seo",
                            "cancel_order_change_links_seo",
                            "price_changing_action_accept_seo",
                            "guarantee_wm",
                            "accept_order_change_links_wm",
                            "price_changing_action_reject_wm",
                            "delete_draft_seo",
                            "buy_from_buy_fail_seo",
                            "delete_from_buy_fail_seo"
                        ]
                    },
                    "placement_ids": {
                        "type": "array",
                        "description": "List of placement IDs to apply the action to",
                        "items": {"type": "integer"}
                    }
                },
                "required": ["action", "placement_ids"]
            }
        ),
        types.Tool(
            name="get_user_info",
            description="Get current user information including account balance (balance field). To top up your "
                        "balance, visit: https://passport.serpzilla.com/deposit/",
            inputSchema={"type": "object", "properties": {}, "required": []}
        )
    ]


@app.call_tool()
async def handle_call_tool(
        name: str,
        arguments: Optional[Dict[str, Any]] = None
) -> list[types.TextContent]:
    """
    Handling tool calls
    """
    try:
        if name == "authorize":
            result = await client.authorize()

        elif name == "list_projects":
            result = await client.get_projects()

        elif name == "create_project":
            domain = arguments.get("domain")
            if not domain:
                raise ValueError("Domain is required")
            result = await client.create_project(domain)

        elif name == "add_article":
            project_id = arguments.get("project_id")
            url = arguments.get("url")
            title = arguments.get("title")
            body = arguments.get("body")
            meta_title = arguments.get("meta_title")
            meta_description = arguments.get("meta_description", "")
            meta_keywords = arguments.get("meta_keywords", "")
            is_comments_disabled = arguments.get("is_comments_disabled", False)
            limit_max_usages = arguments.get("limit_max_usages", 1)

            result = await client.add_article(project_id, url, title, body, meta_title, meta_description, meta_keywords,
                                              is_comments_disabled, limit_max_usages)

        elif name == "get_project_content_list":
            project_id = arguments.get("project_id")
            creation_source = arguments.get("creation_source")
            substring_text = arguments.get("substring_text")
            url_ids = arguments.get("url_ids")
            content_type = arguments.get("content_type")
            status = arguments.get("status")
            content_status_ids = arguments.get("content_status_ids")
            from_ = arguments.get("from")
            limit = arguments.get("limit")
            order_by = arguments.get("order_by")
            order_direction = arguments.get("order_direction")
            async_url_id = arguments.get("async_url_id")
            show_async_content_load = arguments.get("show_async_content_load")

            result = await client.get_project_content_list(
                project_id=project_id,
                creation_source=creation_source,
                substring_text=substring_text,
                url_ids=url_ids,
                content_type=content_type,
                status=status,
                content_status_ids=content_status_ids,
                from_=from_,
                limit=limit,
                order_by=order_by,
                order_direction=order_direction,
                async_url_id=async_url_id,
                show_async_content_load=show_async_content_load
            )

        elif name == "search_sites":
            project_id = arguments.get("project_id")
            link_type = arguments.get("link_type")

            filters = {
                "price_from": arguments.get("price_from"),
                "price_to": arguments.get("price_to"),
                "language": arguments.get("language"),
                "majestic_cf_from": arguments.get("majestic_cf_from"),
                "majestic_cf_to": arguments.get("majestic_cf_to"),
                "majestic_tf_from": arguments.get("majestic_tf_from"),
                "majestic_tf_to": arguments.get("majestic_tf_to"),
                "moz_da_from": arguments.get("moz_da_from"),
                "moz_da_to": arguments.get("moz_da_to"),
                "moz_page_rank_from": arguments.get("moz_page_rank_from"),
                "moz_page_rank_to": arguments.get("moz_page_rank_to"),
                "moz_page_authority_from": arguments.get("moz_page_authority_from"),
                "moz_page_authority_to": arguments.get("moz_page_authority_to"),
                "moz_spam_score_from": arguments.get("moz_spam_score_from"),
                "moz_spam_score_to": arguments.get("moz_spam_score_to"),
                "external_links_to": arguments.get("external_links_to"),
                "domain_level": arguments.get("domain_level"),
                "days_old_whois_from": arguments.get("days_old_whois_from"),
                "ahrefs_dr_from": arguments.get("ahrefs_dr_from"),
                "ahrefs_dr_to": arguments.get("ahrefs_dr_to"),
                "ahrefs_backlinks_from": arguments.get("ahrefs_backlinks_from"),
                "ahrefs_backlinks_to": arguments.get("ahrefs_backlinks_to"),
                "ahrefs_keywords_from": arguments.get("ahrefs_keywords_from"),
                "ahrefs_keywords_to": arguments.get("ahrefs_keywords_to"),
                "keywords": arguments.get("keywords"),
                "avg_placement_time_from": arguments.get("avg_placement_time_from"),
                "avg_placement_time_to": arguments.get("avg_placement_time_to"),
                "placement_probability_from": arguments.get("placement_probability_from"),
                "placement_probability_to": arguments.get("placement_probability_to"),
                "pages_google_from": arguments.get("pages_google_from"),
                "pages_google_to": arguments.get("pages_google_to"),
                "semrush_as_from": arguments.get("semrush_as_from"),
                "semrush_as_to": arguments.get("semrush_as_to"),
                "semrush_domains_from": arguments.get("semrush_domains_from"),
                "semrush_domains_to": arguments.get("semrush_domains_to"),
                "traffic_semrush_from": arguments.get("traffic_semrush_from"),
                "traffic_ahrefs_from": arguments.get("traffic_ahrefs_from"),
            }

            # Remove None values to avoid passing unnecessary fields
            filters = {k: v for k, v in filters.items() if v is not None}

            if not project_id or not link_type:
                raise ValueError("project_id and link_type are required")

            result = await client.search_sites(
                project_id, link_type, **filters
            )

        elif name == "get_site_info":
            site_id = arguments.get("site_id")
            if not site_id:
                raise ValueError("site_id is required")
            result = await client.get_site_info(site_id)

        elif name == "purchase_placement":
            project_id = arguments.get("project_id")
            site_id = arguments.get("site_id")
            link_type = arguments.get("link_type")
            url_id = arguments.get("url_id")
            text_id = arguments.get("text_id")
            article_id = arguments.get("article_id")
            search_history_id = arguments.get("search_history_id")
            is_content_need_approval = arguments.get("is_content_need_approval", False)

            if not project_id or not site_id or not link_type:
                raise ValueError("project_id, site_id and link_type are required")

            # If it's a news article, article_id is needed; otherwise url_id and text_id are needed
            if link_type == "news":
                if not article_id:
                    raise ValueError("article_id is required for news placements")
            else:
                if not url_id or not text_id:
                    raise ValueError("url_id and text_id are required for this placement type")

            result = await client.purchase_placement(
                project_id=project_id,
                site_id=site_id,
                link_type=link_type,
                url_id=url_id,
                text_id=text_id,
                article_id=article_id,
                search_history_id=search_history_id,
                is_content_need_approval=is_content_need_approval
            )

        elif name == "get_project_placements":
            project_id = arguments.get("project_id")
            if not project_id:
                raise ValueError("project_id is required")
            result = await client.get_project_placements(project_id)

        elif name == "perform_placement_action":
            action = arguments.get("action")
            placement_ids = arguments.get("placement_ids")
            if not action or not placement_ids:
                raise ValueError("action and placement_ids are required")
            if not isinstance(placement_ids, list) or not all(isinstance(x, int) for x in placement_ids):
                raise ValueError("placement_ids must be a list of integers")
            result = await client.perform_placement_action(action, placement_ids)

        elif name == "get_user_info":
            result = await client.get_user_info()

        else:
            raise ValueError(f"Unknown tool: {name}")

        return [types.TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )]

    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({"error": str(e)}, ensure_ascii=False)
        )]


async def main():
    """
    Running MCP server
    """
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="serpzilla-mcp-server",
                server_version="1.0.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
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
            name="add_text",
            description="Add text for promoting URL",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "Project ID"
                    },
                    "url": {
                        "type": "string",
                        "description": "Promoted URL"
                    },
                    "texts": {
                        "type": "array",
                        "description": "List of texts with anchors",
                        "items": {
                            "type": "object",
                            "properties": {
                                "text": {
                                    "type": "string",
                                    "description": "Text with anchor in format #a#anchor#/a#"
                                }
                            }
                        }
                    }
                },
                "required": ["project_id", "url", "texts"]
            }
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

        elif name == "add_text":
            project_id = arguments.get("project_id")
            url = arguments.get("url")
            texts = arguments.get("texts")

            if not project_id or not url or not texts:
                raise ValueError("project_id, url and texts are required")

            result = await client.add_texts(project_id, url, texts)

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
"""
FastMCP server exposing ActionAgent as HTTP MCP tools.

Usage:
    python mcp_servers/action_agent_server.py

This starts a Starlette + Uvicorn server that exposes ActionAgent
methods as MCP-compatible tools over Server-Sent Events (SSE).
Your ADK Agent can then connect to: http://localhost:8002/sse
"""

import sys
import os
import yaml
import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Route, Mount

# Ensure repo root on sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.marketo_client import MarketoClient
from utils.action_agent import ActionAgent

# Correct FastMCP import
from fastmcp import FastMCP
from mcp.server.sse import SseServerTransport

# ------------------------------------------------------------------------------
# Load configuration
# ------------------------------------------------------------------------------

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "config.yaml")
try:
    with open(CONFIG_PATH, "r") as fh:
        cfg = yaml.safe_load(fh)
except FileNotFoundError:
    cfg = {}

mcfg = cfg.get("settings", {}).get("marketo", {})

identity_base = mcfg.get("identity_base") or os.environ.get("MARKETO_IDENTITY_BASE")
rest_base = mcfg.get("rest_base") or os.environ.get("MARKETO_REST_BASE")
client_id = mcfg.get("client_id") or os.environ.get("MARKETO_CLIENT_ID")
client_secret = mcfg.get("client_secret") or os.environ.get("MARKETO_CLIENT_SECRET")

print("identity_base is", identity_base)

marketo = MarketoClient(client_id, client_secret, identity_base, rest_base)
agent = ActionAgent(marketo)

# ------------------------------------------------------------------------------
# Create FastMCP and register tools
# ------------------------------------------------------------------------------

mcp = FastMCP(name="marketo-action-agent")

@mcp.tool()
def trigger_campaign(campaign_id: int, input_payload: dict) -> dict:
    """
    Trigger a Marketo campaign by ID.

    Args:
        campaign_id: The ID of the Marketo campaign.
        input_payload: Dictionary of parameters to send.

    Returns:
        API response from Marketo.
    """
    return agent.trigger_campaign(campaign_id, input_payload)

@mcp.tool()
def create_smart_campaign(name: str, folder_id: int, folder_type: str, description: str = "") -> dict:
    """
    Create a new Marketo Smart Campaign.

    Args:
        name: The name of the smart campaign to create.
        folder_id: The ID of the folder or program where the campaign will be created.
        folder_type: The type of the folder - must be either 'Folder' or 'Program'.
        description: Optional description for the smart campaign.

    Returns:
        API response from Marketo containing the created campaign details.
    """
    return agent.create_smart_campaign(name, folder_id, folder_type, description)

@mcp.tool()
def update_smart_campaign_by_id(smart_campaign_id: int, name: str = None, description: str = None) -> dict:
    """
    Update a Marketo Smart Campaign's name and/or description.

    At least one of 'name' or 'description' must be provided.

    Args:
        smart_campaign_id: The ID of the Marketo smart campaign to update.
        name: Optional new name for the smart campaign.
        description: Optional new description for the smart campaign.

    Returns:
        API response from Marketo containing the updated campaign details.
    """
    return agent.update_smart_campaign(smart_campaign_id, name, description)

@mcp.tool()
def get_campaign(campaign_id: str) -> dict:
    """
    Retrieve details about a specific Marketo campaign.

    Args:
        campaign_id: The campaign ID.

    Returns:
        Campaign details as a dictionary.
    """
    return agent.get_campaign(campaign_id)

@mcp.tool()
def get_smart_list(smart_list_id: int) -> dict:
    """
    Retrieve a specific smart list by ID from Marketo.

    Args:
        smart_list_id: The smart list ID.

    Returns:
        Smart list details as a dictionary.
    """
    return agent.get_smart_list(smart_list_id)

@mcp.tool()
def get_lead_by_id(lead_id: int, fields: list = None) -> dict:
    """
    Retrieve a specific lead by ID from Marketo.

    Args:
        lead_id: The Marketo lead ID to fetch.
        fields: Optional list of field names to return. If not specified, returns all fields.

    Returns:
        Lead details as a dictionary.
    """
    return agent.get_lead_by_id(lead_id, fields)

@mcp.tool()
def get_leads_by_filter_type(filter_type: str, filter_values: list, fields: list = None, batch_size: int = 300) -> dict:
    """
    Retrieve multiple leads by filter type (email, id, cookie, etc.).

    Args:
        filter_type: Type of filter to use (e.g., 'email', 'id', 'cookie').
        filter_values: List of values to filter by.
        fields: Optional list of field names to return.
        batch_size: Number of leads to return (max 300).

    Returns:
        Dictionary containing list of matching leads.
    """
    return agent.get_leads_by_filter_type(filter_type, filter_values, fields, batch_size)

@mcp.tool()
def describe_lead() -> dict:
    """
    Get metadata about available lead fields in Marketo.

    Returns:
        Dictionary containing field metadata including field names, data types, 
        whether they're REST readable/updatable, etc.
    """
    return agent.describe_lead()

@mcp.tool()
def get_lead_partitions() -> dict:
    """
    Retrieve all lead partitions configured in the Marketo instance.

    Returns:
        Dictionary containing list of lead partitions with their IDs and names.
    """
    return agent.get_lead_partitions()

@mcp.tool()
def get_leads_by_program(program_id: int, fields: list = None, batch_size: int = 300) -> dict:
    """
    Retrieve leads that are members of a specific Marketo program.

    Args:
        program_id: The Marketo program ID.
        fields: Optional list of field names to return.
        batch_size: Number of leads to return (max 300).

    Returns:
        Dictionary containing list of leads in the program.
    """
    return agent.get_leads_by_program(program_id, fields, batch_size)

@mcp.tool()
def get_leads_by_smart_list(smart_list_id: int, fields: list = None, batch_size: int = 300, next_page_token: str = None) -> dict:
    """
    Retrieve leads that are members of a specific Smart List.

    Args:
        smart_list_id: The Marketo Smart List ID.
        fields: Optional list of field names to return.
        batch_size: Number of leads to return (max 300).
        next_page_token: Token for pagination to get next page of results.

    Returns:
        Dictionary containing list of leads and pagination info (nextPageToken if more results exist).
    """
    return agent.get_leads_by_smart_list(smart_list_id, fields, batch_size, next_page_token)

@mcp.tool()
def get_program_by_id(program_id: int) -> dict:
    """
    Retrieve a specific program by ID from Marketo.

    Args:
        program_id: The Marketo program ID.

    Returns:
        Program details as a dictionary.
    """
    return agent.get_program_by_id(program_id)

@mcp.tool()
def get_program_by_name(name: str, include_tags: bool = False, include_costs: bool = False) -> dict:
    """
    Retrieve a program by its name from Marketo.

    Args:
        name: Name of the program.
        include_tags: Set true to populate program tags.
        include_costs: Set true to populate program costs.

    Returns:
        Program details as a dictionary.
    """
    return agent.get_program_by_name(name, include_tags, include_costs)

@mcp.tool()
def clone_program(program_id: int, name: str, folder_id: int, folder_type: str, description: str = "") -> dict:
    """
    Clone an existing Marketo program.

    Args:
        program_id: The ID of the program to clone.
        name: Name of the new cloned program (max 255 characters).
        folder_id: The ID of the folder where the cloned program will be created.
        folder_type: The type of the folder - must be either 'Folder' or 'Program'.
        description: Optional description for the cloned program.

    Returns:
        API response from Marketo containing the cloned program details.
    """
    return agent.clone_program(program_id, name, folder_id, folder_type, description)
##--------------------------------------------------------------------------------------------------------------------------
# Token Update Tools
@mcp.tool()
def get_tokens(folder_id: int, folder_type: str = "Folder") -> dict:
    """
    Get My Tokens from a Marketo folder.

    Args:
        folder_id: The Marketo folder ID.
        folder_type: Type of folder - 'Folder' or 'Program' (default: 'Folder').

    Returns:
        Dictionary containing folder tokens.
    """
    return agent.get_tokens(folder_id, folder_type)

# @mcp.tool()
# def update_program_tokens(program_id: int, tokens: dict) -> dict:
#     """
#     Auto-populate My Tokens in a Marketo program.

#     Args:
#         program_id: The Marketo program ID.
#         tokens: Dictionary mapping token names to values.

#     Returns:
#         API response with updated token details.
#     """
#     return agent.update_program_tokens(program_id, tokens)

# Email Update Tools
@mcp.tool()
def get_email_by_name(name: str, status: str = None, folder: dict = None) -> dict:
    """
    Get an email asset by name from Marketo.

    Args:
        name: Name of the email to retrieve.
        status: Optional status filter - 'approved' or 'draft'.
        folder: Optional parent folder specification with 'id' and 'type' keys.

    Returns:
        Dictionary containing email details.
    """
    return agent.get_email_by_name(name, status, folder)

@mcp.tool()
def get_email_by_id(email_id: int, status: str = None) -> dict:
    """
    Get an email asset by ID from Marketo.

    Args:
        email_id: The Marketo email asset ID.
        status: Optional status filter - 'approved' or 'draft'.

    Returns:
        Dictionary containing email details.
    """
    return agent.get_email_by_id(email_id, status)
    
@mcp.tool()
def get_program_emails(program_id: int) -> dict:
    """
    Get all email assets from a Marketo program.

    Args:
        program_id: The Marketo program ID.

    Returns:
        Dictionary containing list of email assets.
    """
    return agent.get_program_emails(program_id)

@mcp.tool()
def get_email_content(email_id: int) -> dict:
    """
    Get email content including subject line and body.

    Args:
        email_id: The Marketo email asset ID.

    Returns:
        Dictionary containing email content variables.
    """
    return agent.get_email_content(email_id)

@mcp.tool()
def update_email_content_fields(
    email_id: int, 
    from_email: dict = None,
    from_name: dict = None,
    reply_to: dict = None,
    subject: dict = None
) -> dict:
    """
    Update email header fields (fromEmail, fromName, replyTo, subject).

    Args:
        email_id: The Marketo email asset ID.
        from_email: Dict with 'type' and 'value' keys for from email field.
        from_name: Dict with 'type' and 'value' keys for from name field.
        reply_to: Dict with 'type' and 'value' keys for reply-to field.
        subject: Dict with 'type' and 'value' keys for subject line field.

    Returns:
        API response with updated email header fields.
    """
    return agent.update_email_content_fields(email_id, from_email, from_name, reply_to, subject)

@mcp.tool()
def update_email_metadata(
    email_id: int,
    description: str = None,
    name: str = None,
    pre_header: str = None,
    operational: bool = None,
    published: bool = None,
    text_only: bool = None,
    web_view: bool = None
) -> dict:
    """
    Update email metadata (description, name, preheader, settings).

    Args:
        email_id: The Marketo email asset ID.
        description: Description of the asset.
        name: Name of the email.
        pre_header: Preheader text for the email.
        operational: Whether email is operational (bypasses unsubscribe status).
        published: Whether email has been published to Sales Insight.
        text_only: Include text-only version when sent.
        web_view: Enable 'View as Web Page' functionality.

    Returns:
        API response with updated email metadata.
    """
    return agent.update_email_metadata(
        email_id, description, name, pre_header,
        operational, published, text_only, web_view
    )

@mcp.tool()
def update_email_content_section(
    email_id: int,
    html_id: str,
    content_type: str,
    value: str,
    alt_text: str = None,
    external_url: str = None,
    height: int = None,
    image: str = None,
    link_url: str = None,
    overwrite: bool = None,
    style: str = None,
    text_value: str = None,
    video_url: str = None,
    width: int = None
) -> dict:
    """
    Update a specific email content section by htmlId.

    Args:
        email_id: The Marketo email asset ID.
        html_id: The HTML ID of the content section to update.
        content_type: Type of content - 'Text', 'DynamicContent', or 'Snippet'.
        value: Value to set for the section.
        alt_text: Alt text for images.
        external_url: External URL.
        height: Image height override.
        image: Multipart file for image upload.
        link_url: Link URL.
        overwrite: Allow overwriting existing content.
        style: CSS style parameter.
        text_value: Text value for the section.
        video_url: Video URL (YouTube or Vimeo only).
        width: Image width override.

    Returns:
        API response with updated content section details.
    """
    return agent.update_email_content_section(email_id, html_id, content_type, value,
        alt_text, external_url, height, image, link_url,
        overwrite, style, text_value, video_url, width
    )

@mcp.tool()
def approve_email(email_id: int) -> dict:
    """
    Approve an email asset.

    Args:
        email_id: The Marketo email asset ID.

    Returns:
        API response confirming email approval.
    """
    return agent.approve_email(email_id)

# Landing Page Update Tools
@mcp.tool()
def get_program_landing_pages(program_id: int) -> dict:
    """
    Get all landing page assets from a Marketo program.

    Args:
        program_id: The Marketo program ID.

    Returns:
        Dictionary containing list of landing page assets.
    """
    return agent.get_program_landing_pages(program_id)

@mcp.tool()
def get_landing_page_content(landing_page_id: int) -> dict:
    """
    Get landing page content sections.

    Args:
        landing_page_id: The Marketo landing page asset ID.

    Returns:
        Dictionary containing landing page editable content sections.
    """
    return agent.get_landing_page_content(landing_page_id)

@mcp.tool()
def update_landing_page_content(landing_page_id: int, content_updates: dict) -> dict:
    """
    Update landing page editable sections, CTAs, banners, forms.

    Args:
        landing_page_id: The Marketo landing page asset ID.
        content_updates: Dictionary mapping content section IDs to new values.

    Returns:
        API response with updated landing page content details.
    """
    return agent.update_landing_page_content(landing_page_id, content_updates)

@mcp.tool()
def approve_landing_page(landing_page_id: int) -> dict:
    """
    Approve a landing page asset.

    Args:
        landing_page_id: The Marketo landing page asset ID.

    Returns:
        API response confirming landing page approval.
    """
    return agent.approve_landing_page(landing_page_id)

@mcp.tool()
def update_landing_page_content_section(
    landing_page_id: int,
    content_id: str,
    content_type: str,
    background_color: str = None,
    border_color: str = None,
    border_style: str = None,
    border_width: str = None,
    height: str = None,
    hide_desktop: bool = None,
    hide_mobile: bool = None,
    image_open_new_window: str = None,
    index: int = None,
    left: str = None,
    link_url: str = None,
    opacity: str = None,
    top: str = None,
    value: str = None,
    width: str = None,
    z_index: str = None
) -> dict:
    """
    Update a specific landing page content section.

    Args:
        landing_page_id: The Marketo landing page asset ID.
        content_id: ID of the landing page content section.
        content_type: Type of content section (Image, Form, Rectangle, Snippet, RichText, HTML, DynamicContent).
        background_color: background-color CSS property.
        border_color: border-color CSS property.
        border_style: border-style CSS property.
        border_width: border-width CSS property.
        height: height CSS property.
        hide_desktop: Hide section on desktop browser (default false).
        hide_mobile: Hide section on mobile browser (default false).
        image_open_new_window: Image link behavior.
        index: Index/order of the section in the landing page.
        left: left CSS property.
        link_url: URL for link type sections.
        opacity: opacity CSS property.
        top: top CSS property.
        value: Content section value.
        width: width CSS property.
        z_index: z-index CSS property.

    Returns:
        API response with updated content section details.
    """
    return agent.update_landing_page_content_section(
        landing_page_id, content_id, content_type,
        background_color, border_color, border_style, border_width,
        height, hide_desktop, hide_mobile, image_open_new_window,
        index, left, link_url, opacity, top, value, width, z_index
    )

@mcp.tool()
def update_landing_page_dynamic_content(
    landing_page_id: int,
    content_id: str,
    background_color: str = None,
    border_color: str = None,
    border_style: str = None,
    border_width: str = None,
    height: str = None,
    hide_desktop: bool = None,
    hide_mobile: bool = None,
    image_open_new_window: str = None,
    left: str = None,
    link_url: str = None,
    opacity: str = None,
    segment: str = None,
    top: str = None,
    content_type: str = None,
    value: str = None,
    width: str = None,
    z_index: str = None
) -> dict:
    """
    Update a landing page dynamic content section.

    Args:
        landing_page_id: The Marketo landing page asset ID.
        content_id: ID of the landing page dynamic content.
        background_color: background-color CSS property.
        border_color: border-color CSS property.
        border_style: border-style CSS property.
        border_width: border-width CSS property.
        height: height CSS property.
        hide_desktop: Hide section on desktop browser (default false).
        hide_mobile: Hide section on mobile browser (default false).
        image_open_new_window: Image link behavior.
        left: left CSS property.
        link_url: URL for link type sections.
        opacity: opacity CSS property.
        segment: Name of the segment to display content for.
        top: top CSS property.
        content_type: Type of content section.
        value: Content section value.
        width: width CSS property.
        z_index: z-index CSS property.

    Returns:
        API response with updated dynamic content details.
    """
    return agent.update_landing_page_dynamic_content(
        landing_page_id, content_id,
        background_color, border_color, border_style, border_width,
        height, hide_desktop, hide_mobile, image_open_new_window,
        left, link_url, opacity, segment, top, content_type,
        value, width, z_index
    )

@mcp.tool()
def add_landing_page_content_section(
    landing_page_id: int,
    content_id: str,
    content_type: str,
    background_color: str = None,
    border_color: str = None,
    border_style: str = None,
    border_width: str = None,
    height: str = None,
    hide_desktop: bool = None,
    hide_mobile: bool = None,
    image_open_new_window: str = None,
    left: str = None,
    link_url: str = None,
    opacity: str = None,
    top: str = None,
    value: str = None,
    width: str = None,
    z_index: str = None
) -> dict:
    """
    Add a new content section to a landing page.

    Args:
        landing_page_id: The Marketo landing page asset ID.
        content_id: ID for the new content section (also the HTML id).
        content_type: Type of content section (Image, Form, Rectangle, Snippet, RichText, HTML).
        background_color: background-color CSS property.
        border_color: border-color CSS property.
        border_style: border-style CSS property.
        border_width: border-width CSS property.
        height: height CSS property.
        hide_desktop: Hide section on desktop browser (default false).
        hide_mobile: Hide section on mobile browser (default false).
        image_open_new_window: Image link behavior.
        left: left CSS property.
        link_url: URL for link type sections.
        opacity: opacity CSS property.
        top: top CSS property.
        value: Content section value.
        width: width CSS property.
        z_index: z-index CSS property.

    Returns:
        API response with new content section details.
    """
    return agent.add_landing_page_content_section(
        landing_page_id, content_id, content_type,
        background_color, border_color, border_style, border_width,
        height, hide_desktop, hide_mobile, image_open_new_window,
        left, link_url, opacity, top, value, width, z_index
    )

# Smart List Tools
@mcp.tool()
def get_smart_list_rules(smart_list_id: int) -> dict:
    """
    Get smart list filter rules.

    Args:
        smart_list_id: The Marketo smart list ID.

    Returns:
        Dictionary containing smart list filter rules and criteria.
    """
    return agent.get_smart_list_rules(smart_list_id)

@mcp.tool()
def update_smart_list_rules(smart_list_id: int, rules: dict) -> dict:
    """
    Update smart list filter criteria.

    Args:
        smart_list_id: The Marketo smart list ID.
        rules: Dictionary containing new filter rules and criteria.

    Returns:
        API response with updated smart list rules.
    """
    return agent.update_smart_list_rules(smart_list_id, rules)

# Smart Campaign Tools
@mcp.tool()
def get_smart_campaign_rules(campaign_id: int) -> dict:
    """
    Get smart campaign smart list rules.

    Args:
        campaign_id: The Marketo smart campaign ID.

    Returns:
        Dictionary containing smart campaign filter rules.
    """
    return agent.get_smart_campaign_rules(campaign_id)

@mcp.tool()
def update_smart_campaign_rules(campaign_id: int, rules: dict) -> dict:
    """
    Update smart campaign filter criteria.

    Args:
        campaign_id: The Marketo smart campaign ID.
        rules: Dictionary containing new filter rules and criteria.

    Returns:
        API response with updated smart campaign rules.
    """
    return agent.update_smart_campaign_rules(campaign_id, rules)

@mcp.tool()
def get_smart_campaign_flow(campaign_id: int) -> dict:
    """
    Get smart campaign flow steps.

    Args:
        campaign_id: The Marketo smart campaign ID.

    Returns:
        Dictionary containing smart campaign flow steps.
    """
    return agent.get_smart_campaign_flow(campaign_id)

@mcp.tool()
def update_smart_campaign_flow(campaign_id: int, flow_steps: dict) -> dict:
    """
    Update smart campaign flow based on requirements.

    Args:
        campaign_id: The Marketo smart campaign ID.
        flow_steps: Dictionary containing new flow steps and actions.

    Returns:
        API response with updated smart campaign flow.
    """
    return agent.update_smart_campaign_flow(campaign_id, flow_steps)

@mcp.tool()
def activate_smart_campaign(campaign_id: int) -> dict:
    """
    Activate a smart campaign.

    Args:
        campaign_id: The Marketo smart campaign ID.

    Returns:
        API response confirming campaign activation.
    """
    return agent.activate_smart_campaign(campaign_id)

@mcp.tool()
def schedule_smart_campaign(campaign_id: int, run_at: str, recipients: dict = None) -> dict:
    """
    Schedule a smart campaign to run at specified time.

    Args:
        campaign_id: The Marketo smart campaign ID.
        run_at: ISO 8601 datetime string for when to run the campaign.
        recipients: Optional dictionary containing recipient criteria.

    Returns:
        API response confirming campaign scheduling.
    """
    return agent.schedule_smart_campaign(campaign_id, run_at, recipients)

@mcp.tool()
def schedule_campaign(
    campaign_id: int,
    input_data: dict = None,
    clone_to_program_name: str = None,
    run_at: str = None,
    tokens: list = None
) -> dict:
    """
    Schedule a batch campaign to run at a specified time.

    Args:
        campaign_id: ID of the batch campaign to schedule.
        input_data: Schedule campaign data containing campaign-specific parameters.
        clone_to_program_name: Name of the resulting program. When set, this will 
            cause the campaign, parent program, and all assets to be cloned with 
            the new name. Programs with snippets, push notifications, in-app messages, 
            static lists, reports, and social assets may not be cloned.
        run_at: ISO 8601 datetime string for when to run the campaign. 
            If unset, the campaign will run 5 minutes after the call is made.
        tokens: List of my tokens to replace during the run of the target campaign. 
            Tokens must be available in a parent program or folder to be replaced.

    Returns:
        API response confirming campaign scheduling with schedule details.
    """
    return agent.schedule_campaign(
        campaign_id, input_data, clone_to_program_name, run_at, tokens
    )


# ToDo: Added in Future
# @mcp.tool()
# def get_campaign_details(campaign_id: int) -> dict:
#     return agent.get_campaign_details(campaign_id)

# @mcp.tool()
# def get_smart_list(smart_list_id: int) -> dict:
#     return agent.get_smart_list(smart_list_id)

@mcp.tool()
def get_folder_program_contents(
    folder_id: int,
    folder_type: str = "Folder",
    max_return: int = None,
    offset: int = None
) -> dict:
    """
    Get Inside contents of a Marketo folder or program.

    Args:
        folder_id: ID of the folder to retrieve.
        folder_type: Type of folder - 'Folder' or 'Program' (default: 'Folder').
        max_return: Maximum number of items to return (max 200, default 20).
        offset: Integer offset for paging.

    Returns:
        Dictionary containing folder contents including assets and sub-folders.
    """
    return agent.get_folder_program_contents(folder_id, folder_type, max_return, offset)

@mcp.tool()
def bulk_import_leads(file_path: str, format: str = "csv", lookup_field: str = "email", partition_name: str = None, list_id: int = None) -> dict:
    """
    Import leads from a file into Marketo.

    Args:
        file_path: Path to the file containing lead data.
        format: Import file format (csv, tsv, ssv). Default is csv.
        lookup_field: Field to use for deduplication. Default is email.
        partition_name: Name of the lead partition to import to.
        list_id: ID of the static list to import into.

    Returns:
        API response with import job details.
    """
    return agent.bulk_import_leads(file_path, format, lookup_field, partition_name, list_id)


# ------------------------------------------------------------------------------
# SSE transport and Starlette app (FIXED)
# ------------------------------------------------------------------------------

# Create SSE transport with the correct endpoint
sse = SseServerTransport("/messages")

async def handle_sse(request: Request):
    """
    Handle incoming SSE connection from an MCP client.
    """
    _server = mcp._mcp_server
    async with sse.connect_sse(
        request.scope,
        request.receive,
        request._send,
    ) as (reader, writer):
        await _server.run(reader, writer, _server.create_initialization_options())

# Wrap handle_post_message as a proper ASGI app
class MessageHandler:
    """ASGI application wrapper for SSE message handling."""
    
    async def __call__(self, scope, receive, send):
        await sse.handle_post_message(scope, receive, send)

# Create Starlette app with proper routes
app = Starlette(
    debug=True,
    routes=[
        Route("/sse", endpoint=handle_sse, methods=["GET"]),
        Mount("/messages", app=MessageHandler()),  # Mount the ASGI app
    ],
)

# ------------------------------------------------------------------------------
# Run server
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    # Use uvicorn directly instead of mcp.run() for better control
    #uvicorn.run(app, host="localhost", port=8002, log_level="info")
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8002))
    uvicorn.run(app, host=host, port=port, log_level="info")
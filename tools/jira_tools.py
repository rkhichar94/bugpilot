import json

import anthropic

from config import settings

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


def _mcp_server() -> dict:
    return {
        "type": "url",
        "url": "https://mcp.atlassian.com/v1/mcp",
        "name": "atlassian",
        "authorization_token": settings.atlassian_mcp_token,
    }


def _extract_obj(text: str) -> dict:
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
    return {}


def _extract_arr(text: str) -> list:
    start = text.find("[")
    end = text.rfind("]") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
    return []


def fetch_issue(issue_key: str) -> dict:
    client = _get_client()
    response = client.beta.messages.create(
        model=settings.claude_model,
        max_tokens=1024,
        system=(
            "You are a Jira data retrieval assistant. "
            "Use the available MCP tools to fetch the requested issue, then "
            "respond with ONLY a JSON object containing exactly these fields: "
            "key, summary, description, status, priority. No other text."
        ),
        messages=[{"role": "user", "content": f"Fetch Jira issue {issue_key}."}],
        mcp_servers=[_mcp_server()],
        betas=["mcp-client-2025-11-20"],
    )
    text = next((b.text for b in response.content if hasattr(b, "text")), "{}")
    result = _extract_obj(text)
    return result or {
        "key": issue_key,
        "summary": "",
        "description": "",
        "status": "",
        "priority": "Unknown",
    }


def search_issues(jql: str, max_results: int = 10) -> list[dict]:
    client = _get_client()
    response = client.beta.messages.create(
        model=settings.claude_model,
        max_tokens=4096,
        system=(
            "You are a Jira data retrieval assistant. "
            "Use the available MCP tools to search for issues, then "
            "respond with ONLY a JSON array. Each element must have: "
            "key, summary, description, status, priority. No other text."
        ),
        messages=[{
            "role": "user",
            "content": f"Search Jira issues using JQL: {jql}\nLimit to {max_results} results.",
        }],
        mcp_servers=[_mcp_server()],
        betas=["mcp-client-2025-11-20"],
    )
    text = next((b.text for b in response.content if hasattr(b, "text")), "[]")
    return _extract_arr(text)


def update_issue_status(issue_key: str, comment: str) -> None:
    client = _get_client()
    client.beta.messages.create(
        model=settings.claude_model,
        max_tokens=256,
        messages=[{
            "role": "user",
            "content": f"Add this comment to Jira issue {issue_key}: {comment}",
        }],
        mcp_servers=[_mcp_server()],
        betas=["mcp-client-2025-11-20"],
    )
    print(f"[jira] Added comment to {issue_key}")

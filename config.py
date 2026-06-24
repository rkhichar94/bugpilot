from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Jira (via Atlassian Remote MCP Server)
    atlassian_mcp_token: str
    jira_project_key: str
    jira_jql_filter: str = "issuetype=Bug AND status=Open"

    # GitHub
    github_token: str
    repo_url: str
    repo_default_branch: str = "main"

    # Workspace
    workspace_dir: str = "/tmp/bug-resolver-workspace"

    # Anthropic
    anthropic_api_key: str
    claude_model: str = "claude-sonnet-4-6"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "bug_issues"

    # LangSmith (optional)
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""

    # Slack (optional)
    slack_webhook_url: str = ""

    class Config:
        env_file = ".env"


settings = Settings()

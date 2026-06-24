import argparse
import os

from config import settings
from graph.orchestrator import build_graph
from tools import jira_tools


def _setup_langsmith() -> None:
    if settings.langchain_tracing_v2 and settings.langchain_api_key:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
        print("[main] LangSmith tracing enabled")


def _extract_stacktrace(issue: dict) -> str:
    desc = issue.get("description", "")
    if "Exception" in desc or "\tat " in desc:
        return desc
    return ""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Multi-Agent AI Bug Resolver",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python main.py                  # process all open bugs from Jira\n"
            "  python main.py --issue PROJ-123 # process a single issue"
        ),
    )
    parser.add_argument("--issue", type=str, help="Single Jira issue key")
    args = parser.parse_args()

    _setup_langsmith()

    if args.issue:
        issues = [jira_tools.fetch_issue(args.issue)]
    else:
        jql = f"project={settings.jira_project_key} AND {settings.jira_jql_filter}"
        print(f"[main] Fetching issues: {jql}")
        issues = jira_tools.search_issues(jql, max_results=10)

    if not issues:
        print("[main] No issues found. Exiting.")
        return

    print(f"[main] Processing {len(issues)} issue(s)")
    graph = build_graph()

    for issue in issues:
        print(f"\n{'='*60}")
        print(f"Processing: {issue['key']} — {issue['summary']}")
        print(f"{'='*60}")

        initial_state = {
            "issue_key": issue["key"],
            "summary": issue["summary"],
            "description": issue.get("description", ""),
            "stacktrace": _extract_stacktrace(issue),
            "retry_count": 0,
            "status": "RUNNING",
        }

        try:
            result = graph.invoke(initial_state)
            status = result.get("status", "DONE")
            detail = result.get("pr_url") or result.get("error", "")
            print(f"\n[main] Result: {status} — {detail}")
        except Exception as exc:
            print(f"\n[main] FAILED for {issue['key']}: {exc}")


if __name__ == "__main__":
    main()

import os
from pathlib import Path
from typing import Any

from git import Repo
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from agents import fix_generator, issue_analyst, pr_creator, test_runner
from config import settings

MAX_RETRIES = 3


class AgentState(TypedDict, total=False):
    # Input
    issue_key: str
    summary: str
    description: str
    stacktrace: str

    # Populated by agents
    similar_issues: list[dict]
    repo_path: str
    relevant_files: list[str]
    fix_description: str
    test_result: dict
    pr_url: str

    # Control flow
    retry_count: int
    status: str
    error: str


# ---------------------------------------------------------------------------
# Node: clone_repo
# ---------------------------------------------------------------------------

def clone_repo(state: AgentState) -> dict[str, Any]:
    issue_key = state["issue_key"]
    target = Path(settings.workspace_dir) / issue_key
    branch = f"fix/ai-{issue_key}"

    if target.exists():
        print(f"[clone_repo] Repo already exists at {target}, skipping clone")
        repo = Repo(str(target))
    else:
        print(f"[clone_repo] Cloning {settings.repo_url} → {target}")
        target.mkdir(parents=True, exist_ok=True)
        repo = Repo.clone_from(settings.repo_url, str(target))

    # Create or checkout fix branch
    existing_branches = [b.name for b in repo.branches]
    if branch in existing_branches:
        repo.git.checkout(branch)
    else:
        repo.git.checkout("-b", branch)

    print(f"[clone_repo] On branch {branch}")
    return {"repo_path": str(target)}


# ---------------------------------------------------------------------------
# Node wrappers
# ---------------------------------------------------------------------------

def node_issue_analyst(state: AgentState) -> dict[str, Any]:
    return issue_analyst.run(state)


def node_fix_generator(state: AgentState) -> dict[str, Any]:
    return fix_generator.run(state)


def node_test_runner(state: AgentState) -> dict[str, Any]:
    return test_runner.run(state)


def node_pr_creator(state: AgentState) -> dict[str, Any]:
    return pr_creator.run(state)


# ---------------------------------------------------------------------------
# Conditional edge after test_runner
# ---------------------------------------------------------------------------

def route_after_tests(state: AgentState) -> str:
    test_result = state.get("test_result", {})
    retry_count = state.get("retry_count", 0)

    if test_result.get("passed"):
        return "pr_creator"
    if retry_count < MAX_RETRIES:
        print(f"[orchestrator] Tests failed — retrying fix (attempt {retry_count + 1}/{MAX_RETRIES})")
        return "fix_generator"
    print("[orchestrator] Max retries reached — marking as FAILED")
    return END


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("clone_repo", clone_repo)
    graph.add_node("issue_analyst", node_issue_analyst)
    graph.add_node("fix_generator", node_fix_generator)
    graph.add_node("test_runner", node_test_runner)
    graph.add_node("pr_creator", node_pr_creator)

    graph.set_entry_point("clone_repo")

    graph.add_edge("clone_repo", "issue_analyst")
    graph.add_edge("issue_analyst", "fix_generator")
    graph.add_edge("fix_generator", "test_runner")

    graph.add_conditional_edges(
        "test_runner",
        route_after_tests,
        {
            "fix_generator": "fix_generator",
            "pr_creator": "pr_creator",
            END: END,
        },
    )
    graph.add_edge("pr_creator", END)

    return graph.compile()

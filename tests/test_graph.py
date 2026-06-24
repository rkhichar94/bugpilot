from unittest.mock import MagicMock, patch

import pytest

from graph.orchestrator import AgentState, build_graph, route_after_tests


# ---------------------------------------------------------------------------
# Unit tests for the routing function
# ---------------------------------------------------------------------------

def test_route_passes_to_pr_creator():
    state = {"test_result": {"passed": True}, "retry_count": 1}
    assert route_after_tests(state) == "pr_creator"


def test_route_retries_on_failure_below_max():
    state = {"test_result": {"passed": False}, "retry_count": 1}
    assert route_after_tests(state) == "fix_generator"


def test_route_ends_on_max_retries():
    from langgraph.graph import END
    state = {"test_result": {"passed": False}, "retry_count": 3}
    assert route_after_tests(state) == END


# ---------------------------------------------------------------------------
# Integration-style smoke test (all external calls mocked)
# ---------------------------------------------------------------------------

@patch("graph.orchestrator.pr_creator.run")
@patch("graph.orchestrator.test_runner.run")
@patch("graph.orchestrator.fix_generator.run")
@patch("graph.orchestrator.issue_analyst.run")
@patch("graph.orchestrator.Repo")
def test_graph_happy_path(
    mock_repo_cls,
    mock_analyst,
    mock_fix,
    mock_tests,
    mock_pr,
    tmp_path,
):
    # Patch workspace so clone_repo writes to tmp_path
    with patch("graph.orchestrator.settings") as mock_settings:
        mock_settings.workspace_dir = str(tmp_path)
        mock_settings.repo_url = "https://github.com/test/repo"
        mock_settings.repo_default_branch = "main"

        # Mock GitPython Repo
        mock_repo = MagicMock()
        mock_repo.branches = []
        mock_repo_cls.return_value = mock_repo
        mock_repo_cls.clone_from.return_value = mock_repo

        # Agent stubs
        mock_analyst.return_value = {"similar_issues": []}
        mock_fix.return_value = {"fix_description": "Fixed NPE", "relevant_files": ["App.java"]}
        mock_tests.return_value = {
            "test_result": {"passed": True, "output": "BUILD SUCCESS", "failed_tests": []},
            "retry_count": 1,
        }
        mock_pr.return_value = {
            "pr_url": "https://github.com/test/repo/pull/1",
            "status": "AWAITING_APPROVAL",
        }

        graph = build_graph()
        result = graph.invoke(
            {
                "issue_key": "TEST-1",
                "summary": "NPE in UserService",
                "description": "java.lang.NullPointerException",
                "stacktrace": "",
                "retry_count": 0,
                "status": "RUNNING",
            }
        )

    assert result.get("pr_url") == "https://github.com/test/repo/pull/1"
    assert result.get("status") == "AWAITING_APPROVAL"
    mock_analyst.assert_called_once()
    mock_fix.assert_called_once()
    mock_tests.assert_called_once()
    mock_pr.assert_called_once()


@patch("graph.orchestrator.pr_creator.run")
@patch("graph.orchestrator.test_runner.run")
@patch("graph.orchestrator.fix_generator.run")
@patch("graph.orchestrator.issue_analyst.run")
@patch("graph.orchestrator.Repo")
def test_graph_retries_on_test_failure(
    mock_repo_cls,
    mock_analyst,
    mock_fix,
    mock_tests,
    mock_pr,
    tmp_path,
):
    with patch("graph.orchestrator.settings") as mock_settings:
        mock_settings.workspace_dir = str(tmp_path)
        mock_settings.repo_url = "https://github.com/test/repo"
        mock_settings.repo_default_branch = "main"

        mock_repo = MagicMock()
        mock_repo.branches = []
        mock_repo_cls.return_value = mock_repo
        mock_repo_cls.clone_from.return_value = mock_repo

        mock_analyst.return_value = {"similar_issues": []}
        mock_fix.return_value = {"fix_description": "Attempted fix", "relevant_files": []}

        # Fail 3 times → graph should reach END with FAILED status
        call_count = {"n": 0}

        def test_side_effect(state):
            call_count["n"] += 1
            return {
                "test_result": {"passed": False, "output": "BUILD FAILURE", "failed_tests": []},
                "retry_count": call_count["n"],
            }

        mock_tests.side_effect = test_side_effect

        graph = build_graph()
        result = graph.invoke(
            {
                "issue_key": "TEST-2",
                "summary": "Persistent failure",
                "description": "",
                "stacktrace": "",
                "retry_count": 0,
                "status": "RUNNING",
            }
        )

    assert call_count["n"] == 3
    assert mock_pr.call_count == 0

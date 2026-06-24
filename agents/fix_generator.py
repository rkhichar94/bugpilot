import json
from typing import Any

import anthropic

from config import settings
from tools.repo_tools import TOOL_DEFINITIONS, TOOL_DISPATCH

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


def _build_system_prompt(state: dict[str, Any]) -> str:
    similar_text = ""
    for s in state.get("similar_issues", []):
        similar_text += (
            f"- {s['issue_key']}: {s['summary']} "
            f"(resolution: {s.get('resolution', 'N/A')}, score: {s['score']})\n"
        )

    return f"""You are an expert Java software engineer resolving bugs in a Maven project.

## Bug Report
Issue: {state['issue_key']}
Summary: {state['summary']}
Description:
{state.get('description', 'N/A')}

Stacktrace:
{state.get('stacktrace', 'N/A')}

## Similar Past Issues (from vector search)
{similar_text or 'No similar issues found.'}

## Instructions
1. Use the available tools to explore the repository structure and read relevant files.
2. Identify the root cause of the bug.
3. Write the fix using write_file — make targeted, minimal changes.
4. After applying the fix, provide a concise explanation of what was changed and why.

Be precise. Do not rewrite entire files unless necessary.
"""


def run(state: dict[str, Any]) -> dict[str, Any]:
    repo_path = state["repo_path"]
    print(f"[fix_generator] Starting Claude tool-use loop for {state['issue_key']} ...")

    client = _get_client()
    messages: list[dict] = [
        {
            "role": "user",
            "content": (
                f"Please fix the bug described in the system prompt. "
                f"The repository is at: {repo_path}\n"
                f"Start by listing the Java files to understand the structure."
            ),
        }
    ]

    fix_description = ""
    relevant_files: list[str] = []
    max_iterations = 20

    for iteration in range(max_iterations):
        print(f"[fix_generator] Iteration {iteration + 1}/{max_iterations}")

        response = client.messages.create(
            model=settings.claude_model,
            max_tokens=4096,
            system=_build_system_prompt(state),
            tools=TOOL_DEFINITIONS,
            messages=messages,
        )

        # Collect assistant message
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            # Extract final text response as fix description
            for block in response.content:
                if hasattr(block, "text"):
                    fix_description = block.text
            print("[fix_generator] Claude finished — end_turn reached")
            break

        if response.stop_reason != "tool_use":
            print(f"[fix_generator] Unexpected stop_reason: {response.stop_reason}")
            break

        # Execute tool calls and collect results
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            tool_name = block.name
            tool_input = block.input
            print(f"[fix_generator] Tool call: {tool_name}({list(tool_input.keys())})")

            func = TOOL_DISPATCH.get(tool_name)
            if func is None:
                result_content = f"ERROR: Unknown tool '{tool_name}'"
            else:
                try:
                    result = func(**tool_input)
                    # Track which files were read or written
                    if tool_name in ("read_file", "write_file"):
                        rel = tool_input.get("relative_path", "")
                        if rel and rel not in relevant_files:
                            relevant_files.append(rel)
                    result_content = json.dumps(result) if isinstance(result, list) else str(result)
                except Exception as exc:
                    result_content = f"ERROR: {exc}"

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_content,
                }
            )

        messages.append({"role": "user", "content": tool_results})
    else:
        print("[fix_generator] Warning: max iterations reached without end_turn")

    return {
        "fix_description": fix_description,
        "relevant_files": relevant_files,
    }

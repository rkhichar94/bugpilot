from typing import Any

from rag.retriever import upsert, search

# Keys read from state
_IN = ("issue_key", "summary", "description", "stacktrace")


def run(state: dict[str, Any]) -> dict[str, Any]:
    issue_key = state["issue_key"]
    summary = state.get("summary", "")
    description = state.get("description", "")
    stacktrace = state.get("stacktrace", "")

    combined_text = f"{summary}\n\n{description}\n\n{stacktrace}".strip()

    print(f"[issue_analyst] Searching for similar issues to {issue_key} ...")
    similar = search(combined_text, top_k=3)
    print(f"[issue_analyst] Found {len(similar)} similar issue(s)")

    # Upsert current issue so future runs can reference it
    upsert(
        issue_key=issue_key,
        text=combined_text,
        metadata={"summary": summary, "resolution": ""},
    )

    return {"similar_issues": similar}

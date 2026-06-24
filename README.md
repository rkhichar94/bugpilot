# Multi-Agent AI Bug Resolver

## Overview

Multi-Agent AI Bug Resolver is an autonomous pipeline that fetches open bug tickets from Jira,
uses Retrieval-Augmented Generation (RAG) to find similar past issues, generates code fixes by
letting Claude explore and edit the repository via tool use, runs Maven tests to validate the
fix, and opens a GitHub Pull Request for human approval — all orchestrated as a LangGraph state
machine.

---

## Architecture

```
                          ┌─────────────────────────────────────────────────┐
                          │              LangGraph State Machine             │
                          │                                                  │
  Jira Bug Issue          │                                                  │
  ──────────────►  [1. clone_repo]                                          │
                          │       │                                          │
                          │       ▼                                          │
                          │  [2. issue_analyst]  ◄──► Qdrant Vector DB      │
                          │       │               (embed + RAG similarity)   │
                          │       ▼                                          │
                          │  [3. fix_generator]  ◄──► Claude (tool-use loop)│
                          │       │               read_file / write_file /   │
                          │       │               list_files / search_files  │
                          │       ▼                                          │
                          │  [4. test_runner]  → mvn test (subprocess)      │
                          │       │                                          │
                          │    passed?                                       │
                          │    ├── YES ──────► [5. pr_creator] ─► GitHub PR │
                          │    │                                    │        │
                          │    │                               Slack notify  │
                          │    └── NO (retry < 3) ──► back to fix_generator │
                          │                                                  │
                          │    NO (retry ≥ 3) ──────────────────► END FAILED│
                          └─────────────────────────────────────────────────┘
```

---

## Tech Stack

| Concern                | Library / Tool                              |
|------------------------|---------------------------------------------|
| Agent orchestration    | LangGraph + LangChain                       |
| LLM                    | Anthropic Claude (`claude-sonnet-4-6`)      |
| Vector DB              | Qdrant (local Docker container)             |
| Embeddings             | `sentence-transformers` `all-MiniLM-L6-v2` |
| Jira integration       | Atlassian Remote MCP Server + Anthropic SDK |
| GitHub integration     | `PyGithub` + `GitPython`                    |
| Test execution         | `subprocess` → `mvn test`                   |
| Observability          | LangSmith (env-var gated)                   |
| Config                 | `pydantic-settings` + `.env`                |
| Entry point            | Plain Python CLI (`python main.py`)         |

---

## AI Concepts Used

**Retrieval-Augmented Generation (RAG)**
Each bug report is embedded into a 384-dimensional vector using `all-MiniLM-L6-v2` and stored
in Qdrant. When a new bug arrives, cosine similarity search surfaces the top-3 most similar
past issues so Claude can reference known resolutions — grounding the fix in prior engineering
knowledge rather than hallucination.

**Multi-Agent Orchestration**
The pipeline is split into four specialised agents (analyst, fix generator, test runner, PR
creator), each with a single responsibility. Separating concerns means each agent can be
tested, replaced, or scaled independently — a key property of production agentic systems.

**LangGraph State Machine**
LangGraph models the pipeline as a directed graph of nodes and edges over a shared
`AgentState` TypedDict. Conditional edges implement the retry loop: if tests fail and the
retry count is below the threshold, the graph routes back to the fix generator automatically
without any imperative control flow in application code.

**Claude Tool-Use Loop**
The fix generator runs an agentic loop where Claude is given four tools (`read_file`,
`write_file`, `list_files`, `search_in_files`). Claude autonomously decides which files to
read, locates the bug, writes the patch, and signals completion via `end_turn` — the
application code simply executes whatever tool calls Claude emits and feeds results back.

**Vector Similarity Search**
Qdrant stores issue embeddings with cosine distance. At query time the system finds semantically
similar issues even when the exact keywords differ — for example "connection pool exhaustion"
matches "too many open database handles" because the embedding space captures meaning, not
surface form.

---

## Setup

### Prerequisites

- Python 3.11+
- Maven (`mvn`) on your `PATH`
- Docker (for Qdrant)
- An Atlassian OAuth access token (for the Remote MCP Server at `https://mcp.atlassian.com`)
- A GitHub personal access token with `repo` scope
- An Anthropic API key

### Step-by-step

```bash
# 1. Clone this repository
git clone https://github.com/yourusername/multi-agent-bug-resolver
cd multi-agent-bug-resolver

# 2. Create your .env file
cp .env.example .env
# Edit .env and fill in all required values

# 3. Start Qdrant locally
docker run -d -p 6333:6333 --name qdrant qdrant/qdrant

# 4. Install Python dependencies
pip install -r requirements.txt

# 5. (Optional) Enable LangSmith tracing
#    Set LANGCHAIN_TRACING_V2=true and LANGCHAIN_API_KEY in .env

# 6. Run on all open bugs
python main.py

# 7. Or run on a single issue
python main.py --issue PROJ-123
```

---

## How It Works

Here is a walkthrough of one issue being processed end-to-end.

**Input:** Jira ticket `PROJ-456` — *"NullPointerException in OrderService when cart is empty"*

1. **clone_repo** — The repo is cloned into `/tmp/bug-resolver-workspace/PROJ-456/` and a
   new branch `fix/ai-PROJ-456` is created.

2. **issue_analyst** — The summary, description, and stacktrace are concatenated and embedded
   into a 384-dim vector. Qdrant is searched for the 3 closest past issues. The current issue
   is also upserted so future runs can reference it. Example result:
   ```
   [PROJ-201] NullPointerException in CartService (score: 0.91)
   [PROJ-334] NPE when user has no active session (score: 0.84)
   ```

3. **fix_generator** — Claude receives a system prompt containing the bug report and similar
   issue resolutions. It then autonomously:
   - Calls `list_files(extension=".java")` to see the project structure
   - Calls `read_file("src/main/java/OrderService.java")` to find the bug
   - Calls `write_file(...)` with a null-check guard added before the empty-cart path
   - Returns a text description: *"Added null check for `cart.getItems()` before iterating..."*

4. **test_runner** — Runs `mvn test -q` via subprocess. If `BUILD SUCCESS` is detected, the
   state moves forward. If `BUILD FAILURE`, `retry_count` increments and the graph loops back
   to `fix_generator` with the failure output included in the next prompt.

5. **pr_creator** — All changes are staged and committed as
   `fix(ai): resolve PROJ-456 — NullPointerException in OrderService when cart`. The branch is
   pushed and a GitHub PR is created with a body that includes the fix description, test
   results, and referenced similar issues. If configured, a Slack message is sent with the PR
   link.

---

## Project Structure

```
multi-agent-bug-resolver/
├── main.py                      # CLI entry point
├── config.py                    # pydantic-settings config
├── .env.example                 # template env file
├── requirements.txt
├── README.md
│
├── graph/
│   └── orchestrator.py          # LangGraph StateGraph definition
│
├── agents/
│   ├── __init__.py
│   ├── issue_analyst.py         # Step 1: embed + RAG similarity search
│   ├── fix_generator.py         # Step 2: Claude tool-use loop → patch
│   ├── test_runner.py           # Step 3: mvn test via subprocess
│   └── pr_creator.py            # Step 4: commit + push + open PR
│
├── rag/
│   ├── __init__.py
│   ├── embedder.py              # sentence-transformers wrapper
│   └── retriever.py             # Qdrant upsert + similarity search
│
├── tools/
│   ├── __init__.py
│   ├── repo_tools.py            # read_file, write_file, list_files, search_in_files
│   └── jira_tools.py            # fetch_issue, update_issue_status
│
└── tests/
    ├── test_embedder.py
    ├── test_repo_tools.py
    └── test_graph.py            # mock-based graph flow tests
```

---

## Running Tests

```bash
pytest tests/ -v
```

The test suite uses `unittest.mock` to stub all external calls (Qdrant, Claude, GitHub, Jira,
Git) so tests run offline with no credentials required.

---

## Environment Variables Reference

| Variable                | Required | Description                                     |
|-------------------------|----------|-------------------------------------------------|
| `ATLASSIAN_MCP_TOKEN`   | Yes      | Atlassian OAuth access token for the Remote MCP Server |
| `JIRA_PROJECT_KEY`      | Yes      | e.g. `PROJ`                                     |
| `JIRA_JQL_FILTER`       | No       | Defaults to `issuetype=Bug AND status=Open`     |
| `GITHUB_TOKEN`          | Yes      | Personal access token with `repo` scope         |
| `REPO_URL`              | Yes      | Full HTTPS URL of the target repository         |
| `REPO_DEFAULT_BRANCH`   | No       | Defaults to `main`                              |
| `ANTHROPIC_API_KEY`     | Yes      | Anthropic API key                               |
| `CLAUDE_MODEL`          | No       | Defaults to `claude-sonnet-4-6`                 |
| `QDRANT_URL`            | No       | Defaults to `http://localhost:6333`             |
| `QDRANT_COLLECTION`     | No       | Defaults to `bug_issues`                        |
| `LANGCHAIN_TRACING_V2`  | No       | Set `true` to enable LangSmith                  |
| `LANGCHAIN_API_KEY`     | No       | Required if tracing is enabled                  |
| `SLACK_WEBHOOK_URL`     | No       | Incoming webhook for PR notifications           |
| `WORKSPACE_DIR`         | No       | Defaults to `/tmp/bug-resolver-workspace`       |

---

## Future Enhancements

- **Neo4j code graph** — Index the repository as a property graph (files → classes → methods →
  calls) so the fix generator can navigate the call stack semantically rather than reading
  files linearly.
- **Multi-language support** — Abstract `test_runner` behind a strategy interface; add Gradle,
  pytest, and npm test runners.
- **Web UI** — A React dashboard showing pipeline status per issue, diff preview, and a
  one-click approve/reject for each AI-generated PR.
- **LLM judge** — Add a post-fix review step where a second Claude call evaluates the patch
  for correctness, security, and style before tests are even run.
- **Incremental embedding** — Sync the entire closed-issues history from Jira on first run to
  pre-populate the Qdrant collection with a rich base of resolved bugs.

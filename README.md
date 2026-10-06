# Multi-agent review analysis prototype

This Week 5 prototype explores the dissertation topic **Development of a Multitask Transformer-Based Model and Web System for Joint Sentiment Analysis and AI-Generated Review Provenance Classification: A Controlled Mixed-Domain Study**.

It demonstrates a typed-message pipeline of seven roles: a coordinator plus six specialists. Given one review, a preprocessing specialist first produces tokens and text features; the other specialists inspect domain context, sentiment, provenance cues, and evidence; a synthesis agent combines their reports. This is a deterministic orchestration prototype, not a trained transformer or a validated AI-authorship detector. The distinction matters: provenance is reported as a heuristic risk estimate with evidence and a caveat, not as proof of authorship.

## Run

Requires Python 3.10+ and no third-party packages or API keys. Check the interpreter first; older system `python3` installations are common:

```bash
python3 --version
python3.12 -m review_agents --text "The delivery was quick, but the battery failed after one day." --domain electronics --log-dir runs
```

Use any Python 3.10+ interpreter for these commands; `python3.12` is shown as an example. The launcher prints a clear error when run with an older Python version.

The saved Week 5 demonstration trace is linked from [the demo scenario](docs/scenarios.md). It records agent invocations separately from LLM/tool calls, then calculates the 40% threshold from actual tool and LLM calls only.

Supported domains: `product`, `electronics`, `hotel`, `movie`, `restaurant`, `mixed`. Use `--json` for a machine-readable final result, `--log-dir runs` to save JSONL agent/tool events, or `--show-trace` to print the agent exchange.

You can also run interactively:

Use any Python 3.10+ interpreter; `python3.12` below is an example.

```bash
python3.12 -m review_agents
```

## Architecture

See [the architecture and week-by-week scope](docs/architecture.md), [agent contracts](docs/agent-specification.md), and [planned evaluation scenarios](docs/scenarios.md).

## What the prototype demonstrates

- Six non-overlapping specialist roles and one orchestration-only coordinator. The coordinator routes the raw review to preprocessing first, then routes the preprocessor JSON output to the analysis agents.
- Structured JSON messages passed between agents; the prototype validates required message-envelope fields and that payloads are JSON objects. Agent-specific payload fields follow the documented contracts but are not checked against a full schema.
- Direct interaction: the evidence agent consumes sentiment and provenance reports; synthesis consumes context, task, and evidence reports.
- Explicit per-run state, a maximum of eight agent steps, bounded retries for message validation, and JSONL event logging.
- A measured workload summary that separately records every specialist invocation and counts tool/LLM calls for the 40% threshold. The demo trace reports each agent's share and whether the largest share stays under the rubric threshold.
- Local domain lexicon and a Python-based text-feature tool as two explicit local information/tools.
- Transparent sentiment and provenance evidence, uncertainty language, and a reminder not to use provenance estimates as an authorship verdict.

## Limitations and next stage

No transformer is loaded or trained. The lexicon scores and provenance cues are placeholders for architecture validation; they have not been calibrated on a controlled mixed-domain corpus. Week 10 work should add the shared multitask model, curated data and split protocol, model/domain tools, stronger evaluation, error recovery, and tests. The architecture document identifies planned integrations without claiming they are already implemented.

## Repository layout

```text
review_agents/       Python package and agent pipeline
data/domain_lexicons.json  Small transparent prototype lexicon
docs/                Architecture, contracts, planned scenarios
runs/                Optional runtime JSONL logs (created by --log-dir)
```
# multi-agent-system

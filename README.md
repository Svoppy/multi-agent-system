# Multi-agent review analysis system

This project implements a review-analysis system for the dissertation **Development of a Multitask Transformer-Based Model and Web System for Joint Sentiment Analysis and AI-Generated Review Provenance Classification: A Controlled Mixed-Domain Study**.

The current prototype has a coordinator and **nine distinct specialists**: request validation, preprocessing, language, domain context, sentiment, provenance, evidence checking, reliability gating, and synthesis. It runs in CLI or a small local web form. It does not yet load a trained Transformer: current task estimates are transparent heuristics, clearly identified in the output.

## Requirements and launch

Python 3.10+; no third-party packages, network access, or API keys required. Check the active interpreter first:

```bash
python3 --version
python3.12 -m review_agents --text "The room was clean and comfortable." --domain hotel --json --log-dir runs
```

Use any installed Python 3.10+ interpreter; `python3.12` is an example. Older Python versions receive a clear compatibility message.

Start the local web UI:

```bash
python3.12 -m review_agents --web --host 127.0.0.1 --port 8000 --log-dir runs
```

Open `http://127.0.0.1:8000`. The server binds to localhost by default. The UI validates requests, abstains on unsupported languages, escapes submitted text, displays the reliability decision, and writes per-run JSONL traces.

## CLI options

- `--text` and `--domain` analyze one review; omit `--text` for interactive mode.
- `--json` prints a structured report.
- `--show-trace` prints the full agent/tool exchange.
- `--log-dir runs` saves success or failure events as JSONL.
- `--web [--host HOST] [--port PORT]` serves the local form.
- Run test scenarios with `python3.12 -m unittest discover -s tests -v`.

## Verification

The test suite covers English analysis and interaction, unsupported-language abstention, neutral domain terms, unknown-domain fallback, invalid input, bounded retry, deadline enforcement, and the web request handler. See [test scenarios and the saved demo trace](docs/scenarios.md). The trace and workload summary are regenerated from the actual pipeline.

JSONL traces include the submitted review text inside inter-agent messages. Use synthetic or approved text for demonstrations, and apply an appropriate retention/access policy before logging real user reviews.

## Design and research materials

- [System architecture](docs/architecture.md)
- [Agent specification](docs/agent-specification.md)
- [Project report](docs/report.md)
- [Research article protocol draft](docs/article-draft.md)
- [Research plan and evaluation protocol](docs/implementation-plan.md)

## Limitations

No Transformer is trained or loaded, no controlled corpus has been assembled, and the heuristic outputs are not research findings. The language classifier is a lightweight gate; the current domain lexicon and provenance cues have not been calibrated. See the report and article draft for the planned data construction, baselines, metrics, ethics and limitations. Do not use provenance scores as proof of authorship.

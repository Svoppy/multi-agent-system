"""Fixed-flow coordinator; it routes work and owns state, never classifies text."""
from pathlib import Path
from typing import Any
from uuid import uuid4
import json
import time

from .agents import (ContextAgent, EvidenceAgent, PreprocessingAgent, ProvenanceAgent,
                     SentimentAgent, SynthesisAgent)
from .messages import AgentMessage, RunState
from .tools import log_event


class Orchestrator:
    STEP_LIMIT = 8
    RETRIES = 1

    def __init__(self):
        self.preprocessing = PreprocessingAgent()
        self.context = ContextAgent()
        self.sentiment = SentimentAgent()
        self.provenance = ProvenanceAgent()
        self.evidence = EvidenceAgent()
        self.synthesis = SynthesisAgent()

    def run(self, review: str, domain: str = "mixed") -> tuple[dict[str, Any], RunState]:
        if not review.strip():
            raise ValueError("Review text cannot be empty")
        if len(review) > 5000:
            raise ValueError("Review is too long (maximum 5000 characters)")
        run_id = str(uuid4())
        state = RunState(run_id, review, domain, step_limit=self.STEP_LIMIT)
        self._invoke(state, self.preprocessing, {"review": review})
        common = state.reports["preprocessing_agent"]
        agents = [self.context, self.sentiment, self.provenance]
        for agent in agents:
            self._invoke(state, agent, common)
        # Explicit hand-off: evidence consumes outputs produced by two independent agents.
        evidence_input = {**common, "sentiment": state.reports["sentiment_agent"],
                          "provenance": state.reports["provenance_agent"]}
        self._invoke(state, self.evidence, evidence_input)
        synthesis_input = {**evidence_input, "context": state.reports["context_agent"],
                           "evidence": state.reports["evidence_agent"]}
        self._invoke(state, self.synthesis, synthesis_input)
        workload = workload_summary(state.events)
        state.reports["synthesis_agent"]["workload"] = workload
        state.events.append({"event": "run_complete", "run_id": run_id, "steps": state.steps,
                             "workload": workload})
        return state.reports["synthesis_agent"], state

    def _invoke(self, state: RunState, agent, payload: dict[str, Any]) -> None:
        if state.steps >= state.step_limit:
            raise RuntimeError("Step limit reached; run stopped to prevent a loop")
        state.steps += 1
        message = AgentMessage.create(state.run_id, "orchestrator", agent.name, "analysis_request", payload)
        started = time.perf_counter()
        for attempt in range(self.RETRIES + 1):
            try:
                message.validate()
                result = agent.execute(state, message.payload)
                response = AgentMessage.create(state.run_id, agent.name, "orchestrator", "analysis_result", result)
                response.validate()
                state.reports[agent.name] = response.payload
                log_event(state, {"event": "agent_call", "run_id": state.run_id, "agent": agent.name,
                                  "step": state.steps, "attempt": attempt + 1, "status": "complete",
                                  "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
                                  "input_message": message.to_dict(), "output_message": response.to_dict()})
                return
            except (ValueError, KeyError, OSError, TypeError) as exc:
                log_event(state, {"event": "agent_call", "run_id": state.run_id, "agent": agent.name,
                                  "step": state.steps, "attempt": attempt + 1, "status": "error",
                                  "error_type": type(exc).__name__, "error": str(exc)})
                if attempt >= self.RETRIES:
                    raise RuntimeError(f"Agent {agent.name} failed: {exc}") from exc


def write_jsonl(state: RunState, log_dir: str) -> Path:
    directory = Path(log_dir)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"{state.run_id}.jsonl"
    with target.open("w", encoding="utf-8") as handle:
        for event in state.events:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    return target


def workload_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Measure LLM/tool call shares; report agent invocations separately."""
    agent_invocations: dict[str, int] = {}
    tool_calls: dict[str, int] = {}
    llm_calls: dict[str, int] = {}
    for event in events:
        if event.get("event") == "agent_call":
            name = event.get("agent", "unknown")
            agent_invocations[name] = agent_invocations.get(name, 0) + 1
        elif event.get("event") == "tool_call":
            name = event.get("agent", "unknown")
            tool_calls[name] = tool_calls.get(name, 0) + 1
        elif event.get("event") == "llm_call":
            name = event.get("agent", "unknown")
            llm_calls[name] = llm_calls.get(name, 0) + 1
    names = sorted(set(agent_invocations) | set(tool_calls) | set(llm_calls))
    total = sum(tool_calls.values()) + sum(llm_calls.values())
    per_agent = {}
    for name in names:
        invocations = agent_invocations.get(name, 0)
        tools = tool_calls.get(name, 0)
        llms = llm_calls.get(name, 0)
        counted = tools + llms
        per_agent[name] = {"agent_invocations": invocations, "tool_calls": tools,
                           "llm_calls": llms, "counted_calls": counted,
                           "share_percent": round(100 * counted / total, 1) if total else 0.0}
    maximum_exact = max((item["counted_calls"] / total for item in per_agent.values()), default=0.0) if total else 0.0
    return {"counting_method": "tool_calls_plus_llm_calls; agent invocations reported separately; orchestrator routing excluded",
            "total_llm_tool_calls": total, "per_agent": per_agent,
            "max_share_percent": round(maximum_exact * 100, 1),
            "under_40_percent": maximum_exact <= 0.40}

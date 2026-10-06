"""Local, inspectable information sources used by prototype agents."""
import json
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
LEXICON_PATH = ROOT / "data" / "domain_lexicons.json"


def _run_tool(state, agent: str, tool: str, inputs: dict[str, Any], operation):
    started = time.perf_counter()
    try:
        output = operation()
    except Exception as exc:
        state.events.append({"event": "tool_call", "run_id": state.run_id, "agent": agent,
                             "tool": tool, "status": "error", "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
                             "inputs": inputs, "error_type": type(exc).__name__, "error": str(exc)})
        raise
    state.events.append({"event": "tool_call", "run_id": state.run_id, "agent": agent,
                         "tool": tool, "status": "complete", "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
                         "inputs": inputs, "output_summary": _summary(output)})
    return output


def _summary(value):
    if isinstance(value, dict) and "domains" in value:
        return {"version": value.get("version"), "domains": sorted(value["domains"])}
    if isinstance(value, dict) and "tokens" in value:
        return {key: val for key, val in value.items() if key != "tokens"}
    if isinstance(value, dict):
        return {key: val for key, val in value.items() if key not in {"positive_evidence", "negative_evidence"}}
    return value


def load_lexicons(state, agent: str) -> dict[str, Any]:
    def load():
        with LEXICON_PATH.open(encoding="utf-8") as handle:
            return json.load(handle)
    return _run_tool(state, agent, "load_domain_lexicon", {"source": "data/domain_lexicons.json"}, load)


def tokenize(text: str) -> list[str]:
    """Tool 1: deterministic token and punctuation feature extraction."""
    return re.findall(r"[\w']+|[!?.,;:]+", text.lower(), flags=re.UNICODE)


def text_features(text: str, state, agent: str) -> dict[str, Any]:
    def extract():
        tokens = tokenize(text)
        words = [item for item in tokens if re.search(r"\w", item)]
        sentences = max(1, len(re.findall(r"[.!?]+", text)))
        return {"tokens": tokens, "word_count": len(words), "sentence_count": sentences,
                "avg_word_length": round(sum(map(len, words)) / max(1, len(words)), 2),
                "exclamation_count": text.count("!"), "comma_count": text.count(",")}
    return _run_tool(state, agent, "text_features", {"input_chars": len(text)}, extract)


def provenance_cues(tokens: list[str], features: dict[str, Any], state, agent: str) -> dict[str, Any]:
    cues = {"overall", "moreover", "furthermore", "therefore", "delve", "seamless", "exceptional"}
    def inspect():
        words = [token for token in tokens if any(char.isalnum() for char in token)]
        cue_hits = sorted(set(words) & cues)
        repeated = [word for word, count in Counter(words).items() if count >= 3 and len(word) > 3]
        reasons = []
        if cue_hits:
            reasons.append("generic_polished_vocabulary")
        if features["avg_word_length"] > 6.0:
            reasons.append("long_average_word_length")
        if features["sentence_count"] >= 3 and features["comma_count"] >= 3:
            reasons.append("regular_structured_prose")
        if repeated:
            reasons.append("repeated_content_words")
        strength = len(reasons)
        return {"label": "higher_ai_style_cue_estimate" if strength >= 2 else "lower_or_uncertain_ai_style_cue_estimate",
                "cue_count": strength, "cue_categories": reasons, "matched_cue_terms": cue_hits,
                "repeated_terms": repeated,
                "confidence": round(min(0.75, 0.4 + strength * 0.1), 2) if strength else 0.35}
    return _run_tool(state, agent, "inspect_provenance_cues",
                     {"token_count": len(tokens), "feature_names": sorted(features)}, inspect)


def check_evidence(tokens: list[str], sentiment: dict[str, Any], provenance: dict[str, Any], state, agent: str) -> dict[str, Any]:
    def check():
        source_tokens = set(tokens)
        cited = [item["term"] for group in (sentiment["positive_evidence"], sentiment["negative_evidence"]) for item in group]
        unsupported_sentiment = sorted(set(cited) - source_tokens)
        cue_terms = provenance["matched_cue_terms"] + provenance["repeated_terms"]
        unsupported_provenance = sorted(set(cue_terms) - source_tokens)
        return {"grounded": not unsupported_sentiment and not unsupported_provenance,
                "unsupported_sentiment_terms": unsupported_sentiment,
                "unsupported_provenance_terms": unsupported_provenance,
                "checks": ["sentiment_terms_in_source", "provenance_terms_in_source"],
                "upstream_agents": ["sentiment_agent", "provenance_agent"]}
    return _run_tool(state, agent, "check_evidence_against_source",
                     {"token_count": len(tokens), "upstream_agents": ["sentiment_agent", "provenance_agent"]}, check)


def log_event(state, event: dict[str, Any]) -> None:
    state.events.append(event)

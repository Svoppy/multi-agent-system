"""Specialist agents, each with one distinct responsibility."""
from typing import Any

from .messages import AgentMessage, RunState
from .tools import (check_evidence, detect_language, load_lexicons,
                    provenance_cues, reliability_gate, text_features,
                    validate_request)


class BaseAgent:
    name = "base"
    tool_count = 0
    required_inputs: tuple[str, ...] = ()
    required_outputs: tuple[str, ...] = ()

    def execute(self, state: RunState, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def validate_input(self, payload: dict[str, Any]) -> None:
        missing = [key for key in self.required_inputs if key not in payload]
        if missing:
            raise ValueError(f"{self.name} input is missing fields: {', '.join(missing)}")

    def validate_output(self, payload: dict[str, Any]) -> None:
        missing = [key for key in self.required_outputs if key not in payload]
        if missing:
            raise ValueError(f"{self.name} output is missing fields: {', '.join(missing)}")


class RequestValidationAgent(BaseAgent):
    """Rejects empty, oversized, or malformed request metadata before analysis."""
    name = "request_validation_agent"
    tool_count = 1
    required_inputs = ("review", "domain")
    required_outputs = ("valid", "errors")

    def execute(self, state, payload):
        return validate_request(payload.get("review"), payload.get("domain"), state, self.name)


class PreprocessingAgent(BaseAgent):
    """Converts a raw review into tokens and simple text features."""
    name = "preprocessing_agent"
    tool_count = 1
    required_inputs = ("review",)
    required_outputs = ("tokens", "features")

    def execute(self, state, payload):
        features = text_features(payload["review"], state, self.name)
        return {"tokens": features["tokens"], "features": features}


class LanguageAgent(BaseAgent):
    """Identifies whether the English-only prototype tools can assess the text."""
    name = "language_agent"
    tool_count = 1
    required_inputs = ("tokens",)
    required_outputs = ("language", "confidence", "supported_for_current_lexicon", "method")

    def execute(self, state, payload):
        return detect_language(payload["tokens"], state, self.name)


class ContextAgent(BaseAgent):
    """Identifies domain terms; does not predict either target label."""
    name = "context_agent"
    tool_count = 1
    required_inputs = ("tokens",)
    required_outputs = ("domain", "matched_domain_terms", "domain_support", "lexicon_version")

    def execute(self, state, payload):
        lexicons = load_lexicons(state, self.name)
        domain_terms = lexicons["domains"].get(state.domain, {})
        tokens = payload["tokens"]
        # context_terms is optional so older lexicon entries remain compatible.
        terms = set(domain_terms.get("context_terms", []))
        terms.update(word for key in ("positive", "negative")
                     for word in domain_terms.get(key, {}))
        terms = sorted(word for word in terms if word in tokens)
        return {"domain": state.domain, "matched_domain_terms": terms,
                "domain_support": "known" if state.domain in lexicons["domains"] else "general_only",
                "lexicon_version": lexicons["version"]}


class SentimentAgent(BaseAgent):
    """Produces a transparent, lexicon-based sentiment estimate."""
    name = "sentiment_agent"
    tool_count = 1
    required_inputs = ("tokens", "language")
    required_outputs = ("label", "score", "confidence", "positive_evidence", "negative_evidence", "method")

    def execute(self, state, payload):
        lexicons = load_lexicons(state, self.name)["domains"]
        tokens = payload["tokens"]
        language = payload["language"]
        if not language["supported_for_current_lexicon"]:
            return {"label": "not_assessed", "score": None, "confidence": 0.0,
                    "positive_evidence": [], "negative_evidence": [],
                    "method": "abstained_unsupported_language", "validated_model": False}
        positive, negative = dict(lexicons["general"]["positive"]), dict(lexicons["general"]["negative"])
        domain = lexicons.get(state.domain, {})
        for word, score in domain.get("positive", {}).items():
            positive[word] = positive.get(word, 0) + score
        for word, score in domain.get("negative", {}).items():
            negative[word] = negative.get(word, 0) + score
        negators = {"not", "never", "no", "isn't", "wasn't", "didn't", "hardly"}
        pos_hits, neg_hits = [], []
        for i, token in enumerate(tokens):
            if token in positive or token in negative:
                score = positive.get(token, 0) - negative.get(token, 0)
                if any(t in negators for t in tokens[max(0, i - 3):i]):
                    score *= -1
                (pos_hits if score > 0 else neg_hits).append({"term": token, "score": round(abs(score), 2)})
        score = sum(x["score"] for x in pos_hits) - sum(x["score"] for x in neg_hits)
        label = "positive" if score > 0.25 else "negative" if score < -0.25 else "neutral_or_mixed"
        evidence = pos_hits + neg_hits
        confidence = min(0.9, 0.5 + abs(score) * 0.08) if evidence else 0.35
        return {"label": label, "score": round(score, 2), "confidence": round(confidence, 2),
                "positive_evidence": pos_hits, "negative_evidence": neg_hits,
                "method": "transparent_prototype_lexicon", "validated_model": False}


class ProvenanceAgent(BaseAgent):
    """Estimates textual AI-style cues, explicitly not factual authorship."""
    name = "provenance_agent"
    tool_count = 1
    required_inputs = ("tokens", "features", "language")
    required_outputs = ("label", "cue_count", "cue_categories", "matched_cue_terms", "confidence", "method", "authorship_conclusion")

    def execute(self, state, payload):
        language = payload["language"]
        if not language["supported_for_current_lexicon"]:
            report = {"label": "not_assessed", "cue_count": 0, "cue_categories": [],
                      "matched_cue_terms": [], "repeated_terms": [], "confidence": 0.0,
                      "method": "abstained_unsupported_language"}
        else:
            report = provenance_cues(payload["tokens"], payload["features"], state, self.name)
        return {**report,
                "method": report.get("method", "unvalidated_heuristics"), "authorship_conclusion": False}


class EvidenceAgent(BaseAgent):
    """Checks that specialist claims are grounded in the submitted text."""
    name = "evidence_agent"
    tool_count = 1
    required_inputs = ("tokens", "sentiment", "provenance")
    required_outputs = ("grounded", "unsupported_sentiment_terms", "unsupported_provenance_terms", "checks")

    def execute(self, state, payload):
        return check_evidence(payload["tokens"], payload["sentiment"],
                              payload["provenance"], state, self.name)


class ReliabilityAgent(BaseAgent):
    """Applies an explicit abstention/review policy to the upstream reports."""
    name = "reliability_agent"
    tool_count = 1
    required_inputs = ("language", "context", "sentiment", "provenance", "evidence")
    required_outputs = ("decision", "reasons", "supported_language", "evidence_grounded")

    def execute(self, state, payload):
        return reliability_gate(payload["language"], payload["context"], payload["sentiment"],
                                payload["provenance"], payload["evidence"], state, self.name)


class SynthesisAgent(BaseAgent):
    """Combines specialist outputs without changing their predictions."""
    name = "synthesis_agent"
    tool_count = 0
    required_inputs = ("sentiment", "provenance", "language", "context", "evidence", "reliability")
    required_outputs = ("run_id", "domain", "sentiment", "provenance", "language", "context",
                        "evidence_review", "reliability", "caveats", "prototype_stage")

    def execute(self, state, payload):
        sentiment, provenance = payload["sentiment"], payload["provenance"]
        context, evidence = payload["context"], payload["evidence"]
        reliability, language = payload["reliability"], payload["language"]
        caveats = ["Prototype heuristics only; no trained transformer is loaded.",
                   "Provenance is a textual cue estimate, not proof of who authored the review."]
        if reliability["decision"] == "abstain":
            caveats.append("The text language is unsupported; task labels are withheld.")
        elif reliability["decision"] == "manual_review":
            caveats.append("Evidence grounding failed; manual review is required.")
        elif reliability["reasons"]:
            caveats.append("Reliability gate: " + ", ".join(reliability["reasons"]) + ".")
        return {"run_id": state.run_id, "domain": state.domain,
                "sentiment": sentiment, "provenance": provenance,
                "language": language, "context": context, "evidence_review": evidence,
                "reliability": reliability, "caveats": caveats,
                "prototype_stage": "week_5_architecture_and_interaction"}


SPECIALISTS = (RequestValidationAgent(), PreprocessingAgent(), LanguageAgent(), ContextAgent(),
               SentimentAgent(), ProvenanceAgent(), EvidenceAgent(), ReliabilityAgent(), SynthesisAgent())

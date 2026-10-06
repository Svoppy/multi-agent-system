"""Specialist agents, each with one distinct responsibility."""
from typing import Any

from .messages import AgentMessage, RunState
from .tools import check_evidence, load_lexicons, provenance_cues, text_features


class BaseAgent:
    name = "base"
    tool_count = 0

    def execute(self, state: RunState, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class PreprocessingAgent(BaseAgent):
    """Converts a raw review into tokens and simple text features."""
    name = "preprocessing_agent"
    tool_count = 1

    def execute(self, state, payload):
        features = text_features(payload["review"], state, self.name)
        return {"tokens": features["tokens"], "features": features}


class ContextAgent(BaseAgent):
    """Identifies domain terms; does not predict either target label."""
    name = "context_agent"
    tool_count = 1

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

    def execute(self, state, payload):
        lexicons = load_lexicons(state, self.name)["domains"]
        tokens = payload["tokens"]
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
    def execute(self, state, payload):
        report = provenance_cues(payload["tokens"], payload["features"], state, self.name)
        return {**report,
                "method": "unvalidated_heuristics", "authorship_conclusion": False}


class EvidenceAgent(BaseAgent):
    """Checks that specialist claims are grounded in the submitted text."""
    name = "evidence_agent"
    tool_count = 1

    def execute(self, state, payload):
        return check_evidence(payload["tokens"], payload["sentiment"],
                              payload["provenance"], state, self.name)


class SynthesisAgent(BaseAgent):
    """Combines specialist outputs without changing their predictions."""
    name = "synthesis_agent"
    tool_count = 0

    def execute(self, state, payload):
        sentiment, provenance = payload["sentiment"], payload["provenance"]
        context, evidence = payload["context"], payload["evidence"]
        caveats = ["Prototype heuristics only; no trained transformer is loaded.",
                   "Provenance is a textual cue estimate, not proof of who authored the review."]
        if sentiment["confidence"] < 0.5 or provenance["confidence"] < 0.5:
            caveats.append("One or more estimates have low evidence support.")
        if not evidence["grounded"]:
            caveats.append("Evidence check found terms not present in the source text.")
        if context["domain_support"] != "known":
            caveats.append("Domain-specific lexicon unavailable; general cues were used.")
        return {"run_id": state.run_id, "domain": state.domain,
                "sentiment": sentiment, "provenance": provenance,
                "context": context, "evidence_review": evidence, "caveats": caveats,
                "prototype_stage": "week_5_architecture_and_interaction"}


SPECIALISTS = (PreprocessingAgent(), ContextAgent(), SentimentAgent(), ProvenanceAgent(),
               EvidenceAgent(), SynthesisAgent())

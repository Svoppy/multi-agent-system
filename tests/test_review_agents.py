import os
import tempfile
import unittest
from io import BytesIO

from review_agents.agents import BaseAgent
from review_agents.messages import RunState
from review_agents.orchestrator import Orchestrator
from review_agents.web import ReviewHandler


class PipelineTests(unittest.TestCase):
    def test_english_end_to_end_and_tool_balance(self):
        result, state = Orchestrator().run(
            "The delivery was quick, but the battery failed after one day.", "electronics")
        self.assertEqual(result["sentiment"]["label"], "negative")
        self.assertTrue(result["evidence_review"]["grounded"])
        self.assertEqual(result["language"]["language"], "en")
        self.assertEqual(result["workload"]["total_llm_tool_calls"], 8)
        self.assertTrue(result["workload"]["under_40_percent"])
        self.assertLessEqual(result["workload"]["max_share_percent"], 40)
        self.assertEqual(sum(event["event"] == "agent_call" for event in state.events), 9)

    def test_unsupported_language_abstains(self):
        result, _ = Orchestrator().run("Очень плохой сервис и ужасный номер.", "hotel")
        self.assertEqual(result["language"]["language"], "cyrillic_unresolved")
        self.assertEqual(result["sentiment"]["label"], "not_assessed")
        self.assertEqual(result["provenance"]["label"], "not_assessed")
        self.assertEqual(result["reliability"]["decision"], "abstain")

    def test_neutral_domain_term_is_context_only(self):
        result, _ = Orchestrator().run("The battery failed.", "electronics")
        self.assertEqual(result["context"]["matched_domain_terms"], ["battery"])
        self.assertEqual(result["sentiment"]["positive_evidence"], [])

    def test_unknown_domain_uses_general_terms_with_caveat(self):
        result, _ = Orchestrator().run("The service was great.", "unseen_domain")
        self.assertEqual(result["context"]["domain_support"], "general_only")
        self.assertIn("domain_specific_lexicon_unavailable", result["reliability"]["reasons"])

    def test_invalid_inputs_are_rejected_by_request_agent(self):
        with self.assertRaisesRegex(ValueError, "cannot be empty"):
            Orchestrator().run("   ", "hotel")
        with self.assertRaisesRegex(ValueError, "maximum 5000"):
            Orchestrator().run("x" * 5001, "hotel")

    def test_agent_failures_are_bounded_and_logged(self):
        orchestrator = Orchestrator()
        state = RunState("test-run", "text", "hotel")

        class FailingAgent(BaseAgent):
            name = "failing_agent"
            def __init__(self):
                self.calls = 0
            def execute(self, state, payload):
                self.calls += 1
                raise ValueError("simulated schema problem")

        agent = FailingAgent()
        with self.assertRaisesRegex(RuntimeError, "after 2 attempts"):
            orchestrator._invoke(state, agent, {})
        self.assertEqual(agent.calls, 2)
        self.assertEqual(sum(event["event"] == "agent_call" for event in state.events), 2)

    def test_time_limit_stops_before_next_agent(self):
        orchestrator = Orchestrator()
        state = RunState("timeout-run", "text", "hotel")
        state.started_monotonic -= orchestrator.TIME_LIMIT_SECONDS + 1
        with self.assertRaisesRegex(RuntimeError, "time limit"):
            orchestrator._invoke(state, BaseAgent(), {})
        self.assertEqual(state.steps, 0)

    def test_local_web_form_returns_analysis(self):
        with tempfile.TemporaryDirectory() as log_dir:
            class OpenBuffer(BytesIO):
                def close(self):
                    self.flush()

            class MemorySocket:
                def __init__(self, request_bytes):
                    self.input = BytesIO(request_bytes)
                    self.output = OpenBuffer()
                def makefile(self, mode, *args, **kwargs):
                    return self.input if "r" in mode else self.output
                def sendall(self, data):
                    self.output.write(data)
                def close(self):
                    pass

            class FakeServer:
                server_version = "ReviewPrototype/1.0"
                sys_version = ""

                def __init__(self):
                    self.log_dir = log_dir

            def request(method, body=b""):
                headers = (f"{method} / HTTP/1.1\r\nHost: localhost\r\nContent-Length: {len(body)}\r\n"
                           "Content-Type: application/x-www-form-urlencoded\r\n\r\n").encode()
                connection = MemorySocket(headers + body)
                ReviewHandler(connection, ("local", 80), FakeServer())
                return connection.output.getvalue()

            get_response = request("GET")
            self.assertIn(b"200 OK", get_response)
            self.assertIn(b"Joint review analysis", get_response)
            post_response = request("POST", b"review=The+room+was+clean.&domain=hotel")
            self.assertIn(b"200 OK", post_response)
            self.assertIn(b"review_with_caveats", post_response)
            self.assertTrue(any(name.endswith(".jsonl") for name in os.listdir(log_dir)))


if __name__ == "__main__":
    unittest.main()

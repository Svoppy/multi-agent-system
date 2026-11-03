"""Small local web interface for the review-analysis prototype."""
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from urllib.parse import parse_qs

from .orchestrator import Orchestrator, write_jsonl


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Review analysis prototype</title><style>
body{font:16px/1.5 system-ui,sans-serif;max-width:880px;margin:3rem auto;padding:0 1rem;color:#16202a;background:#f6f8fa}
main{background:white;padding:2rem;border:1px solid #d9e0e7;border-radius:12px}label{display:block;margin:.8rem 0 .3rem}
textarea,input{font:inherit;width:100%;box-sizing:border-box;padding:.7rem;border:1px solid #aab6c2;border-radius:6px}
button{margin-top:1rem;padding:.7rem 1rem;background:#183d67;color:white;border:0;border-radius:6px}
.notice{padding:.9rem;background:#fff7dc;border-left:4px solid #d39c00}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f2f4f7;padding:1rem}
</style></head><body><main><h1>Joint review analysis</h1>
<p>This local prototype estimates sentiment and checks limited textual provenance cues.</p>
<form method="post"><label for="review">Review</label><textarea id="review" name="review" maxlength="5000" required rows="5">{review}</textarea>
<label for="domain">Domain</label><input id="domain" name="domain" maxlength="40" value="{domain}" required>
<button type="submit">Analyze review</button></form>
{result}
<p class="notice">Prototype heuristics only. Provenance cues do not establish who authored a review. Unsupported languages are not classified.</p>
</main></body></html>"""


def _page(review: str = "", domain: str = "mixed", result: str = "") -> bytes:
    body = (PAGE.replace("{review}", escape(review, quote=True))
            .replace("{domain}", escape(domain, quote=True)).replace("{result}", result))
    return body.encode("utf-8")


def _result_html(result: dict) -> str:
    summary = {
        "language": result["language"],
        "sentiment": result["sentiment"],
        "provenance": result["provenance"],
        "evidence_review": result["evidence_review"],
        "reliability": result["reliability"],
        "caveats": result["caveats"],
        "workload": result["workload"],
    }
    return "<h2>Result</h2><pre>" + escape(json.dumps(summary, ensure_ascii=False, indent=2)) + "</pre>"


class ReviewHandler(BaseHTTPRequestHandler):
    server_version = "ReviewPrototype/1.0"

    def do_GET(self):
        self._respond(200, _page())

    def do_POST(self):
        orchestrator = Orchestrator()
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 0 or length > 12000:
                raise ValueError("Request is too large")
            fields = parse_qs(self.rfile.read(length).decode("utf-8"), keep_blank_values=True)
            review = fields.get("review", [""])[0]
            domain = fields.get("domain", ["mixed"])[0]
            result, state = orchestrator.run(review, domain)
            write_jsonl(state, str(self.server.log_dir))
            self._respond(200, _page(review, domain, _result_html(result)))
        except (ValueError, UnicodeDecodeError) as exc:
            if orchestrator.last_state:
                write_jsonl(orchestrator.last_state, str(self.server.log_dir))
            self._respond(400, _page(result="<p role=\"alert\">" + escape(str(exc)) + "</p>"))
        except RuntimeError as exc:
            if orchestrator.last_state:
                write_jsonl(orchestrator.last_state, str(self.server.log_dir))
            self._respond(503, _page(result="<p role=\"alert\">" + escape(str(exc)) + "</p>"))

    def _respond(self, status: int, body: bytes):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        # Keep local development output concise; analysis traces are in JSONL.
        return


def serve(host: str = "127.0.0.1", port: int = 8000, log_dir: str = "runs"):
    server = ThreadingHTTPServer((host, port), ReviewHandler)
    server.log_dir = log_dir
    print(f"Review prototype running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

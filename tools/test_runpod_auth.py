"""Exercise the real handler's authentication without a model, GPU or server imports."""
import ast
import hmac
from email.message import Message
from pathlib import Path
from types import SimpleNamespace
import unittest


source = Path(__file__).resolve().parents[1] / "serve" / "server.py"
tree = ast.parse(source.read_text(encoding="utf-8"))
methods = [node for node in ast.walk(tree)
           if isinstance(node, ast.FunctionDef) and node.name == "_authorized"]
assert len(methods) == 1, "Expected one real authentication handler"
scope = {"hmac": hmac, "svc": SimpleNamespace(api_key="app-secret")}
exec(compile(ast.Module(body=methods, type_ignores=[]), str(source), "exec"), scope)
authorized = scope["_authorized"]


class AuthenticationTests(unittest.TestCase):
    def check_headers(self, headers, allowed):
        message = Message()
        for key, value in headers.items():
            message[key] = value
        rejected = []
        handler = SimpleNamespace(headers=message, _json=lambda status, body: rejected.append(status))
        self.assertEqual(authorized(handler), allowed)
        self.assertEqual(rejected, [] if allowed else [401])

    def test_missing_key(self):
        self.check_headers({}, False)

    def test_bearer_key(self):
        self.check_headers({"Authorization": "Bearer app-secret"}, True)

    def test_application_header(self):
        self.check_headers({"X-API-Key": "app-secret"}, True)

    def test_gateway_and_application_keys(self):
        self.check_headers({"Authorization": "Bearer gateway-secret", "X-API-Key": "app-secret"}, True)

    def test_gateway_key_is_not_application_key(self):
        self.check_headers({"Authorization": "Bearer gateway-secret"}, False)

    def test_wrong_application_key(self):
        self.check_headers({"Authorization": "Bearer gateway-secret", "X-API-Key": "wrong"}, False)

    def test_conflicting_explicit_application_key(self):
        self.check_headers({"Authorization": "Bearer app-secret", "X-API-Key": "wrong"}, False)


if __name__ == "__main__":
    unittest.main()

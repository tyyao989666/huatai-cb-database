"""Public browsing must never depend on an account backend."""

import ast
from pathlib import Path
import sys
import unittest

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class PublicAccessTest(unittest.TestCase):
    def test_no_account_backend_import(self):
        tree = ast.parse((ROOT / "app.py").read_text(encoding="utf-8"))
        imports = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        self.assertNotIn("supabase_backend", imports)
        self.assertNotIn("sqlite3", imports)

    def test_desktop_and_mobile_are_public(self):
        for mobile in (False, True):
            with self.subTest(mobile=mobile):
                app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30)
                if mobile:
                    app.query_params["view"] = "mobile"
                # Stale account state from an existing session must not activate
                # any remote read, saved-plan UI or personal data access.
                app.session_state["auth_user"] = {"id": "old-session"}
                app.run()
                self.assertFalse(app.exception, [e.message for e in app.exception])
                self.assertTrue(app.get("download_button"))
                self.assertTrue(any(t.key == "query_filter" for t in app.text_input))
                self.assertFalse(app.get("form"))
                labels = [e.label for e in (*app.text_input, *app.button, *app.expander)]
                self.assertFalse(any(word in label for label in labels for word in ("登录", "注册", "密码", "邮箱")))
                rendered = "\n".join(m.value for m in app.markdown)
                self.assertNotIn("mobile-login", rendered)
                self.assertNotIn('id="workspace"', rendered)


if __name__ == "__main__":
    unittest.main()

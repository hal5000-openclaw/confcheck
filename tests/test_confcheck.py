import os, sys, unittest, tempfile, json, io
from contextlib import redirect_stdout
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import confcheck


def kinds(ps):
    return [(l, k) for l, k, _ in ps]


class Ini(unittest.TestCase):
    def test_clean(self):
        self.assertEqual(confcheck.check_ini("[a]\nx=1\ny: 2\n"), [])

    def test_problems(self):
        t = "[a]\nx=1\nx=2\nbad line\nz=\n[a]\n"
        self.assertEqual(kinds(confcheck.check_ini(t)), [
            (3, "duplicate_key"), (4, "unparseable"), (5, "empty_value"), (6, "duplicate_section")])


class Toml(unittest.TestCase):
    def test_clean(self):
        self.assertEqual(confcheck.check_toml('a = 1\n[t]\nb = "x"\n'), [])

    def test_syntax_line(self):
        ps = confcheck.check_toml('a = 1\nb = = 2\n')
        self.assertEqual(ps[0][:2], (2, "syntax"))

    def test_dup_key_is_syntax(self):
        self.assertEqual(confcheck.check_toml("a=1\na=2\n")[0][1], "syntax")


class Cli(unittest.TestCase):
    def run_cli(self, name, text, *extra):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, name)
            open(p, "w").write(text)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = confcheck.main([p, *extra])
            return rc, buf.getvalue()

    def test_exit_codes(self):
        self.assertEqual(self.run_cli("a.ini", "[a]\nx=1\n")[0], 0)
        self.assertEqual(self.run_cli("a.ini", "[a]\nx=\n")[0], 1)

    def test_json(self):
        rc, out = self.run_cli("a.toml", "a = =\n", "--json")
        self.assertEqual(rc, 1)
        self.assertEqual(list(json.loads(out).values())[0][0]["kind"], "syntax")


if __name__ == "__main__":
    unittest.main()

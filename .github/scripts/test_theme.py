# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The page's one theme is read from the Markdown stub, and only from there."""
from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import theme  # noqa: E402

STUB = """jobs:
  markdown:
    uses: tannergolden/markdown/.github/workflows/markdown.yml@v1
    with:
      mode: profile
{line}
      elements: false
"""


class Theme(unittest.TestCase):
    def test_reads_the_theme_however_the_line_is_written(self):
        for line in ("      theme: blackprint", "      theme: 'blackprint'", '      theme: "blackprint"',
                     "      theme: blackprint      # the page's one theme", "\ttheme:blackprint"):
            self.assertEqual(theme.theme(STUB.format(line=line)), "blackprint", line)

    def test_a_stub_that_names_none_leaves_each_kit_to_its_own_file(self):
        self.assertEqual(theme.theme(STUB.format(line="")), "")
        self.assertEqual(theme.theme(STUB.format(line="      # theme: greenprint  # commented out")), "")

    def test_a_theme_defined_in_the_repository_is_read_as_well(self):
        self.assertEqual(theme.theme(STUB.format(line="      theme: gold-print-2")), "gold-print-2")

    def test_a_stub_that_names_two_is_refused(self):
        with self.assertRaises(ValueError):
            theme.theme(STUB.format(line="      theme: blackprint\n      theme: redprint"))

    def test_the_stub_in_this_repository_names_the_blackprint(self):
        stub = Path(__file__).resolve().parents[1] / "workflows" / "markdown.yml"
        self.assertEqual(theme.theme(stub.read_text(encoding="utf-8")), "blackprint")

    def test_the_command_prints_the_theme_and_survives_a_missing_stub(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "markdown.yml"
            path.write_text(STUB.format(line="      theme: tealprint"), encoding="utf-8")
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                self.assertEqual(theme.main([str(path)]), 0)
                self.assertEqual(theme.main([str(Path(tmp) / "missing.yml")]), 0)
            self.assertEqual(out.getvalue(), "tealprint\n")
            self.assertIn("::warning::", err.getvalue())


if __name__ == "__main__":
    unittest.main()

# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The page's one theme, read from the Markdown stub.

The stub, .github/workflows/markdown.yml, names the theme once, and the
Markdown workflow hands it to every kit it runs: the banners, the badges and
the elements. Health and Elements draw with the same kits on schedules of
their own, so they read the theme here, from the stub, rather than keep a
copy that could drift from it. Prints the theme, or nothing when the stub
names none, which leaves each kit to its own file. Stdlib only.

    python3 .github/scripts/theme.py [.github/workflows/markdown.yml]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

STUB = Path(".github") / "workflows" / "markdown.yml"
# `theme: blackprint` under the stub's `with:`, quoted or not, with a comment after it or none.
# A line commented out starts with `#`, so it never matches.
LINE = re.compile(r"""^[ \t]+theme:[ \t]*(?P<quote>['"]?)(?P<name>[a-z0-9-]*)(?P=quote)[ \t]*(?:#.*)?$""", re.M)


def theme(text: str) -> str:
    """The theme the stub names, or "" when it names none."""
    names = [m.group("name") for m in LINE.finditer(text)]
    if len(names) > 1:
        raise ValueError(f"the stub names a theme {len(names)} times; name it once")
    return names[0] if names else ""


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    path = Path(args[0]) if args else STUB
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"::warning::cannot read {path} ({exc}); each kit draws in its own file's print", file=sys.stderr)
        return 0
    try:
        print(theme(text))
    except ValueError as exc:
        print(f"::error::{path}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

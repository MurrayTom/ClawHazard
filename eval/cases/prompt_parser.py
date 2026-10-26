from __future__ import annotations

import re


_USER_SECTION = re.compile(
    r"^##\s+User Input\s*$\n(?P<body>.*?)(?=^##\s+|\Z)",
    flags=re.MULTILINE | re.DOTALL | re.IGNORECASE,
)


def extract_user_input(prompt_markdown: str) -> str:
    """Return only the user request, excluding benchmark annotations."""
    match = _USER_SECTION.search(prompt_markdown)
    if match:
        return match.group("body").strip()
    return prompt_markdown.strip()

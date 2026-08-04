import re
from typing import Any


def parse_markdown(content: str) -> tuple[dict[str, Any], str]:
    """Parse markdown frontmatter and content.
    Returns (metadata, body).
    """
    metadata = {}
    body = content

    # Try parsing yaml-like frontmatter
    frontmatter_match = re.match(r"^---\n(.*?)\n---\n(.*)", content, re.DOTALL)
    if frontmatter_match:
        fm_text = frontmatter_match.group(1)
        body = frontmatter_match.group(2)
        for line in fm_text.split("\n"):
            if ":" in line:
                key, val = line.split(":", 1)
                metadata[key.strip().lower()] = val.strip()

    # If no frontmatter, try to find a title from the first heading
    if "title" not in metadata:
        title_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
        if title_match:
            metadata["title"] = title_match.group(1).strip()

    return metadata, body.strip()

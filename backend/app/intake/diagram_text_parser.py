"""Turns a drawio XML export or a Mermaid text file into a flat list of
component labels — no LLM involved. This is the text-only path for Design
Review mode; PNG/PDF (which genuinely need vision) are a later phase.
"""

import re
from xml.etree import ElementTree

_MERMAID_LABEL_PATTERN = re.compile(r"[\[\(\{]{1,2}\"?([^\[\](){}\"]+)\"?[\]\)\}]{1,2}")


def _looks_like_drawio(text: str) -> bool:
    stripped = text.lstrip()
    return stripped.startswith("<mxfile") or stripped.startswith("<mxGraphModel") or "<mxCell" in stripped[:2000]


def _parse_drawio_labels(text: str) -> list[str]:
    try:
        root = ElementTree.fromstring(text)
    except ElementTree.ParseError:
        return []
    labels = []
    for cell in root.iter("mxCell"):
        value = cell.get("value")
        if value:
            clean = re.sub(r"<[^>]+>", " ", value).strip()
            if clean:
                labels.append(clean)
    return labels


def _parse_mermaid_labels(text: str) -> list[str]:
    labels = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("%%"):
            continue
        for match in _MERMAID_LABEL_PATTERN.finditer(line):
            label = match.group(1).strip()
            if label and not label.isspace():
                labels.append(label)
    return labels


def extract_component_labels(diagram_text: str) -> list[str]:
    """Best-effort label extraction. Returns [] rather than raising if the
    text doesn't parse as either format — the caller falls back to using
    the raw text directly."""
    if not diagram_text or not diagram_text.strip():
        return []
    if _looks_like_drawio(diagram_text):
        return _parse_drawio_labels(diagram_text)
    return _parse_mermaid_labels(diagram_text)


def diagram_text_to_description(diagram_text: str) -> str:
    labels = extract_component_labels(diagram_text)
    if labels:
        return "Architecture diagram components: " + ", ".join(dict.fromkeys(labels))
    # Unparseable as drawio/mermaid — still hand the raw text to the LLM
    # layer rather than dropping it silently.
    return diagram_text.strip()

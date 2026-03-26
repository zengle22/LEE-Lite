"""Structured TSX/JSX UI source extraction helpers."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


COMMENT_BLOCK_PATTERN = re.compile(r"/\*.*?\*/", re.DOTALL)
COMMENT_LINE_PATTERN = re.compile(r"//.*?$", re.MULTILINE)
BRACED_STRING_PATTERN = re.compile(r"=\{\s*(['\"])(.*?)\1\s*\}", re.DOTALL)
ROUTE_TAG_PATTERN = re.compile(r"<Route\b([^>]*)/?>", re.IGNORECASE)
ROUTE_OBJECT_PATTERN = re.compile(r"\bpath\s*:\s*['\"](/[^'\"]+)['\"]", re.IGNORECASE)
ATTR_PATTERN = re.compile(r"([A-Za-z_:][-A-Za-z0-9_:.]*)\s*=\s*['\"]([^'\"]*)['\"]")


def _clean_source(text: str) -> str:
    cleaned = COMMENT_BLOCK_PATTERN.sub("", text)
    cleaned = COMMENT_LINE_PATTERN.sub("", cleaned)
    return cleaned


def _clean_fragment(text: str) -> str:
    cleaned = text.replace("htmlFor=", "for=")
    cleaned = BRACED_STRING_PATTERN.sub(lambda match: f'="{match.group(2)}"', cleaned)
    cleaned = re.sub(r"=\{[^{}]*\}", '=""', cleaned)
    return cleaned


def _attrs(raw_attrs: str) -> dict[str, str]:
    return {key.lower(): value.strip() for key, value in ATTR_PATTERN.findall(raw_attrs)}


def _selector(entry: dict[str, str]) -> str:
    if entry.get("testid"):
        return f"[data-testid='{entry['testid']}']"
    if entry.get("id"):
        return f"#{entry['id']}"
    if entry.get("element") in {"input", "textarea", "select"} and entry.get("name"):
        return f"input[name='{entry['name']}']"
    return ""


def _route_entries(text: str) -> list[dict[str, str]]:
    routes: list[dict[str, str]] = []
    seen: set[str] = set()
    for match in ROUTE_TAG_PATTERN.finditer(text):
        attrs = _attrs(match.group(1))
        path = attrs.get("path", "").strip()
        if path and path not in seen:
            seen.add(path)
            routes.append({"path": path, "source_kind": "jsx_route"})
    for path in ROUTE_OBJECT_PATTERN.findall(text):
        normalized = path.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            routes.append({"path": normalized, "source_kind": "route_object"})
    return routes


def _jsx_fragments(text: str) -> list[str]:
    fragments: list[str] = []
    cursor = 0
    while True:
        start = text.find("return (", cursor)
        if start < 0:
            return fragments
        open_index = text.find("(", start)
        depth = 0
        end = open_index
        while end < len(text):
            char = text[end]
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    fragments.append(text[open_index + 1 : end])
                    cursor = end + 1
                    break
            end += 1
        else:
            return fragments


class _JsxCatalogParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.entries: list[dict[str, str]] = []
        self.labels: dict[str, str] = {}
        self._stack: list[dict[str, Any]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {str(key).lower(): str(value or "").strip() for key, value in attrs}
        tag_name = tag.lower()
        if tag_name == "label":
            self._stack.append({"tag": "label", "for": attr_map.get("for", ""), "text": []})
            return
        if tag_name == "button":
            self._stack.append({"tag": "button", "attrs": attr_map, "text": []})
            return
        if tag_name in {"input", "textarea", "select"}:
            self.entries.append(
                {
                    "element": tag_name,
                    "testid": attr_map.get("data-testid", ""),
                    "id": attr_map.get("id", ""),
                    "name": attr_map.get("name", ""),
                    "role": attr_map.get("role", ""),
                    "label": self.labels.get(attr_map.get("id", ""), ""),
                    "text": attr_map.get("aria-label", ""),
                    "selector": "",
                }
            )

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_data(self, data: str) -> None:
        if not self._stack:
            return
        text = data.strip()
        if text:
            self._stack[-1]["text"].append(text)

    def handle_endtag(self, tag: str) -> None:
        tag_name = tag.lower()
        if not self._stack or self._stack[-1]["tag"] != tag_name:
            return
        item = self._stack.pop()
        text = " ".join(item.get("text", [])).strip()
        if tag_name == "label":
            target = str(item.get("for", "")).strip()
            if target and text:
                self.labels[target] = text
            return
        if tag_name == "button":
            attrs = item.get("attrs", {})
            self.entries.append(
                {
                    "element": "button",
                    "testid": str(attrs.get("data-testid", "")).strip(),
                    "id": str(attrs.get("id", "")).strip(),
                    "name": text or str(attrs.get("aria-label", "")).strip(),
                    "role": str(attrs.get("role", "button")).strip() or "button",
                    "label": "",
                    "text": text,
                    "selector": "",
                }
            )


def _element_entries(text: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for fragment in _jsx_fragments(text):
        parser = _JsxCatalogParser()
        parser.feed(_clean_fragment(fragment))
        for item in parser.entries:
            entry = dict(item)
            entry["selector"] = _selector(entry)
            entries.append(entry)
    return entries


def parse_code_file(path: Path) -> dict[str, Any]:
    text = _clean_source(path.read_text(encoding="utf-8", errors="ignore"))
    return {
        "path": str(path),
        "routes": _route_entries(text),
        "elements": _element_entries(text),
    }

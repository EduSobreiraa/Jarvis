"""Minimal DuckDuckGo HTML search for the Jarvis local tool loop."""

from html.parser import HTMLParser
from urllib.parse import parse_qs, urlparse

import requests


TOOL = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the public web when the user explicitly asks for current information or a web search. The query is sent to DuckDuckGo; do not include personal or confidential details.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Short, non-sensitive search terms."}},
            "required": ["query"],
        },
    },
}


class _Results(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = []
        self.current = None
        self.last_item = None
        self.capture = None
        self.capture_tag = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get("class", "").split()
        if tag == "a" and "result__a" in classes:
            self.current = {"title": "", "url": attrs.get("href", ""), "snippet": ""}
            self.capture = "title"
            self.capture_tag = "a"
        elif self.last_item is not None and tag in {"a", "div"} and "result__snippet" in classes:
            self.current = self.last_item
            self.capture = "snippet"
            self.capture_tag = tag

    def handle_data(self, data):
        if self.current is not None and self.capture:
            self.current[self.capture] += data

    def handle_endtag(self, tag):
        if self.current is None:
            return
        if self.capture == "title" and tag == "a":
            self.capture = None
            self.capture_tag = None
            if self.current["title"].strip():
                self.items.append(self.current)
                self.last_item = self.current
            self.current = None
        elif self.capture == "snippet" and tag == self.capture_tag:
            self.capture = None
            self.capture_tag = None
            self.current = None


def _destination(href):
    parsed = urlparse(href)
    if parsed.hostname and parsed.hostname.endswith("duckduckgo.com"):
        target = parse_qs(parsed.query).get("uddg", [None])[0]
        if target:
            return target
    return href


def web_search(query, session=None, limit=5):
    query = " ".join(str(query).split())
    if not query or len(query) > 300:
        raise ValueError("A busca precisa ter entre 1 e 300 caracteres.")
    client = session or requests
    response = client.get(
        "https://html.duckduckgo.com/html/",
        params={"q": query},
        headers={"User-Agent": "Jarvis/1.0 (local assistant; web search)"},
        timeout=(5, 15),
    )
    response.raise_for_status()
    parser = _Results()
    parser.feed(response.text)
    results = [
        {"title": item["title"].strip(), "url": _destination(item["url"]), "snippet": item["snippet"].strip()}
        for item in parser.items[: max(1, min(int(limit), 5))]
    ]
    return results

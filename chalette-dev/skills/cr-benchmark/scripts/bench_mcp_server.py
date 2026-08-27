#!/usr/bin/env python3
"""Mock connector MCP server for BENCH1.

Serves the canned connector fixture JSON (gmail / calendar / granola) from a
workspace copy's ``_hq/connectors/`` directory over stdio MCP, with tool
names mirroring the real connectors. Both benchmark arms attach the same
servers, so "bare Claude with the normal connectors" is literally true and
neither arm ever touches a live account.

Usage (one process per connector, selected by --server):
    python bench_mcp_server.py --server gmail    --connectors-dir <ws>/_hq/connectors
    python bench_mcp_server.py --server calendar --connectors-dir ...
    python bench_mcp_server.py --server granola  --connectors-dir ...

Pure stdlib; newline-delimited JSON-RPC 2.0 per the MCP stdio transport.
Read-only by construction: the server only ever reads the fixture files.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROTOCOL_FALLBACK = "2025-06-18"


def _load(connectors_dir: Path, name: str) -> dict:
    p = connectors_dir / f"{name}_responses.json"
    return json.loads(p.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- tool impls

def gmail_tools(connectors_dir: Path):
    data = _load(connectors_dir, "gmail")["gmail_search"]["queries"]

    def search_threads(args: dict) -> dict:
        q = (args.get("query") or "").strip()
        threads = data.get(q)
        if threads is None:
            # Canned fixture: any query falls back to the default inbox slice.
            threads = next(iter(data.values()), [])
        return {"threads": threads, "query_used": q or "(default)"}

    return {
        "search_threads": {
            "fn": search_threads,
            "description": "Search email threads. Returns thread id, subject, sender, snippet, timestamp.",
            "schema": {"type": "object",
                       "properties": {"query": {"type": "string",
                                                "description": "Gmail-style search query"}},
                       "required": []},
        },
    }


def calendar_tools(connectors_dir: Path):
    data = _load(connectors_dir, "calendar")["calendar_list_events"]["windows"]

    def list_events(args: dict) -> dict:
        window = args.get("window") or "today"
        events = data.get(window)
        if events is None:
            events = data.get("today", [])
        return {"window": window, "events": events}

    return {
        "list_events": {
            "fn": list_events,
            "description": "List calendar events for a window ('today' or 'next_7_days').",
            "schema": {"type": "object",
                       "properties": {"window": {"type": "string",
                                                 "enum": ["today", "next_7_days"]}},
                       "required": []},
        },
    }


def granola_tools(connectors_dir: Path):
    data = _load(connectors_dir, "granola")["granola_get_transcript"]["doc_ids"]

    def list_meetings(args: dict) -> dict:
        rows = []
        for doc_id, doc in data.items():
            rows.append({
                "doc_id": doc_id,
                "title": doc.get("title", doc_id),
                "date": doc.get("date"),
                "attendees": doc.get("attendees", []),
                "duration": doc.get("duration"),
            })
        return {"meetings": rows}

    def get_meeting_transcript(args: dict) -> dict:
        doc_id = args.get("doc_id") or ""
        doc = data.get(doc_id)
        if doc is None:
            return {"error": f"unknown doc_id '{doc_id}'",
                    "known_doc_ids": sorted(data)}
        return {"doc_id": doc_id, "title": doc.get("title", doc_id),
                "date": doc.get("date"), "attendees": doc.get("attendees", []),
                "transcript": doc.get("transcript", "")}

    return {
        "list_meetings": {
            "fn": list_meetings,
            "description": "List recent meetings with doc ids, titles, dates, and attendees.",
            "schema": {"type": "object", "properties": {}, "required": []},
        },
        "get_meeting_transcript": {
            "fn": get_meeting_transcript,
            "description": "Fetch the full transcript of a meeting by doc_id.",
            "schema": {"type": "object",
                       "properties": {"doc_id": {"type": "string"}},
                       "required": ["doc_id"]},
        },
    }


SERVERS = {"gmail": gmail_tools, "calendar": calendar_tools, "granola": granola_tools}


# ---------------------------------------------------------------- MCP plumbing

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", required=True, choices=sorted(SERVERS))
    ap.add_argument("--connectors-dir", required=True)
    args = ap.parse_args()

    tools = SERVERS[args.server](Path(args.connectors_dir))

    def reply(msg_id, result=None, error=None):
        out = {"jsonrpc": "2.0", "id": msg_id}
        if error is not None:
            out["error"] = error
        else:
            out["result"] = result
        sys.stdout.write(json.dumps(out) + "\n")
        sys.stdout.flush()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        method = msg.get("method", "")
        msg_id = msg.get("id")
        if msg_id is None:
            continue  # notification (e.g. notifications/initialized) -- no reply
        if method == "initialize":
            client_proto = (msg.get("params") or {}).get("protocolVersion", PROTOCOL_FALLBACK)
            reply(msg_id, {
                "protocolVersion": client_proto,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": f"bench-{args.server}", "version": "1.0"},
            })
        elif method == "tools/list":
            reply(msg_id, {"tools": [
                {"name": name, "description": t["description"], "inputSchema": t["schema"]}
                for name, t in tools.items()
            ]})
        elif method == "tools/call":
            params = msg.get("params") or {}
            name = params.get("name")
            t = tools.get(name)
            if t is None:
                reply(msg_id, error={"code": -32602, "message": f"unknown tool {name}"})
                continue
            try:
                result = t["fn"](params.get("arguments") or {})
                reply(msg_id, {"content": [
                    {"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=1)}
                ]})
            except Exception as exc:  # fixture read errors -> visible, not silent
                reply(msg_id, {"content": [{"type": "text", "text": f"ERROR: {exc}"}],
                               "isError": True})
        elif method == "ping":
            reply(msg_id, {})
        elif method in ("resources/list", "prompts/list"):
            key = method.split("/")[0]
            reply(msg_id, {key: []})
        else:
            reply(msg_id, error={"code": -32601, "message": f"method {method} not supported"})
    return 0


if __name__ == "__main__":
    sys.exit(main())

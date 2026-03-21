"""
Cortex MCP Server — serves file context to Claude Code via Model Context Protocol.

Usage in .claude/settings.json:
{
  "mcpServers": {
    "cortex": {
      "command": "cortex",
      "args": ["mcp"]
    }
  }
}
"""
import json
import sys
import os
from pathlib import Path


def get_context_for_file(file_path: str, repo_root: str) -> str:
    """Read .claude/docs/<file>.md if it exists."""
    doc = Path(repo_root) / ".claude" / "docs" / (file_path + ".md")
    if doc.exists():
        return doc.read_text(encoding='utf-8')
    return f"No context for {file_path}. Run: cortex analyze"


def run_mcp_server():
    """Run MCP server on stdio."""
    repo_root = os.getcwd()

    def send(obj):
        sys.stdout.write(json.dumps(obj) + "\n")
        sys.stdout.flush()

    def error_response(id_, code, message):
        send({"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}})

    # Send server info on startup
    send({
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {}
    })

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue

        req_id = req.get("id")
        method = req.get("method", "")
        params = req.get("params", {})

        if method == "initialize":
            send({
                "jsonrpc": "2.0", "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "cortex", "version": "0.1.0"}
                }
            })

        elif method == "tools/list":
            send({
                "jsonrpc": "2.0", "id": req_id,
                "result": {
                    "tools": [
                        {
                            "name": "get_file_context",
                            "description": "Get historical insights, pitfalls, related files, and security notes for a file",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "file_path": {
                                        "type": "string",
                                        "description": "Relative path to the file (e.g. src/auth.py)"
                                    }
                                },
                                "required": ["file_path"]
                            }
                        },
                        {
                            "name": "get_project_summary",
                            "description": "Get overall project summary including architecture and security report",
                            "inputSchema": {
                                "type": "object",
                                "properties": {}
                            }
                        }
                    ]
                }
            })

        elif method == "tools/call":
            tool_name = params.get("name", "")
            args = params.get("arguments", {})

            if tool_name == "get_file_context":
                file_path = args.get("file_path", "")
                context = get_context_for_file(file_path, repo_root)
                send({
                    "jsonrpc": "2.0", "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": context}]
                    }
                })

            elif tool_name == "get_project_summary":
                summary_path = Path(repo_root) / ".claude" / "docs" / "SUMMARY.md"
                security_path = Path(repo_root) / ".claude" / "docs" / "SECURITY_REPORT.md"
                text = ""
                if summary_path.exists():
                    text += summary_path.read_text(encoding='utf-8') + "\n\n"
                if security_path.exists():
                    text += security_path.read_text(encoding='utf-8')
                if not text:
                    text = "No summary found. Run: cortex analyze"
                send({
                    "jsonrpc": "2.0", "id": req_id,
                    "result": {"content": [{"type": "text", "text": text}]}
                })
            else:
                error_response(req_id, -32601, f"Unknown tool: {tool_name}")

        elif method == "ping":
            send({"jsonrpc": "2.0", "id": req_id, "result": {}})

        else:
            # Unknown method — return empty result (don't error on notifications)
            if req_id is not None:
                send({"jsonrpc": "2.0", "id": req_id, "result": {}})

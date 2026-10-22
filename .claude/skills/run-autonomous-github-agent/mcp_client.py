"""Drive mcp_server/server.py over real MCP stdio.

usage: mcp_client.py list
       mcp_client.py call <tool> '<json-args>'
Inherits env (GITHUB_TOKEN, DRY_RUN). DRY_RUN is forced to "true" unless
the caller exported DRY_RUN explicitly.
"""

import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


async def main(argv: list[str]) -> int:
    env = dict(os.environ)
    env.setdefault("DRY_RUN", "true")
    params = StdioServerParameters(
        command=sys.executable,
        args=[os.path.join(REPO, "mcp_server", "server.py")],
        env=env,
        cwd=os.getcwd(),  # driver cds to $AGA_WORK: keeps the repo .env out
    )
    async with stdio_client(params) as (r, w), ClientSession(r, w) as s:
        await s.initialize()
        if argv[0] == "list":
            for t in (await s.list_tools()).tools:
                print(f"{t.name:20} {(t.description or '').splitlines()[0]}")
            return 0
        if argv[0] == "call":
            args = json.loads(argv[2]) if len(argv) > 2 else {}
            res = await s.call_tool(argv[1], args)
            for c in res.content:
                print(getattr(c, "text", c))
            return 1 if res.isError else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1:] or ["help"])))

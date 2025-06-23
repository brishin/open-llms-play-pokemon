#!/usr/bin/env python3

import logging
import sys

from fastmcp import FastMCP

from open_llms_play_pokemon.game_state.game_state_parsing import (
    get_game_state_json,
    get_game_state_text,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("Open LLMs Play Pokemon")

mcp.tool(name_or_fn=get_game_state_json)
mcp.tool(name_or_fn=get_game_state_text)


def main():
    """Main entry point - can run as CLI or MCP server."""
    if len(sys.argv) >= 3:
        # CLI mode: python -m open_llms_play_pokemon.mcp_server <function> <state_file>
        function_name = sys.argv[1]
        state_file_path = sys.argv[2]
        if function_name == "get_game_state_text":
            result = get_game_state_text(state_file_path)
            print(result)
        elif function_name == "get_game_state_json":
            import json

            result = get_game_state_json(state_file_path)
            print(json.dumps(result, indent=2))
        else:
            print(f"Unknown function: {function_name}")
            print(
                "Usage: python -m open_llms_play_pokemon.mcp_server <get_game_state_text|get_game_state_json> <state_file>"
            )
            sys.exit(1)
    else:
        # MCP server mode
        logger.info("Starting Pokemon Red MCP Server...")
        mcp.run()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

import logging

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


if __name__ == "__main__":
    logger.info("Starting Pokemon Red MCP Server...")
    mcp.run()

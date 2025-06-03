# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

- **Run the main Pokemon player**: `python -m open-llms-play-pokemon.main`
- **Install dependencies**: `uv sync` (project uses uv for dependency management)
- **Run tests**: `uv run python -m pytest test_action_parser.py -v`
- **Format code**: `uv run ruff format .`
- **Lint code**: `uv run ruff check . --fix`
- **Deploy LLM server**: `modal deploy server/llm_server.py`
- **Test LLM server**: `modal run server/llm_server.py::test`

## Architecture Overview

This project implements an AI agent that plays Pokemon Red using vision-language models. The architecture consists of:

### Core Components

1. **PokemonRedPlayer** (`open-llms-play-pokemon/main.py`): Main game controller that integrates PyBoy emulator with AI decision-making
2. **ActionParser** (`open-llms-play-pokemon/action_parser.py`): Parses AI responses and executes button sequences on PyBoy emulator
3. **LLM Server** (`server/llm_server.py`): Modal-based vLLM server running UI-TARS-1.5-7B model for game vision understanding
4. **Game Tools** (`open-llms-play-pokemon/tools.py`): GameBoy button mapping utilities for LLM function calling

### Key Technical Details

- **Emulator**: Uses PyBoy to run Pokemon Red ROM with symbol file support
- **AI Model**: ByteDance-Seed/UI-TARS-1.5-7B vision-language model via OpenAI-compatible API
- **Game States**: Preserved game states in `/game/` directory for different progress points
- **Environment**: Requires `.env` file with `OPENAI_BASE_URL` and `OPENAI_API_KEY` for LLM server connection

### Game State Management

The `/game/` directory contains various saved states representing different progress points in Pokemon Red. The main player loads `init.state` by default but can be modified to start from different states for testing specific scenarios.

### Development Notes

- Model runs on Modal with A10G GPU, auto-scales based on usage
- Game runs at 6x speed for faster AI iteration
- Screen captures are base64-encoded and sent to vision model for action decisions
- AI responses are parsed to extract button sequences in format: `buttons(sequence='button1 button2')`
- Action parser handles validation, error recovery, and PyBoy integration
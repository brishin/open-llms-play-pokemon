# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

- **Run the main Pokemon player**: `python -m open_llms_play_pokemon.agents.main`
- **Run the DSPy-based Pokemon player**: `python -m open_llms_play_pokemon.agents.main_dspy --steps 5 --headless` (Use the given arguments unless specified otherwise)
- **Install dependencies**: `uv sync` (project uses uv for dependency management)
- **Run all tests**: `uv run pytest tests/ -v`
- **Run specific test**: `uv run pytest tests/test_action_parser.py -v`
- **Run all code quality checks**: `./check.sh` (format, lint, typecheck)
- **Format code**: `uv run ruff format .`
- **Lint code**: `uv run ruff check . --fix`
- **Type check**: `uv run pyright`
- **Deploy LLM server**: `modal deploy server/llm_server.py`
- **Test LLM server**: `modal run server/llm_server.py::test`
- **Get MLflow experiments**: `python mlflow/get_experiments.py` (fetch recent experiments with table output)
- **Get MLflow runs**: `python mlflow/get_runs.py --limit 5 --status FINISHED` (fetch recent successful runs)

## Architecture Overview

This project implements an AI agent that plays Pokemon Red using vision-language models. The architecture consists of:

### Core Components

1. **PokemonRedPlayer** (`open-llms-play-pokemon/agents/main.py`): Original game controller that integrates PyBoy emulator with AI decision-making
2. **PokemonRedDSPyPlayer** (`open-llms-play-pokemon/agents/main_dspy.py`): DSPy-based implementation with structured reasoning modules
3. **ActionParser** (`open-llms-play-pokemon/emulation/action_parser.py`): Parses AI responses and executes button sequences on PyBoy emulator
4. **LLM Server** (`server/llm_server.py`): Modal-based vLLM server running UI-TARS-1.5-7B model for game vision understanding
5. **Game Tools** (`open-llms-play-pokemon/tools.py`): GameBoy button mapping utilities for LLM function calling

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

### MLflow Integration

- **MLflow Server**: Runs on `http://localhost:8080` by default for experiment tracking
- **Experiment Management**: Use `python mlflow/get_experiments.py` to fetch and display recent experiments
  - Supports multiple output formats: `--format table|json|csv`
  - Configurable limits: `--limit N` (default: 3)
  - Custom tracking URI: `--tracking-uri http://custom:port`
  - Sorting options: `--sort-by creation_time|last_update_time|name`
- **Run Management**: Use `python mlflow/get_runs.py` to fetch and display recent runs
  - Filter by experiment: `--experiment-name "open-llms-play-pokemon"` or `--experiment-id ID`
  - Filter by status: `--status FINISHED|FAILED|RUNNING`
  - Sort by: `--sort-by start_time|end_time|status` with `--order asc|desc`
  - Shows run details: status, duration, artifact count, key metrics

### Verification Process for main_dspy.py Changes

When making changes to the DSPy implementation or game state system, follow this verification process:

1. **Run the DSPy Player**: `python -m open_llms_play_pokemon.agents.main_dspy --steps 10 --headless`
2. **Check Latest Runs**: `python mlflow/get_runs.py --limit 1 --status FINISHED`
3. **Verify Artifacts**: Ensure proper artifact count and file sizes are maintained
4. **Validate Data Structure**: Download and inspect game state JSON files to verify:
   - Dataclass structures are properly serialized
   - Key fields like `directions_available` have expected values
   - File sizes match expected data richness (~15-25KB for comprehensive data)
   - No runtime errors or data corruption

### DSPy Implementation

The DSPy version (`agents/main_dspy.py`) provides a more structured approach with:

- **VisionAnalyzer**: DSPy module that analyzes game screens and identifies current situation
- **ActionPlanner**: DSPy module that decides optimal actions based on game analysis
- **PokemonRedDSPyAgent**: Main agent that coordinates vision analysis and action planning
- **Structured Signatures**: Clear input/output definitions for vision analysis and action planning
- **Better Reasoning**: Explicit reasoning chains and structured decision-making process

## Code Guidance

- Do not add code comments unless the code is particularly complicated.
- **IMPORTANT**: Always run `./check.sh` after making code changes to ensure formatting, linting, and type checking pass.
- **DSPy Development**: When working with DSPy framework, reference `.cursor/rules/dspy.mdc` for best practices and guidelines.

## Testing Conventions

This project follows specific Python testing conventions using **pytest** as the primary testing framework.

### **Test Structure and Organization**

- **Test Directory**: All tests are located in `/tests/` at the project root
- **File Naming**: Use `test_<module_name>.py` pattern (e.g., `test_game_state.py`, `test_screen_analyzer.py`)
- **Function Naming**: Use descriptive `test_<behavior_description>()` names that clearly indicate what is being tested
- **Class Naming**: Use `Test<ComponentName><Aspect>` pattern for test classes when grouping related tests

### **Running Tests**

- **All Tests**: `uv run pytest tests/ -v` (verbose output recommended)
- **Specific Test File**: `uv run pytest tests/test_<module>.py -v`
- **Integration with Quality Checks**: Tests are included in `./check.sh` script alongside formatting and linting

### **Testing Patterns**

#### **Mocking and Test Isolation**
- Use `unittest.mock.Mock` and `MagicMock` for dependency isolation
- Mock PyBoy memory views with custom `__getitem__` behavior for game state testing
- Use `pytest.monkeypatch` for replacing functions during tests
- Apply `@patch` decorators for external system mocking

#### **Test Data Creation**
- Create helper factory functions for reusable test objects (e.g., `create_test_tile_data()`)
- Use hardcoded test values that represent realistic game states
- Accept parameters in factory functions to customize test scenarios
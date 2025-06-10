"""DSPy Evaluator for Pokemon Red

This evaluator adapts the simple coordinate-based exploration reward that the
`red_gym_env_v2.py` environment in *Pokemon Red Experiments* uses.  It counts
how many **unique** (x, y) overworld coordinates the agent visits in a short
roll-out starting from a saved game state.  This acts as a proxy for useful
progress (moving, exploring, leaving the initial room, etc.) while being
light-weight enough to run during unit tests.

The evaluator is implemented on top of `dspy.evaluate.Evaluate` so it can be
plugged straight into DSPy optimisation workflows (e.g. MIPRO, COPRO, SIMBA …)
without any additional glue-code.

Key design points
-----------------
1.  **Symbol parsing** – Rather than hard-coding Game Boy RAM addresses, we
    read `game/pokered.sym` at import time and resolve the labels `wXCoord`
    and `wYCoord`.  This keeps the implementation robust to different ROM/
    disassembly versions as long as the symbols are present.
2.  **Headless PyBoy** –  The roll-out uses the existing `GameEmulator` class
    in *open-llms-play-pokemon* with the SDL window disabled so evaluation can
    run inside CI pipelines.
3.  **Minimal Loop** –  For each example we execute the student/agent for
    `max_steps` button presses (defaults to 40).  After every action we tick
    PyBoy to let the game update for a few frames (configurable via
    `frames_per_step`).
4.  **Metric** –  The metric simply returns the number of newly discovered
    coordinates (`int`).  `dspy.evaluate.Evaluate` will average these scores
    across the dev-set and report a single scalar.

Usage example
-------------
>>> from dspy.evaluate import Evaluate
>>> from open_llms_play_pokemon.main_dspy import PokemonRedDSPyAgent
>>> from open_llms_play_pokemon.evaluators.pokemon_red_evaluator import (
...     build_devset, exploration_metric)
>>> student = PokemonRedDSPyAgent(on_buttons_pressed=lambda _: None)  # mock
>>> evaluator = Evaluate(devset=build_devset(), metric=exploration_metric)
>>> print(evaluator(student))
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import List, Tuple

import dspy  # type: ignore
from dspy.evaluate import Evaluate  # type: ignore  # re-export for convenience

from ..game_emulator import GameEmulator
from ..main_dspy import GameState, PokemonRedDSPyAgent

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Utilities for reading symbol addresses
# ---------------------------------------------------------------------------

_SYM_PATH = Path(__file__).resolve().parent.parent / "game" / "pokered.sym"
_PLAYER_COORD_LABELS = {
    "x": re.compile(r"\bwXCoord\b", re.IGNORECASE),
    "y": re.compile(r"\bwYCoord\b", re.IGNORECASE),
}


def _load_player_coord_addresses(sym_path: Path = _SYM_PATH) -> Tuple[int, int]:
    """Return (x_addr, y_addr) RAM addresses by parsing *pokered.sym*."""
    if not sym_path.exists():
        raise FileNotFoundError(f"Symbol file not found: {sym_path}")

    x_addr = y_addr = None
    with sym_path.open() as fh:
        for line in fh:
            # Each line is like "00:d362 wXCoord"
            parts = line.strip().split()
            if len(parts) != 2:
                continue
            address_hex, label = parts
            match_x = _PLAYER_COORD_LABELS["x"].search(label)
            match_y = _PLAYER_COORD_LABELS["y"].search(label)
            if match_x:
                x_addr = int(address_hex.split(":")[1], 16)
            elif match_y:
                y_addr = int(address_hex.split(":")[1], 16)
            if x_addr is not None and y_addr is not None:
                break

    if x_addr is None or y_addr is None:
        raise RuntimeError("Failed to locate wXCoord / wYCoord in symbol file")

    logger.debug("Using player coord addresses – x: %#x, y: %#x", x_addr, y_addr)
    return x_addr, y_addr


_PLAYER_X_ADDR, _PLAYER_Y_ADDR = _load_player_coord_addresses()


# ---------------------------------------------------------------------------
# Roll-out helper
# ---------------------------------------------------------------------------


def _unique_coord_rollout(
    student: PokemonRedDSPyAgent,
    save_state_path: Path,
    max_steps: int = 40,
    frames_per_step: int = 60,
) -> int:
    """Run *student* for *max_steps* starting from *save_state_path*.

    Returns the count of unique (x, y) coordinates visited (excluding the
    starting coordinate).
    """
    emulator = GameEmulator(headless=True)
    emulator.load_state(save_state_path.name)  # path is resolved relative to /game

    def _coords() -> Tuple[int, int]:
        mem = emulator.pyboy.memory
        return mem[_PLAYER_X_ADDR], mem[_PLAYER_Y_ADDR]

    visited = { _coords() }

    for _ in range(max_steps):
        screen_b64 = emulator.get_screen_base64()
        game_state = GameState(screen_base64=screen_b64)
        parsed_action = student.forward(game_state)
        emulator.execute_action(parsed_action)
        emulator.pyboy.tick(frames_per_step, render=False)
        visited.add(_coords())

    # NB: emulator.cleanup() will be called automatically when GameEmulator
    # destructs (it owns the PyBoy instance).
    return len(visited) - 1  # exclude starting tile


# ---------------------------------------------------------------------------
# DSPy Evaluate glue
# ---------------------------------------------------------------------------

class RolloutSignature(dspy.Signature):
    """Signature describing a *PlayEpisode* call for the evaluator."""

    save_state: str = dspy.InputField(desc="Filename of a PyBoy save-state to load")
    # During prediction we return a numeric score
    exploration_score: int = dspy.OutputField()


class PlayEpisode(dspy.Module):
    """Module that runs a short game roll-out and reports an exploration score."""

    def __init__(self, student: PokemonRedDSPyAgent, *, max_steps: int = 40):
        super().__init__()
        self.student = student
        self.max_steps = max_steps

    def forward(self, save_state: str) -> dspy.Prediction:  # type: ignore[override]
        score = _unique_coord_rollout(
            self.student, Path(__file__).resolve().parent.parent / "game" / save_state, max_steps=self.max_steps
        )
        return dspy.Prediction(exploration_score=score)


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

_DEF_STATE_FILES = ["init.state"]  # extend as you add more dev examples


def build_devset(state_files: List[str] | None = None) -> List[dspy.Example]:
    """Create a dev-set from *state_files* (Game Boy save-states).

    Each Example only needs the *save_state* input because the evaluator does
    not rely on any gold output.
    """
    if state_files is None:
        state_files = _DEF_STATE_FILES
    devset: List[dspy.Example] = []
    for fname in state_files:
        e = dspy.Example(save_state=fname).with_inputs("save_state")
        devset.append(e)
    return devset


def exploration_metric(gold: dspy.Example, pred: dspy.Prediction, trace=None) -> int:  # noqa: D401 – simple metric
    """Return the exploration score produced by *PlayEpisode*."""
    return int(getattr(pred, "exploration_score", 0))


__all__ = [
    "Evaluate",  # re-export so users can do `from ... import Evaluate`
    "PlayEpisode",
    "RolloutSignature",
    "build_devset",
    "exploration_metric",
]
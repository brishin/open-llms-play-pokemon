"""
Test warp tile visualization in walkable grid text output.

This test verifies that warp tiles are properly displayed as 'W' in the
walkable grid visualization.
"""


from open_llms_play_pokemon.game_state.game_state_parsing import format_game_state_text


class TestWarpGridOutput:
    """Test warp tile display in walkable grid visualization."""

    def test_warp_tile_shows_as_w_in_grid(self):
        """Test that warp tiles show as 'W' in the walkable grid."""
        # Create a mock game state with a simple tile matrix containing a warp tile
        game_state = {
            "step_counter": 0,
            "current_map": 38,
            "player_x": 4,
            "player_y": 3,
            "directions_available": {
                "north": True,
                "south": True,
                "east": True,
                "west": True,
            },
            "player_name": "TEST",
            "party_count": 0,
            "badges_obtained": 0,
            "is_in_battle": False,
            "tile_matrix": {
                "tiles": [
                    # Row 0-1 (will be processed as grid row 0)
                    [{"is_walkable": False, "is_warp_tile": False} for _ in range(20)],
                    [{"is_walkable": False, "is_warp_tile": False} for _ in range(20)],
                    # Row 2-3 (will be processed as grid row 1) - add warp at position (14, 3)
                    [{"is_walkable": False, "is_warp_tile": False} for _ in range(20)],
                    [
                        {"is_walkable": False, "is_warp_tile": False}
                        if i != 14
                        else {"is_walkable": True, "is_warp_tile": True}
                        for i in range(20)
                    ],
                    # Add more rows to reach 18 total
                    *[
                        [
                            {"is_walkable": False, "is_warp_tile": False}
                            for _ in range(20)
                        ]
                        for _ in range(14)
                    ],
                ]
            },
        }

        # Format the game state as text
        text_output = format_game_state_text(game_state)

        # Check that the walkable grid includes warp symbol explanation
        assert "W = warp" in text_output, (
            "Grid legend should include warp symbol explanation"
        )

        # Check that a 'W' appears in the grid (representing the warp tile)
        lines = text_output.split("\n")
        grid_lines = []
        in_grid = False

        for line in lines:
            if "WALKABLE GRID" in line:
                in_grid = True
                continue
            elif in_grid and line.strip() == "":
                break
            elif in_grid:
                grid_lines.append(line)

        # The warp tile at position (14, 3) should appear as 'W' in grid position (7, 1)
        # (since we process every 2x2 area: 14//2 = 7, 3//2 = 1 but it's bottom-left)
        assert len(grid_lines) >= 2, (
            f"Expected at least 2 grid lines, got {len(grid_lines)}"
        )

        # Row 1 (index 1) should contain the warp tile
        if len(grid_lines) > 1:
            row_with_warp = grid_lines[1]
            assert "W" in row_with_warp, (
                f"Expected 'W' in grid row, got: '{row_with_warp}'"
            )

    def test_warp_priority_over_walkable_in_grid(self):
        """Test that warp tiles take priority over walkable symbol in grid display."""
        # Create a tile that is both walkable AND a warp
        game_state = {
            "step_counter": 0,
            "current_map": 38,
            "player_x": 4,
            "player_y": 3,
            "directions_available": {
                "north": True,
                "south": True,
                "east": True,
                "west": True,
            },
            "player_name": "TEST",
            "party_count": 0,
            "badges_obtained": 0,
            "is_in_battle": False,
            "tile_matrix": {
                "tiles": [
                    # Row 0-1
                    [{"is_walkable": False, "is_warp_tile": False} for _ in range(20)],
                    [{"is_walkable": False, "is_warp_tile": False} for _ in range(20)],
                    # Row 2-3 - tile that is both walkable and warp
                    [{"is_walkable": False, "is_warp_tile": False} for _ in range(20)],
                    [
                        {"is_walkable": False, "is_warp_tile": False}
                        if i != 10
                        else {
                            "is_walkable": True,
                            "is_warp_tile": True,
                        }  # Both walkable AND warp
                        for i in range(20)
                    ],
                    # Add more rows
                    *[
                        [
                            {"is_walkable": False, "is_warp_tile": False}
                            for _ in range(20)
                        ]
                        for _ in range(14)
                    ],
                ]
            },
        }

        text_output = format_game_state_text(game_state)

        # Should show 'W' not '.' for the tile that is both walkable and warp
        lines = text_output.split("\n")
        grid_lines = []
        in_grid = False

        for line in lines:
            if "WALKABLE GRID" in line:
                in_grid = True
                continue
            elif in_grid and line.strip() == "":
                break
            elif in_grid:
                grid_lines.append(line)

        # The warp tile should show as 'W', not '.'
        if len(grid_lines) > 1:
            row_with_warp = grid_lines[1]
            # Position 10//2 = 5, so character at index 5 should be 'W'
            assert len(row_with_warp) > 5, f"Grid row too short: '{row_with_warp}'"
            assert row_with_warp[5] == "W", (
                f"Expected 'W' at position 5, got '{row_with_warp[5]}' in row: '{row_with_warp}'"
            )

    def test_regular_walkable_tiles_still_show_as_dot(self):
        """Test that regular walkable tiles (non-warp) still show as '.' in grid."""
        game_state = {
            "step_counter": 0,
            "current_map": 38,
            "player_x": 4,
            "player_y": 3,
            "directions_available": {
                "north": True,
                "south": True,
                "east": True,
                "west": True,
            },
            "player_name": "TEST",
            "party_count": 0,
            "badges_obtained": 0,
            "is_in_battle": False,
            "tile_matrix": {
                "tiles": [
                    # Row 0-1
                    [{"is_walkable": False, "is_warp_tile": False} for _ in range(20)],
                    [{"is_walkable": False, "is_warp_tile": False} for _ in range(20)],
                    # Row 2-3 - regular walkable tile (not warp)
                    [{"is_walkable": False, "is_warp_tile": False} for _ in range(20)],
                    [
                        {"is_walkable": False, "is_warp_tile": False}
                        if i != 6
                        else {
                            "is_walkable": True,
                            "is_warp_tile": False,
                        }  # Walkable but NOT warp
                        for i in range(20)
                    ],
                    # Add more rows
                    *[
                        [
                            {"is_walkable": False, "is_warp_tile": False}
                            for _ in range(20)
                        ]
                        for _ in range(14)
                    ],
                ]
            },
        }

        text_output = format_game_state_text(game_state)

        lines = text_output.split("\n")
        grid_lines = []
        in_grid = False

        for line in lines:
            if "WALKABLE GRID" in line:
                in_grid = True
                continue
            elif in_grid and line.strip() == "":
                break
            elif in_grid:
                grid_lines.append(line)

        # The walkable (non-warp) tile should show as '.'
        if len(grid_lines) > 1:
            row_with_walkable = grid_lines[1]
            # Position 6//2 = 3, so character at index 3 should be '.'
            assert len(row_with_walkable) > 3, (
                f"Grid row too short: '{row_with_walkable}'"
            )
            assert row_with_walkable[3] == ".", (
                f"Expected '.' at position 3, got '{row_with_walkable[3]}' in row: '{row_with_walkable}'"
            )

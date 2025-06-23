"""
Test warp tile classification to ensure tiles are properly classified as WARP instead of ROAD.

This test verifies the fix for tile ID 26 being incorrectly classified as ROAD
when it should be WARP in certain tilesets like REDS_HOUSE_2.
"""

from open_llms_play_pokemon.game_state.data.tile_data_constants import TilesetID
from open_llms_play_pokemon.game_state.tile_data import TileType, classify_tile_type


class TestWarpTileClassification:
    """Test that warp tiles are properly classified over road tiles."""

    def test_tile_26_classified_as_warp_in_reds_house_2(self):
        """Test that tile ID 26 is classified as WARP in REDS_HOUSE_2 tileset."""
        # Tile 26 (0x1A) should be WARP in REDS_HOUSE_2, not ROAD
        tile_type = classify_tile_type(
            tile_id=26, is_walkable=True, tileset_id=TilesetID.REDS_HOUSE_2
        )

        assert tile_type == TileType.WARP, (
            f"Tile ID 26 in REDS_HOUSE_2 should be WARP, got {tile_type}. "
            "This was previously incorrectly classified as ROAD."
        )

    def test_tile_26_classified_as_warp_in_all_relevant_tilesets(self):
        """Test that tile ID 26 is classified as WARP in all tilesets where it's defined."""
        warp_tilesets = [
            TilesetID.REDS_HOUSE_1,
            TilesetID.REDS_HOUSE_2,
            TilesetID.CAVERN,
            TilesetID.LOBBY,
            TilesetID.MANSION,
        ]

        for tileset in warp_tilesets:
            tile_type = classify_tile_type(
                tile_id=26, is_walkable=True, tileset_id=tileset
            )

            assert tile_type == TileType.WARP, (
                f"Tile ID 26 in {tileset.name} should be WARP, got {tile_type}"
            )

    def test_tile_26_still_road_in_overworld(self):
        """Test that tile ID 26 is still classified as ROAD in OVERWORLD where it's not a warp."""
        # In OVERWORLD, tile 26 should still be ROAD since it's not in WARP_TILES
        tile_type = classify_tile_type(
            tile_id=26, is_walkable=True, tileset_id=TilesetID.OVERWORLD
        )

        assert tile_type == TileType.ROAD, (
            f"Tile ID 26 in OVERWORLD should be ROAD, got {tile_type}"
        )

    def test_warp_priority_over_road_classification(self):
        """Test that warp classification takes priority over road range (20-30)."""
        # Test with other tiles in the 20-30 range that are warps
        test_cases = [
            (TilesetID.REDS_HOUSE_1, 28),  # 0x1C - should be WARP
            (TilesetID.MANSION, 28),  # 0x1C - should be WARP
            (TilesetID.LOBBY, 28),  # 0x1C - should be WARP
        ]

        for tileset, tile_id in test_cases:
            tile_type = classify_tile_type(
                tile_id=tile_id, is_walkable=True, tileset_id=tileset
            )

            assert tile_type == TileType.WARP, (
                f"Tile ID {tile_id} in {tileset.name} should be WARP (priority over ROAD), got {tile_type}"
            )

    def test_road_tiles_still_work_when_not_warps(self):
        """Test that tiles in 20-30 range are still classified as ROAD when not warp/ledge tiles."""
        # Test tiles in road range that are not defined as warp, door, or ledge tiles
        # Exclude: 27 (0x1B - door), 29 (0x1D - ledge), others may have special functions
        road_tiles = [21, 22, 23, 24, 25, 30]

        for tile_id in road_tiles:
            tile_type = classify_tile_type(
                tile_id=tile_id, is_walkable=True, tileset_id=TilesetID.OVERWORLD
            )

            assert tile_type == TileType.ROAD, (
                f"Tile ID {tile_id} in OVERWORLD should be ROAD, got {tile_type}"
            )

    def test_overworld_door_tiles_are_warps(self):
        """Test that OVERWORLD door tiles (27, 88) are properly classified as WARP."""
        door_tiles = [27, 88]  # 0x1B, 0x58 in decimal

        for tile_id in door_tiles:
            tile_type = classify_tile_type(
                tile_id=tile_id, is_walkable=True, tileset_id=TilesetID.OVERWORLD
            )

            assert tile_type == TileType.WARP, (
                f"Tile ID {tile_id} in OVERWORLD should be WARP (door tile), got {tile_type}"
            )

    def test_capture_regression_tile_26_position_14_5(self):
        """Regression test for specific capture `20250622_202433` position (14, 5) tile 26."""
        # This was the original issue - tile 26 at position (14, 5) in REDS_HOUSE_2
        # was being classified as ROAD instead of WARP
        tile_type = classify_tile_type(
            tile_id=26, is_walkable=True, tileset_id=TilesetID.REDS_HOUSE_2
        )

        assert tile_type == TileType.WARP, (
            "Regression test failed: Tile 26 at position (14, 5) in capture `20250622_202433` "
            f"should be WARP, got {tile_type}. This tile should trigger map transitions."
        )

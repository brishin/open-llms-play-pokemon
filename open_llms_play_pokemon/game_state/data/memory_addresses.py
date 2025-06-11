from enum import IntEnum


class MemoryAddresses(IntEnum):
    player_name = 0xD158
    party_count = 0xD163
    # Party Pokemon HP addresses (current HP)
    party_mon_1_hp = 0xD16C
    party_mon_2_hp = 0xD198
    party_mon_3_hp = 0xD1C4
    party_mon_4_hp = 0xD1F0
    party_mon_5_hp = 0xD21C
    party_mon_6_hp = 0xD248
    # Party Pokemon Max HP addresses
    party_mon_1_max_hp = 0xD18D
    party_mon_2_max_hp = 0xD1B9
    party_mon_3_max_hp = 0xD1E5
    party_mon_4_max_hp = 0xD211
    party_mon_5_max_hp = 0xD23D
    party_mon_6_max_hp = 0xD269
    # Party Pokemon Level addresses
    party_mon_1_level = 0xD18C
    party_mon_2_level = 0xD1B8
    party_mon_3_level = 0xD1E4
    party_mon_4_level = 0xD210
    party_mon_5_level = 0xD23C
    party_mon_6_level = 0xD268
    # Game state
    obtained_badges = 0xD356
    current_map = 0xD35E
    y_coord = 0xD361
    x_coord = 0xD362
    # Battle state
    battle_mon_hp = 0xD015
    battle_mon_max_hp = 0xD017  # Adding missing max HP
    enemy_mon_hp = 0xCFE6
    enemy_mon_max_hp = 0xCFE8  # Adding missing enemy max HP
    is_in_battle = 0xD057
    # Event flags range
    event_flags_start = 0xD747
    event_flags_end = 0xD87E
    # Opponent Pokemon levels (for difficulty tracking)
    opp_mon_1_level = 0xD8C5
    opp_mon_2_level = 0xD8F1
    opp_mon_3_level = 0xD91D
    opp_mon_4_level = 0xD949
    opp_mon_5_level = 0xD975
    opp_mon_6_level = 0xD9A1

"""Reviewed ROM enablement and explicit wire mappings; never inferred from IDs.

Schema 2's 255 command ceiling is an authoring bound, not an enabled whitelist.
Each content revision below remains immutable when a later revision is added.
"""
LEGACY_FIELD_CAPABILITIES = ['break_crack', 'burn_thorns', 'draw_ore', 'drive_sail', 'earth_socket', 'expose_fire', 'expose_stone', 'expose_wind', 'fill_basin', 'fire_socket', 'grow_bridge', 'grow_roots', 'ignite', 'link_pools', 'press_weight', 'reveal_current', 'tune_latch', 'turn_vane', 'uncap_well', 'wind_socket', 'wood_socket', 'reel_load', 'store_heat', 'float_load', 'align_rail']
FIELD_CAPABILITIES = LEGACY_FIELD_CAPABILITIES + ['refract_beam']
# Explicit mappings make a new capability/gate/trial a reviewable wire decision.
CAPABILITY_MASKS = dict(zip(FIELD_CAPABILITIES, [
    0x00000001, 0x00000002, 0x00000004, 0x00000008, 0x00000010,
    0x00000020, 0x00000040, 0x00000080, 0x00000100, 0x00000200,
    0x00000400, 0x00000800, 0x00001000, 0x00002000, 0x00004000,
    0x00008000, 0x00010000, 0x00020000, 0x00040000, 0x00080000,
    0x00100000, 0x00200000, 0x00400000, 0x00800000, 0x01000000,
    0x02000000]))
GATE_MASKS = {'grove_clear':1, 'sky_clear':2, 'core_clear':4,
              'reed_basin_restored':8, 'north_harbor_ready':16,
              'north_counterworks_stable':32, 'south_ready':64}
# name: (immutable family, local key, wire bit, introduced revision, sources)
TRIAL_POLICY = {
    'restore_hearth':('F001',1,1,1,(1,)),
    'restore_canopy':('F002',1,2,1,(4,)),
    'mend_wind_loom':('F003',1,4,1,(7,)),
    'raise_amber_arch':('F004',1,8,1,(10,)),
    'join_two_pools':('F005',1,16,2,(13,)),
    'tension_roof':('F007',1,32,3,(19,)),
    'dry_ledger':('F008',1,64,3,(22,)),
    'fragile_cargo':('F025',1,128,3,(73,)),
    'balanced_reach':('F026',1,256,3,(75,)),
    'compass_round':('F027',1,512,3,(77,)),
    'south_root_supports':('F009',1,1,4,(25,)),
    'south_drainage_branches':('F010',1,1,4,(28,)),
    'south_demo_receivers':('F028',1,1,4,(79,)),
    'south_safe_drying':('F029',1,1,4,(81,)),
    'south_shade_loop':('F030',1,1,4,(83,)),
    'south_paired_catches':('F031',1,1,4,(85,)),
    'south_canopy_route':('F032',1,1,4,(87,)),
    'south_runnel_sources':('F033',1,1,4,(89,)),
    'south_screened_beacons':('F034',1,1,4,(91,)),
    'south_socket_diagram':('F035',1,1,4,(93,)),
}
SOUTHERN_FORMS = [25,26,28,29,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94]
SOUTHERN_EDGES = [[25,26],[28,29],[79,80],[81,82],[83,84],[85,86],[87,88],[89,90],[91,92],[93,94]]
# Each list is explicit table order. Existing prefixes may never be reordered.
REVISION_POLICY = {
    1: {'forms':[1,2,4,5,7,8,10,11], 'abilities':[1,2,3,4,5,6,7,8],
        'edges':[[1,2],[4,5],[7,8],[10,11]], 'learns':12},
    2: {'forms':[1,2,4,5,7,8,10,11,13,14,16], 'abilities':[1,2,3,4,5,6,7,8,9,10,11],
        'edges':[[1,2],[4,5],[7,8],[10,11],[13,14]], 'learns':16},
    3: {'forms':[1,2,4,5,7,8,10,11,13,14,16,19,20,22,23,73,74,75,76,77,78],
        'abilities':[1,2,3,4,5,6,7,8,9,10,11,13,14,15,16,17,18,19,20,21,22],
        'edges':[[1,2],[4,5],[7,8],[10,11],[13,14],[19,20],[22,23],[73,74],[75,76],[77,78]], 'learns':31},
    4: {'forms':[1,2,4,5,7,8,10,11,13,14,16,19,20,22,23,73,74,75,76,77,78,
                  25,26,28,29,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94],
        'abilities':[1,2,3,4,5,6,7,8,9,10,11,13,14,15,16,17,18,19,20,21,22,
                     23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42],
        'edges':[[1,2],[4,5],[7,8],[10,11],[13,14],[19,20],[22,23],[73,74],[75,76],[77,78],
                 [25,26],[28,29],[79,80],[81,82],[83,84],[85,86],[87,88],[89,90],[91,92],[93,94]], 'learns':61},
}

# Approved Magma current-only extension; revisions1–4 above remain frozen.
MAGMA_FORMS = [31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 95, 96, 97, 98, 99, 100]
MAGMA_EDGES = [[31, 32], [32, 33], [34, 35], [35, 36], [37, 38], [37, 39], [40, 41], [40, 42], [43, 44], [43, 45], [46, 47], [46, 48], [95, 96], [97, 98], [99, 100]]
CURRENT_POLARITY_OVERRIDES = {39: 'yang', 48: 'yin'}
GATE_MASKS.update({'magma_ready':256, 'caldera_open':512})
TRIAL_POLICY.update({
    'magma_three_cool_shelves':('F011',1,1,5,(31,)),
    'magma_one_hearth_three_uses':('F011',2,2,5,(32,)),
    'magma_a_walkable_load':('F012',1,1,5,(34,)),
    'magma_the_unbroken_crossing':('F012',2,2,5,(35,)),
    'magma_shelter_the_roots':('F013',1,1,5,(37,)),
    'magma_scatter_the_canopy':('F013',2,2,5,(37,)),
    'magma_keep_the_last_drop':('F014',1,1,5,(40,)),
    'magma_share_the_runnel':('F014',2,2,5,(40,)),
    'magma_true_the_buried_seam':('F015',1,1,5,(43,)),
    'magma_balance_the_hanging_note':('F015',2,2,5,(43,)),
    'magma_lift_the_warm_air':('F016',1,1,5,(46,)),
    'magma_settle_the_ash':('F016',2,2,5,(46,)),
    'magma_find_the_cold_seam':('F036',1,1,5,(95,)),
    'magma_the_cloth_stays_clear':('F037',1,1,5,(97,)),
    'magma_the_quiet_chord':('F038',1,1,5,(99,)),
})
TRIAL_PREREQUISITES = {'magma_one_hearth_three_uses': 1, 'magma_the_unbroken_crossing': 1}
REVISION_POLICY[5] = {'forms':REVISION_POLICY[4]['forms'] + MAGMA_FORMS,
    'abilities':REVISION_POLICY[4]['abilities'] + list(range(43,67)),
    'edges':REVISION_POLICY[4]['edges'] + MAGMA_EDGES, 'learns':102}

# Reviewed Underwater current-only append; revisions1–5 above remain frozen.
UNDERWATER_FORMS = [49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72]
UNDERWATER_EDGES = [[49, 50], [49, 51], [52, 53], [52, 54], [55, 56], [55, 57], [58, 59], [58, 60], [61, 62], [61, 63], [64, 65], [64, 66], [67, 68], [67, 69], [70, 71], [70, 72]]
FIELD_CAPABILITIES += ['echo_outline', 'shift_ballast', 'inscribe_trace', 'unfold_screen']
CAPABILITY_MASKS.update({'echo_outline': 67108864, 'shift_ballast': 134217728, 'inscribe_trace': 268435456, 'unfold_screen': 536870912})
GATE_MASKS.update({'underwater_ready':1024, 'palinode_open':2048})
CURRENT_POLARITY_OVERRIDES.update({49: 'yin', 50: 'yin', 51: 'yang', 52: 'yang', 53: 'yin', 54: 'yang', 55: 'yang', 56: 'yang', 57: 'yin', 58: 'yin', 59: 'yin', 60: 'yang', 61: 'yang', 62: 'yin', 63: 'yang', 64: 'yin', 65: 'yin', 66: 'yang', 67: 'yang', 68: 'yang', 69: 'yin', 70: 'yin', 71: 'yin', 72: 'yang'})
TRIAL_POLICY.update({
    'uw_read_the_missing_edge':('F017', 1, 1, 6, (49,)),
    'uw_leave_a_silent_margin':('F017', 2, 2, 6, (49,)),
    'uw_one_low_one_high':('F018', 1, 1, 6, (52,)),
    'uw_hold_the_middle_depth':('F018', 2, 2, 6, (52,)),
    'uw_draw_an_open_ladder':('F019', 1, 1, 6, (55,)),
    'uw_make_a_nested_bower':('F019', 2, 2, 6, (55,)),
    'uw_roll_the_near_edge':('F020', 1, 1, 6, (58,)),
    'uw_leave_two_windows':('F020', 2, 2, 6, (58,)),
    'uw_warm_the_outer_crown':('F021', 1, 1, 6, (61,)),
    'uw_write_a_warm_path':('F021', 2, 2, 6, (61,)),
    'uw_turn_the_five_petals':('F022', 1, 1, 6, (64,)),
    'uw_fold_without_overlap':('F022', 2, 2, 6, (64,)),
    'uw_keep_the_hinge_clear':('F023', 1, 1, 6, (67,)),
    'uw_cross_once_return_once':('F023', 2, 2, 6, (67,)),
    'uw_keep_the_diagonal_open':('F024', 1, 1, 6, (70,)),
    'uw_frame_the_empty_center':('F024', 2, 2, 6, (70,)),
})
REVISION_POLICY[6] = {"forms":REVISION_POLICY[5]["forms"] + UNDERWATER_FORMS,
    "abilities":REVISION_POLICY[5]["abilities"] + list(range(67,91)),
    "edges":REVISION_POLICY[5]["edges"] + UNDERWATER_EDGES, "learns":142}

# Reviewed Return I current-only append; revisions1-6 above remain frozen.
RETURN_FORMS = [3, 6, 9, 12, 15, 17, 18, 21, 24, 27, 30, 101, 102, 103, 104]
RETURN_EDGES = [[2, 3], [5, 6], [8, 9], [11, 12], [14, 15], [16, 17], [17, 18], [20, 21], [23, 24], [26, 27], [29, 30], [101, 102], [103, 104]]
GATE_MASKS.update({'return_ready':4096, 'home_map_joined':8192})
TRIAL_POLICY.update({
    'return_two_waiting_hearths':('F001', 2, 1024, 7, (2,)),
    'return_shelter_with_an_opening':('F002', 2, 1024, 7, (5,)),
    'return_sail_stop':('F003', 2, 1024, 7, (8,)),
    'return_walking_friend':('F004', 2, 1024, 7, (11,)),
    'return_water_around_reeds':('F005', 2, 1024, 7, (14,)),
    'return_quiet_beat':('F006', 1, 1024, 7, (16,)),
    'return_bell_empty_middle':('F006', 2, 2048, 7, (17,)),
    'return_load_nobody_drops':('F007', 2, 1024, 7, (20,)),
    'return_last_shelter':('F008', 2, 1024, 7, (23,)),
    'return_branch_air':('F009', 2, 1024, 7, (26,)),
    'return_patient_spillway':('F010', 2, 1024, 7, (29,)),
    'return_listen_without_pulling':('F039', 1, 1024, 7, (101,)),
    'return_passenger_safe_landing':('F040', 1, 1024, 7, (103,)),
})
TRIAL_PREREQUISITES.update({
    'return_two_waiting_hearths':1,
    'return_shelter_with_an_opening':2,
    'return_sail_stop':4,
    'return_walking_friend':8,
    'return_water_around_reeds':16,
    'return_bell_empty_middle':1024,
    'return_load_nobody_drops':32,
    'return_last_shelter':64,
    'return_branch_air':1,
    'return_patient_spillway':1,
})
REVISION_POLICY[7] = {'forms':REVISION_POLICY[6]['forms'] + RETURN_FORMS,
    'abilities':REVISION_POLICY[6]['abilities'] + list(range(91,106)),
    'edges':REVISION_POLICY[6]['edges'] + RETURN_EDGES, 'learns':180}

# Reviewed Shared Horizons append; revisions1-7 above remain frozen.
HORIZONS_FORMS = list(range(105,121))
HORIZONS_EDGES = [[105,106],[107,108],[109,110],[111,112]]
# Command IDs and form IDs are separate namespaces. In particular command121
# belongs to ordinary form120 while legendary form121 remains disabled.
HORIZONS_SIGNATURES = {105:106,106:107,107:108,108:109,109:110,110:111,
    111:112,112:113,113:114,114:115,115:116,116:117,117:118,118:119,
    119:120,120:121}
HORIZONS_INHERITED_COMMANDS = {106:106,108:108,110:110,112:112}
GATE_MASKS.update({'horizons_ready':16384})
TRIAL_POLICY.update({
    'horizons_a_hem_with_an_opening':('F041', 1, 1024, 8, (105,)),
    'horizons_a_warmth_that_can_breathe':('F042', 1, 1024, 8, (107,)),
    'horizons_a_weight_with_a_way_back':('F043', 1, 1024, 8, (109,)),
    'horizons_light_through_two_hands':('F044', 1, 1024, 8, (111,)),
})
REVISION_POLICY[8] = {'forms':REVISION_POLICY[7]['forms'] + HORIZONS_FORMS,
    'abilities':REVISION_POLICY[7]['abilities'] + list(range(106,122)),
    'edges':REVISION_POLICY[7]['edges'] + HORIZONS_EDGES, 'learns':200}

# Current-only final chapter. No new capability, evolution or personal trial bit.
COVENANT_FORMS = list(range(121,129))
COVENANT_SIGNATURES = {121:12,122:122,123:123,124:124,125:125,126:126,127:127,128:128}
COVENANT_SUPPORT_COMMANDS = [[106,108,110,102,104],[106,104],[108,102],
    [110,106],[102,106],[106,112],[104,110],[108,102,110]]
COVENANT_GATE_NAMES = ['stilltide_covenant','covenant_vowbough','covenant_kilnwhorl',
    'covenant_cairnward','covenant_bellmantle','covenant_shadeweaver',
    'covenant_tideplume','covenant_hearthmoth']
REVISION_POLICY[9] = {'forms':REVISION_POLICY[8]['forms'] + COVENANT_FORMS,
    'abilities':REVISION_POLICY[8]['abilities'] + [12] + list(range(122,129)),
    'edges':REVISION_POLICY[8]['edges'][:], 'learns':209}

# Canonical current-preservation pins captured before this append from the
# accepted Shared Horizons C baseline. These are not a historical save reader.
# Command12 and form121 preserve the entire disabled draft rows; only their
# unimplemented gate/trial placeholder is superseded by schema3 covenant data.
COVENANT_PRESERVATION_SHA256 = {
    'forms': 'fd77eb542395d355cdae9d98dcaea107677c781472fdc095321972233f5597b0',
    'abilities': '02049bdd048a00c09c0f73cfddfb5673d5a87f36dde333d8f0905ff398149cda',
    'stilltide': '69567e7f808054bc5f035592d492dee805905bbe62bf99bd8f8a0752350a3a20',
    'evolutions': '10e7dcf6792f6734a69fc7e75d0f20fa1d0eb35cb26484e52740528b48957eb0',
    'trial_bindings': 'd80abdab83d0803e0a644d02ee108a581aafd74721ba80fb275cd59914d7d669',
    'families': 'ef33a28486a49a02964f188dacaeb7454371b12b573e98568967887b39fcb48d',
    'field_capabilities': '31645300160f1892d8d187c234d2bd165703194c796054b21433eb66d513c63c',
    'gates': 'fabecdc2542dd097c3020e0ec09c316e6a4b4e93ee27221c7fcca36c5409618e',
    'trials': '67f3925b725ada50b7724f2b58b3ab066545cd8f8bd11238a009f0e24d4550ab',
}

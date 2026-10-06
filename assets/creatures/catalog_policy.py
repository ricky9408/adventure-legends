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

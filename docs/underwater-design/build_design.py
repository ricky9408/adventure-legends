"""Design artifacts only. Reads Magma; writes only beside this script."""
from pathlib import Path
import copy, hashlib, json, re
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parents[2]/'adventure-legends-magma'
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'assets/creatures'))
from catalog_source import load_catalog

def write(name,data):
 p=ROOT/name
 s=json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n'
 assert len(s.encode())<90000,(name,len(s.encode()))
 p.write_text(s)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
catalog=load_catalog(BASE/'assets/creatures/catalog.json')
enabled=json.loads((BASE/'assets/creatures/enabled.json').read_text())
# Name, phase, polarities, visual brief per form, locomotion per form.
FAMILIES=[
(17,'water',['yin','yin','yang'],['Inkbud','Scriptcuttle','Fanfolio'],[
 'A teardrop cuttlefish with a blunt living face, six short arm tips and two long bracket feelers; dark mantle separated from pale fins.',
 'A long rectangular cuttlefish mantle between two scalloped fin rails; four long arms curl into open brackets beneath its large eyes.',
 'A broad cuttlefish with joined webbed arms spread into two offset fans; the face sits in a deep central V, with a short mantle behind.'],[
 'Mantle pulses forward, fins ripple left-to-right, feelers catch up.',
 'Long steady fin-wave glide, then separate left and right bracket-arm folds.',
 'Alternating broad fan strokes, a sideways bank, and a deliberate web fold.']),
(18,'earth',['yang','yin','yang'],['Bobclam','Keelcasket','Crownfloat'],[
 'A living rounded clam with two unequal chalk valves, a visible smiling hinge face and one thick scalloped foot.',
 'A long low clam with an open split-keel lower valve, broad muscular foot and an eye-bearing upper lip projecting forward.',
 'A tall clam with two thin high valves held in an open crown above its face; a short inflated foot forms a visible round ballast below.'],[
 'Foot reaches, shell tips forward, valves clap gently after the pull.',
 'Low foot ripples while the keel rocks in opposite phase; eyelids track the path.',
 'Foot inflates for a short buoyant rise then settles; valves open asymmetrically.']),
(19,'wood',['yang','yang','yin'],['Frondfoal','Trellisseer','Bowercoil'],[
 'An upright seahorse with a leaf-frilled short snout, two small fins and a single hook tail with a bare visible tip.',
 'A tall seahorse whose paired branching back fronds frame an open ladder behind its small living face; long nearly straight tail.',
 'A compact seahorse curled sideways around one broad living kelp loop, head outside the loop and fins above its low center.'],[
 'Two fin flutters, forward nod and uncoiling tail step without a static hover.',
 'Long upright fin strokes; the tail straightens and the open frond ladder flexes.',
 'Tail hooks, releases and rolls one quarter-turn while the face remains upright.']),
(20,'metal',['yin','yin','yang'],['Rimlet','Gateshield','Stencilback'],[
 'A low horseshoe-crab animal with a smooth U-shaped metal rim, two bright front eyes, six tiny feet and a slender jointed tail.',
 'A narrow horseshoe body whose two upright rim halves form an open portal around its face; splayed rear feet and a fork-ended tail.',
 'A broad rectangular horseshoe shell with two large asymmetric open windows; a living face and short feet remain visible at its front.'],[
 'Six feet scuttle in offset pairs, tail steers late and the rim dips.',
 'Diagonal braced steps, opening rim halves and a two-beat gate-close gesture.',
 'Wide planted stride; front shell lifts first, followed by a flat deliberate stamp.']),
(21,'fire',['yang','yin','yang'],['Ventplume','Haloworm','Trailwick'],[
 'A short soft tube-worm with a rounded face below a forked warm feather crown; flexible pale tube ends in three root toes.',
 'A tall tube-worm whose two offset half-fan crowns leave an open crescent above its blinking face; a narrow coiled foot.',
 'A low long tube-worm with four separated glowing mantle folds, exposed forward eyes and a single trailing wick-like feeler.'],[
 'Toes grip, tube stretches, crown opens and contracts in a breathing beat.',
 'Foot uncoils, neck bows, two half-fans open in opposite order.',
 'Muscular waves travel along the soft tube; folds brighten from head to tail.']),
(22,'wood',['yin','yin','yang'],['Palmstar','Crossbloom','Foldrunner'],[
 'A soft five-armed sea star with a raised expressive center and broad kelp-edged arm tips; gaps are wide and individually readable.',
 'A high-centered star with four long unequal cross arms and a fifth short rear arm; open diagonal gaps and a face held above the center.',
 'A long folded star animal walking on three joined zigzag arms while two short forearms frame its face; no radial silhouette at rest.'],[
 'Two arms plant while three reach; the raised face tilts before each turn.',
 'Opposite arms extend together and the center rises, then alternating arms settle.',
 'A traveling accordion fold changes the two major bends; forearms feel the next step.']),
(23,'metal',['yang','yang','yin'],['Linkeel','Hingejaw','Claspcoil'],[
 'A slender eel with a soft blunt face, three separated metallic collar plates and a flexible bare tail; no legs or wing fins.',
 'An angular eel with two long articulated body sections, an open elbow gap and a broad hinged jaw around a visible living face.',
 'A short thick eel curled into an unequal figure eight with two open loops; face rests beside the crossing and tail remains free.'],[
 'One lateral body wave travels through all three loose collars; eyes lead the turn.',
 'Front segment aims, rear segment swings around a clearly planted joint, jaw closes.',
 'Large loop contracts as small loop expands, then the crossing moves one foot-length.']),
(24,'water',['yin','yin','yang'],['Combgleam','Veilglass','Triadome'],[
 'A translucent oval comb-jelly with a small face, four broad ciliary comb bands and two short joined feeding lobes, never an umbrella.',
 'A tall diamond comb-jelly with one broad diagonal veil and two separated trailing lobes; its face shows through a pale central window.',
 'A low triangular comb-jelly with three connected soft corner lobes around an open-looking central window; two eyes sit on the leading lobe.'],[
 'Four comb bands ripple in sequence while the oval body compresses lengthwise.',
 'Diagonal veil folds across the body and opens on the other side; lobes trail.',
 'Three corners pulse one at a time, giving a slow turning glide and clear landing shadow.'])]
# One explicit geometry/control contract per command; no generic colored-bolt generator.
# Name, primitive, geometry, control, startup/active/lifetime/cooldown, damage cap, old cousins, difference.
ACTIONS=[
('Range Echo','return_range_band','Outbound nondamaging lane36x8; return only damages its marked forward18..30px band.', 'Face the range bracket before R; no tracking after startup.',12,18,36,90,16,[39,52],'Range-band occupancy, not a marked weapon follow-up or close square rush arrest.'),
('Bracket Fold','converging_diagonal_brackets','Two20px diagonal segments sweep inward from lateral +/-14 to a point28px forward; neither is a projectile.', 'Left/right during the first8 updates chooses the folding diagonal; otherwise facing default.',14,12,38,120,24,[34,54],'Moving inward diagonal brackets with a closing seam, not a static crossing gate or traveling band.'),
('Margin Cycle','ordered_corner_cells','Four8x8 corner cells of a40x24 rectangle activate one at a time in clockwise order; sides and center never damage.', 'First8 updates choose the starting corner with one cardinal direction; all corners are previewed.',16,24,48,120,24,[5,66],'Ordered discrete corners, rather than a line of cells or continuous lobed ring edge.'),
('Ballast Nudge','perpendicular_side_push','One12x16 shell stroke24px ahead deals16Q4 and pushes an ordinary target6px perpendicular, swept in1px steps.', 'Left/right during first8 updates chooses the push side; player never moves.',12,6,28,90,16,[17,25],'Explicit lateral displacement perpendicular to facing, not forward surge or widening wedge.'),
('Keel Return','entry_edge_retrace','A20x20 open keel outline catches one entering ordinary foe; after8 updates nudges it at most8px back toward its recorded entry edge.', 'Place with facing; entry edge is recorded once and visibly highlighted.',14,32,54,120,24,[26,31],'Remembers the entrant edge and reverses that approach, not melee parry or fixed side diversion.'),
('Crown Teeter','alternating_weight_lobes','Two14x12 lobes24px ahead exchange raised/lowered states twice; only the downward lobe damages; central8px corridor stays empty.', 'Choose initial lower side during first8 updates; second fall is automatic.',16,20,48,120,24,[62,48],'Repeated inverse paired-lobe states with a permanent center corridor, not consecutive forward wedges or a crescent.'),
('Crook Reach','three_segment_hook','A3px-wide U path goes forward20, sideways12, back8; swept tip stops on the first wall.', 'Left/right in first8 updates chooses hook side; total path40px.',12,20,40,90,16,[64,18],'Three-segment returning hook can reach a nearby flank; neither existing two-segment L can do this.'),
('Trellis Quarter','anchored_quadrant_sweep','One16px frond pivots through90 degrees around a point20px ahead; inner6px hub is harmless; entire sweep is wall-clipped.', 'Startup selects clockwise/counterclockwise; pivot and swept sector are visible.',16,18,44,120,24,[38,57],'Remote anchored quarter-sector, not player-centered crescent or swing plus released shard.'),
('Bower Ladder','staggered_disjoint_rungs','Three12x4 bars at forward12/24/36 and alternating lateral offsets-10/+10/-10 activate near-to-far with8-update intervals.', 'Facing rotates the ladder; side selection mirrors the offsets, never length or damage.',16,24,48,120,24,[5,53],'A staggered corridor of separated transverse rungs with open gaps, not straight hearth cells or co-located drops.'),
('Rimcrawl','near_wall_tangent_crawl','A6px rim travels16px then follows the near face of its first wall for at most24px; convex corners stop it; no crossing the wall.', 'Choose tangential left/right in startup; without a wall it ends after16px.',12,28,44,90,16,[41,56],'Wall-tangent surface crawl rather than a reflected ray or straight corkscrew; preview shows the stop corner.'),
('Gate Release','directional_exit_slit','Two18px parallel lips separated12px register one target entering from the front; only that target leaving the back triggers the24Q4 close.', 'Facing selects entry/exit; backing out safely cancels; no target is trapped.',14,132,154,180,24,[34,47],'Directed enter-then-exit receipt, not arbitrary crossing or contact counter; no collision wall.'),
('Stencil Press','perforated_rectangle_stamp','A28x24 stamp24px ahead leaves two6x10 empty windows at offset-8/+7; after18 warning updates its solid stencil hits once.', 'Left/right startup mirrors the unequal windows; all safe holes are previewed.',18,4,34,120,24,[45,51],'Perforated nonconvex filled footprint with two holes, rather than radial burst or solid landing cell.'),
('Warm Script','triangular_wave_trace','One3px trace advances32px along a triangular centerline of lateral amplitude6 and period16; no homing or fork.', 'Facing sets axis; startup side changes initial wave slope.',12,16,36,90,16,[1,58],'Bounded oscillating lane with four turns, not straight or diagonal dart.'),
('Halfhalo','opposed_semicircle_sequence','A12px front semicircle then a24px rear semicircle grow in sequence; each retains a90-degree gap; one target budget across both.', 'Startup side chooses gap diagonal; the second gap is opposite.',16,24,50,120,24,[30,66],'Alternating opposite semicircle lobes, not a whole annulus or five-lobed full ring.'),
('Wicktrace','recorded_player_trail','Record four player positions over12 updates, each segment capped12px; after12 warning updates a warm tip retraces up to36px in reverse.', 'Walk to draw the preview during the first12 active-play updates; standing creates only one8px spark.',12,24,56,120,24,[42,40],'Input-authored multi-segment spatial history, not recall down a current lane or enemy-to-enemy link.'),
('Palmturn','five_tip_partial_rotation','Five4x4 arm-tip cells at radius16 rotate exactly72 degrees as one procedural shape; center and connecting arms are harmless.', 'Startup side selects rotation direction; no full orbit or retained shield.',12,15,38,90,16,[66,37],'Five discrete rotating tips with safe gaps, not an expanding edge or Y fork.'),
('Crossbloom','anisotropic_hollow_cross','Four4px-wide arms extend to horizontal +/-24 and vertical +/-12 around a point16px ahead; central8x8 square remains harmless.', 'Startup up/down swaps the long and short axes; expansion is one bounded shape.',16,16,44,120,24,[50,34],'Unequal cross axes with hollow center, not parallel roots or two facing blades.'),
('Accordion Run','two_hinge_articulated_sweep','A36px ribbon of three12px segments folds at two joints from straight to a mirrored Z;2px tips damage, broad ribbon body is visual only.', 'Startup side chooses Z orientation; both hinge arcs preview before movement.',16,18,46,120,24,[64,24],'Two simultaneously moving hinges with three segments, not a tip following two fixed segments.'),
('Coil Meter','out_of_phase_zigzag_pulses','A fixed36px zigzag with two90-degree joints carries two6px pulses in opposite directions; only one pulse is damaging at a time.', 'Startup side mirrors the zigzag; alternating live pulse is bright and solid-outline.',12,24,44,90,16,[63,65],'Alternating-direction occupancy of a bent lane, not one moving bud or outward bead fan.'),
('Hinge Bite','remote_hinged_bar','A20px narrow jaw bar pivots90 degrees around a visible joint28px ahead; require player-to-joint and joint-to-hit line of sight.', 'Choose pivot side in first8 updates; jaw point stays fixed after startup.',16,14,42,120,24,[57,33],'Remote jaw pivot with two line-of-sight checks, not local swing-and-shard or frontal contact parry.'),
('Loopclasp','figure_eight_crossing_gate','Two unequal loop outlines of radii10 and16 share one8x8 crossing; alternating loops prime the crossing twice; only the crossing damages.', 'Facing aligns the long loop; startup side selects which loop primes first.',18,24,52,120,24,[30,66],'Localized timed crossing within a figure-eight preview, not damage on a ring perimeter.'),
('Combfront','gapped_moving_fence','One24px transverse comb with four3px damaging teeth and four3px gaps advances24px; all teeth stop together at first scenery contact.', 'Facing sets motion; startup side shifts tooth alignment by3px.',12,16,36,90,16,[54,65],'Moving fence with real traversable hit gaps, not solid band or divergent beads.'),
('Veil Divide','alternating_triangle_partition','A28x28 square24px ahead alternately activates its two triangles; a6px diagonal stripe stays harmless and each target hits once total.', 'Startup left/right chooses diagonal; first triangle is marked with dots, second with stripes.',18,24,52,120,24,[50,60],'Alternating filled half-planes separated by a safe diagonal, not root lines or projectile-consuming screen.'),
('Triad Nest','hollow_triangle_interior','An equilateral-like triangle with vertices(0,24),(-18,-10),(18,-10) about a point24px ahead flashes its interior after20 updates; central6x6 hole stays harmless.', 'Startup up/down inverts the triangle around the same center; no vertex can cross solid scenery.',20,4,38,120,24,[51,66],'Triangle interior with a center aperture, not solid small marker or ring-edge-only damage.')]
CAPS=[['echo_outline'],['shift_ballast'],['grow_roots','inscribe_trace'],['draw_ore','align_rail','unfold_screen'],['store_heat','ignite'],['grow_bridge','inscribe_trace'],['tune_latch','align_rail'],['refract_beam','echo_outline']]
NEW_CAPS=[('echo_outline',27,1<<26),('shift_ballast',28,1<<27),('inscribe_trace',29,1<<28),('unfold_screen',30,1<<29)]
forms=[];abilities=[];contracts=[];family_cards=[]
for fi,(fam,phase,polarities,names,silhouettes,motions) in enumerate(FAMILIES):
 base=49+3*fi
 for n in range(3):
  idx=fi*3+n; fid=base+n; aid=67+idx; a=ACTIONS[idx]
  stats=([34,36,30,44,36] if n==0 else ([46,42,54,62,36] if n==1 else [40,62,36,48,54]))
  # Slight redistribution for distinct phase roles, preserving exact stat total.
  if fi%2:stats[0]+=4;stats[4]-=4
  form={'id':fid,'name':names[n],'phase':phase,'polarity':polarities[n],
   'stats':dict(zip(['vitality','power','guard','focus','haste'],stats)), 'stat_total':sum(stats),
   'signature_ability':aid,'learnset':[{'level':1,'ability_id':67+fi*3}]+([] if n==0 else [{'level':28,'ability_id':aid}]),
   'field_caps':CAPS[fi], 'silhouette':silhouettes[n], 'motion':motions[n],
   'role':['Readable positioning and field teacher','Deliberate control and protected gaps','Expressive movement and spatial offense'][n],
   'acquisition':{'kind':'bond_trial' if n==0 else 'evolution','repeatable':n==0}}
  if n==0:form['acquisition']['gate']=f'underwater_source_{fam}'
  forms.append(form)
  abilities.append({'id':aid,'name':a[0],'phase':phase,'handler':a[0].lower().replace(' ','_'), 'cooldown_updates':a[7], 'effect':a[2]+' '+a[3], 'field_caps':CAPS[fi]})
  contracts.append({'form_id':fid,'ability_id':aid,'primitive':a[1],'geometry':a[2],'control':a[3],
   'startup_updates':a[4],'active_updates':a[5],'lifetime_updates':a[6],'cooldown_updates':a[7],'damage_q4_per_target_max':a[8],
   'max_moving_objects':2 if idx in [1,18] else 1,'max_enemy_slots':6,'nearest_existing_ability_ids':a[9],'difference':a[10],
   'native_art':{'walk_box':[16,16],'portrait_box':[32,32],'directions':4,'walk_frames_per_direction':4,'ability_poses':3,'no_scaled_base':True},
   'collision':'Every damaging swept segment checks scenery and target line of sight; dynamic geometry changes invalidate blocked shape without extending age, cooldown or hit ledger.',
   'target_policy':'One snapshotted cast; spawn-generation hit receipts; ordinary displacement only; bosses retain authored vulnerability and never move/retime from this command.'})
 family_cards.append({'family_id':f'F{fam:03}','base_form':base,'branches':[base+1,base+2],'phase':phase,'branch_decision':ACTIONS[fi*3+1][1]+' versus '+ACTIONS[fi*3+2][1],
  'repeat_source':f'UW_REPEAT_{fam}','individuals_required':2,'history_forms':3,'base_command_inherited':67+fi*3})
write('creature_forms.json',forms);write('ability_contracts.json',contracts);write('families.json',family_cards)
# Eight connected places, four dungeon rooms. Local coordinates are concept geometry, not implemented collision.
AREA_SPEC=[
(46,'Nacreway','town',[480,320],['rest','sanctuary','archive keeper','shellwright','market','two teaching ponds'],[47,48],None,0),
(47,'Siltglass Commons','exploration',[480,320],['echo practice','buoyancy causeway','fallen chart','open meadow combat'],[46,50],None,0),
(48,'Kelp Promenade','exploration',[480,320],['woven frond alleys','living migration lane','visible crabs','safe observation benches'],[46,49,51],None,0),
(49,'Hollow Oyster Garden','discovery',[240,160],['hollow shell rooms','sound shadows','comb-jelly nursery','clue mural'],[48,52],None,0),
(50,'Palinode Vestibule','dungeon',[240,160],['two overlapping map leaves','movable ballast shelves','persistent first archive record'],[47,51],40,0),
(51,'Countercurrent Stacks','dungeon',[480,320],['split-level shelves','visible marked lift','quiet refuge','missing procession sketch'],[50,52,48],40,1),
(52,'Listening Chamber','dungeon',[240,160],['sound-shadow floor','two conflicting recollections','open-water return lift'],[51,53,49],40,3),
(53,'Vestige Court','finale',[240,160],['broken procession sculpture','guardian relief','final memory window','return arch'],[52,46],40,7)]
areas=[]
for rid,name,kind,size,landmarks,adj,q,prefix in AREA_SPEC:
 areas.append({'id':rid,'name':name,'kind':kind,'size_px':size,'visit_byte':4,'visit_bit':1<<(rid-46),'neighbors':adj,
 'landmarks':landmarks,'main_route':rid in [46,47,50,51,52,53], 'entry_quest':q,'entry_objective_prefix':prefix,
 'arrival_gate':'magma_quest_32_claimed' if rid==46 else 'underwater_town_visited',
 'spawn_policy':{'0':'first entrance safe landing','1':'return landing','2':'town-anchor landing' if rid in [46,47] else 'disabled'},
 'anchor_byte':4 if rid in [46,47] else None,'anchor_bit':1<<(rid-46) if rid in [46,47] else 0,
 'main_required_capabilities':['echo_outline','shift_ballast'] if rid>=50 else [],
 'safe_reset':'Visible shell-shaped RESET pedestal outside movable-object reach; A then confirm restores this room puzzle and respawns hero at its nearest safe landing, no HP/rewards lost.',
 'footprint_contract':'10x10 player footprint; all ordinary corridors >=24px; interaction target >=16x16; puzzle targets >=20x20 with shape+animation clues; no unmarked swim-through solids.'})
# Main narrative event geometries and exact persistent evidence.
PUZZLES=[
{'id':'UW_P_TUTOR_ECHO','area':46,'quest':38,'objective_bit':1,'position':[120,104],'required_caps':[],
 'logic':'Compare a solid scalloped plaque and a hollow dotted plaque; keeper demonstrates echoes, then the player selects the matching visible outline with A.',
 'hint':'A hollow shell gives a broken outline. Look at its edge, not its color.','reset':'Either plaque can be inspected repeatedly; choosing wrong never consumes anything.'},
{'id':'UW_P_TUTOR_BALLAST','area':46,'quest':39,'objective_bit':1,'position':[340,108],'required_caps':[],
 'logic':'A transparent buoyancy diagram and hand lever raise one empty shelf while its paired shell lowers. Step off the shelf and use the lever again to show the return route.',
 'hint':'One rises when the other settles. The handle works from this landing.','reset':'Lever is always on stable ground; A reverses either state.'},
{'id':'UW_P_FIRST_RETURN','area':47,'quest':39,'objective_bit':2,'position':[240,164],'required_caps':[],
 'logic':'Walk a short loop around the low shelf to its visible other landing; no ability or gear is needed. Talk to the shellwright on return for Bobclam.',
 'hint':'The pale stepping shells stay in place when the shelf moves.','reset':'No persistent moving state; both fixed landings remain reachable.'},
{'id':'UW_P_OVERLAY','area':50,'quest':40,'objective_bit':1,'position':[120,72],'required_caps':['echo_outline','shift_ballast'],
 'logic':'Echo reveals a permanent dotted shoreline on one of two translucent map leaves. Toggle a marked ballast shelf to overlay the broken coastline, then manually rotate the other leaf90 degrees until the two positive and negative outlines agree.',
 'hint':'The torn edge fits the empty space in the other map. You can study both as long as you need.','reset':'Pedestal at[28,128] restores leaf rotations and shelf. Exit at[120,146] never closes.'},
{'id':'UW_P_COUNTERCURRENT','area':51,'quest':40,'objective_bit':2,'position':[240,136],'required_caps':['shift_ballast'],
 'logic':'Two linked lifts have different footprints. Choose the wide shelf as a bridge, walk its fixed side loop and lower the narrow shelf into a drawn recess. Read the procession sketch from the resulting high landing; no object is carried.',
 'hint':'The long shelf can meet both landings. Its partner belongs in the narrow outline.','reset':'Pedestals[40,276] and[424,76] reach the same safe canonical arrangement; no hero may be inside a changed solid.'},
{'id':'UW_P_NEGATIVE_SPACE','area':52,'quest':40,'objective_bit':4,'position':[120,80],'required_caps':['echo_outline'],
 'logic':'Echo traces sound around two curved baffles. Move the baffles manually until their unlit sound-shadow overlaps the missing footstep motif. The answer is the quiet negative space, never a particular audio frequency.',
 'hint':'The drawing shows where no note returns. Trace the quiet gap.','reset':'Pedestal[24,132] restores baffles; all states retain an outer walking ring >=24px.'},
{'id':'UW_P_COURT','area':53,'quest':40,'objective_bit':8,'position':[120,64],'required_caps':['echo_outline','shift_ballast'],
 'logic':'Two memory leaves give complementary versions of a procession. Echo reveals the guardian sculpture response; shift its marked ballast to open a safe side alcove, then bait its telegraphed sweep from either side and use the starter sword on the visible exposed joint. Three successful openings settle the guardian; no timer or damage race.',
 'hint':'Its gaze follows the open page. The alcove holds still when the crest sweeps.','reset':'Defeat/death or RESET returns to entrance with guardian full health, no loss of completed prior-room records. Exit remains available.'}]
# Quests are independently bounded IDs, never used as XP or gear source IDs.
QUESTS=[
(38,'The Map That Listens',3,False,[],49,None,'Inspect the echo plaques; hear the keeper describe both missing versions; accept Inkbud at the sanctuary.'),
(39,'Room to Rise',3,False,[],52,None,'Use the safe manual ballast demonstration, walk the Commons return loop, and accept Bobclam.'),
(40,'A Place for Both Stories',15,True,[38,39],None,None,'Recover the coastline, procession sketch and quiet motif across the archive, then settle the Vestige and preserve both accounts.'),
(41,'The Unfinished Parade',7,False,[38],None,31,'Speak with the market cook, frame-maker and returning dancer; arrange their three distinct route sketches in chronological order on the public wall.'),
(42,'A Window for Small Feet',3,False,[39],None,32,'Watch a tiny shoal use its visible migration lane; open the low screen from the far side without closing that lane.'),
(43,'The Quiet Seat',3,False,[],None,33,'Find the signed listening bench and compare its two pictured sound shadows; choose a baffle position that leaves the seating alcove quiet.'),
(44,'Glass from Two Shores',3,False,[],None,34,'Read the shellwright display and the Oyster Garden etching; fit their two differently shaped fragments without spending a collectible.'),
(45,'A Way to Come Home',7,False,[40],None,35,'Open the archive return arch, walk the whole town-to-garden return loop, and show the keeper the completed route; optional celebration and travel convenience.')]
quests=[]
for q,name,mask,prefix,prior,recruit,gear,text in QUESTS:
 quests.append({'id':q,'name':name,'objective_mask':mask,'prefix_required':prefix,'prerequisite_claimed_quests':prior,'recruit_form':recruit,
  'equipment_reward_source':gear,'xp_event_id':280+q-38,'xp':160,'description':text,'variable_max':0,
  'claim_policy':'Exact READY mask; stage all rewards, admitted grant if present, then commit quest state+reward bit together. Failure preserves every byte and READY invitation.',
  'main_route':q in [38,39,40],'reward_receipt':'quest.rewards bit equal to quest ID; CLAIMED iff reward bit'})
# Sixth gear source is the final optional quest's bundle; two gear pieces still staged atomically.
quests[-1]['equipment_reward_source']=None;quests[-1]['equipment_reward_sources']=[35,36]
GEAR=[(6,'Shellscribe Sword','weapon','sword',31,41,[1,0,0,0,0,0,3,0]),
(13,'Nacrepoint Lance','weapon','lance',32,42,[0,1,0,-2,0,0,4,0]),
(38,'Pearlweave Mail','body',None,33,43,[0,2,4,0,0,0,0,0]),
(54,'Driftstep Boots','boots',None,34,44,[0,0,0,6,1,0,0,0]),
(68,'Mapfold Belt','belt',None,35,45,[0,0,8,-2,0,2,0,0]),
(86,'Quietwater Ring','ring',None,36,45,[0,1,0,0,0,2,0,0])]
equipment=[]
for iid,name,slot,weapon,source,q,stats in GEAR:
 item={'id':iid,'key':f'ITEM_{iid:03}','name':name,'slot':slot,'status':'proposed','unique':True,'max_rank':0,
 'stats':dict(zip(['attack_q4','defense_q4','hp_q4','speed_q8_delta','roll_reduction','power_reduction','reach_px','stagger'],stats)),
 'description':['An optional underwater sidegrade.','No breathing meter or route permission.']}
 if weapon:item['weapon_class']=weapon
 equipment.append({'item':item,'reward_source':source,'quest_id':q,'never_mandatory':True})
write('world_plan.json',{'status':'DESIGN_ONLY_NOT_IMPLEMENTED','areas':areas,'puzzles':PUZZLES,'quests':quests,'equipment':equipment,
 'route_contract':{'entry_quest':32,'main_quests':[38,39,40],'teaching_forms':[49,52],'required_gear_ids':[1],
  'requires_core_ending':False,'requires_optional_old_quests':False,'requires_evolution':False,'requires_grinding':False,
  'oxygen_timer':False,'mandatory_timing_puzzle':False,'screen':[240,160],'hud':'Small floating edge HUD; world rendered behind all160 rows; no fixed20px status band.',
  'main_path':[46,47,50,51,52,53,46], 'optional_loops':[[46,48,49,48,46],[48,51,52,49,48]],
  'permanent_returns':[{'from':53,'to':46,'requires_quest':40},{'from':51,'to':48,'requires_quest':42},{'from':52,'to':49,'requires_quest':44}],
  'entry_note':'Magma q32 is the preceding main chapter completion, not a new optional-quest requirement. Preserve all old routes and Core ending state.'}})
# Local trial keys1/2 reuse wire bits1/2 only inside an explicitly qualified family.
TRIAL_SPEC=[
(17,1,'read_the_missing_edge',50,[64,72],'echo_outline','Reconstruct a missing shoreline from one positive echo and its mirrored negative impression. Rotate a transparent leaf until both edges agree, then read the actual absent section with Inkbud.','Four leaf rotations and a mirror state; compare outlines rather than a sequence of switches.','The missing piece is the space the other page leaves.'),
(17,2,'leave_a_silent_margin',52,[172,72],'echo_outline','Place two curved baffles so a drawn crescent remains silent while the nearby broad border is still echoed. Read both sample points with the same Inkbud; a fully silent room is not a solution.','Complement constraint: exactly the crescent is occluded, the border remains audible/visible.','Keep the quiet inside the crescent, not everywhere.'),
(18,1,'one_low_one_high',51,[104,224],'shift_ballast','Choose which of two unequal connected shelves receives ballast. Step across its lowered surface, then raise it from the far lever to prove a usable return landing. Bobclam must make both ballast casts.','Two-state mechanism plus far-side reachability; fixed side landing prevents trapping.','The broad shelf can touch both ledges.'),
(18,2,'hold_the_middle_depth',49,[92,108],'shift_ballast','Set two independent chalk floats to opposite ballast states so a broad specimen tray sits at the middle pictured depth. Walk around its dry outline and show it can be approached from both sides.','Two binary controls, one depth comparison and two spatial approaches; no timing or carried load.','Equal pull in opposite directions holds the center still.'),
(19,1,'draw_an_open_ladder',48,[144,92],'inscribe_trace','Use Frondfoal to trace the two side rails of a visible seed-ladder on separate tagged stems, then manually unfold its cross-frond. The open central notch must remain untraced.','Graph construction with a forbidden middle segment; all stems visually distinguishable.','Its small travelers use the space between the rails.'),
(19,2,'make_a_nested_bower',48,[354,224],'grow_roots','Curl two rooted fronds around a marked empty nursery circle, leaving the smaller outer doorway open. View the shape from both observation stones before Frondfoal joins the final root.','Enclosure and intentional gap, not every green socket; no seed carrying.','Shelter the circle; leave its little door.'),
(20,1,'roll_the_near_edge',50,[176,112],'align_rail','Align a horseshoe guide around the near faces of an L-shaped barrier so a marked demonstration bead returns to its starting lane without passing through the central wall. Rimlet confirms the final alignment.','Trace continuity along two sides of a wall; manually reversible guides.','The bead stays on the side you can touch.'),
(20,2,'leave_two_windows',51,[360,224],'unfold_screen','Unfold a perforated screen over two large outlined motifs. Slide the screen until both different-shaped motifs remain visible through its two windows, then close only its outer rim with Rimlet.','Two-shape registration and negative space; a solid cover visibly fails.','A cover can protect the border and still show both pictures.'),
(21,1,'warm_the_outer_crown',49,[172,52],'store_heat','Observe two heat bands on a ceramic flower display. Have Ventplume warm the outer half-fan, turn the display manually and cool its center at the marked stone. The inner unhatched motif must remain unchanged.','Ordered heat transfer between a rotating surface and a passive sink; no timer or inventory heat count.','The marked rim needs warmth; the pale center does not.'),
(21,2,'write_a_warm_path',48,[368,88],'ignite','Guide Ventplume along four adjacent visible stencil pads in either of two valid routes so a continuous warm line joins a beginning and ending mark while avoiding the shaded nursery tile.','Simple path on a2x3 grid with a forbidden tile; no hidden pixel target or exact frame window.','The line may bend. It must never cross the shaded leaf.'),
(22,1,'turn_the_five_petals',48,[96,224],'inscribe_trace','Compare a five-armed route medallion with a rotated mural. Palmstar traces the correct starting arm, and the player rotates the medallion until all differently shaped tips overlay the mural.','Fivefold orientation with asymmetric landmarks; not color matching alone.','Follow the arm with the notch before turning the others.'),
(22,2,'fold_without_overlap',51,[360,96],'grow_bridge','Fold a three-panel living frond bridge into a pictured zigzag without overlapping its two narrow refuge pads. Palmstar binds the two visible joints from separate reachable landings.','Planar folding and non-overlap constraint with two joint receipts, not linear switch order.','The small pale islands must stay uncovered.'),
(23,1,'keep_the_hinge_clear',51,[144,96],'align_rail','Turn an articulated bronze drawing around its fixed center pin. Linkeel aligns each of its two joints only when the previewed sweep misses a marked fragile frame.','Swept-volume clearance with two alternative valid end angles and no timing.','Look at the whole turning arc, not only its end.'),
(23,2,'cross_once_return_once',52,[64,104],'tune_latch','Lay a figure-eight demonstration cord on a visible peg board with exactly one shared crossing. Linkeel tunes the crossing, the player follows both lobes and returns to the start without using the same lobe twice.','Two-loop walk proof with a shared junction; no pressure plate held or object carried.','Two journeys share one meeting place.'),
(24,1,'keep_the_diagonal_open',49,[64,56],'refract_beam','Angle two translucent screens to light opposite triangular murals while leaving their drawn diagonal passage unlit. Combgleam demonstrates the two receivers in either order.','Partition constraint and line-of-sight, not a three-receiver sequence.','Light the pictures on both sides; leave the diagonal clear.'),
(24,2,'frame_the_empty_center',52,[176,112],'echo_outline','Choose three corner reflectors from four large tagged pedestals so their outlined triangle surrounds a quiet central motif. Combgleam echoes the three selected corners; the unchosen fourth stays dim.','Three-of-four convex enclosure with a protected central aperture; all alternatives freely reversible.','The picture belongs inside the frame, untouched.')]
trials=[];bindings=[];evolutions=[]
for fam,key,short,area,pos,cap,logic,test,hint in TRIAL_SPEC:
 base=49+(fam-17)*3;target=base+key;name='uw_'+short
 aid=62+(fam-17)*2+(key-1)
 trial={'id':name,'family_id':f'F{fam:03}','local_trial_id':key,'wire_mask':1<<(key-1),'from_form_id':base,'target_form_id':target,
 'area':area,'position':pos,'source_token':f'UW_SOURCE_{fam}','required_capability':cap,'required_command':67+(fam-17)*3,
 'field_aid_index':aid,'xp_event_id':384+aid,'description':logic,'success_predicate':test,'player_hint':hint,
 'training_floor':{'level':28,'bond':45},'context':'underwater_ready','prerequisite_trial_mask':0,
 'reset':'A clearly labeled nearby RESET restores this trial only; exit/death/load/selected-instance change discards transient proof. Previous completed trial bits and history remain.',
 'receipt':'Attempt locks slot+instance_id+base_form+family+key+source+room_generation. Each required cast must come from that exact instance and base command. Complete only with solved geometry, then stage that individual and OR the single qualified bit.',
 'replay':'Same instance/key returns UNCHANGED before floors or XP. New individual must personally replay every spatial/cast proof; lifetime aid bit cannot substitute. Trial floors may still be earned if the global first-aid XP was already used.'}
 trials.append(trial)
 bindings.append({'trial_id':name,'family_id':f'F{fam:03}','local_trial_id':key,'wire_mask':1<<(key-1),'introduced_content_revision':6,'prerequisite_trial_mask':0,'from_form_ids':[base]})
 evolutions.append({'from':base,'to':target,'min_level':28,'min_bond':45,'required_gate':'underwater_ready','required_trial':name,'location':'sanctuary','player_confirm':True,'consumed_item':None})
write('trial_contracts.json',trials)
# Acquisition is bounded deterministic invitation work, not rare drops or random palette enemies.
SOURCE_SPEC=[
(17,46,[120,104],38,'The keeper introduces the cuttlefish after the two echo-plaque observations.','After a retained Scriptcuttle or Fanfolio, return to the keeper and compare a different pair of large torn-outline leaves. A second Inkbud chooses to join after an explicit invitation.'),
(18,46,[340,108],39,'The shellwright introduces Bobclam after the safe manual ballast loop.','After either clam branch, use the separate twin-basin demonstration behind the shellwright: leave both fixed landings reachable, then invite the observing Bobclam.'),
(19,48,[144,92],None,'Follow two visibly nibbled fronds to a seahorse at the open ladder; match its simple stem shape with a manual fold, then invite it.','A second family member visits the far bower after either branch exists. Complete a different two-state frond fold and return to its clearly marked perch; every invitation needs a new completed attempt.'),
(20,47,[376,184],None,'Watch a horseshoe animal circle a bronze edge. Turn its one broad guide back toward the safe sand and speak at the visible resting hollow.','After either branch, a traveling Rimlet appears beside the second guide. Guide its demonstration bead around the near side of the visible block and meet it at the end; no defeating or drop roll.'),
(21,49,[172,52],None,'A painted vent-flower marker points at a blinking crown. Use the manual shade to expose a warm rim without touching the pale center; invite Ventplume.','After either branch, inspect the newly opened side niche. Set its two large shutters to the pictured half-open pattern and wait for the scripted crown-opening animation, which has no time limit.'),
(22,48,[96,224],None,'A five-toed trail leads to a sea star turning a medallion. Rotate the matching floor drawing one step, then invite Palmstar from the accessible center.','After either branch, the second sea star is at a different marked medallion. Reconstruct its asymmetric orientation and return the manual ring to the exit-safe position before inviting it.'),
(23,51,[144,96],None,'Two storyboards show an eel passing beside a hinged frame. Inspect both, set the frame clear of its drawn sweep, then approach the now-visible open nook.','After either branch, Linkeel returns at the high observation nook. Align a two-joint drawing to either safe angle and inspect its whole sweep. This uses manual handles, not a newly evolved ability.'),
(24,49,[64,56],None,'Read the garden mural, echo the broad dotted arch with Inkbud, then follow the now-visible comb ripples to a fully drawn jelly beside the bench.','After either branch, the nursery shows a second Combgleam beside a new picture frame. Overlay two manual transparent leaves while keeping their diagonal gap open, then invite it explicitly.')]
sources=[]
for idx,(fam,area,pos,q,first,repeat) in enumerate(SOURCE_SPEC):
 sources.append({'family_id':f'F{fam:03}','base_form_id':49+idx*3,'token':f'UW_SOURCE_{fam}','token_id':idx+1,'area':area,'position':pos,
 'first_flow':first,'quest_receipt':q,'field_receipt':None if q is not None else {'byte':10,'bit':1<<(idx-2)},
 'first_field_aid_index':None if q is not None else 78+idx-2,
 'repeat_flow':repeat,'repeat_token':f'UW_REPEAT_{fam}','repeat_token_id':17+idx,
 'repeat_first_extra_receipt':{'byte':17,'bit':1<<idx},
 'repeat_requires':'First-source receipt and at least one retained terminal form of this exact family; no optional quest, gear, rare drop, level or separate chapter ending.',
 'repeat_transaction':'Lock source attempt generation at solved geometry; explicit A invitation; admitted real new instance; consume the transient invitation once. Exit/re-enter or RESET begins a fresh authored attempt. A held/repeated A in the same solved attempt cannot grant twice.',
 'repeat_rewards':'Only the new base individual; zero gear, quest reward, XP event, party bond, copied trial bits or collection reward replay. First-extra receipt is provenance, never a repeat-blocking flag.',
 'grant_level':{'minimum':26,'maximum':32,'basis':'current valid party median, clamp; empty party uses26'},'grant_bond':20,'trial_flags_on_grant':0,
 'party':'Never replace a party slot; auto-place only if existing grant behavior allows an empty slot, otherwise storage and readable notice.',
 'capacity':'creatures_grant_admitted and monotonic nonzero instance_id; reserve all72 final terminal opportunities, extras<=88. Typed FULL/RESERVED/ID_EXHAUSTED leaves all bytes and invitation unchanged.',
 'discovery_receipt':{'byte':20,'mask':3,'prefix':True} if fam==23 else ({'byte':21,'mask':7,'prefix':True} if fam==24 else None)})
write('acquisition_contracts.json',sources)
gates=[{'id':'underwater_arrival','kind':'story','requires':['caldera_open']},
 {'id':'underwater_q38','kind':'story','requires':['underwater_arrival']}, {'id':'underwater_q39','kind':'story','requires':['underwater_arrival']},
 {'id':'underwater_ready','kind':'story','requires':['underwater_q38','underwater_q39']},
 {'id':'palinode_open','kind':'story','requires':['underwater_ready']}]
for fam,_,_,q,_,_ in SOURCE_SPEC:gates.append({'id':f'underwater_source_{fam}','kind':'side_quest','requires':[f'underwater_q{q}' if q is not None else 'underwater_arrival']})
write('catalog_delta.json',{'status':'DESIGN_ONLY_NOT_IMPLEMENTED','target_content_revision':6,'new_form_ids':list(range(49,73)),
 'slot_status_updates':{str(i):'proposed' for i in range(49,73)},'new_field_capabilities':[x[0] for x in NEW_CAPS],
 'abilities':abilities,'evolutions':evolutions,'gates':gates,'trials':[{'id':t['id'],'description':t['description']} for t in trials], 'trial_bindings':bindings,
 'enabled_ability_ids':list(range(67,91)), 'explicit_polarity_by_form':{str(f['id']):f['polarity'] for f in forms},
 'legendary_ids_still_disabled':list(range(121,129))})
# Read authoritative numeric sources; do not accept outdated prose counts as policy.
source_paths=['assets/creatures/catalog.json','assets/creatures/catalog.schema.json','assets/creatures/enabled.json',
 'assets/creatures/identity-lock.json','assets/creatures/terminal-topology.json','assets/creatures/catalog_policy.py',
 'assets/history/creatures-v1-v4.json','assets/history/released-creature-relations-v4.json',
 'assets/equipment/catalog.json','src/progression_events.c','src/creatures.h','src/equipment.h','src/equipment_data.c',
 'src/save5.h','src/save5.c','src/save5_history_policy.h','src/obj_layout.h','src/magma_quests.c','src/magma_game.c',
 'src/trials.c','src/progression.c','src/game.c','linker.ld','build/emberbond.map','build/emberbond.gba']
maptext=(BASE/'build/emberbond.map').read_text()
def section(name):
 m=re.search(r'^\.'+name+r'\s+0x[0-9a-f]+\s+(0x[0-9a-f]+)',maptext,re.M);assert m,name;return int(m[1],16)
oldgear=json.loads((BASE/'assets/equipment/catalog.json').read_text())['items']
oldgearids=[i['id'] for i in oldgear]
oldregions={0:63,1:255,2:255,3:255,8:255,9:127,16:15,18:3,19:7}
newregions=[{'byte':4,'mask':255,'meaning':'Visits:bit0..7 areas46..53'},
 {'byte':10,'mask':63,'meaning':'First field sources F019..F024 in order; teaching sources use quests38/39'},
 {'byte':17,'mask':255,'meaning':'First extra individual for F017..F024; provenance only, not maximum repeat count'},
 {'byte':20,'mask':3,'meaning':'F023 discovery inspected-storyboard prefix0/1/3; source requires3'},
 {'byte':21,'mask':7,'meaning':'F024 mural/arch/ripple discovery prefix0/1/3/7; source requires7'}]
alloc={'schema_version':1,'status':'DESIGN_ONLY_NOT_IMPLEMENTED','target_content_revision':6,
 'baseline':{'reference_directory':str(BASE),'content_revision':enabled['content_revision'],'forms':len(enabled['enabled_form_ids']),
  'commands':len(enabled['enabled_ability_ids']),'evolution_edges':len(enabled['enabled_evolutions']),'learns':102,
  'retained_individuals_after_full_magma_acceptance':34,'quests':38,'areas':46,'gear':len(oldgear),
  'native_acceptance_note':'Magma source tables are the numeric authority;65-form native acquisition remains a separate parent acceptance gate. This proposal is conditional on that acceptance.'},
 'append':{'form_ids':list(range(49,73)),'family_ids':[f'F{i:03}' for i in range(17,25)],'ability_ids':list(range(67,91)),
  'area_ids':list(range(46,54)),'quest_ids':list(range(38,46)),
  'equipment_ids':[g[0] for g in GEAR],'equipment_reward_sources':list(range(31,37)),
  'capabilities':[{'name':n,'key':k,'mask':m} for n,k,m in NEW_CAPS],
  'context_bits':[{'gate':'underwater_ready','mask':1024,'derived_from_claimed_quests':[38,39]}, {'gate':'palinode_open','mask':2048,'derived_from_claimed_quests':[40]}],
  'trial_bindings':bindings,'region_flags':newregions,'anchor':{'byte':4,'mask':3,'areas':[46,47]},
  'encounter_events':[{'area':47,'first':256,'count':4},{'area':48,'first':260,'count':2},{'area':50,'first':262,'count':1},{'area':51,'first':263,'count':2},{'area':52,'first':265,'count':1},{'area':53,'first':266,'count':2}],
  'quest_xp_event_ids':list(range(280,288)),'trial_field_aid_indices':list(range(62,78)),'source_field_aid_indices':list(range(78,84)),
  'generic_creature_reward_ids':[],'source_token_ids':list(range(1,9)),'repeat_token_ids':list(range(17,25))},
 'existing_namespaces':{'form_ids':enabled['enabled_form_ids'],'ability_ids':enabled['enabled_ability_ids'],'area_ids':list(range(46)),
  'quest_ids':list(range(38)),'equipment_ids':oldgearids,'equipment_reward_sources':list(range(31)),
  'region_flag_masks':{str(k):v for k,v in oldregions.items()},'anchor_bytes':[0,1,2,3],
  'ordinary_events':list(range(180))+list(range(180,192))+list(range(220,232))+list(range(240,248)),
  'field_aid_indices_conservatively_reserved':list(range(62)),
  'event_audit':'progression_encounter_event reserves old area*6 slots0..179; Southern explicit180..191; Magma encounters220..231 and quests240..247. Field0..7 original trials; conservatively reserve8..39 for old authored chapter policy, Magma40..61. Repeat sources add no event IDs.',
  'context_mask':1023,'capability_keys':list(range(1,27))},
 'result_after_real_acceptance':{'form_histories':89,'retained_individuals':50,'commands':89,'evolution_edges':51,'learns':142,'quests':46,'areas':54,'gear':37,
  'new_real_grants':16,'new_history_forms':24,'remaining_form_ids':sorted(set(range(1,129))-set(enabled['enabled_form_ids'])-set(range(49,73)))},
 'limits':{'instance_slots':160,'final_terminal_opportunities':72,'extra_copy_budget':88,'event_capacity':512,'ordinary_event_exclusive_limit':384,
  'field_event_base':384,'field_aid_capacity':128,'quest_capacity':64,'region_flag_bytes':32,'anchor_bytes':16,'gear_bag':48,
  'equipment_source_capacity':64,'capability_bits':32,'trial_bits_per_family':16,'instance_wire_bytes':24,
  'save_bank_offsets':[512,6656],'save_bank_bytes':6144,'used_save_payload_bytes':5056,'reserved_tail_bytes':1088,'sram_bytes':32768},
 'wire_contract':{'wire_version':5,'writes_content_revision':6,'history_revisions_frozen':[1,2,3,4,5],
  'migration':'Decode by exact original revision; preserve every typed old byte and semantic relationship. No recruit, level, trial, reward, equipment, visit or quest is invented on load. New reserved fields stayzero until earned.',
  'historical_release_gate':'Freeze the accepted Magma revision5 creature/equipment/quest/source/room policies, including its final legacy-save fix, before adding revision6. Current-only data must never rewrite v1..v5 historical tables.',
  'admission':'Prospective matching against immutable72 terminal opportunities is a gameplay admission rule, not a save-validity predicate. Legal grandfathered over-budget states remain loadable and saveable.',
  'guard':'If old history semantics cannot be represented under revision6, stop for an explicit migration design; never silently normalize or reject a previously legal save.'},
 'budgets':{'baseline_rom_bytes':(BASE/'build/emberbond.gba').stat().st_size,'baseline_ewram_data_bytes':section('data'),'baseline_ewram_bss_bytes':section('bss'),
  'baseline_iwram_code_bytes':section('iwram'),'incremental_rom_cap_bytes':2097152,'incremental_ewram_cap_bytes':8192,'incremental_iwram_cap_bytes':384,
  'rom_limit_bytes':33554432,'ewram_limit_bytes':262144,'iwram_code_limit_bytes':28672,'iwram_stack_reserve_bytes':4096,
  'rom_line_items':{'eight_dual_parity_backgrounds':1536000,'walk_pixels_24x16x16x4x4':98304,'ability_poses_24x16x16x4x3':73728,
   'portraits_24x32x32':24576,'props_24x256x3':18432,'ui_gear_labels':32768,'cold_runtime_code':98304,'catalog_policy_geometry':8192},
  'ewram_line_items':{'single_power_snapshot_and_ledger':512,'room_puzzle_state':256,'trial_proof':192,'bounded_render_staging':1024,'safety_margin':6208},
  'new_iwram_policy':'ROM code by default; no broad *game.o linker match. At most384 additional hot bytes after measured necessity; preserve4KiB stack reserve and measure high-water.',
  'obj_vram_used_end':16256,'obj_vram_capacity':16384,'new_obj_vram_bytes':0,'region_tile_slots_reused':20,
  'oam_engine_drop_threshold':120,'underwater_oam_hard_budget':112,'ambient_oam_budget':8,
  'frame_hz_target':59.7275,'hardware_cycles_per_frame':280896,'full_frame_acceptance_max_cycles':280896,
  'target_p99_cycles':267000,'save_step_budget_default':1024,'save_step_budget_max':3072,
  'performance_status':'Budget and required acceptance only; no Underwater native ROM, runtime profile, art or performance measurement exists.'},
 'source_hashes':{p:sha(BASE/p) for p in source_paths}}
write('underwater_allocation.json',alloc)
roadmap=[
 {'milestone':'Underwater: Nacreway and Palinode','new_form_ids':list(range(49,73)),'cumulative_forms':89,'new_individuals':16,'retained':50,'quest_ids':list(range(38,46)),'new_gear_count':6,'cumulative_gear':37,'field_aid_indices':list(range(62,84))},
 {'milestone':'Homeward Mastery: return to existing towns','new_form_ids':[3,6,9,12,15,17,18,21,24,27,30],'cumulative_forms':100,'new_individuals':0,'retained':50,'quest_ids':list(range(46,50)),'new_gear_count':4,'cumulative_gear':41,'field_aid_indices':list(range(84,95)),
  'scope':'Eleven authored evolutions for ten already-owned families, including17->18 after16->17. New per-family trial keys and old-town return puzzles; no replacement of original edges or outcomes.'},
 {'milestone':'Crossroads Expeditions: six new lineages','new_form_ids':list(range(101,113)),'cumulative_forms':112,'new_individuals':6,'retained':56,'quest_ids':list(range(50,56)),'new_gear_count':3,'cumulative_gear':44,'field_aid_indices':list(range(95,101)),
  'scope':'F039..F044 linear_two, one guaranteed meaningful acquisition and personal evolution each; exact shapes/identities remain reserved.'},
 {'milestone':'Five-Phase Pilgrimage: eight singular companions','new_form_ids':list(range(113,121)),'cumulative_forms':120,'new_individuals':8,'retained':64,'quest_ids':list(range(56,60)),'new_gear_count':2,'cumulative_gear':46,'field_aid_indices':list(range(101,109)),
  'scope':'F045..F052 single forms; eight separately authored nonrandom discoveries in return-route spaces, with four shared narrative quests but distinct acquisition proofs.'},
 {'milestone':'Eight Legendary Covenants','new_form_ids':list(range(121,129)),'cumulative_forms':128,'new_individuals':8,'retained':72,'quest_ids':list(range(60,64)),'new_gear_count':2,'cumulative_gear':48,'field_aid_indices':list(range(109,117)),
  'scope':'Eight distinct optional authored gates with specific one-time receipts; only one active legendary remains allowed. Existing design-only121/ability12 is re-reviewed, never enabled merely because present in catalog.'}]
write('completion_roadmap.json',{'status':'FINITE_DESIGN_ROADMAP_NOT_IMPLEMENTATION','milestones':roadmap,'remaining_unassigned_field_aids':list(range(117,128)),
 'future_command_reservations':{'homeward':list(range(91,102)),'crossroads':list(range(102,114)),'singulars':list(range(114,122)),'legendary':[12]+list(range(122,129))},
 'native_gate_for_every_milestone':'Only count after ordinary-controller acquisition, same-individual trial/evolution, save/reboot, unique art/handler behavior and full-frame performance acceptance. Tables, generated history bits and synthetic SRAM are insufficient.'})

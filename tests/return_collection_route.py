"""Actual-controller Return collection route; spoiler-bearing developer evidence."""
TRIALS = [
    (54, 2, 3, 1, (48, 144), (96, 144), ((64, 80), (128, 112)), (96, 112)),
    (54, 5, 6, 2, (432, 144), (368, 144), ((336, 72), (416, 104), (376, 112)), (416, 160)),
    (57, 8, 9, 3, (48, 120), (128, 48), ((80, 80), (176, 80)), (128, 112)),
    (61, 11, 12, 4, (208, 112), (120, 80), ((64, 80), (176, 80)), (120, 104)),
    (56, 14, 15, 9, (48, 240), (80, 176), ((80, 80), (80, 208)), (120, 240)),
    (55, 16, 17, 11, (208, 112), (120, 108), ((64, 72), (120, 72), (176, 72)), (208, 96)),
    (60, 17, 18, 11, (40, 108), (120, 80), ((64, 56), (176, 56), (120, 56)), (176, 108)),
    (57, 20, 21, 13, (448, 144), (368, 112), ((320, 64), (416, 80)), (416, 112)),
    (57, 23, 24, 15, (48, 264), (128, 264), ((80, 208), (176, 240), (208, 192)), (112, 240)),
    (58, 26, 27, 23, (448, 176), (368, 144), ((320, 80), (416, 112)), (416, 160)),
    (58, 29, 30, 25, (48, 264), (128, 192), ((80, 224), (176, 224)), (192, 256)),
    (56, 101, 102, 102, (448, 96), (368, 112), ((336, 80), (416, 144), (368, 240)), (416, 208)),
    (59, 103, 104, 104, (208, 112), (120, 104), ((64, 56), (192, 56)), (192, 96)),
]


class ReturnCollectionRoute:
    def optional_quests(self):
        self.travel(22)
        self.target(352, 176)
        self.travel(57)
        self.target(304, 272)
        self.cast_target(self.story_form(1), 1, 304, 240)
        self.travel(16)
        self.target(112, 144)
        self.check(self.quest(52) == 3, 'manual hood and genuine ignition earn quest52')
        self.travel(54)
        self.cast_target(self.story_form(4), 2, 240, 72)
        self.cast_target(self.story_form(1), 1, 272, 240)
        self.target(240, 240)
        for area, point in ((56, (432, 256)), (57, (432, 272)), (58, (240, 240))):
            self.travel(area)
            self.target(*point)
        self.travel(30)
        self.target(448, 192)
        self.check(all(self.quest(q) == 3 for q in range(54)), 'all54 quests retain genuinely claimed rewards')
        self.check(sum(bool(g.item_id) for g in self.state().equipment.bag) == 42, 'all42 gear items are genuinely retained')
        self.snapshot('03-all54-quests42-gear')

    def begin_return_trial(self, index):
        area, form, target, command, lectern, manual, points, walk = TRIALS[index]
        self.travel(area)
        self.owned_select(form)
        self.set_command(command)
        self.ready()
        identity = self.selected().instance_id
        slot = self.roster().party[self.roster().selected_party]
        self.target(*lectern)
        t = self.trial()
        self.check(t.index == index and t.instance_id == identity and t.slot == slot and t.form == form,
                   'actual lectern binds exact predecessor, immutable identity and roster slot')
        self.snapshot(f'trial-{index:02d}-start')
        return identity, slot

    def trial_cast(self, index, point, direction=1):
        _, form, _, command, _, _, points, _ = TRIALS[index]
        # Every approach uses normal radius4 navigation; no pixel-perfect retry.
        distance = 24 if command in (1, 3, 9, 11, 13, 15, 102, 104) else 18
        self.cast_target(form, command, *points[point], distance=distance, direction=direction,
                         label=f'trial-{index:02d}-actual-cast-{point}', prepare=False)

    def solve_return_trial(self, index):
        *_, manual, points, walk = TRIALS[index]
        adjust = lambda: self.target(*manual)
        walk_to = lambda: (self.goto(*walk, radius=4), self.step(4), self.settle())
        cast = lambda n: self.trial_cast(index, n)
        if index in (0, 10):
            adjust(); cast(0); cast(1)
        elif index == 1:
            cast(0); cast(1); adjust(); walk_to()
        elif index in (2, 3, 4, 12):
            adjust(); cast(0); walk_to(); cast(1)
        elif index == 5:
            adjust(); cast(0); cast(1); cast(2)
        elif index in (6, 8):
            adjust(); cast(0); cast(1)
        elif index == 7:
            cast(0); adjust(); walk_to(); cast(1)
        elif index == 9:
            adjust(); cast(0); cast(1); adjust(); walk_to()
        elif index == 11:
            cast(0); cast(1); walk_to(); cast(2)
        else:
            raise AssertionError(('unknown authored trial', index))

    def reset_return(self):
        big = self.get('room') in (54, 56, 57, 58)
        point = (40, 276) if big else (24, 132)
        # Small boards are near the southern wall. Approach from the north so
        # ordinary pathfinding never walks down the central exit en route.
        self.target(*point, 1 if big else 0)
        self.check(self.return_local('reset_confirm') == 1, 'RESET needs an explicit second A')
        self.tap('A')
        self.settle()
        self.check(not self.return_local('reset_confirm') and self.trial().index == 255, 'confirmed RESET cancels local proof and lands safely')
        mask, width, _ = self.mask()
        self.check(not mask[self.get('py') * width + self.get('px')], 'reset landing has a collision-safe five-pixel footprint')

    def trial_wrong_side_retry(self, index):
        identity, slot = self.begin_return_trial(index)
        before = bytes(self.roster().instances[slot])
        self.trial_cast(index, 0, direction=0)
        self.check(bytes(self.roster().instances[slot]) == before and self.trial().casts == 0,
                   'wrong-side real cast gives no personal proof or floor')
        self.check(any(row['toast_ticks'] > 0 and row['toast_id'] == self.ui_ids['TX_RT_WRONG_SIDE']
                       for row in self.frame_windows[-1]['trace']), 'wrong-side refusal has visible readable feedback during the actual cast')
        self.reset_return()
        return identity

    def evolve_return(self, source, target, identity, slot):
        self.travel(54)
        self.target(72, 256)
        self.owned_select(source)
        self.check(self.selected().instance_id == identity, 'sanctuary chooses the same trial-qualified individual')
        self.open_tab(3)
        self.tap('SELECT')
        self.wait_evolution(require_ready=False)
        before = self.state_signature()
        self.tap('B')
        self.check(self.get('game_state') == 3 and self.state_signature() == before, 'canceling explicit evolution leaves durable state byte-identical')
        self.tap('SELECT')
        self.wait_evolution()
        self.check(self.get('progression_evolution_target') == target, 'evolution preview names the exact earned terminal form')
        self.e.screenshot(self.out / f'evolution-{source}-{target}-choice.png')
        self.tap('A')
        self.wait_evolution(8)
        self.settle()
        self.close_menu()
        c = self.roster().instances[slot]
        self.check(c.instance_id == identity and c.form_id == target, 'confirmed evolution transforms the original individual in place')
        self.acquisitions.append({'source': 'same-instance explicit evolution', 'from': source,
                                  'form': target, 'instance_id': identity, 'slot': slot, 'frame': self.e.frame})
        self.snapshot(f'evolved-{target}')

    def collection_route(self):
        self.check(not self.minimal, 'full acquisition producer requires genuinely earned89 baseline')
        self.optional_quests()
        for index, definition in enumerate(TRIALS):
            source, target = definition[1:3]
            self.trial_wrong_side_retry(index)
            identity, slot = self.begin_return_trial(index)
            before = self.roster().instances[slot]
            old_flags = before.trial_flags
            self.solve_return_trial(index)
            c = self.roster().instances[slot]
            self.check(c.instance_id == identity and c.form_id == source and c.trial_flags != old_flags,
                       'authored controller trial awards only the exact retained predecessor')
            self.check(c.level >= (28 if index in (5, 11, 12) else 32) and c.bond >= (45 if index in (5, 11, 12) else 60),
                       'personal trial earns the stated no-grind floor')
            self.snapshot(f'trial-{index:02d}-earned')
            self.begin_return_trial(index)
            before_replay = self.state_signature()
            self.check(self.trial().replay == 1, 'same-individual completed trial enters harmless rehearsal')
            self.solve_return_trial(index)
            self.check(self.state_signature() == before_replay, 'rehearsal gives no duplicate floor, credit, item or quest')
            self.evolve_return(source, target, identity, slot)
        expected = sorted(self.old_history + [3, 6, 9, 12, 15, 17, 18, 21, 24, 27, 30, 101, 102, 103, 104])
        self.check(self.collection() == expected and len(self.live()) == 52, 'one fresh acquisition producer genuinely earns104 histories on52 retained individuals')
        self.check(self.old_ids <= {c.instance_id for c in self.live()}, 'all50 old immutable individual identities survive')
        self.travel(54)
        self.target(72, 256)
        self.snapshot('04-all104-earned52-saved')
        self.cold_reboot('05-all104-cold-reboot')
        self.coverage.append('fresh-uninterrupted-controller-producer-all104-52individuals-54quests-42gear')

    def repeat_return(self, source):
        area, form, command, invite, marker, point, walk = ((55, 102, 102, (208, 80), None, (120, 80), (208, 112))
                                                          if source == 17 else
                                                          (58, 104, 104, (400, 240), (368, 272), (368, 240), (400, 272)))
        self.travel(area)
        self.owned_select(form)
        self.set_command(command)
        self.ready()
        before = {c.instance_id: bytes(c) for c in self.live()}
        rewards = bytes(self.state().quests.rewards), bytes(self.state().equipment), bytes(self.roster().lifetime_field_aid)
        self.target(*invite)
        self.check(self.return_local('repeat_active') == source, 'repeat invitation begins an explicit fresh encounter')
        if marker:
            self.target(*marker)
        else:
            self.target(64, 112); self.target(176, 112)
        self.cast_target(form, command, *point, prepare=False)
        self.goto(*walk, radius=4)
        self.step(4)
        self.check(self.return_local('repeat_stage') == 2, 'actual repeat geometry and bank walk prepare invitation')
        self.target(*invite)
        self.check(len(self.live()) == len(before) and self.return_local('invite_confirm') == 1, 'first repeat A cannot grant a companion')
        self.tap('B')
        self.check(not self.return_local('invite_confirm') and len(self.live()) == len(before), 'B cancels repeat invitation without consuming it')
        self.target(*invite)
        self.step(20, 'DOWN')
        self.check(not self.return_local('invite_confirm') and len(self.live()) == len(before), 'walking away cancels repeat confirmation harmlessly')
        self.target(*invite)
        self.check(len(self.live()) == len(before) and self.return_local('invite_confirm') == 1, 'fresh first A after repeat walkaway cannot grant')
        self.tap('A')
        self.settle()
        fresh = [c for c in self.live() if c.instance_id not in before]
        self.check(len(fresh) == 1 and fresh[0].form_id == form - 1 and fresh[0].trial_flags == 0,
                   'second A grants one fresh untrialed base copy with a unique identity')
        self.check(all(bytes(c) == before[c.instance_id] for c in self.live() if c.instance_id in before), 'repeat grants alter no earlier individual')
        self.check(rewards == (bytes(self.state().quests.rewards), bytes(self.state().equipment), bytes(self.roster().lifetime_field_aid)), 'repeat grants no quest reward, gear or lifetime trial credit')
        after = self.state_signature()
        self.target(*invite)
        self.tap('A')
        self.settle()
        self.check(self.state_signature() == after, 'consumed repeat attempt cannot duplicate the reward')
        self.snapshot('repeat-' + str(source) + '-earned')
        return fresh[0].instance_id

    def repeat_route(self):
        self.snapshot('repeat-branch-all104-base')
        self.repeat_return(17)
        self.repeat_return(18)
        self.check(len(self.live()) == 54 and len(self.collection()) == 104, 'optional repeat branch retains54 individuals and unchanged104 history')
        for index in (11, 12):
            identity, slot = self.begin_return_trial(index)
            before_credit = bytes(self.roster().lifetime_field_aid)
            self.solve_return_trial(index)
            self.check(self.roster().instances[slot].trial_flags and bytes(self.roster().lifetime_field_aid) == before_credit,
                       'fresh repeat earns its own personal trial without duplicate global lifetime credit')
            self.evolve_return(TRIALS[index][1], TRIALS[index][2], identity, slot)
        self.snapshot('repeat-branch54-terminal')
        self.restore('repeat-branch-all104-base')
        self.check(len(self.live()) == 52, 'optional repeat branch is kept separate from52-individual completion producer')

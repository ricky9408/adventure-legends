"""Current physical controls for controller-only routes; never remap raw input.

Callers name a field intention explicitly. Menu/context cancellation continues
to use raw B, and every button below passes through the route's traced step/tap.
"""


FIELD_PICKER_HOLD_UPDATES = 13


class CurrentFieldControls:
    def _field_read(self, name):
        reader = getattr(self, 'get', None) or self.g
        return reader(name)

    def _field_roster(self):
        reader = getattr(self, 'roster', None)
        if reader:
            return reader()
        reader = getattr(self, 'save_state', None)
        if reader:
            return reader().roster
        import ctypes
        from test_save5 import Save
        return Save.from_buffer_copy(self.e.bytes(self.sym['adventure_save'], ctypes.sizeof(Save))).roster

    def _field_event(self, intention, **detail):
        if not hasattr(self, 'field_control_events'):
            self.field_control_events = []
        self.field_control_events.append({'intention': intention,
            'hardware_frame': self.e.frame, 'session': getattr(self, 'session', 0), **detail})

    def _field_ready_for_input(self):
        assert self._field_read('game_state') == 1, 'Field controls require actual PLAY'
        assert not self._field_read('quickparty_open'), 'Field action cannot bypass the selector'

    def field_ability_key(self):
        self._field_ready_for_input()
        self._field_event('ability-edge', physical='B')
        return 'B'

    def field_ability(self, hold=2, release=2):
        self._field_ready_for_input()
        self._field_event('ability', physical='B', hold=hold, release=release)
        self.tap('B', hold, release)

    def hold_field_ability(self, frames=1):
        self._field_ready_for_input()
        self._field_event('ability-hold', physical='B', frames=frames)
        self.step(frames, 'B')

    def set_summoned(self, summoned, hold=2, release=2):
        self._field_ready_for_input()
        if bool(self._field_read('summoned')) != bool(summoned):
            self.step(1)  # A previous raw R hold must not swallow this fresh edge.
            self._field_event('summon' if summoned else 'recall', physical='R')
            self.tap('R', hold, release)
        assert bool(self._field_read('summoned')) == bool(summoned), 'Physical R sets companion presence'

    def open_owned_carousel(self):
        """Hold L through all13 protected arming updates before any direction."""
        self._field_ready_for_input()
        self.step(1)  # Release the prior physical action before a fresh L edge.
        roster = self._field_roster()
        before=bytes(roster)
        current=roster.party[roster.selected_party]
        for update in range(1,FIELD_PICKER_HOLD_UPDATES+1):
            self.step(1,'L')
            assert self._field_read('quickparty_open'), 'Held L owns all arming updates'
            assert bool(self._field_read('quickparty_visible'))==(update==FIELD_PICKER_HOLD_UPDATES), 'Carousel becomes visible on the13th held update'
            if update<FIELD_PICKER_HOLD_UPDATES:
                assert self._field_read('quickparty_candidate')==255, 'Arming keeps the candidate private until ready'
            assert bytes(self._field_roster())==before, 'Arming never changes roster or selection'
        assert self._field_read('quickparty_candidate')==current, 'Visible carousel starts at the current individual'
        self._field_event('open-owned-carousel',physical='L',hold_updates=FIELD_PICKER_HOLD_UPDATES)
        return current

    def select_owned_instance(self, index):
        """Reach an actual owned roster index using held L and fresh Left/Right."""
        self._field_ready_for_input()
        roster = self._field_roster()
        owned = [i for i, member in enumerate(roster.instances) if member.flags & 1]
        assert index in owned, ('Requested individual is not owned', index)
        current=self.open_owned_carousel()
        roster=self._field_roster()
        owned=[i for i,member in enumerate(roster.instances)if member.flags&1]
        instances = bytes(roster.instances)
        assert self._field_read('quickparty_candidate') == current, 'Selector opens on the current individual'
        start = self._field_read('quickparty_candidate')
        if current in owned:
            right = (owned.index(index) - owned.index(current)) % len(owned)
            left = (owned.index(current) - owned.index(index)) % len(owned)
            direction = 'RIGHT' if right <= left else 'LEFT'
        else:
            direction = 'RIGHT'
        for _ in range(len(owned) + 1):
            if self._field_read('quickparty_candidate') == index:
                break
            self.step(1, 'L+' + direction)
            self.step(1, 'L')  # Fresh direction edges, independent of 24/6 repeat.
            assert bytes(self._field_roster().instances) == instances, 'Browsing never changes an individual'
        assert self._field_read('quickparty_candidate') == index, ('Owned carousel failed to reach individual', index)
        self.step(1)  # Physical L release commits through the actual engine.
        assert not self._field_read('quickparty_open'), 'Releasing physical L closes the selector'
        selected = self._field_roster()
        assert selected.party[selected.selected_party] == index, 'L release selects the requested owned individual'
        assert bytes(selected.instances) == instances, 'Selection retains every individual byte'
        self._field_event('select-owned', physical='L+' + direction + ', release L',
                          from_index=start, roster_index=index,
                          instance_id=selected.instances[index].instance_id,
                          owned_count=len(owned), hold_updates=FIELD_PICKER_HOLD_UPDATES)

    def select_owned_identity(self, identity):
        matches = [i for i, member in enumerate(self._field_roster().instances)
                   if member.flags & 1 and member.instance_id == identity]
        assert len(matches) == 1, ('Owned identity must resolve exactly once', identity)
        self.select_owned_instance(matches[0])

    def select_owned_form(self, form):
        roster = self._field_roster()
        current = roster.party[roster.selected_party]
        matches = [i for i, member in enumerate(roster.instances)
                   if member.flags & 1 and member.form_id == form]
        assert matches, ('Requested form has not been earned', form)
        self.select_owned_instance(current if current in matches else matches[0])

    def select_next_owned(self):
        roster = self._field_roster()
        owned = [i for i, member in enumerate(roster.instances) if member.flags & 1]
        current = roster.party[roster.selected_party]
        assert current in owned
        self.select_owned_instance(owned[(owned.index(current) + 1) % len(owned)])


def require_current_acceptance(script):
    """Keep old standalone routes explicitly historical; imports stay reusable."""
    from pathlib import Path
    root = Path(script).resolve().parents[1]
    if (root / 'src/field_controls.h').is_file():
        raise SystemExit('HISTORICAL ONLY: this standalone target retains original control contracts. '
                         'Run python3 tools/run_gameplay_ci.py --suite native --output build/<fresh-directory> '
                         'for current B ability / R presence / all-owned L+Left/Right acceptance. '
                         'Historical source proofs run through tests/field_controls_boundary.py.')

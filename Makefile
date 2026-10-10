# Emberbond: freestanding ARM7TDMI GBA homebrew.
# Set DEVKITARM=/path/to/devkitARM, or ARM_PREFIX=/path/to/arm-none-eabi-.
# No libgba or target libc dependency is required.
ifneq ($(strip $(DEVKITARM)),)
  ARM_PREFIX ?= $(DEVKITARM)/bin/arm-none-eabi-
else ifneq ($(wildcard tools/sysroot/usr/bin/arm-none-eabi-gcc),)
  ARM_PREFIX ?= $(CURDIR)/tools/sysroot/usr/bin/arm-none-eabi-
else
  ARM_PREFIX ?= arm-none-eabi-
endif
export ARM_PREFIX

CC := $(ARM_PREFIX)gcc
OBJCOPY := $(ARM_PREFIX)objcopy
SIZE := $(ARM_PREFIX)size
NM := $(ARM_PREFIX)nm
PYTHON ?= python3
BUILD := build
TARGET := $(BUILD)/emberbond
# Expand only at recipe execution, after all has produced the candidate files.
NORTHERN_ARGS = --rom $(TARGET).gba --symbols $(TARGET).sym --expected-rom-sha $$( $(PYTHON) tools/file_sha256.py $(TARGET).gba ) --expected-symbols-sha $$( $(PYTHON) tools/file_sha256.py $(TARGET).sym )
CPUFLAGS := -mcpu=arm7tdmi -mthumb-interwork
CFLAGS := $(CPUFLAGS) -mthumb -O2 -g -std=c99 -ffreestanding -fno-builtin \
          -fno-strict-aliasing -fomit-frame-pointer -Wall -Wextra \
          -MMD -MP
ASFLAGS := $(CPUFLAGS) -marm -g -x assembler-with-cpp
LDFLAGS := $(CPUFLAGS) -mthumb -nostdlib -Wl,-T,linker.ld,-Map,$(TARGET).map
OBJECTS := $(BUILD)/startup.o $(BUILD)/music.o $(BUILD)/music_data.o $(BUILD)/game.o $(BUILD)/assets.o $(BUILD)/ui.o $(BUILD)/world.o $(BUILD)/campaign_art.o $(BUILD)/campaign_rules.o $(BUILD)/save4.o $(BUILD)/creatures.o $(BUILD)/creature_data.o $(BUILD)/save5.o $(BUILD)/progression.o $(BUILD)/progression_events.o $(BUILD)/evolution_art.o $(BUILD)/advanced_powers.o $(BUILD)/trials.o $(BUILD)/trial_art.o $(BUILD)/quickparty.o $(BUILD)/equipment.o $(BUILD)/equipment_data.o $(BUILD)/combat_rules.o $(BUILD)/weapon_actions.o $(BUILD)/gear_runtime.o $(BUILD)/gear_menu.o $(BUILD)/gear_preview.o $(BUILD)/gear_preview_text.o $(BUILD)/regional_quests.o $(BUILD)/regional_creature_art.o $(BUILD)/regional_powers.o $(BUILD)/region_art.o $(BUILD)/region_game.o $(BUILD)/northern_creature_art.o $(BUILD)/north_art.o $(BUILD)/north_game.o $(BUILD)/northern_quests.o $(BUILD)/northern_powers.o $(BUILD)/northern_power_art.o $(BUILD)/south_art.o $(BUILD)/south_game.o $(BUILD)/southern_quests.o $(BUILD)/southern_creature_art.o $(BUILD)/southern_powers.o $(BUILD)/southern_power_art.o $(BUILD)/magma_art.o $(BUILD)/magma_game.o $(BUILD)/magma_quests.o $(BUILD)/magma_creature_art.o $(BUILD)/magma_powers.o $(BUILD)/magma_power_art.o $(BUILD)/underwater_art.o $(BUILD)/underwater_game.o $(BUILD)/underwater_quests.o $(BUILD)/underwater_creature_art.o $(BUILD)/underwater_powers.o $(BUILD)/underwater_power_art.o $(BUILD)/return_art.o $(BUILD)/return_game.o $(BUILD)/return_quests.o $(BUILD)/return_creature_art.o $(BUILD)/return_powers.o $(BUILD)/return_power_art.o $(BUILD)/return_legacy_powers.o $(BUILD)/horizons_art.o $(BUILD)/horizons_game.o $(BUILD)/horizons_quests.o $(BUILD)/horizons_creature_art.o $(BUILD)/horizons_powers.o $(BUILD)/horizons_power_art.o $(BUILD)/horizons_audio.o $(BUILD)/covenants_art.o $(BUILD)/covenants_game.o $(BUILD)/covenants_quests.o $(BUILD)/covenants_creature_art.o $(BUILD)/covenants_powers.o $(BUILD)/covenants_power_art.o $(BUILD)/story_rewards.o $(BUILD)/journal_nav.o $(BUILD)/economy.o $(BUILD)/travel_feedback.o $(BUILD)/connected_roads.o $(BUILD)/save_feedback.o $(BUILD)/game_shop.o $(BUILD)/treasure_text_text.o $(BUILD)/feedback_world.o $(BUILD)/journey_goal.o $(BUILD)/journey_map.o $(BUILD)/journey_map_text.o $(BUILD)/companion_guide.o $(BUILD)/companion_guide_text.o $(BUILD)/opening_scene.o $(BUILD)/opening_scene_data.o $(BUILD)/ending_credits.o $(BUILD)/ending_credits_text.o

.PHONY: all clean tools assets test-tools test test-campaign test-systems test-quickparty test-quickparty-evolved test-equipment test-regional test-northern test-northern-host quickparty-video gameplay-video developer-video
all: $(TARGET).gba

$(BUILD):
	mkdir -p $(BUILD)

$(BUILD)/%.o: src/%.c | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/music.o: src/music.c | $(BUILD)
	$(CC) $(filter-out -mthumb,$(CFLAGS)) -marm -c $< -o $@

$(BUILD)/startup.o: src/startup.s | $(BUILD)
	$(CC) $(ASFLAGS) -c $< -o $@

$(TARGET).elf: $(OBJECTS) linker.ld
	$(CC) $(LDFLAGS) $(OBJECTS) -lgcc -o $@
	$(SIZE) $@
	$(NM) -n $@ > $(TARGET).sym

$(TARGET).gba: $(TARGET).elf tools/fix_header.py tools/freeze_runtime_sources.py
	$(OBJCOPY) -O binary $< $@
	$(PYTHON) tools/fix_header.py $@
	$(PYTHON) tools/freeze_runtime_sources.py --output $(BUILD)/source-hashes.json

# Generated asset C files ship with the source. Regeneration is optional and
# needs Pillow plus the fonts used by the artwork/UI generator scripts.
assets:
	$(PYTHON) tools/generate_connected_roads.py
	$(PYTHON) assets/generate_assets.py
	$(PYTHON) assets/generate_ui.py
	$(PYTHON) tools/generate_journey_map.py
	$(PYTHON) assets/generate_companion_guide.py
	$(PYTHON) assets/generate_gear_preview.py
	$(PYTHON) assets/generate_treasure_text.py
	$(PYTHON) assets/generate_opening_scene.py
	$(PYTHON) assets/generate_ending_credits.py
	$(PYTHON) assets/generate_world.py
	$(PYTHON) assets/generate_campaign.py
	$(PYTHON) assets/generate_campaign_rules.py
	$(PYTHON) assets/creatures/format_catalog.py
	$(PYTHON) assets/creatures/generate_data.py
	$(PYTHON) assets/generate_evolutions.py
	$(PYTHON) assets/generate_trials.py
	$(PYTHON) assets/equipment/generate_data.py
	$(PYTHON) assets/generate_region.py
	$(PYTHON) assets/generate_regional_creatures.py
	$(PYTHON) assets/generate_northern_creatures.py
	$(PYTHON) assets/generate_northern_region.py
	$(PYTHON) assets/generate_southern_region.py
	$(PYTHON) assets/generate_southern_creatures.py
	$(PYTHON) assets/generate_magma_region.py
	$(PYTHON) assets/generate_magma_creatures.py
	$(PYTHON) assets/generate_underwater_region.py
	$(PYTHON) assets/generate_underwater_creatures.py --world-successor connected-roads-c4
	$(PYTHON) assets/generate_return_region.py
	$(PYTHON) assets/generate_return_trials.py
	$(PYTHON) assets/generate_return_creatures.py --world-successor connected-roads-c4
	$(PYTHON) assets/generate_return_powers.py
	$(PYTHON) assets/generate_horizons_region.py
	$(PYTHON) assets/generate_horizons_creatures.py
	$(PYTHON) assets/generate_horizons_powers.py
	$(PYTHON) assets/generate_covenants_region.py
	$(PYTHON) assets/generate_covenants_work.py
	$(PYTHON) assets/generate_covenants_creatures.py
	$(PYTHON) assets/generate_covenants_powers.py
	$(PYTHON) assets/generate_feedback_world.py
	$(PYTHON) tools/generate_feedback_title.py
	$(PYTHON) tools/generate_southern_beams.py
	$(PYTHON) tools/generate_font_credits.py

tools:
	./tools/install_tools.sh

# Retained early controller recipes target their historical navigation.
# They are not the current release acceptance aggregate.
test-historical-workflows: all
	$(PYTHON) tests/playthrough.py
	$(PYTHON) tests/review_tests.py
	$(PYTHON) tests/exploration_tests.py
	$(PYTHON) tests/test_save4.py
	$(PYTHON) tests/test_save5.py
	$(PYTHON) tests/test_southern_save.py
	$(PYTHON) tests/test_southern_save_limits.py
	$(PYTHON) tests/test_progression_events.py
	$(PYTHON) tests/test_creatures.py
	$(PYTHON) tests/test_trials.py
	$(PYTHON) tests/test_save_feedback.py
	$(MAKE) test-equipment
	$(MAKE) test-systems
	$(MAKE) test-quickparty
	$(MAKE) test-quickparty-evolved
	$(MAKE) test-campaign
	$(MAKE) test-regional
	$(MAKE) test-northern
	$(MAKE) test-southern

# State fixtures and timing evidence are always produced by this exact ROM.
test-campaign: all
	$(PYTHON) tools/archive_test_output.py build/campaign-performance-minimal build/campaign-performance-optional
	$(PYTHON) tests/campaign_tests.py --output build/campaign-qa
	$(PYTHON) tests/campaign_tests.py --optional --output build/campaign-optional
	$(PYTHON) tests/campaign_performance.py --campaign build/campaign-qa/campaign-report.json --output build/campaign-performance-minimal --strict-cold
	$(PYTHON) tests/campaign_performance.py --campaign build/campaign-optional/campaign-report.json --output build/campaign-performance-optional --strict-cold

# New-system routes include deliberate declines, interrupted commits and native
# full-screen/OAM/cadence checks. Legacy input is a pinned real prior-ROM save.
test-systems: all
	$(PYTHON) tests/new_game_confirmation.py --rom $(TARGET).gba --symbols $(TARGET).sym --output build/new-game-confirmation
	$(PYTHON) tests/quickparty_migration_tests.py --rom $(TARGET).gba --symbols $(TARGET).sym --output build/pr5-quickparty-migration-qa
	$(PYTHON) tests/expedition_tests.py --rom $(TARGET).gba --symbols $(TARGET).sym --output build/expedition-qa
	$(PYTHON) tests/fullscreen_tests.py --rom $(TARGET).gba --symbols $(TARGET).sym --output build/fullscreen-qa
	$(PYTHON) tests/evolution_tests.py --rom $(TARGET).gba --symbols $(TARGET).sym --output build/evolution-qa
	$(PYTHON) tests/evolution_tests.py --rom $(TARGET).gba --symbols $(TARGET).sym --six-hearts --output build/evolution-six-hearts
	$(PYTHON) tests/evolution_tests.py --rom $(TARGET).gba --symbols $(TARGET).sym --legacy-save tests/fixtures/v4/migration-campaign-complete.sav --legacy-report tests/fixtures/v4/migration-provenance.json --output build/evolution-migrated
	$(PYTHON) tests/advanced_power_tests.py --journey build/evolution-qa/evolution-report.json --output build/advanced-power-qa --source-contracts

gameplay-video: all
	$(PYTHON) tools/archive_test_output.py build/horizons-teaser
	$(PYTHON) tests/capture_horizons_teaser.py --candidate-root build/horizons-native --prior-h-root build/horizons-prior-h-inputs --producer-report build/horizons-native/minimal-water/horizons-journey.json --producer-sha $$( $(PYTHON) tools/file_sha256.py build/horizons-native/minimal-water/horizons-journey.json ) --output build/horizons-teaser

# Spoiler-bearing full route is development evidence, not the default trailer.
developer-video: all
	$(PYTHON) tests/capture_campaign_video.py

test-tools:
	$(PYTHON) tools/smoke_tests/test_bridge.py

.PHONY: test-journey-guidance-host
test-journey-guidance-host: all
	$(PYTHON) tools/archive_test_output.py build/journey-guidance-host
	$(PYTHON) tools/run_journey_guidance_host.py --output build/journey-guidance-host

clean:
	rm -f $(BUILD)/*.o $(BUILD)/*.d $(TARGET).elf $(TARGET).gba $(TARGET).map $(TARGET).sym

-include $(OBJECTS:.o=.d)

test-quickparty: all
	$(PYTHON) tests/quickparty_tests.py --rom $(TARGET).gba --symbols $(TARGET).sym --output build/quickparty-qa
	$(PYTHON) tests/quickparty_tests.py --rom $(TARGET).gba --symbols $(TARGET).sym --synthetic-interruptions --output build/quickparty-synthetic-qa

# Requires the matching controller journey produced by test-systems.
test-quickparty-evolved: all
	$(PYTHON) tests/quickparty_tests.py --rom $(TARGET).gba --symbols $(TARGET).sym --journey build/evolution-qa/evolution-report.json --output build/quickparty-evolved-qa

quickparty-video: all
	$(PYTHON) tests/capture_quickparty_demo.py

# Host/core/art contracts are distinct from controller-only native journeys.
test-equipment:
	$(PYTHON) tests/test_equipment.py
	$(PYTHON) tests/test_weapon_actions.py
	$(PYTHON) tests/test_gear_runtime.py
	$(PYTHON) tests/test_gear_numbers.py
	$(PYTHON) tests/test_gear_hearts.py
	$(PYTHON) tests/test_regional_quests.py
	$(PYTHON) tests/test_regional_adapters.py
	$(PYTHON) tests/test_region_art.py
	$(PYTHON) tests/test_regional_creature_art.py
	$(PYTHON) tests/test_region_game.py

# Controller-only regional journey seeds the same-ROM combat/collection suite.
test-regional: all
	$(PYTHON) tests/region_journey.py --rom $(TARGET).gba --symbols $(TARGET).sym --output build/region-journey
	$(PYTHON) tests/region_combat_tests.py --rom $(TARGET).gba --symbols $(TARGET).sym --source-report build/region-journey/region-journey.json --output build/region-combat

# Host contracts are separate from native collection and frame-cadence evidence.
test-northern-host:
	$(PYTHON) tests/test_creature_sparse.py
	$(PYTHON) tests/test_north_art.py
	$(PYTHON) tests/test_north_game.py
	NORTH_SANITIZE=1 $(PYTHON) tests/test_north_game.py
	$(PYTHON) tests/test_northern_creature_art.py
	$(PYTHON) tests/test_northern_powers.py
	$(PYTHON) tests/northern_host_cases.py --output build/northern-host-cases.json

# All fixtures are earned by this exact cartridge. No prior-ROM machine states.
test-northern: all test-northern-host
	$(PYTHON) tests/northern_journey.py $(NORTHERN_ARGS) --output build/northern-journey
	$(PYTHON) tests/test_northern_source_provenance.py --source-report build/northern-journey/northern-journey.json --rom $(TARGET).gba --symbols $(TARGET).sym --output build/northern-source-provenance.json
	$(PYTHON) tests/northern_sky_route.py $(NORTHERN_ARGS) --output build/northern-sky-route
	$(PYTHON) tests/northern_stress.py $(NORTHERN_ARGS) --journey-report build/northern-journey/northern-journey.json --output build/northern-stress
	$(PYTHON) tests/northern_boss_controls.py $(NORTHERN_ARGS) --journey-report build/northern-journey/northern-journey.json --output build/northern-boss-controls
	$(PYTHON) tests/northern_modal_pixels.py $(NORTHERN_ARGS) --source-report build/northern-journey/northern-journey.json --output build/northern-modal-pixels
	$(PYTHON) tests/northern_combat_tests.py $(NORTHERN_ARGS) --source-report build/northern-journey/northern-journey.json --output build/northern-combat

# Development Southern acceptance: authoring/host contracts, not acquisition.
test-southern-host:
	$(PYTHON) tests/test_arm_toolchain.py
	$(PYTHON) assets/creatures/format_catalog.py --check
	$(PYTHON) tests/test_southern_catalog.py
	$(PYTHON) tests/test_southern_creature_core.py
	$(PYTHON) tests/test_creature_branches.py
	$(PYTHON) tests/test_southern_creature_art.py
	$(PYTHON) tests/test_south_art.py
	$(PYTHON) tests/test_south_game.py
	SOUTH_SANITIZE=1 $(PYTHON) tests/test_south_game.py
	$(PYTHON) tests/test_southern_save.py
	$(PYTHON) tests/test_southern_save_limits.py
	$(PYTHON) tests/test_southern_powers.py
	$(PYTHON) tests/test_southern_validation_optimization.py
	$(PYTHON) tests/test_geometry_fingerprint.py
	$(PYTHON) tests/test_quickparty_scan.py

# Every route earns its own source SRAM on the exact cartridge under test.
.PHONY: test-southern test-southern-host
test-southern: all test-southern-host
	$(PYTHON) tests/southern_minimal_route.py $(NORTHERN_ARGS) --source-manifest build/source-hashes.json --output build/southern-minimal-route
	$(PYTHON) tests/southern_journey.py $(NORTHERN_ARGS) --source-manifest build/source-hashes.json --output build/southern-journey
	$(PYTHON) tests/southern_targeting.py $(NORTHERN_ARGS) --source-manifest build/source-hashes.json --output build/southern-targeting
	$(PYTHON) tests/southern_optics.py $(NORTHERN_ARGS) --source-manifest build/source-hashes.json --output build/southern-optics
	$(PYTHON) tests/southern_controls.py $(NORTHERN_ARGS) --source-manifest build/source-hashes.json --output build/southern-controls
	$(PYTHON) tests/southern_selector.py $(NORTHERN_ARGS) --source-manifest build/source-hashes.json --earned-report build/southern-journey/southern-journey.json --output build/southern-selector
	$(PYTHON) tests/southern_combat_tests.py $(NORTHERN_ARGS) --elf $(TARGET).elf --source-manifest build/source-hashes.json --source-report build/southern-journey/southern-journey.json --output build/southern-combat
	$(PYTHON) tests/southern_native_performance.py $(NORTHERN_ARGS) --elf $(TARGET).elf --source-manifest build/source-hashes.json --source-report build/southern-journey/southern-journey.json --output build/southern-performance
	$(PYTHON) tests/southern_render_controls.py $(NORTHERN_ARGS) --elf $(TARGET).elf --source-manifest build/source-hashes.json --source-report build/southern-journey/southern-journey.json --output build/southern-render


# Reviewed historical policy/multi-trial foundation, before new region enablement.
.PHONY: test-magma-architecture
test-magma-architecture:
	$(PYTHON) tools/generate_creature_history.py --check
	$(PYTHON) assets/creatures/generate_data.py --check
	$(PYTHON) tests/test_magma_architecture.py
	$(PYTHON) tests/test_magma_history_core.py
	$(PYTHON) tests/test_save5_history.py
	$(PYTHON) tests/test_save5_history_differential.py

# Current Magma host contracts are separate from earned native gameplay.
.PHONY: test-magma-host test-magma test-magma-native
test-magma-host: test-magma-architecture
	$(PYTHON) tests/test_magma_catalog_policy.py
	$(PYTHON) tests/test_magma_creature_core.py
	$(PYTHON) tests/test_magma_legacy_admission.py
	$(PYTHON) tests/test_southern_frozen_fixtures.py
	$(PYTHON) tests/test_magma_creature_art.py
	$(PYTHON) tests/test_magma_art.py
	$(PYTHON) tests/test_magma_game.py
	$(PYTHON) tests/test_magma_save.py
	$(PYTHON) tests/test_magma_save_limits.py
	$(PYTHON) tests/test_magma_powers.py
	$(PYTHON) tests/test_magma_evolution_ui.py
	$(PYTHON) tests/test_magma_evidence.py
	mkdir -p $(BUILD)
	$(PYTHON) tests/test_deferred_probe_launcher.py
	$(PYTHON) tests/test_deferred_probe_mapping.py
	# The original one-update anchor oracle remains preserved with frozen F.
	# Current runtime validates the same transaction across bounded updates.
	$(PYTHON) tools/run_bounded_magma_save_probe.py

# New native outputs are archived before replay; no old run is relabeled.
test-magma: test-magma-host test-magma-native

test-magma-native: all
	$(PYTHON) tools/archive_test_output.py build/magma-journey build/magma-minimal build/magma-controls build/magma-retained build/magma-combat build/magma-performance build/magma-teaching-boss
	$(PYTHON) tests/magma_journey.py $(NORTHERN_ARGS) --output build/magma-journey --scope full
	$(PYTHON) tools/archive_magma_test_sources.py build/magma-journey/magma-journey.json
	$(PYTHON) tests/magma_minimal_route.py $(NORTHERN_ARGS) --source-manifest build/source-hashes.json --output build/magma-minimal
	$(PYTHON) tests/magma_controls.py $(NORTHERN_ARGS) --source-manifest build/source-hashes.json --source-report build/magma-journey/magma-journey.json --output build/magma-controls
	$(PYTHON) tests/magma_retained_controls.py $(NORTHERN_ARGS) --source-manifest build/source-hashes.json --source-report build/magma-journey/magma-journey.json --output build/magma-retained
	$(PYTHON) tests/magma_combat_tests.py $(NORTHERN_ARGS) --source-manifest build/source-hashes.json --source-report build/magma-journey/magma-journey.json --source-snapshot 09-all65-earned-town --output build/magma-combat
	$(PYTHON) tests/magma_native_performance.py $(NORTHERN_ARGS) --source-manifest build/source-hashes.json --source-report build/magma-journey/magma-journey.json --source-snapshot 09-all65-earned-town --output build/magma-performance
	$(PYTHON) tests/magma_combat_tests.py $(NORTHERN_ARGS) --source-manifest build/source-hashes.json --source-report build/magma-journey/magma-journey.json --source-snapshot 02-teaching-companions --case teaching-boss --output build/magma-teaching-boss

# Expanded chapter checks remain separate from controller-only release routes.
.PHONY: test-underwater-host
test-underwater-host:
	$(PYTHON) tests/test_underwater_creature_core.py
	$(PYTHON) tests/test_underwater_history_differential.py
	$(PYTHON) tests/test_underwater_creature_art.py
	$(PYTHON) tests/test_underwater_art.py
	$(PYTHON) tests/test_underwater_game.py
	$(PYTHON) tests/test_underwater_clear_box.py
	UNDERWATER_WORLD_POWERS=1 $(PYTHON) tests/test_underwater_game.py
	$(PYTHON) tests/test_underwater_landings.py
	$(PYTHON) tests/test_underwater_localization.py
	$(PYTHON) tests/test_underwater_save.py
	$(PYTHON) tests/test_underwater_transactions.py
	$(PYTHON) tests/test_underwater_powerloss.py
	$(PYTHON) tests/test_underwater_return_spawns.py
	$(PYTHON) tests/test_underwater_powers.py
	$(PYTHON) tests/test_magma_evolution_ui.py

# Native producers earn their own fixtures before exact-ROM dependent checks.
.PHONY: test-underwater test-underwater-native
test-underwater: test-underwater-host test-underwater-native
test-underwater-native: all
	$(PYTHON) tools/archive_test_output.py build/underwater-native
	$(PYTHON) tools/run_underwater_native.py --rom $(TARGET).gba --symbols $(TARGET).sym --source-manifest build/source-hashes.json --output build/underwater-native

# Current Return7 authoring/core/geometry/transaction gates. Native controller
# acquisition, combat and presentation remain a separate exact-ROM recipe.
.PHONY: test-return-host
test-return-host:
	$(PYTHON) tests/test_return_catalog.py
	$(PYTHON) tests/test_return_history_core.py
	$(PYTHON) tests/test_return_history_differential.py
	$(PYTHON) tests/test_return_current_masks.py
	$(PYTHON) tests/test_return_creature_art.py
	$(PYTHON) tests/test_return_geometry.py
	$(PYTHON) tests/test_return_world.py
	$(PYTHON) tests/test_return_transactions.py
	$(PYTHON) tests/test_return_powerloss.py
	$(PYTHON) tests/test_return_migration_powerloss.py
	$(PYTHON) tests/test_return_sanitizers.py
	$(PYTHON) tests/test_return_powers.py
	$(PYTHON) tests/test_return_legacy_powers.py
	$(PYTHON) tests/test_return_tile_lease.py
	$(PYTHON) tests/test_magma_recruit_transactions.py
	$(PYTHON) tests/test_magma_recruit_runtime.py
	$(PYTHON) tests/test_magma_evolution_ui.py
	$(PYTHON) tests/test_obj_upload_wordpath.py
	$(PYTHON) tests/test_magma_boundary_engine_contract.py
	$(PYTHON) tools/archive_test_output.py build/return-host-boundaries
	$(PYTHON) tests/test_magma_boundaries.py --output build/return-host-boundaries/magma-strict.json
	$(PYTHON) tests/test_magma_boundaries.py --sanitize --output build/return-host-boundaries/magma-sanitized.json
	$(PYTHON) tests/test_southern_enter_job.py --output build/return-host-boundaries/southern-strict.json
	$(PYTHON) tests/test_southern_enter_job.py --sanitize --output build/return-host-boundaries/southern-sanitized.json
	$(PYTHON) tools/run_bounded_magma_save_probe.py
	$(PYTHON) tests/underwater_engine_review/run_probe.py test_bounded_southern_rest.py

.PHONY: test-return-native test-return-modal
test-return-native: all
	$(PYTHON) tools/archive_test_output.py build/return-native
	$(PYTHON) tools/run_return_native.py $(NORTHERN_ARGS) --elf $(TARGET).elf --source-manifest build/source-hashes.json --source-root . --expected-elf-sha $$( $(PYTHON) tools/file_sha256.py $(TARGET).elf ) --expected-manifest-sha $$( $(PYTHON) tools/file_sha256.py build/source-hashes.json ) --output build/return-native

# Frozen prior native hashes make the synthetic full-screen comparison portable.
# This is pixel regression coverage, separate from controller/timing acceptance.
test-return-modal: all
	$(PYTHON) tools/archive_test_output.py build/return-modal-pixels
	$(PYTHON) tests/return_modal_boundary_matrix.py --baseline-report tests/fixtures/return-modal-e-golden.json.gz --after-root . --output build/return-modal-pixels

# Shared Horizons content8: host correctness and native controller acquisition
# are separate gates. The native bridge exposes no game-memory write or
# machine-state loading API; prior inputs are exact accepted H ordinary saves.
.PHONY: test-horizons-host test-horizons-native test-horizons
test-horizons: test-horizons-host test-horizons-native
test-horizons-host:
	$(PYTHON) tests/test_horizons_catalog.py
	$(PYTHON) tests/test_horizons_history.py
	$(PYTHON) tests/test_horizons_transactions.py
	$(PYTHON) tests/test_horizons_preflight_ownership.py
	$(PYTHON) tests/test_horizons_powerloss.py
	$(PYTHON) tests/test_horizons_sanitizers.py
	$(PYTHON) tests/test_horizons_creature_art.py
	$(PYTHON) tests/test_horizons_geometry.py
	$(PYTHON) tests/test_horizons_world.py
	$(PYTHON) tests/test_horizons_aim_binding.py
	$(PYTHON) tests/test_horizons_powers.py
	$(PYTHON) tests/test_horizons_power_rows.py
	$(PYTHON) tests/test_horizons_snapshot_contract.py
	$(PYTHON) tests/test_collision_rects.py
	COLLISION_RECTS_SANITIZE=1 $(PYTHON) tests/test_collision_rects.py
	$(PYTHON) tests/test_collision_rects_capacity.py
	$(PYTHON) tests/test_collision_rects_arm.py
	$(PYTHON) tests/test_horizons_audio.py
	$(PYTHON) tests/test_horizons_camera.py --report build/horizons-camera-host.json
	$(PYTHON) tests/test_horizons_stage_panel.py --report build/horizons-stage-panel-host.json
	$(PYTHON) tests/check_horizons_field_feasibility.py
	$(PYTHON) tests/test_return_tile_lease.py

test-horizons-native: all
	./tools/build_horizons_mgba_bridge.sh
	$(PYTHON) tools/prepare_horizons_prior_fixtures.py --output build/horizons-prior-h-inputs
	$(PYTHON) tools/archive_test_output.py build/horizons-native
	$(PYTHON) tools/run_horizons_native.py --candidate build --source-root . --h-native-root build/horizons-prior-h-inputs --output build/horizons-native

# Run test-return-native first; this gate authenticates that earned same-ROM
# producer and its SRAM. NumPy/SciPy are used only for sample comparison.
.PHONY: test-music
test-music: all
	$(PYTHON) tools/archive_test_output.py build/music-transport
	$(PYTHON) tests/music_transport.py --rom $(TARGET).gba --producer-report build/return-native/full/return-journey.json --producer-sha $$( $(PYTHON) tools/file_sha256.py build/return-native/full/return-journey.json ) --output build/music-transport

# Content9 host correctness and genuine controller acceptance are separate.
# Native acceptance earns both original Core preludes and all dependent routes.
.PHONY: test-covenants test-covenants-host test-covenants-native
test-covenants: test-covenants-host test-covenants-native

test-covenants-host: all
	$(PYTHON) tools/archive_test_output.py build/covenants-host
	$(PYTHON) tools/run_covenants_host.py --output build/covenants-host

test-covenants-native: all
	./tools/build_horizons_mgba_bridge.sh
	$(PYTHON) tools/archive_test_output.py build/covenants-native
	$(PYTHON) tools/run_covenants_acceptance.py --candidate build --source-root . --prior-root . --output build/covenants-native

.PHONY: test-player-feedback-host
test-player-feedback-host: all
	$(PYTHON) tools/archive_test_output.py build/player-feedback-host
	$(PYTHON) tools/run_player_feedback_host.py --output build/player-feedback-host

.PHONY: test-connected-roads-host
test-connected-roads-host: all
	$(PYTHON) tools/archive_test_output.py build/connected-roads-host
	$(PYTHON) tools/run_connected_roads_host.py --output build/connected-roads-host

.PHONY: test-gear-preview-host
test-gear-preview-host: all
	$(PYTHON) tests/test_gear_preview.py
	$(PYTHON) tests/gear_readable_layout.py
	$(PYTHON) tests/test_player_feedback_gear_cache.py
	$(PYTHON) tests/test_gear_numbers.py
	$(PYTHON) tests/test_gear_hearts.py
	$(PYTHON) tests/test_shared_text_spans.py
	$(PYTHON) tests/test_player_feedback_menu.py
	$(PYTHON) tests/test_companion_guide.py

.PHONY: test-equipment-rewards-host test-historical-workflows
test: test-equipment-rewards-host
test-equipment-rewards-host: all
	$(PYTHON) tools/archive_test_output.py build/equipment-rewards-host-current
	$(PYTHON) tools/run_equipment_rewards_host.py --output build/equipment-rewards-host-current

.PHONY: font-assets
font-assets:
	$(PYTHON) assets/generate_ui.py
	$(PYTHON) tools/generate_journey_map.py
	$(PYTHON) assets/generate_companion_guide.py
	$(PYTHON) assets/generate_gear_preview.py
	$(PYTHON) assets/generate_treasure_text.py
	$(PYTHON) assets/generate_opening_scene.py
	$(PYTHON) assets/generate_ending_credits.py
	$(PYTHON) tools/generate_font_credits.py

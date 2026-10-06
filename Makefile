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
OBJECTS := $(BUILD)/startup.o $(BUILD)/game.o $(BUILD)/assets.o $(BUILD)/ui.o $(BUILD)/world.o $(BUILD)/campaign_art.o $(BUILD)/campaign_rules.o $(BUILD)/save4.o $(BUILD)/creatures.o $(BUILD)/creature_data.o $(BUILD)/save5.o $(BUILD)/progression.o $(BUILD)/evolution_art.o $(BUILD)/advanced_powers.o $(BUILD)/trials.o $(BUILD)/trial_art.o $(BUILD)/quickparty.o $(BUILD)/equipment.o $(BUILD)/equipment_data.o $(BUILD)/combat_rules.o $(BUILD)/weapon_actions.o $(BUILD)/gear_runtime.o $(BUILD)/gear_menu.o $(BUILD)/regional_quests.o $(BUILD)/regional_creature_art.o $(BUILD)/regional_powers.o $(BUILD)/region_art.o $(BUILD)/region_game.o $(BUILD)/northern_creature_art.o $(BUILD)/north_art.o $(BUILD)/north_game.o $(BUILD)/northern_quests.o $(BUILD)/northern_powers.o $(BUILD)/northern_power_art.o

.PHONY: all clean tools assets test-tools test test-campaign test-systems test-quickparty test-quickparty-evolved test-equipment test-regional test-northern test-northern-host quickparty-video gameplay-video developer-video
all: $(TARGET).gba

$(BUILD):
	mkdir -p $(BUILD)

$(BUILD)/%.o: src/%.c | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/startup.o: src/startup.s | $(BUILD)
	$(CC) $(ASFLAGS) -c $< -o $@

$(TARGET).elf: $(OBJECTS) linker.ld
	$(CC) $(LDFLAGS) $(OBJECTS) -lgcc -o $@
	$(SIZE) $@
	$(NM) -n $@ > $(TARGET).sym

$(TARGET).gba: $(TARGET).elf tools/fix_header.py
	$(OBJCOPY) -O binary $< $@
	$(PYTHON) tools/fix_header.py $@

# Generated asset C files ship with the source. Regeneration is optional and
# needs Pillow plus the fonts used by the artwork/UI generator scripts.
assets:
	$(PYTHON) assets/generate_assets.py
	$(PYTHON) assets/generate_ui.py
	$(PYTHON) assets/generate_world.py
	$(PYTHON) assets/generate_campaign.py
	$(PYTHON) assets/generate_campaign_rules.py
	$(PYTHON) assets/creatures/generate_data.py
	$(PYTHON) assets/generate_evolutions.py
	$(PYTHON) assets/generate_trials.py
	$(PYTHON) assets/equipment/generate_data.py
	$(PYTHON) assets/generate_region.py
	$(PYTHON) assets/generate_regional_creatures.py
	$(PYTHON) assets/generate_northern_creatures.py
	$(PYTHON) assets/generate_northern_region.py

tools:
	./tools/install_tools.sh

test: all
	$(PYTHON) tests/playthrough.py
	$(PYTHON) tests/review_tests.py
	$(PYTHON) tests/exploration_tests.py
	$(PYTHON) tests/test_save4.py
	$(PYTHON) tests/test_save5.py
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
	$(PYTHON) tests/quickparty_migration_tests.py --rom $(TARGET).gba --symbols $(TARGET).sym --output build/pr5-quickparty-migration-qa
	$(PYTHON) tests/expedition_tests.py --rom $(TARGET).gba --symbols $(TARGET).sym --output build/expedition-qa
	$(PYTHON) tests/fullscreen_tests.py --rom $(TARGET).gba --symbols $(TARGET).sym --output build/fullscreen-qa
	$(PYTHON) tests/evolution_tests.py --rom $(TARGET).gba --symbols $(TARGET).sym --output build/evolution-qa
	$(PYTHON) tests/evolution_tests.py --rom $(TARGET).gba --symbols $(TARGET).sym --six-hearts --output build/evolution-six-hearts
	$(PYTHON) tests/evolution_tests.py --rom $(TARGET).gba --symbols $(TARGET).sym --legacy-save tests/fixtures/v4/migration-campaign-complete.sav --legacy-report tests/fixtures/v4/migration-provenance.json --output build/evolution-migrated
	$(PYTHON) tests/advanced_power_tests.py --journey build/evolution-qa/evolution-report.json --output build/advanced-power-qa --source-contracts

gameplay-video: all
	$(PYTHON) tests/capture_northern_teaser.py $(NORTHERN_ARGS) --output build/northern-teaser/release

# Spoiler-bearing full route is development evidence, not the default trailer.
developer-video: all
	$(PYTHON) tests/capture_campaign_video.py

test-tools:
	$(PYTHON) tools/smoke_tests/test_bridge.py

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

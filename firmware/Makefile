# CORDIC-vs-minimax firmware build
# Usage:
#   make TOTAL_BITS=16 FRAC_BITS=14
#   make sweep                        (builds all 3 canonical widths)
#
# Invoke with Atmel Studio make if not on PATH:
#   "C:\Program Files (x86)\Atmel\Studio\7.0\shellutils\make.exe" TOTAL_BITS=16 FRAC_BITS=14

MCU      = atxmega128a1u
F_CPU    = 32000000UL
PYTHON   = python

CC       = avr-gcc
OBJCOPY  = avr-objcopy
OBJDUMP  = avr-objdump
SIZE     = avr-size

TOTAL_BITS ?= 16
FRAC_BITS  ?= 14

BUILD    = build/q$(TOTAL_BITS)_$(FRAC_BITS)
HOSTGEN  = ../hostgen/gen_constants.py

SRCS     = main.c cordic.c poly.c bench.c uart.c
OBJS     = $(patsubst %.c,$(BUILD)/%.o,$(SRCS))
ELF      = $(BUILD)/firmware.elf
HEX      = $(BUILD)/firmware.hex
LSS      = $(BUILD)/firmware.lss

CFLAGS   = -mmcu=$(MCU) -DF_CPU=$(F_CPU)
CFLAGS  += -DTOTAL_BITS=$(TOTAL_BITS) -DFRAC_BITS=$(FRAC_BITS)
CFLAGS  += -Os -Wall -Wextra -std=gnu99
CFLAGS  += -I. -I$(BUILD)
LDFLAGS  = -mmcu=$(MCU)

.PHONY: all sweep clean disasm

all: $(HEX)

# --- directory creation ---
$(BUILD):
	if not exist "$(subst /,\,$(BUILD))" mkdir "$(subst /,\,$(BUILD))"

# --- host-side constant generation ---
$(BUILD)/generated.h: $(HOSTGEN) | $(BUILD)
	$(PYTHON) $(HOSTGEN) $(TOTAL_BITS) $(FRAC_BITS) > $@

# --- compile ---
$(BUILD)/%.o: %.c fixed_point.h cordic.h poly.h bench.h uart.h $(BUILD)/generated.h | $(BUILD)
	$(CC) $(CFLAGS) -c -o $@ $<

# --- link ---
$(ELF): $(OBJS)
	$(CC) $(LDFLAGS) -o $@ $^

# --- outputs ---
$(HEX): $(ELF)
	$(OBJCOPY) -O ihex -R .eeprom $< $@
	$(SIZE) --format=avr --mcu=$(MCU) $<

disasm: $(ELF)
	$(OBJDUMP) -d -S $< > $(LSS)

# --- sweep all canonical widths ---
sweep:
	$(MAKE) TOTAL_BITS=8  FRAC_BITS=6
	$(MAKE) TOTAL_BITS=16 FRAC_BITS=14
	$(MAKE) TOTAL_BITS=32 FRAC_BITS=30

clean:
	if exist build rmdir /s /q build

#pragma once
#include <stdint.h>

enum Next : uint8_t { TO_SLEEP, TO_SIMON };

Next picker_run();   // the turn picker: the mode it always wakes in
void simon_run();    // Simon, started by MODE; returns to the picker at game over or on MODE
void spin(uint8_t level, uint16_t step_ms);   // one lap of the seats, clockwise from seat 1

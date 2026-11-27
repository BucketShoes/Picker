// Picker box: wakes on any button in the turn picker, MODE switches to Simon, and it sleeps when left alone.
#include <Arduino.h>
#include "board.h"
#include "buttons.h"
#include "games.h"
#include "leds.h"
#include "power.h"

void setup() {
    board_init();
    buttons_reset(0);
    leds_start();
    spin(gamma16(12), 80);   // on power-up (cell in): one lap, which also checks every LED
}

void loop() {
    if (picker_run() == TO_SIMON)
        simon_run();         // then back to the picker, which sleeps when left alone
    else
        power_sleep();       // returns on a press, which then counts in the picker
}

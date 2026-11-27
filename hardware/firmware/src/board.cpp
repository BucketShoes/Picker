#include <avr/power.h>
#include <avr/wdt.h>
#include "board.h"

// Runs before Arduino's init(): clear a watchdog reset and set the clock to 8 MHz / 2 = 4 MHz, whatever CKDIV8 is.
static void early_init() __attribute__((naked, used, section(".init3")));
static void early_init() {
    MCUSR = 0;
    wdt_disable();
    CLKPR = _BV(CLKPCE);   // (avr-libc's clock_prescale_set() doesn't cover the 328PB)
    CLKPR = _BV(CLKPS0);   // divide by 2; must follow within 4 cycles, interrupts are still off here
}

void board_init() {
    // Set the port values before the directions, so no LED flashes on.
    PORTB = IDLE_PB;
    PORTC = PULL_PC;
    PORTD = IDLE_PD;
    DDRB = LED_PB;
    DDRC = 0;
    DDRD = LED_PD;
#ifdef PORTE
    PORTE = _BV(PE2) | _BV(PE3);
    DDRE = 0;
#endif
    // Nothing analog: ADC and comparator off. Only Timer 0 (millis) and Timer 2 (LED PWM) stay powered.
    ADCSRA = 0;
    ACSR = _BV(ACD);
    power_all_disable();
    power_timer0_enable();
    power_timer2_enable();
}

uint16_t btn_raw() {
    uint8_t b = ~PINB, c = ~PINC, d = ~PIND;
    uint16_t m = 0;
    for (uint8_t i = 0; i <= SEATS; i++)
        if ((b & BTN_B[i]) | (c & BTN_C[i]) | (d & BTN_D[i]))
            m |= 1u << i;
    return m;
}

void btn_port_masks(uint16_t m, uint8_t *b, uint8_t *c, uint8_t *d) {
    *b = *c = *d = 0;
    for (uint8_t i = 0; i <= SEATS; i++)
        if (m & (1u << i)) {
            *b |= BTN_B[i];
            *c |= BTN_C[i];
            *d |= BTN_D[i];
        }
}

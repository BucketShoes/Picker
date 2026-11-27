// Power-down sleep (about 0.2 uA), woken by any button.
#pragma once

// Returns after a button press, with the LEDs restarted. A button still held when it goes to sleep (stuck in a pocket,
// say) is driven low instead of pulled up, so it draws nothing, and no longer wakes it; the watchdog checks every 8 s
// (about 3 uA while any is stuck) whether it has been released.
void power_sleep();

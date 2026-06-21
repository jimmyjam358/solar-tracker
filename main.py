import time
import machine
from senko import Senko

# =====================================================================
# 1. SAFE HARDWARE INITIALIZATION (GPIO 25 and 33 stay dead on boot)
# =====================================================================
IN1 = machine.Pin(25, machine.Pin.OUT, value=0)
IN2 = machine.Pin(33, machine.Pin.OUT, value=0)

def absolute_stop():
    IN1.value(0)
    IN2.value(0)

absolute_stop()

# =====================================================================
# 2. CONFIGURATION & LIMITS
# =====================================================================
GITHUB_USER = "your_actual_github_username"
GITHUB_REPO = "your_repo_name"
OTA = Senko(user=GITHUB_USER, repo=GITHUB_REPO, files=["main.py"])

# Limit Switch Pins (NC Setup: 0 = Safe, 1 = Tripped/Broken Wire)
EAST_ENDSTOP = machine.Pin(26, machine.Pin.IN, machine.Pin.PULL_UP)
WEST_ENDSTOP = machine.Pin(27, machine.Pin.IN, machine.Pin.PULL_UP)

# =====================================================================
# 3. MAIN ROUTINE
# =====================================================================
def main():
    # Check for updates over Wi-Fi
    try:
        if OTA.update():
            absolute_stop()
            machine.reset()
    except:
        pass

    absolute_stop()

    while True:
        # If either switch opens/trips, force the H-bridge inputs to 0
        if EAST_ENDSTOP.value() == 1 or WEST_ENDSTOP.value() == 1:
            absolute_stop()
            time.sleep(1) 
        else:
            # Standby mode until we add the solar tracking math
            absolute_stop()
            time.sleep(0.1)

if __name__ == "__main__":
    main()


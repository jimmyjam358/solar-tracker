import time
import machine
from senko import Senko

# =====================================================================
# 1. HARDWARE & CONFIGURATION SETUP
# =====================================================================

GITHUB_USER = "your_actual_github_username"
GITHUB_REPO = "your_repo_name"
OTA = Senko(user=GITHUB_USER, repo=GITHUB_REPO, files=["main.py"])

# --- Motor Driver Pins (H-Bridge IN1/IN2) ---
IN1 = machine.Pin(12, machine.Pin.OUT)
IN2 = machine.Pin(14, machine.Pin.OUT)

# --- Limit Switch Pins (NC Setup) ---
# Safe/Unclicked = 0 | Triggered/Clicked = 1
EAST_ENDSTOP = machine.Pin(26, machine.Pin.IN, machine.Pin.PULL_UP)
WEST_ENDSTOP = machine.Pin(27, machine.Pin.IN, machine.Pin.PULL_UP)

def motor_stop():
    """Forces both control pins to 0 instantly cutting motor power"""
    IN1.value(0)
    IN2.value(0)

# Ensure motors are dead before doing anything else
motor_stop()

# =====================================================================
# 2. SAFE MOVEMENT ENGINE
# =====================================================================

def safe_drive(direction):
    """
    Drives the motor in a direction ONLY if the safety switch is clear.
    direction: 'EAST' or 'WEST'
    """
    # Read switches right now
    east_hit = EAST_ENDSTOP.value()
    west_hit = WEST_ENDSTOP.value()

    if direction == "WEST":
        if west_hit == 1:
            print("🚨 Cannot move WEST. West switch is already pressed!")
            motor_stop()
            return
        # Clear to move
        IN1.value(0)
        IN2.value(1)

    elif direction == "EAST":
        if east_hit == 1:
            print("🚨 Cannot move EAST. East switch is already pressed!")
            motor_stop()
            return
        # Clear to move
        IN1.value(1)
        IN2.value(0)

# =====================================================================
# 3. CORE OPERATIONAL SAFETY LOOP
# =====================================================================

def run_solar_tracking_cycle():
    """
    Main loop monitoring. If any motor pins are active, 
    this cuts them instantly if a switch changes state.
    """
    east_state = EAST_ENDSTOP.value()
    west_state = WEST_ENDSTOP.value()
    
    print(f"[MONITOR] East Switch: {east_state} | West Switch: {west_state}")
    
    # Absolute safety override: If an endstop is active, kill pins 12 and 14
    if east_state == 1 or west_state == 1:
        motor_stop()

def main():
    print("Checking GitHub for code updates...")
    try:
        if OTA.update():
            print("📣 New code update found and applied! Rebooting ESP32...")
            machine.reset()
        else:
            print("☑️ Code is up to date.")
    except Exception as e:
        print(f"⚠️ OTA Check failed: {e}")

    # Double-check motors are stopped post-boot
    motor_stop()

    # Infinite safe loop
    while True:
        run_solar_tracking_cycle()
        time.sleep(0.5) # Fast 500ms safety scanning rate

if __name__ == "__main__":
    main()






import time
import machine
import math
from senko import Senko

# =====================================================================
# 1. HARDWARE & CONFIGURATION SETUP
# =====================================================================

# --- OTA Configuration ---
# Replace these strings with your exact GitHub details
GITHUB_USER = "jimmyjam358"
GITHUB_REPO = "solar-tracker"
OTA = Senko(user=GITHUB_USER, repo=GITHUB_REPO, files=["main.py"])

# --- Motor Driver Pins (H-Bridge IN1/IN2) ---
IN1 = machine.Pin(12, machine.Pin.OUT)
IN2 = machine.Pin(14, machine.Pin.OUT)

# --- Limit Switch Pins ---
# Configured with internal pull-ups. Assumes Normally Closed (NC) for safety.
# (Reads 0 when safe/closed, Reads 1 when clicked/open/broken wire)
EAST_ENDSTOP = machine.Pin(26, machine.Pin.IN, machine.Pin.PULL_UP)
WEST_ENDSTOP = machine.Pin(27, machine.Pin.IN, machine.Pin.PULL_UP)

# --- Physical Frame Geometry Limits ---
HARD_LIMIT_WEST = 15.2   # Maximum tilt facing open sky
HARD_LIMIT_EAST = -24.2  # Maximum tilt facing the roofline

# Software buffers (stops 2 degrees before hitting the physical switches)
SOFT_LIMIT_MAX = HARD_LIMIT_WEST - 2.0  # 13.2°
SOFT_LIMIT_MIN = HARD_LIMIT_EAST + 2.0  # -22.2°

# Simulated tracking variables (keeps track of where the panel is pointing)
current_panel_angle = 0.0 

# =====================================================================
# 2. MOTOR CONTROL FUNCTIONS WITH SAFETY GUARDRAILS
# =====================================================================

def motor_stop():
    """Cuts power to the motor instantly"""
    IN1.value(0)
    IN2.value(0)

def drive_motor(direction, duration_seconds):
    """
    Drives the motor in a specific direction while actively monitoring endstops.
    direction: 'WEST' or 'EAST'
    """
    global current_panel_angle
    
    if direction == "WEST":
        # Check if we are already past our soft max limit before moving
        if current_panel_angle >= SOFT_LIMIT_MAX:
            print("✋ Already at maximum safe West limit. Movement blocked.")
            return
        IN1.value(0)
        IN2.value(1)
    elif direction == "EAST":
        # Check if we are already past our soft min limit before moving
        if current_panel_angle <= SOFT_LIMIT_MIN:
            print("✋ Already at minimum safe East limit. Movement blocked.")
            return
        IN1.value(1)
        IN2.value(0)

    start_time = time.time()
    while time.time() - start_time < duration_seconds:
        # HARDWARE SAFETY SHIELD:
        # If an endstop opens (value == 1), cut power instantly and break loop
        if WEST_ENDSTOP.value() == 1 and direction == "WEST":
            print("🚨 West Endstop hit! Emergency stop triggered.")
            current_panel_angle = HARD_LIMIT_WEST
            break
        if EAST_ENDSTOP.value() == 1 and direction == "EAST":
            print("🚨 East Endstop hit! Emergency stop triggered.")
            current_panel_angle = HARD_LIMIT_EAST
            break
            
        time.sleep(0.1)
    
    motor_stop()

# =====================================================================
# 3. WEATHER OVERRIDE LOGIC (AUTOMATIC TRACKING BYPASS)
# =====================================================================

def trigger_snow_dump():
    """Forces panel to tilt as high as the 4x4 post safely allows to shed snow"""
    print(f"❄️ Snow override active. Moving to max safe tilt: {SOFT_LIMIT_MAX}°")
    # In a full build, this would calculate the time needed to reach max tilt
    drive_motor("WEST", 15) 
    current_panel_angle = SOFT_LIMIT_MAX

def trigger_wind_safety():
    """Drops the panel down toward the roofline to minimize wind profile"""
    print(f"⚠️ High wind override active. Dropping to low profile: {SOFT_LIMIT_MIN}°")
    drive_motor("EAST", 15)
    current_panel_angle = SOFT_LIMIT_MIN

# =====================================================================
# 4. CORE OPERATIONAL LOOPS
# =====================================================================

def run_solar_tracking_cycle():
    """
    Placeholder for the daily sun tracking math.
    This will calculate where the sun is, check it against your soft limits,
    and drive the motor to adjust the panel angle smoothly.
    """
    print(f"[SYSTEM] Loop active. Monitoring for weather overrides... Current Tilt: {current_panel_angle}°")
    
    # Example placeholder behavior:
    # If a variable 'weather_status' says 'snow', it triggers the override.
    # Otherwise, it adjusts a few degrees to follow the sun.
    pass

def main():
    print("Checking GitHub for code updates...")
    try:
        if OTA.update():
            print("📣 New code update found and applied! Rebooting ESP32...")
            machine.reset()
        else:
            print("☑️ Code is up to date.")
    except Exception as e:
        print(f"⚠️ OTA Check skipped or failed: {e}")

    # Ensure motors are stopped on startup
    motor_stop()

    # Infinite loop running your outdoor tracking/monitoring system
    while True:
        run_solar_tracking_cycle()
        time.sleep(10) # Checks/adjusts every 10 seconds

if __name__ == "__main__":
    main()



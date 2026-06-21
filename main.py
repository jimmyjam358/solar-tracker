import time
import machine
import ntptime
import network
from senko import Senko

# =====================================================================
# 1. HARDWARE SETUP
# =====================================================================
IN1 = machine.Pin(25, machine.Pin.OUT, value=0)
IN2 = machine.Pin(33, machine.Pin.OUT, value=0)

EAST_ENDSTOP = machine.Pin(26, machine.Pin.IN, machine.Pin.PULL_UP)
WEST_ENDSTOP = machine.Pin(27, machine.Pin.IN, machine.Pin.PULL_UP)

led = machine.Pin(2, machine.Pin.OUT, value=0)

def motor_stop():
    IN1.value(0)
    IN2.value(0)

def move_west():
    if WEST_ENDSTOP.value() == 0:
        IN1.value(0)
        IN2.value(1)
    else:
        motor_stop()

def move_east():
    if EAST_ENDSTOP.value() == 0:
        IN1.value(1)
        IN2.value(0)
    else:
        motor_stop()

def blink_error_code(count):
    motor_stop()
    while True:
        for _ in range(count):
            led.value(1)
            time.sleep(0.2)
            led.value(0)
            time.sleep(0.2)
        time.sleep(1.5)

# Ensure motors are stopped on startup
motor_stop()

# =====================================================================
# 2. RUNTIME BOOT CHECKS
# =====================================================================
wlan = network.WLAN(network.STA_IF)
if not wlan.isconnected():
    blink_error_code(1) # Flash 1: No Wi-Fi

GITHUB_USER = "your_actual_github_username"
GITHUB_REPO = "your_repo_name"
OTA = Senko(user=GITHUB_USER, repo=GITHUB_REPO, files=["main.py"])

try:
    if OTA.update():
        motor_stop()
        machine.reset()
exceptException as e:
    blink_error_code(2) # Flash 2: GitHub/OTA error

try:
    ntptime.settime()
except:
    blink_error_code(3) # Flash 3: NTP Time sync error

# =====================================================================
# 3. FIXED SOLAR ENGINE WITH NEUTRAL PARKING
# =====================================================================
HARD_LIMIT_WEST = 15.2
HARD_LIMIT_EAST = -24.2
TOTAL_TRAVEL_ARC = HARD_LIMIT_WEST - HARD_LIMIT_EAST

START_HOUR = 8
END_HOUR = 18
TOTAL_TRACKING_SECONDS = (END_HOUR - START_HOUR) * 3600

def get_target_angle(current_hour, current_minute, current_second):
    """Calculates target angle, forcing 0.0° (FLAT) if outside tracking hours"""
    # NIGHTTIME PARKING OVERRIDE: If the sun is down, force the mount flat
    if current_hour < START_HOUR or current_hour >= END_HOUR:
        print("[SOLAR] Outside tracking hours. Target is 0.0° (Flat/Neutral Parking).")
        return 0.0  
        
    # Daytime tracking math
    seconds_since_start = ((current_hour - START_HOUR) * 3600) + (current_minute * 60) + current_second
    progress = seconds_since_start / TOTAL_TRACKING_SECONDS
    target_angle = HARD_LIMIT_EAST + (progress * TOTAL_TRAVEL_ARC)
    return target_angle

# =====================================================================
# 4. MAIN RUNTIME LOOP
# =====================================================================
def main():
    led.value(1) # Solid light confirms main loop is successfully running
    
    # We don't know where the frame is physically pointing when we power it up,
    # so we start our software estimation at neutral (0.0)
    current_estimated_angle = 0.0 

    while True:
        # Hardware E-Stop Shield
        if EAST_ENDSTOP.value() == 1 or WEST_ENDSTOP.value() == 1:
            motor_stop()
            time.sleep(1)
            continue

        # Fetch current internet time from internal RTC
        local_time = time.localtime()
        hour = local_time[3]
        minute = local_time[4]
        second = local_time[5]

        # Get where we need to be (Will return 0.0 right now since it's past END_HOUR)
        target_angle = get_target_angle(hour, minute, second)

        # Drive motor to match the target
        if target_angle > current_estimated_angle + 0.5:
            move_west()
            time.sleep(0.5)
            motor_stop()
            current_estimated_angle += 0.5 
        elif target_angle < current_estimated_angle - 0.5:
            move_east()
            time.sleep(0.5)
            motor_stop()
            current_estimated_angle -= 0.5
        else:
            # On target (e.g. successfully parked at 0.0°)
            motor_stop()
            
        time.sleep(10)

if __name__ == "__main__":
    main()






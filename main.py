import time
import machine
import ntptime
from senko import Senko

# =====================================================================
# 1. HARDWARE CONFIGURATION (Safe Boot Pins)
# =====================================================================
IN1 = machine.Pin(25, machine.Pin.OUT, value=0)
IN2 = machine.Pin(33, machine.Pin.OUT, value=0)

# Limit Switches (0 = Closed/Safe, 1 = Open/Tripped)
EAST_ENDSTOP = machine.Pin(26, machine.Pin.IN, machine.Pin.PULL_UP)
WEST_ENDSTOP = machine.Pin(27, machine.Pin.IN, machine.Pin.PULL_UP)

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

# =====================================================================
# 2. AUTOMATIC OTA UPDATE CHECK
# =====================================================================
GITHUB_USER = "your_actual_github_username"
GITHUB_REPO = "your_repo_name"
OTA = Senko(user=GITHUB_USER, repo=GITHUB_REPO, files=["main.py"])

try:
    if OTA.update():
        motor_stop()
        machine.reset()
except:
    pass

motor_stop()

# =====================================================================
# 3. TIME & SOLAR TRACKING LOGIC
# =====================================================================
# Your custom tracking window boundaries
HARD_LIMIT_WEST = 15.2
HARD_LIMIT_EAST = -24.2
TOTAL_TRAVEL_ARC = HARD_LIMIT_WEST - HARD_LIMIT_EAST # 39.4 degrees total

# Define tracking hours (e.g., 8:00 AM to 6:00 PM = 10 hour tracking day)
START_HOUR = 8
END_HOUR = 18
TOTAL_TRACKING_SECONDS = (END_HOUR - START_HOUR) * 3600

def sync_time():
    """Syncs internal clock with internet time"""
    try:
        ntptime.settime()
        print("⏰ Time synced successfully with NTP server.")
    except:
        print("⚠️ Time sync failed. Retrying next cycle.")

def get_target_angle(current_hour, current_minute, current_second):
    """Calculates exactly where the panel should be based on the time of day"""
    if current_hour < START_HOUR:
        return HARD_LIMIT_EAST # Morning: Face East waiting for sun
    if current_hour >= END_HOUR:
        return HARD_LIMIT_WEST # Evening: Stay West
        
    # Calculate how many seconds we are into the tracking day
    seconds_since_start = ((current_hour - START_HOUR) * 3600) + (current_minute * 60) + current_second
    
    # Progress percentage through the day (0.0 to 1.0)
    progress = seconds_since_start / TOTAL_TRACKING_SECONDS
    
    # Linear interpolation across your 39.4 degree movement arc
    target_angle = HARD_LIMIT_EAST + (progress * TOTAL_TRAVEL_ARC)
    return target_angle

# =====================================================================
# 4. MAIN OPERATIONAL LOOP
# =====================================================================
def main():
    sync_time()
    last_sync = time.time()
    
    # Simulated tracking baseline (starts at East limit)
    current_estimated_angle = HARD_LIMIT_EAST 

    while True:
        # 1. Active Hardware Safety Shield
        if EAST_ENDSTOP.value() == 1 or WEST_ENDSTOP.value() == 1:
            motor_stop()
            time.sleep(1)
            continue

        # 2. Sync time once an hour
        if time.time() - last_sync > 3600:
            sync_time()
            last_sync = time.time()

        # 3. Get current local time (GMT offset adjusted if necessary)
        local_time = time.localtime()
        hour = local_time[3]
        minute = local_time[4]
        second = local_time[5]

        # 4. Calculate where the panel *should* be right now
        target_angle = get_target_angle(hour, minute, second)

        # 5. Drive motor to match the sun
        # If the panel is behind the sun, move West
        if target_angle > current_estimated_angle + 0.5:
            move_west()
            time.sleep(0.5) # Run motor in small safe bursts
            motor_stop()
            current_estimated_angle += 0.5 
            
        # If it's night/resetting time, move back East
        elif target_angle < current_estimated_angle - 0.5:
            move_east()
            time.sleep(0.5)
            motor_stop()
            current_estimated_angle -= 0.5
        else:
            # On target. Hold position.
            motor_stop()
            
        time.sleep(10) # Evaluate position every 10 seconds

if __name__ == "__main__":
    main()




import time
import machine
from senko import Senko

# --- OTA Configuration ---
GITHUB_USER = "jimmyjam358"
GITHUB_REPO = "your_solar_tracker_repo"

# Senko watches only main.py here to protect your working boot.py
OTA = Senko(
    user=GITHUB_USER,
    repo=GITHUB_REPO,
    files=["main.py"]
)

def run_test_logic():
    """
    Your current temporary test bench logic.
    """
    print("The bench is alive")
    # You can toggle a pin here or leave it as a heartbeat log

def main():
    print("Checking GitHub for code updates...")
    
    try:
        if OTA.update():
            print("📣 New update found and applied! Rebooting...")
            machine.reset()
        else:
            print("✅ Code is up to date.")
    except Exception as e:
        print(f"⚠️ OTA Check failed: {e}. Running current local script.")

    # Main Test Bench Loop
    while True:
        run_test_logic()
        
        # Check GitHub for changes every 60 seconds while we test
        time.sleep(60)

if __name__ == "__main__":
    main()


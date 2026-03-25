import psutil
import os
import subprocess
import re

def get_power_plan():
    try:
        result = subprocess.run(["powercfg", "/getactivescheme"], capture_output=True, text=True, timeout=5)
        match = re.search(r'\((.+?)\)', result.stdout)
        if match: return match.group(1).strip()
    except: pass
    return "Unknown"

cpu = psutil.cpu_percent(interval=1)
ram = psutil.virtual_memory().percent
power = get_power_plan()

print(f"CPU:{cpu}")
print(f"RAM:{ram}")
print(f"PowerPlan:{power}")

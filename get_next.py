import json
import os
import subprocess
from datetime import datetime, timedelta

import jdatetime

base_directory = "gregorian"
jalali_base_directory = "jalali"

# Find the latest date directory
year_directories = sorted(
    [
        d for d in os.listdir(os.path.join(base_directory))
        if os.path.isdir(os.path.join(base_directory, d)) and d.isdigit()
    ],
    reverse=True,
)
year_dir = year_directories[0]
month_directories = sorted(
    [
        d for d in os.listdir(os.path.join(base_directory, year_dir))
        if os.path.isdir(os.path.join(base_directory, year_dir, d)) and d.isdigit()
    ],
    reverse=True,
)
month_dir = month_directories[0]
latest_files = sorted(
    [
        f for f in os.listdir(os.path.join(base_directory, year_dir, month_dir))
        if os.path.isfile(os.path.join(base_directory, year_dir, month_dir, f)) and f.isdigit()
    ],
    reverse=True,
)
latest_file = latest_files[0]

# Define full path of latest file and the date
full_path = os.path.join(base_directory, year_dir, month_dir, latest_file)
latest_date_str = f"{year_dir}/{month_dir}/{latest_file}"
latest_date = datetime.strptime(latest_date_str, '%Y/%m/%d')

# Find the next date
next_date = latest_date + timedelta(days=1)
next_date_str = next_date.strftime('%Y/%m/%d')

# Run the bonbast command and save the JSON to the next date file
bonbast_process = subprocess.run(
    ["bonbast", "history", "--date", next_date_str, "--json"],
    capture_output=True,
    text=True,
)
try:
    json_output = json.loads(bonbast_process.stdout.strip())
except:
    json_output = None
    pass

if bonbast_process.returncode == 0 and json_output:
    # JSON is valid and not empty, save it to the file

    # -- Gregorian output
    # Create the next date directory
    next_directory = os.path.join(base_directory, next_date.strftime('%Y'), next_date.strftime('%m'))
    os.makedirs(next_directory, exist_ok=True)
    file_path = os.path.join(next_directory, next_date.strftime('%d'))
    with open(file_path, "w") as json_file:
        json_file.write(json.dumps(json_output, indent=2, ensure_ascii=False))

    # -- Jalali output
    # Convert to jalali and create directory
    jalali_date = jdatetime.date.fromgregorian(date=next_date)
    next_jalali_directory = os.path.join(jalali_base_directory, jalali_date.strftime('%Y'), jalali_date.strftime('%m'))
    os.makedirs(next_jalali_directory, exist_ok=True)
    jalali_file_path = os.path.join(next_jalali_directory, jalali_date.strftime('%d'))
    with open(jalali_file_path, "w") as json_file:
        json_file.write(json.dumps(json_output, indent=2, ensure_ascii=False))

    print(f"JSON output saved to {file_path} and {jalali_file_path}.")
else:
    # JSON is empty or not valid, do nothing
    print("JSON output is empty or not valid.")

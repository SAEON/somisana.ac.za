import os
import requests
from datetime import datetime, timedelta

# Define constants
BASE_URL = "https://somisana.ocean.gov.za/sa-west/v1.0/forecasts"
LOCAL_DIR = "/home/nc.memela/Projects/somisana-current_running_file/public"
LOG_FILE = os.path.join(LOCAL_DIR, "download_log.txt")

GIF_FILES = ["croco_avg_temp_100m.gif", "croco_avg_temp_surf.gif", "croco_avg_temp_bot.gif"]

def get_today_date_path():
    """Return today's date path in the required format YYYYMM/YYYYMMDD."""
    today = datetime.utcnow()
    return f"{today.strftime('%Y%m')}/{today.strftime('%Y%m%d')}_00"

def get_latest_available_url():
    """Check for the latest available data, going back if today's is missing."""
    today = datetime.utcnow()
    
    for days_back in range(7):  # Look back up to a week
        date_path = (today - timedelta(days=days_back)).strftime('%Y%m/%Y%m%d_00')
        url = f"{BASE_URL}/{date_path}/MERCATOR-GFS"
        if check_url_exists(url):
            return url
    return None

def check_url_exists(url):
    """Check if the URL is reachable (test with HEAD request)."""
    try:
        response = requests.head(url, timeout=10)
        return response.status_code == 200
    except requests.RequestException:
        return False

def download_gif(url, filename):
    """Download the GIF from the given URL and save it locally."""
    gif_url = f"{url}/{filename}"
    local_path = os.path.join(LOCAL_DIR, filename)
    
    try:
        response = requests.get(gif_url, timeout=15)
        if response.status_code == 200:
            with open(local_path, 'wb') as f:
                f.write(response.content)
            return True
        else:
            return False
    except requests.RequestException:
        return False

def log_download_attempt(success, date):
    """Log the attempt in a text file."""
    with open(LOG_FILE, "a") as log:
        status = "Success" if success else "Failure"
        log.write(f"{date}: {status}\n")

def main():
    """Main function to check and download the latest GIFs."""
    os.makedirs(LOCAL_DIR, exist_ok=True)
    
    latest_url = get_latest_available_url()
    if not latest_url:
        print("No recent valid forecast found. Keeping existing files.")
        log_download_attempt(False, datetime.utcnow().strftime('%Y-%m-%d'))
        return

    success = False
    for gif in GIF_FILES:
        if download_gif(latest_url, gif):
            success = True

    log_download_attempt(success, datetime.utcnow().strftime('%Y-%m-%d'))

if __name__ == "__main__":
    main()


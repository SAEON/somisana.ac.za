import os
import requests
import socket
from datetime import datetime, timedelta

# Detect environment based on hostname
hostname = socket.gethostname()

if "ocimsvaps.ocean.gov.za" in hostname:  # Actual server hostname
    BASE_DIR = "/home/nkululeko/somisana.ac.za/public"
elif "COMP000000183" in hostname: #server hostname
    BASE_DIR = "/home/nc.memela/Projects/somisana.ac.za/public"

# Define constants
BASE_URLS = {
    "sa-west": "https://somisana.ocean.gov.za/sa-west/v1.0/forecasts",
    "sa-southeast": "https://somisana.ocean.gov.za/sa-southeast/v1.0/forecasts"
}

LOCAL_DIRS = {
    "sa-west": os.path.join(BASE_DIR, "sa-west/latest_forecasts"),
    "sa-southeast": os.path.join(BASE_DIR, "sa-southeast/latest_forecasts")
}

MODELS = ["HYCOM-GFS", "MERCATOR-GFS","HYCOM-SAWS", "MERCATOR-SAWS"]
GIF_FILES = ["croco_avg_temp_100m.gif", "croco_avg_temp_surf.gif", "croco_avg_temp_bot.gif"]
LOG_FILE = os.path.join(BASE_DIR, "download_log.txt")

def get_date_path(days_back=0):
    """Return the date path in the required format YYYYMM/YYYYMMDD."""
    date = datetime.utcnow() - timedelta(days=days_back)
    return f"{date.strftime('%Y%m')}/{date.strftime('%Y%m%d')}_00"

def check_url_exists(url):
    """Check if the URL is reachable (test with HEAD request)."""
    try:
        response = requests.head(url, timeout=10)
        return response.status_code == 200
    except requests.RequestException:
        return False

def get_latest_available_url(base_url):
    """Find the latest available forecast data URL by checking past days."""
    for days_back in range(7):  # Look back up to a week
        date_path = get_date_path(days_back)
        for model in MODELS:
            url = f"{base_url}/{date_path}/{model}"
            if check_url_exists(url):
                return url, date_path
    return None, None

def download_gif(url, filename, local_path):
    """Download the GIF from the given URL and save it locally."""
    gif_url = f"{url}/{filename}"
    try:
        response = requests.get(gif_url, timeout=15)
        if response.status_code == 200:
            with open(local_path, 'wb') as f:
                f.write(response.content)
            return True
    except requests.RequestException:
        pass
    return False

def log_download_attempt(region, model, success, date):
    """Log the attempt in a text file."""
    with open(LOG_FILE, "a") as log:
        status = "Success" if success else "Failure"
        log.write(f"{date} - {region}/{model}: {status}\n")

def main():
    """Main function to download the latest GIFs from both regions."""
    for region, base_url in BASE_URLS.items():
        for model in MODELS:
            latest_url, date_path = get_latest_available_url(base_url)
            if not latest_url:
                print(f"No recent valid forecast found for {region}/{model}. Skipping.")
                log_download_attempt(region, model, False, datetime.utcnow().strftime('%Y-%m-%d'))
                continue

            save_dir = os.path.join(LOCAL_DIRS[region], model)
            os.makedirs(save_dir, exist_ok=True)  # Ensure the directory exists

            success = False
            for gif in GIF_FILES:
                local_path = os.path.join(save_dir, gif)
                if download_gif(latest_url, gif, local_path):
                    success = True

            log_download_attempt(region, model, success, datetime.utcnow().strftime('%Y-%m-%d'))

if __name__ == "__main__":
    main()

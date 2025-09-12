#!/usr/bin/env python3
import os
import socket
from datetime import datetime, timedelta

import requests

# ---------------- CONFIG ----------------
LOOKBACK_DAYS = 7  # how many days back to search
TIMEOUT = 20       # seconds for HTTP requests
DEBUG = os.getenv("DL_DEBUG", "0") == "1"

# Regions and base URLs on your file server
BASE_URLS = {
    "sa-west": "https://somisana.ocean.gov.za/sa-west/v1.0/forecasts",
    "sa-southeast": "https://somisana.ocean.gov.za/sa-southeast/v1.0/forecasts",
}

# Models and filenames to download
MODELS = ["HYCOM-GFS", "MERCATOR-GFS", "HYCOM-SAWS", "MERCATOR-SAWS"]
GIF_FILES = [
    "croco_avg_temp_100m.mp4",
    "croco_avg_temp_surf.mp4",
    "croco_avg_temp_bot.mp4",
    "croco_avg_temp_anom_100m.mp4",
    "croco_avg_temp_anom_surf.mp4",
    "croco_avg_temp_anom_bot.mp4",

]

# ---------------- PATHS -----------------
hostname = socket.gethostname().lower()
if "ocimsvaps" in hostname:
    BASE_DIR = "/home/nkululeko/somisana.ac.za/public"
elif "comp000000183" in hostname:
    BASE_DIR = "/home/nc.memela/Projects/somisana.ac.za/public"
else:
    BASE_DIR = os.getcwd()  # fallback

LOCAL_DIRS = {
    "sa-west": os.path.join(BASE_DIR, "sa-west/latest_forecasts"),
    "sa-southeast": os.path.join(BASE_DIR, "sa-southeast/latest_forecasts"),
}
LOG_FILE = os.path.join(BASE_DIR, "download_log.txt")


# --------------- UTILS ------------------
def log(msg: str):
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{ts}] {msg}")

def dprint(msg: str):
    if DEBUG:
        log(f"DEBUG: {msg}")

def get_date_path(days_back=0):
    """Return 'YYYYMMDD_00' (no YYYYMM directory)."""
    date = datetime.utcnow() - timedelta(days=days_back)
    return f"{date.strftime('%Y%m%d')}_00"


def check_file_exists(url: str, timeout=TIMEOUT) -> bool:
    """
    Use GET with a Range header so we don't download the whole file.
    Many servers mishandle HEAD; accept 200 or 206 (Partial Content).
    """
    try:
        headers = {"Range": "bytes=0-0"}
        r = requests.get(
            url, headers=headers, timeout=timeout, allow_redirects=True, stream=True
        )
        dprint(f"check_file_exists: {url} -> {r.status_code}")
        return r.status_code in (200, 206)
    except requests.RequestException as e:
        dprint(f"check_file_exists ERROR: {url} -> {e}")
        return False

def get_latest_available_url(base_url: str, model: str):
    """
    Find the latest directory URL that actually contains any of the GIF_FILES
    for the specified model. Returns (dir_url, date_path) or (None, None).
    """
    for days_back in range(LOOKBACK_DAYS):
        date_path = get_date_path(days_back)
        # Test existence by checking one of the files under that path
        for fname in GIF_FILES:
            test_url = f"{base_url}/{date_path}/{model}/{fname}"
            dprint(f"Probing: {test_url}")
            if check_file_exists(test_url):
                # Return the directory URL so we can fetch all files from it
                dir_url = f"{base_url}/{date_path}/{model}"
                return dir_url, date_path
    return None, None

def download_file(url: str, local_path: str) -> bool:
    """
    Download a file via GET. Returns True on success.
    """
    try:
        r = requests.get(url, timeout=TIMEOUT, allow_redirects=True)
        if r.status_code == 200 and r.content:
            with open(local_path, "wb") as f:
                f.write(r.content)
            return True
        else:
            dprint(f"download_file WARN: {url} -> {r.status_code}")
            return False
    except requests.RequestException as e:
        dprint(f"download_file ERROR: {url} -> {e}")
        return False

def log_download_attempt(region: str, model: str, success: bool, date_str: str):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    status = "Success" if success else "Failure"
    with open(LOG_FILE, "a") as logf:
        logf.write(f"{date_str} - {region}/{model}: {status}\n")


# --------------- MAIN -------------------
def main():
    today = datetime.utcnow().strftime("%Y-%m-%d")
    for region, base_url in BASE_URLS.items():
        for model in MODELS:
            dir_url, date_path = get_latest_available_url(base_url, model)
            if not dir_url:
                log(f"No recent valid forecast found for {region}/{model}. Skipping.")
                log_download_attempt(region, model, False, today)
                continue

            save_dir = os.path.join(LOCAL_DIRS[region], model)
            os.makedirs(save_dir, exist_ok=True)

            success_any = False
            for fname in GIF_FILES:
                src = f"{dir_url}/{fname}"
                dst = os.path.join(save_dir, fname)
                if download_file(src, dst):
                    log(f"Downloaded {region}/{model}/{fname} from {date_path} -> {dst}")
                    success_any = True
                else:
                    log(f"Missing/failed: {region}/{model}/{fname} ({src})")

            log_download_attempt(region, model, success_any, today)


if __name__ == "__main__":
    main()


import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import plotly.express as px
import plotly.io as pio
import glob
import os
import pandas as pd

# Detect environment based on hostname
HOSTNAME = os.uname().nodename

if HOSTNAME == "COMP000000183":
    print("Running on Local Machine:", HOSTNAME)
    DATA_DIR = "/home/nc.memela/Projects/tmp/sat-sst"
elif HOSTNAME == "ocimsvaps.ocean.gov.za":
    print("Running on Server:", HOSTNAME)
    DATA_DIR = "/home/nkululeko/tmp/sat-sst"
else:
    print("this is nonsense, what HOST is this?")

# Find NetCDF files using glob
original_files = glob.glob(f"{DATA_DIR}/*.nc")  # Daily SST
monthly_files = glob.glob(f"{DATA_DIR}/long-record/METOFFICE-GLO-SST-L4-NRT-OBS-SST-V2_monthly_*.nc")  # Monthly mean SST

# Ensure at least one file is found
if not original_files:
    raise FileNotFoundError(f"❌ No daily SST NetCDF files found in {DATA_DIR}")

if not monthly_files:
    raise FileNotFoundError(f"❌ No monthly SST NetCDF files found in {DATA_DIR}/long-record/")

# Select the first file in each case
original_file = original_files[0]  # Daily SST
monthly_file = monthly_files[0]    # Monthly mean SST

print(f"📂 Using daily SST file: {original_file}")
print(f"📂 Using monthly mean SST file: {monthly_file}")

# Open datasets
ds_original = xr.open_dataset(original_file)
ds_monthly = xr.open_dataset(monthly_file)

# Ensure 'analysed_sst' exists in both datasets
if 'analysed_sst' not in ds_original or 'analysed_sst' not in ds_monthly:
    raise KeyError("❌ Variable 'analysed_sst' not found in one of the datasets.")

# Convert SST to Celsius using scale factor & offset
scale_factor = ds_original['analysed_sst'].attrs.get('scale_factor', 1)
offset = ds_original['analysed_sst'].attrs.get('add_offset', 0)

analysed_sst_original = (ds_original['analysed_sst'].isel(time=0) * scale_factor) + offset - 273.15
analysed_sst_monthly = (ds_monthly['analysed_sst'] * scale_factor) + offset - 273.15

# Extract coordinates
lon = ds_original['longitude']
lat = ds_original['latitude']

# Handle fill values
fill_value = ds_original['analysed_sst'].attrs.get('_FillValue', -32768)
analysed_sst_original = analysed_sst_original.where(analysed_sst_original != fill_value)
analysed_sst_monthly = analysed_sst_monthly.where(analysed_sst_monthly != fill_value)

# --- Fully Dynamic Weighted Monthly Mean Transition ---
def weighted_monthly_mean(time_array, monthly_data):
    """
    Computes a dynamically weighted SST mean based on proximity to mid-month.
    Handles all month lengths, leap years, and missing months correctly.
    """
    time_index = pd.to_datetime(time_array.values)

    # Print debug info
    print("\n🕒 Daily SST Time Values:\n", time_index)
    print("📅 Monthly SST Time Values:\n", monthly_data['time'].values[:5])  # Print first 5 timestamps

    month_days = time_index.days_in_month
    day_of_month = time_index.day

    # Compute weights
    W_prev = np.zeros_like(day_of_month, dtype=float)
    W_current = np.zeros_like(day_of_month, dtype=float)
    W_next = np.zeros_like(day_of_month, dtype=float)

    mask_before_mid = day_of_month < 15
    W_prev[mask_before_mid] = 1 - (day_of_month[mask_before_mid] / 15)
    W_current[mask_before_mid] = day_of_month[mask_before_mid] / 15

    mask_mid = day_of_month == 15
    W_current[mask_mid] = 1

    mask_after_mid = day_of_month > 15
    W_current[mask_after_mid] = 1 - ((day_of_month[mask_after_mid] - 15) / (month_days[mask_after_mid] - 15))
    W_next[mask_after_mid] = (day_of_month[mask_after_mid] - 15) / (month_days[mask_after_mid] - 15)

    # Clip weights
    W_prev = np.clip(W_prev, 0, 1)
    W_current = np.clip(W_current, 0, 1)
    W_next = np.clip(W_next, 0, 1)

    # Convert to scalar integers
    current_month = int(time_index.month[0])  # Extract single value
    prev_month = int((time_index - pd.DateOffset(months=1)).month[0])
    next_month = int((time_index + pd.DateOffset(months=1)).month[0])

    # Debugging prints
    print("\n📅 Current Month:", current_month)
    print("📅 Previous Month:", prev_month)
    print("📅 Next Month:", next_month)
    # print("🔎 Monthly Data Unique Months:", np.unique(monthly_data['time'].dt.month))

    # Ensure selection works properly by using `.where()` instead of `.sel()`
    historical_current = monthly_data.where(monthly_data['time'].dt.month == current_month, drop=True).mean(dim="time", skipna=True)
    historical_prev = monthly_data.where(monthly_data['time'].dt.month == prev_month, drop=True).mean(dim="time", skipna=True)
    historical_next = monthly_data.where(monthly_data['time'].dt.month == next_month, drop=True).mean(dim="time", skipna=True)

    # Debugging prints for dataset filtering
    #print("\n🔍 Filtered Historical Current SST:\n", historical_current)
    #print("🔍 Filtered Historical Previous SST:\n", historical_prev)
    #print("🔍 Filtered Historical Next SST:\n", historical_next)

    # Compute weighted SST
    smoothed_sst = (historical_prev * W_prev) + (historical_current * W_current) + (historical_next * W_next)

    return smoothed_sst



# -------------------- MAIN PROCESSING --------------------

# Apply the weighted transition for smoother anomalies
print("🔍 Applying weighted monthly mean transition...")
analysed_sst_smooth = weighted_monthly_mean(ds_original['time'], ds_monthly['analysed_sst'])

# Compute the SST anomaly
analysed_sst_anomaly = analysed_sst_original - analysed_sst_smooth

# Extract date strings
original_date_str = str(ds_original['time'].values[0])[:10]
anomaly_date_str = str(ds_monthly['time'].values[-1])[:10]

# -------------------- PLOTTING --------------------

# --- Static SST Plot ---
plt.figure(figsize=(8, 6))
ax = plt.axes(projection=ccrs.PlateCarree())

p1 = ax.pcolormesh(lon, lat, analysed_sst_original, cmap='jet', transform=ccrs.PlateCarree(), zorder=1)
ax.set_title(f'Sea Surface Temperature ({original_date_str})')

cbar = plt.colorbar(p1, orientation='vertical', shrink=0.8, pad=0.05)
cbar.set_label('SST (°C)')

ax.coastlines(resolution='50m', color='black', linewidth=1, zorder=2)
ax.add_feature(cfeature.BORDERS, linestyle=':', edgecolor='black', zorder=2)
ax.add_feature(cfeature.LAND, color='saddlebrown', zorder=0)

plt.savefig('analysed_sst_static.png', dpi=300, bbox_inches='tight')
plt.close()

# --- Static SST Anomaly Plot ---
plt.figure(figsize=(8, 6))
ax = plt.axes(projection=ccrs.PlateCarree())

vmax = np.nanmax(np.abs(analysed_sst_anomaly))
p2 = ax.pcolormesh(lon, lat, analysed_sst_anomaly, cmap='RdBu_r', vmin=-vmax, vmax=vmax, transform=ccrs.PlateCarree(), zorder=1)
ax.set_title(f'SST Anomaly ({original_date_str} vs Weighted Monthly Mean)')

cbar = plt.colorbar(p2, orientation='vertical', shrink=0.8, pad=0.05)
cbar.set_label('SST Anomaly (°C)')

ax.coastlines(resolution='50m', color='black', linewidth=1, zorder=2)
ax.add_feature(cfeature.BORDERS, linestyle=':', edgecolor='black', zorder=2)
ax.add_feature(cfeature.LAND, color='saddlebrown', zorder=0)

plt.savefig('analysed_sst_anomaly_static.png', dpi=300, bbox_inches='tight')
plt.close()

# --- Interactive SST Plot ---
fig1 = px.imshow(
    analysed_sst_original.values,
    labels={'color': 'SST (°C)'},
    x=lon.values,
    y=lat.values,
    color_continuous_scale='Jet',
    aspect='auto',
    origin='lower'
)

# --- Interactive SST Anomaly Plot ---
fig2 = px.imshow(
    analysed_sst_anomaly.values,
    labels={'color': 'SST Anomaly (°C)'},
    x=lon.values,
    y=lat.values,
    color_continuous_scale='RdBu_r',
    aspect='auto',
    origin='lower'
)
pio.write_html(fig1, file='analysed_sst_map_interactive.html', auto_open=False)
pio.write_html(fig2, file='analysed_sst_anomaly_map_interactive.html', auto_open=False)

print("✅ Process complete! SST anomaly has been computed and plotted.")


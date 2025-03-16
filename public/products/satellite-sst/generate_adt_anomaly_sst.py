import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import plotly.express as px
import plotly.io as pio
import glob
import os

# Detect environment based on hostname
HOSTNAME = os.uname().nodename

if HOSTNAME == "COMP000000183":
    print("Running on Local Machine:", HOSTNAME)
    DATA_DIR = "/home/nc.memela/Projects/tmp/sat-sst"
elif HOSTNAME == "ocimsvaps.ocean.gov.za":
    print("Running on Server:", HOSTNAME)
    DATA_DIR = "/home/nkululeko/tmp/sat-sst"
else:
    print("this is nonsense, what HOST it this?")

# Find NetCDF files using glob
original_files = glob.glob(f"{DATA_DIR}/*.nc")
anomaly_files = glob.glob(f"{DATA_DIR}/long-record/*.nc")

# Ensure at least one file is found
if not original_files:
    raise FileNotFoundError(f"❌ No SST NetCDF files found in {DATA_DIR}")

if not anomaly_files:
    raise FileNotFoundError(f"❌ No anomaly NetCDF files found in {DATA_DIR}/long-record/")

# Select the first file in each case
original_file = original_files[0]  # Picks the first file
anomaly_file = anomaly_files[0]    # Picks the first anomaly file

print(f"📂 Using original SST file: {original_file}")
print(f"📂 Using anomaly SST file: {anomaly_file}")

# Open datasets
ds_original = xr.open_dataset(original_file)
ds_anomaly = xr.open_dataset(anomaly_file)

# Ensure 'analysed_sst' exists in both datasets
if 'analysed_sst' not in ds_original or 'analysed_sst' not in ds_anomaly:
    raise KeyError("❌ Variable 'analysed_sst' not found in one of the datasets.")

# Apply scale factor and convert from Kelvin to Celsius
scale_factor = ds_original['analysed_sst'].attrs.get('scale_factor', 1)
analysed_sst_original = (ds_original['analysed_sst'].isel(time=0) * scale_factor) - 273.15
analysed_sst_long_term = (ds_anomaly['analysed_sst'] * scale_factor) - 273.15

# Extract coordinates
lon = ds_original['longitude']
lat = ds_original['latitude']

# Handle fill values
analysed_sst_original = analysed_sst_original.where(analysed_sst_original != -2147483647)
analysed_sst_long_term = analysed_sst_long_term.where(analysed_sst_long_term != -2147483647)

# Compute mean and anomaly
analysed_sst_mean = analysed_sst_long_term.mean(dim='time')
analysed_sst_anomaly = analysed_sst_original - analysed_sst_mean

# Extract date strings
original_date_str = str(ds_original['time'].values[0])[:10]
anomaly_date_str = str(ds_anomaly['time'].values[-1])[:10]

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
ax.set_title(f'SST Anomaly ({original_date_str} vs Long-term Mean)')

cbar = plt.colorbar(p2, orientation='vertical', shrink=0.8, pad=0.05)
cbar.set_label('SST Anomaly (°C)')

ax.coastlines(resolution='50m', color='black', linewidth=1, zorder=2)
ax.add_feature(cfeature.BORDERS, linestyle=':', edgecolor='black', zorder=2)
ax.add_feature(cfeature.LAND, color='saddlebrown', zorder=0)

plt.savefig('analysed_sst_anomaly_static.png', dpi=300, bbox_inches='tight')
plt.close()

# --- Interactive Plotly SST Map ---
analysed_sst_original_data = analysed_sst_original.values
analysed_sst_anomaly_data = analysed_sst_anomaly.values
lon_values, lat_values = np.meshgrid(lon, lat)

# Ensure correct orientation
if lat_values[0, 0] > lat_values[-1, 0]:
    analysed_sst_original_data = np.flipud(analysed_sst_original_data)
    analysed_sst_anomaly_data = np.flipud(analysed_sst_anomaly_data)
    lat_values = np.flipud(lat_values)

# Interactive SST Plot
fig1 = px.imshow(
    analysed_sst_original_data,
    labels={'color': 'SST (°C)'},
    x=lon_values[0],
    y=lat_values[:, 0],
    color_continuous_scale='Jet',
    aspect='auto',
    origin='lower'
)

fig1.update_layout(
    title={'text': f'SST ({original_date_str})', 'y': 0.95, 'x': 0.5, 'xanchor': 'center', 'yanchor': 'top'},
    xaxis_title='Longitude',
    yaxis_title='Latitude',
    coloraxis_colorbar=dict(title='SST (°C)', title_side='right')
)

# Interactive SST Anomaly Plot
fig2 = px.imshow(
    analysed_sst_anomaly_data,
    labels={'color': 'SST Anomaly (°C)'},
    x=lon_values[0],
    y=lat_values[:, 0],
    color_continuous_scale='RdBu_r',
    aspect='auto',
    origin='lower',
    zmin=-vmax,
    zmax=vmax
)

fig2.update_layout(
    title={'text': f'SST Anomaly ({anomaly_date_str} vs Long-term Mean)', 'y': 0.95, 'x': 0.5, 'xanchor': 'center', 'yanchor': 'top'},
    xaxis_title='Longitude',
    yaxis_title='Latitude',
    coloraxis_colorbar=dict(title='SST Anomaly (°C)', title_side='right')
)

# Save interactive plots
pio.write_html(fig1, file='analysed_sst_map_interactive_sst.html', auto_open=False)
pio.write_html(fig2, file='analysed_sst_anomaly_map_interactive_sst.html', auto_open=False)

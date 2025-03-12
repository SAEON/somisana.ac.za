import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import plotly.express as px
import plotly.io as pio
import os

import socket

# Detect the environment based on hostname
HOSTNAME = socket.gethostname()

if HOSTNAME == "COMP000000183":
    print("📌 Running on Local Machine")
    BASE_DIR = "/home/nc.memela/Projects/tmp/sat-sst"
elif "ocean-access" in HOSTNAME:  # Adjust this for your server naming convention
    print("📌 Running on Server")
    BASE_DIR = "/home/ocean-access/tmp/sat-sst"
else:
    raise EnvironmentError("🚨 Unknown environment. Please configure the correct BASE_DIR.")

# Define input directories
input_directory = os.path.join(BASE_DIR, "long-record")

# Automatically find the most recent files in the directory
sst_files = [f for f in os.listdir(input_directory) if f.endswith('.nc')]
sst_files.sort()

# Assuming the last file is the most recent for the single day and the first is the long-term data
original_file = os.path.join(input_directory, sst_files[-1])
anomaly_file = os.path.join(input_directory, sst_files[0])

# Load the additional long-term record file for 90th percentile
MHW_long_record_file = "METOFFICE-GLO-SST-L4-NRT-OBS-SST-V2_multi-vars_10.02E-39.97E_39.97S-20.02S_2024-01-01-2025-03-10.nc"
long_record_file = os.path.join(input_directory, MHW_long_record_file)

# Load datasets
ds_original = xr.open_dataset(original_file)
ds_anomaly = xr.open_dataset(anomaly_file)
ds_long_record = xr.open_dataset(long_record_file)

# Select the SST variable and convert to degrees Celsius
sst_original = ds_original['analysed_sst'].isel(time=0) - 273.15
sst_long_term = ds_anomaly['analysed_sst'] - 273.15
sst_long_record = ds_long_record['analysed_sst'] - 273.15

# Extract coordinates
lon = ds_original['longitude']
lat = ds_original['latitude']

# Handle fill values
sst_original = sst_original.where(sst_original != -2147483647)
sst_long_term = sst_long_term.where(sst_long_term != -2147483647)
sst_long_record = sst_long_record.where(sst_long_record != -2147483647)

# Compute the long-term 90th percentile threshold using the long record
sst_threshold = sst_long_record.quantile(0.9, dim='time')

# Compute marine heatwave as SST exceeding the 90th percentile
marine_heatwave = sst_original - sst_threshold
marine_heatwave = marine_heatwave.where(marine_heatwave > 0)

# Extract date strings
original_date_str = str(ds_original['time'].values[0])[:10]
anomaly_date_str = str(ds_anomaly['time'].values[-1])[:10]

# --- Separate Static Plots for SST and Marine Heatwave ---

# Plot 1: Sea Surface Temperature (SST)
plt.figure(figsize=(8, 6))
ax = plt.axes(projection=ccrs.PlateCarree())

p1 = ax.pcolormesh(lon, lat, sst_original, cmap='jet', transform=ccrs.PlateCarree(), zorder=1)

ax.coastlines(resolution='50m', color='black', linewidth=1, zorder=3)
ax.add_feature(cfeature.BORDERS, linestyle=':', edgecolor='black', zorder=3)
ax.add_feature(cfeature.LAND, color='saddlebrown', zorder=0)  # Brown land mask
ax.set_title(f'Sea Surface Temperature (°C) ({anomaly_date_str})', fontsize=14, pad=10)

gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5)
gl.top_labels = False
gl.right_labels = False
cbar = plt.colorbar(p1, orientation='vertical', shrink=0.8, pad=0.05)
cbar.set_label('SST (°C)')

plt.savefig('sst_static.png', dpi=300, bbox_inches='tight')
plt.close()

# Plot 2: Marine Heatwave
plt.figure(figsize=(8, 6))
ax = plt.axes(projection=ccrs.PlateCarree())

p2 = ax.pcolormesh(lon, lat, marine_heatwave, cmap='YlOrRd', transform=ccrs.PlateCarree(), zorder=1)

ax.coastlines(resolution='50m', color='black', linewidth=1, zorder=3)
ax.add_feature(cfeature.BORDERS, linestyle=':', edgecolor='black', zorder=3)
ax.add_feature(cfeature.LAND, color='saddlebrown', zorder=0)  # Brown land mask
ax.set_title(f'Marine Heatwave (SST > 90th Percentile)\n({original_date_str} vs Long-term Mean)', fontsize=14, pad=10)

gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5)
gl.top_labels = False
gl.right_labels = False
cbar = plt.colorbar(p2, orientation='vertical', shrink=0.8, pad=0.05)
cbar.set_label('Marine Heatwave (°C)')

plt.savefig('marine_heatwave_static.png', dpi=300, bbox_inches='tight')
plt.close()

# --- Interactive Side-by-Side Plot with Plotly ---

# Prepare data for interactive plots
sst_original_data = sst_original.values
marine_heatwave_data = marine_heatwave.values
lon_values, lat_values = np.meshgrid(lon, lat)

# Ensure correct orientation
if lat_values[0, 0] > lat_values[-1, 0]:
    sst_original_data = np.flipud(sst_original_data)
    marine_heatwave_data = np.flipud(marine_heatwave_data)
    lat_values = np.flipud(lat_values)

# Create side-by-side interactive plots
fig1 = px.imshow(
    sst_original_data,
    labels={'color': 'SST (°C)'},
    x=lon_values[0],
    y=lat_values[:, 0],
    color_continuous_scale='Jet',
    aspect='auto',
    origin='lower'
)
fig1.update_geos(
    showland=True,
    landcolor='saddlebrown',  # Brown land mask
    showcountries=True,
    showcoastlines=True,
    coastlinecolor='black'
)
fig1.update_layout(
    title={
        'text': f'Sea Surface Temperature (°C) ({original_date_str})',
        'y': 0.95,
        'x': 0.5,
        'xanchor': 'center',
        'yanchor': 'top'
    },
    xaxis_title='Longitude',
    yaxis_title='Latitude',
    coloraxis_colorbar=dict(title='SST (°C)', title_side='right'),
)

fig2 = px.imshow(
    marine_heatwave_data,
    labels={'color': 'Marine Heatwave (°C)'},
    x=lon_values[0],
    y=lat_values[:, 0],
    color_continuous_scale='YlOrRd',
    aspect='auto',
    origin='lower'
)
fig2.update_geos(
    showland=True,
    landcolor='saddlebrown',  # Brown land mask
    showcountries=True,
    showcoastlines=True,
    coastlinecolor='black'
)
fig2.update_layout(
    title={
        'text': f'Marine Heatwave (SST > 90th Percentile)\n({original_date_str} vs Long-term Mean)',
        'y': 0.95,
        'x': 0.5,
        'xanchor': 'center',
        'yanchor': 'top'
    },
    xaxis_title='Longitude',
    yaxis_title='Latitude',
    coloraxis_colorbar=dict(title='Marine Heatwave (°C)', title_side='right'),
)

# Save the interactive plots as HTML files
pio.write_html(fig1, file='sst_map_interactive_sst.html', auto_open=False)
pio.write_html(fig2, file='marine_heatwave_map_interactive_sst.html', auto_open=False)

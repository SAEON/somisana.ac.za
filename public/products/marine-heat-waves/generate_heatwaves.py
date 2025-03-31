import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import plotly.express as px
import plotly.io as pio
import os
import glob
import socket

# Detect the environment based on hostname
HOSTNAME = socket.gethostname()

if HOSTNAME == "COMP000000183":
    print("📌 Running on Local Machine")
    BASE_DIR = "/home/nc.memela/Projects/tmp/sat-sst"
elif HOSTNAME == "ocimsvaps.ocean.gov.za":
    print("📌 Running on Server")
    BASE_DIR = "/home/nkululeko/tmp/sat-sst"
else:
    raise EnvironmentError("🚨 Unknown environment. Please configure the correct BASE_DIR.")

# Define input directory
input_directory = os.path.join(BASE_DIR, "long-record")

# Find all .nc files in the long-record directory
sst_files = [f for f in os.listdir(input_directory) if f.endswith('.nc')]
sst_files.sort()

# Use the most recent file as today's file
todays_file = os.path.join(input_directory, sst_files[-1])

# Use the first file in the list as the long-term record file
long_record_file = os.path.join(input_directory, sst_files[0])

# Load datasets
ds_todays = xr.open_dataset(todays_file)
ds_long_record = xr.open_dataset(long_record_file)

# Select SST variable and convert to degrees Celsius
sst_original = ds_todays['analysed_sst'].isel(time=0) - 273.15
sst_long_record = ds_long_record['analysed_sst'] - 273.15

# Extract coordinates
lon = ds_todays['longitude']
lat = ds_todays['latitude']

# Handle fill values
sst_original = sst_original.where(sst_original != -2147483647)
sst_long_record = sst_long_record.where(sst_long_record != -2147483647)

# Compute the 90th percentile threshold using long-term record
sst_threshold = sst_long_record.quantile(0.9, dim='time')

# Compute marine heatwave as SST exceeding the 90th percentile
marine_heatwave = sst_original - sst_threshold
marine_heatwave = marine_heatwave.where(marine_heatwave > 0) - 273.15

# Extract date string
original_date_str = str(ds_todays['time'].values[0])[:10]
#anomaly_date_str = original_date_str  # Reusing the same date
long_record_date_str = str(ds_long_record['time'].values[-1])[:10]

print("original_date_str",original_date_str)
print("long_record_date_str",long_record_date_str)

# --- Static Plot: Sea Surface Temperature ---
plt.figure(figsize=(8, 6))
ax = plt.axes(projection=ccrs.PlateCarree())

p1 = ax.pcolormesh(lon, lat, sst_original, cmap='jet', transform=ccrs.PlateCarree(), zorder=1)

ax.coastlines(resolution='50m', color='black', linewidth=1, zorder=3)
ax.add_feature(cfeature.BORDERS, linestyle=':', edgecolor='black', zorder=3)
ax.add_feature(cfeature.LAND, color='saddlebrown', zorder=0)
ax.set_title(f'Sea Surface Temperature (°C) ({long_record_date_str})', fontsize=14, pad=10)

gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5)
gl.top_labels = False
gl.right_labels = False

cbar = plt.colorbar(p1, orientation='vertical', shrink=0.8, pad=0.05)
cbar.set_label('SST (°C)')

plt.savefig('sst_static.png', dpi=300, bbox_inches='tight')
plt.close()

# --- Static Plot: Marine Heatwave ---
plt.figure(figsize=(8, 6))
ax = plt.axes(projection=ccrs.PlateCarree())

p2 = ax.pcolormesh(lon, lat, marine_heatwave, cmap='YlOrRd', transform=ccrs.PlateCarree(), zorder=1)

ax.coastlines(resolution='50m', color='black', linewidth=1, zorder=3)
ax.add_feature(cfeature.BORDERS, linestyle=':', edgecolor='black', zorder=3)
ax.add_feature(cfeature.LAND, color='saddlebrown', zorder=0)
ax.set_title(f'Marine Heatwave (SST > 90th Percentile)\n({long_record_date_str} vs Long-term Mean)', fontsize=14, pad=10)

gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5)
gl.top_labels = False
gl.right_labels = False

cbar = plt.colorbar(p2, orientation='vertical', shrink=0.8, pad=0.05)
cbar.set_label('Marine Heatwave (°C)')

plt.savefig('marine_heatwave_static.png', dpi=300, bbox_inches='tight')
plt.close()

# --- Interactive Plotly Plots ---

# Prepare data
sst_original_data = sst_original.values
marine_heatwave_data = marine_heatwave.values
lon_values, lat_values = np.meshgrid(lon, lat)

# Flip latitude if needed
if lat_values[0, 0] > lat_values[-1, 0]:
    sst_original_data = np.flipud(sst_original_data)
    marine_heatwave_data = np.flipud(marine_heatwave_data)
    lat_values = np.flipud(lat_values)

# Interactive SST plot
fig1 = px.imshow(
    sst_original_data,
    labels={'color': 'SST (°C)'},
    x=lon_values[0],
    y=lat_values[:, 0],
    color_continuous_scale='Jet',
    aspect='auto',
    origin='lower'
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

# Interactive Marine Heatwave plot
fig2 = px.imshow(
    marine_heatwave_data,
    labels={'color': 'Marine Heatwave (°C)'},
    x=lon_values[0],
    y=lat_values[:, 0],
    color_continuous_scale='YlOrRd',
    aspect='auto',
    origin='lower'
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

# Save HTML versions
pio.write_html(fig1, file='sst_map_interactive_sst.html', auto_open=False)
pio.write_html(fig2, file='marine_heatwave_map_interactive_sst.html', auto_open=False)

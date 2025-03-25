import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import plotly.express as px
import plotly.io as pio
import glob
import socket

# Detect the environment based on hostname
HOSTNAME = socket.gethostname()

if HOSTNAME == "COMP000000183":
    print("📌 Running on Local Machine")
    BASE_DIR = "/home/nc.memela/Projects/tmp/sat-ssh"
elif HOSTNAME == "ocimsvaps.ocean.gov.za":  # Adjust this for your server naming convention
    print("📌 Running on Server")
    BASE_DIR = "/home/nkululeko/tmp/sat-ssh"
else:
    raise EnvironmentError("🚨 Unknown environment. Please configure the correct BASE_DIR.")

# Load both datasets (original single day and long-term data)
# Find NetCDF files
original_files = glob.glob(f"{BASE_DIR}/long-record/*.nc")
anomaly_files = glob.glob(f"{BASE_DIR}/*.nc")

# Ensure at least one file exists
if not original_files:
    raise FileNotFoundError("❌ No original NetCDF files found in /home/nc.memela/Projects/tmp/sat-ssh/long-record/")
if not anomaly_files:
    raise FileNotFoundError("❌ No anomaly NetCDF files found in /home/nc.memela/Projects/tmp/sat-ssh/")

# Select the first file
original_file = original_files[0]
anomaly_file = anomaly_files[0]

print(f"📂 Using original file: {original_file}")
print(f"📂 Using anomaly file: {anomaly_file}")

# Open datasets
ds_original = xr.open_dataset(original_file)
ds_anomaly = xr.open_dataset(anomaly_file)


# Access scale factor from attributes (default to 1 if not present)
scale_factor = ds_original['adt'].attrs.get('scale_factor', 1)

# Select the ADT (Absolute Dynamic Topography) variable and apply the scale factor
adt_original = ds_original['adt'].isel(time=0) * scale_factor
adt_long_term = ds_anomaly['adt'] * scale_factor

# Extract coordinates
lon = ds_original['longitude']
lat = ds_original['latitude']

# Handle fill values
adt_original = adt_original.where(adt_original != -2147483647)
adt_long_term = adt_long_term.where(adt_long_term != -2147483647)

# Compute the long-term mean and anomaly
adt_mean = adt_long_term.mean(dim='time')
adt_anomaly = adt_original - adt_mean

# Extract date strings
original_date_str = str(ds_original['time'].values[0])[:10]
anomaly_date_str = str(ds_anomaly['time'].values[-1])[:10]

# --- Separate Static Plots for SSH and SSH Anomaly ---

# Plot 1: Absolute Dynamic Topography (SSH)
plt.figure(figsize=(8, 6))
ax = plt.axes(projection=ccrs.PlateCarree())

p1 = ax.pcolormesh(lon, lat, adt_original, cmap='jet', transform=ccrs.PlateCarree(), zorder=1)
contour_levels = np.linspace(np.nanmin(adt_original), np.nanmax(adt_original), 10)  # Fewer contour levels
cs = ax.contour(lon, lat, adt_original, levels=contour_levels, colors='black', linewidths=0.8, transform=ccrs.PlateCarree(), zorder=2)

# Add contour labels every few contours
ax.clabel(cs, inline=True, fontsize=8, fmt='%1.1f', inline_spacing=5)

ax.coastlines(resolution='50m', color='black', linewidth=1, zorder=3)
ax.add_feature(cfeature.BORDERS, linestyle=':', edgecolor='black', zorder=3)
ax.add_feature(cfeature.LAND, color='saddlebrown', zorder=0)  # Brown land mask
ax.set_title(f'Absolute Dynamic Topography ({anomaly_date_str})')

gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5)
gl.top_labels = False
gl.right_labels = False
cbar = plt.colorbar(p1, orientation='vertical', shrink=0.8, pad=0.05)
cbar.set_label('SSH (m)')

plt.savefig('adt_static_ssh.png', dpi=300, bbox_inches='tight')
plt.close()

# Plot 2: SSH Anomaly with RdBu Colormap Centered at Zero
plt.figure(figsize=(8, 6))
ax = plt.axes(projection=ccrs.PlateCarree())

vmax = np.nanmax(np.abs(adt_anomaly))
p2 = ax.pcolormesh(lon, lat, adt_anomaly, cmap='RdBu', vmin=-vmax, vmax=vmax, transform=ccrs.PlateCarree(), zorder=1)

ax.coastlines(resolution='50m', color='black', linewidth=1, zorder=3)
ax.add_feature(cfeature.BORDERS, linestyle=':', edgecolor='black', zorder=3)
ax.add_feature(cfeature.LAND, color='saddlebrown', zorder=0)  # Brown land mask
ax.set_title(f'SSH Anomaly ({anomaly_date_str} vs Long-term Mean)')

gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5)
gl.top_labels = False
gl.right_labels = False
cbar = plt.colorbar(p2, orientation='vertical', shrink=0.8, pad=0.05)
cbar.set_label('SSH Anomaly (m)')

plt.savefig('adt_anomaly_static_ssh.png', dpi=300, bbox_inches='tight')
plt.close()

# --- Interactive Side-by-Side Plot with Plotly ---

# Prepare data for interactive plots
adt_original_data = adt_original.values
adt_anomaly_data = adt_anomaly.values
lon_values, lat_values = np.meshgrid(lon, lat)

# Ensure correct orientation
if lat_values[0, 0] > lat_values[-1, 0]:
    adt_original_data = np.flipud(adt_original_data)
    adt_anomaly_data = np.flipud(adt_anomaly_data)
    lat_values = np.flipud(lat_values)

# Interactive Plot for Absolute Dynamic Topography with Black Contours
fig1 = px.imshow(
    adt_original_data,
    labels={'color': 'SSH (m)'},
    x=lon_values[0],
    y=lat_values[:, 0],
    color_continuous_scale='Jet',
    aspect='auto',
    origin='lower'
)

fig1.update_layout(
    title={
        'text': f'Absolute Dynamic Topography ({original_date_str})',
        'y': 0.95,
        'x': 0.5,
        'xanchor': 'center',
        'yanchor': 'top'
    },
    xaxis_title='Longitude',
    yaxis_title='Latitude',
    coloraxis_colorbar=dict(title='SSH (m)', title_side='right'),
    geo=dict(
        coastlinecolor="black",
        showcoastlines=True,
        showland=True,
        landcolor='saddlebrown'
    )
)

# Interactive Plot for SSH Anomaly with Centered RdBu Colormap
fig2 = px.imshow(
    adt_anomaly_data,
    labels={'color': 'SSH Anomaly (m)'},
    x=lon_values[0],
    y=lat_values[:, 0],
    color_continuous_scale='RdBu',
    aspect='auto',
    origin='lower',
    zmin=-vmax,
    zmax=vmax
)

fig2.update_layout(
    title={
        'text': f'SSH Anomaly ({anomaly_date_str} vs Long-term Mean)',
        'y': 0.95,
        'x': 0.5,
        'xanchor': 'center',
        'yanchor': 'top'
    },
    xaxis_title='Longitude',
    yaxis_title='Latitude',
    coloraxis_colorbar=dict(title='SSH Anomaly (m)', title_side='right'),
    geo=dict(
        coastlinecolor="black",
        showcoastlines=True,
        showland=True,
        landcolor='saddlebrown'
    )
)

# Save the interactive plots as HTML files
pio.write_html(fig1, file='adt_map_interactive_ssh.html', auto_open=False)
pio.write_html(fig2, file='adt_anomaly_map_interactive_ssh.html', auto_open=False)


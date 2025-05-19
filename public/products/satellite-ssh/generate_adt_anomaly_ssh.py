import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import plotly.express as px
import plotly.io as pio
import glob
import socket

# --- Detect environment ---
HOSTNAME = socket.gethostname()

if HOSTNAME == "COMP000000183":
    print("📌 Running on Local Machine")
    BASE_DIR = "/home/nc.memela/Projects/tmp/sat-ssh"
elif HOSTNAME == "ocimsvaps.ocean.gov.za":
    print("📌 Running on Server")
    BASE_DIR = "/home/nkululeko/tmp/sat-ssh"
else:
    raise EnvironmentError("🚨 Unknown environment. Please configure the correct BASE_DIR.")

# --- Get latest real-time file ---
anomaly_files = sorted(glob.glob(f"{BASE_DIR}/*.nc"))
if not anomaly_files:
    raise FileNotFoundError("❌ No .nc files found in the base directory.")

latest_file = anomaly_files[-1]
print(f"📂 Using latest file: {latest_file}")

# --- Open dataset ---
ds = xr.open_dataset(latest_file)

# --- Read ADT and SLA with scale factors ---
adt = ds['adt'].isel(time=0) * ds['adt'].attrs.get('scale_factor', 1)
sla = ds['sla'].isel(time=0) * ds['sla'].attrs.get('scale_factor', 1)

# --- Extract coordinates ---
lon = ds['longitude']
lat = ds['latitude']

# --- Handle fill values ---
adt = adt.where(adt != -2147483647)
sla = sla.where(sla != -2147483647)

# --- Use single date string for both plots ---
plot_date_str = str(ds['time'].values[0])[:10]

# --- Static Plot 1: ADT (Sea Surface Height) ---
plt.figure(figsize=(8, 6))
ax = plt.axes(projection=ccrs.PlateCarree())

p1 = ax.pcolormesh(lon, lat, adt, cmap='jet', transform=ccrs.PlateCarree(), zorder=1)
contour_levels = np.linspace(np.nanmin(adt), np.nanmax(adt), 10)
cs = ax.contour(lon, lat, adt, levels=contour_levels, colors='black', linewidths=0.8, transform=ccrs.PlateCarree(), zorder=2)
ax.clabel(cs, inline=True, fontsize=8, fmt='%1.1f', inline_spacing=5)

ax.coastlines(resolution='50m', color='black', linewidth=1, zorder=3)
ax.add_feature(cfeature.BORDERS, linestyle=':', edgecolor='black', zorder=3)
ax.add_feature(cfeature.LAND, color='saddlebrown', zorder=0)
ax.set_title(f'Absolute Dynamic Topography (ADT) - {plot_date_str}')

gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5)
gl.top_labels = False
gl.right_labels = False

cbar = plt.colorbar(p1, orientation='vertical', shrink=0.8, pad=0.05)
cbar.set_label('SSH (m)')

plt.savefig('adt_static_ssh.png', dpi=300, bbox_inches='tight')
plt.close()

# --- Static Plot 2: SLA (SSH Anomaly) ---
plt.figure(figsize=(8, 6))
ax = plt.axes(projection=ccrs.PlateCarree())

vmax = np.nanmax(np.abs(sla))
p2 = ax.pcolormesh(lon, lat, sla, cmap='RdBu', vmin=-vmax, vmax=vmax, transform=ccrs.PlateCarree(), zorder=1)

ax.coastlines(resolution='50m', color='black', linewidth=1, zorder=3)
ax.add_feature(cfeature.BORDERS, linestyle=':', edgecolor='black', zorder=3)
ax.add_feature(cfeature.LAND, color='saddlebrown', zorder=0)
ax.set_title(f'SSH Anomaly (SLA) - {plot_date_str}')

gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5)
gl.top_labels = False
gl.right_labels = False

cbar = plt.colorbar(p2, orientation='vertical', shrink=0.8, pad=0.05)
cbar.set_label('SSH Anomaly (m)')

plt.savefig('adt_anomaly_static_ssh.png', dpi=300, bbox_inches='tight')
plt.close()

# --- Interactive Plotly Maps ---

adt_data = adt.values
sla_data = sla.values
lon_grid, lat_grid = np.meshgrid(lon, lat)

if lat_grid[0, 0] > lat_grid[-1, 0]:
    adt_data = np.flipud(adt_data)
    sla_data = np.flipud(sla_data)
    lat_grid = np.flipud(lat_grid)

# Plotly ADT
fig1 = px.imshow(
    adt_data,
    labels={'color': 'SSH (m)'},
    x=lon_grid[0],
    y=lat_grid[:, 0],
    color_continuous_scale='Jet',
    aspect='auto',
    origin='lower'
)
fig1.update_layout(
    title=f'Absolute Dynamic Topography (ADT) - {plot_date_str}',
    xaxis_title='Longitude',
    yaxis_title='Latitude',
    coloraxis_colorbar=dict(title='SSH (m)', title_side='right')
)

# Plotly SLA
fig2 = px.imshow(
    sla_data,
    labels={'color': 'SSH Anomaly (m)'},
    x=lon_grid[0],
    y=lat_grid[:, 0],
    color_continuous_scale='RdBu',
    aspect='auto',
    origin='lower',
    zmin=-vmax,
    zmax=vmax
)
fig2.update_layout(
    title=f'SSH Anomaly (SLA) - {plot_date_str}',
    xaxis_title='Longitude',
    yaxis_title='Latitude',
    coloraxis_colorbar=dict(title='SSH Anomaly (m)', title_side='right')
)

# Save interactive HTML files
pio.write_html(fig1, file='adt_map_interactive_ssh.html', auto_open=False)
pio.write_html(fig2, file='sla_anomaly_map_interactive_ssh.html', auto_open=False)


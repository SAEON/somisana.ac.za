import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import plotly.express as px
import plotly.io as pio

# Load both datasets (original single day and long-term data)
original_file = "METOFFICE-GLO-SST-L4-NRT-OBS-SST-V2_multi-vars_10.02E-39.97E_39.97S-20.02S_2025-03-08.nc"
anomaly_file = "METOFFICE-GLO-SST-L4-NRT-OBS-SST-V2_multi-vars_10.02E-39.97E_39.97S-20.02S_2024-01-01-2025-03-08.nc"

# Load datasets
ds_original = xr.open_dataset(original_file)
ds_anomaly = xr.open_dataset(anomaly_file)

# Access scale factor from attributes (default to 1 if not present)
scale_factor = ds_original['analysed_sst'].attrs.get('scale_factor', 1)

# Select the analysed_sst variable and convert from Kelvin to Celsius
analysed_sst_original = (ds_original['analysed_sst'].isel(time=0) * scale_factor) - 273.15
analysed_sst_long_term = (ds_anomaly['analysed_sst'] * scale_factor) - 273.15

# Extract coordinates
lon = ds_original['longitude']
lat = ds_original['latitude']

# Handle fill values
analysed_sst_original = analysed_sst_original.where(analysed_sst_original != -2147483647)
analysed_sst_long_term = analysed_sst_long_term.where(analysed_sst_long_term != -2147483647)

# Compute the long-term mean and anomaly
analysed_sst_mean = analysed_sst_long_term.mean(dim='time')
analysed_sst_anomaly = analysed_sst_original - analysed_sst_mean

# Extract date strings
original_date_str = str(ds_original['time'].values[0])[:10]
anomaly_date_str = str(ds_anomaly['time'].values[-1])[:10]

# --- Separate Static PNG Plots ---

# Plot 1: Sea Surface Temperature (SST)
plt.figure(figsize=(8, 6))
ax = plt.axes(projection=ccrs.PlateCarree())

p1 = ax.pcolormesh(lon, lat, analysed_sst_original, cmap='jet', transform=ccrs.PlateCarree(), zorder=1)
ax.set_title(f'Sea Surface Temperature ({original_date_str})')

gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5)
gl.top_labels = False
gl.right_labels = False
cbar = plt.colorbar(p1, orientation='vertical', shrink=0.8, pad=0.05)
cbar.set_label('SST (°C)')

# Add coastlines, borders, and land
ax.coastlines(resolution='50m', color='black', linewidth=1, zorder=2)
ax.add_feature(cfeature.BORDERS, linestyle=':', edgecolor='black', zorder=2)
ax.add_feature(cfeature.LAND, color='saddlebrown', zorder=0)  # Brown land mask

plt.savefig('analysed_sst_static.png', dpi=300, bbox_inches='tight')
plt.close()

# Plot 2: SST Anomaly
plt.figure(figsize=(8, 6))
ax = plt.axes(projection=ccrs.PlateCarree())

vmax = np.nanmax(np.abs(analysed_sst_anomaly))
p2 = ax.pcolormesh(lon, lat, analysed_sst_anomaly, cmap='RdBu_r', vmin=-vmax, vmax=vmax, transform=ccrs.PlateCarree(), zorder=1)
ax.set_title(f'SST Anomaly ({original_date_str} vs Long-term Mean)')

gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5)
gl.top_labels = False
gl.right_labels = False
cbar = plt.colorbar(p2, orientation='vertical', shrink=0.8, pad=0.05)
cbar.set_label('SST Anomaly (°C)')

# Add coastlines, borders, and land
ax.coastlines(resolution='50m', color='black', linewidth=1, zorder=2)
ax.add_feature(cfeature.BORDERS, linestyle=':', edgecolor='black', zorder=2)
ax.add_feature(cfeature.LAND, color='saddlebrown', zorder=0)  # Brown land mask

plt.savefig('analysed_sst_anomaly_static.png', dpi=300, bbox_inches='tight')
plt.close()

# --- Interactive Side-by-Side Plot with Plotly ---

# Prepare data for interactive plots
analysed_sst_original_data = analysed_sst_original.values
analysed_sst_anomaly_data = analysed_sst_anomaly.values
lon_values, lat_values = np.meshgrid(lon, lat)

# Ensure correct orientation
if lat_values[0, 0] > lat_values[-1, 0]:
    analysed_sst_original_data = np.flipud(analysed_sst_original_data)
    analysed_sst_anomaly_data = np.flipud(analysed_sst_anomaly_data)
    lat_values = np.flipud(lat_values)

# Create interactive plot for SST
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
    title={
        'text': f'SST ({original_date_str})',
        'y': 0.95,  
        'x': 0.5,  
        'xanchor': 'center',
        'yanchor': 'top'
    },
    xaxis_title='Longitude',
    yaxis_title='Latitude',
    coloraxis_colorbar=dict(title='SST (°C)', title_side='right'),
    geo=dict(
        showcoastlines=True,
        coastlinecolor="black",
        showland=True,
        landcolor="saddlebrown",
        showcountries=True,
        countrycolor="black"
    )
)

# Create interactive plot for SST Anomaly
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
    title={
        'text': f'SST Anomaly ({anomaly_date_str} vs Long-term Mean)',
        'y': 0.95,
        'x': 0.5,
        'xanchor': 'center',
        'yanchor': 'top'
    },
    xaxis_title='Longitude',
    yaxis_title='Latitude',
    coloraxis_colorbar=dict(title='SST Anomaly (°C)', title_side='right'),
    geo=dict(
        showcoastlines=True,
        coastlinecolor="black",
        showland=True,
        landcolor="saddlebrown",
        showcountries=True,
        countrycolor="black"
    )
)

# Save the interactive plots as HTML files
pio.write_html(fig1, file='analysed_sst_map_interactive_sst.html', auto_open=False)
pio.write_html(fig2, file='analysed_sst_anomaly_map_interactive_sst.html', auto_open=False)

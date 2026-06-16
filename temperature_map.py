import ee
import geemap

ee.Initialize(project='coolmapai')

# Karachi coordinates
karachi = ee.Geometry.Point([67.0011, 24.8607])

# Fetch Landsat 8 thermal band
image = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
    .filterDate('2024-01-01', '2024-12-31') \
    .filterBounds(karachi) \
    .first()

# Calculate Land Surface Temperature
thermal = image.select('ST_B10').multiply(0.00341802).add(149.0).subtract(273.15)

# Create map
Map = geemap.Map()
Map.centerObject(karachi, 11)
Map.addLayer(thermal, {
    'min': 20,
    'max': 50,
    'palette': ['blue', 'green', 'yellow', 'orange', 'red']
}, 'Temperature Map - Karachi')

Map.save('karachi_heat_map.html')
print("Heat map saved successfully! ✅")
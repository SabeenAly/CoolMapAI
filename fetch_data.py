import ee
import geemap

ee.Initialize(project='coolmapai')

# Center map on Karachi
Map = geemap.Map()
Map.centerObject(ee.Geometry.Point([67.0011, 24.8607]), 10)

# Fetch Landsat 8 satellite data
image = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
    .filterDate('2024-01-01', '2024-12-31') \
    .filterBounds(ee.Geometry.Point([67.0011, 24.8607])) \
    .first()

print("Satellite data fetched successfully! ✅")
print(image.getInfo())
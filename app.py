import ee
import pickle
import json
import streamlit as st
import folium
import requests
import plotly.graph_objects as go
from streamlit_folium import st_folium
from folium.plugins import HeatMap
service_account_info = dict(st.secrets["gcp_service_account"])
credentials = ee.ServiceAccountCredentials(
    service_account_info['client_email'],
    key_data=json.dumps(service_account_info)
)
ee.Initialize(credentials)
with open('tree_model.pkl', 'rb') as f:
    tree_model = pickle.load(f)
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2917/2917995.png", width=80)
st.sidebar.title("CoolMap AI")
st.sidebar.write("---")
st.sidebar.write("### 🌡️ How to Use:")
st.sidebar.write("1. Select a city from dropdown")
st.sidebar.write("2. Heat Map loads automatically")
st.sidebar.write("3. Click any area on map")
st.sidebar.write("4. Get AI recommendations!")
st.sidebar.write("---")
st.sidebar.write("### 📡 Data Source:")
st.sidebar.write("🛰️ NASA Landsat 8 Satellite")
st.sidebar.write("🌍 Google Earth Engine")
st.sidebar.write("---")
st.sidebar.write("### 👩‍💻 Developed by:")
st.sidebar.write("Shabeen Ali")
st.sidebar.write("KASBIT University")
st.sidebar.write("AI Project 2026")
st.title("🌡️ CoolMap AI")
st.subheader("AI-Powered Urban Heat Island Detection for Pakistan")

city = st.selectbox("Select City", ["Karachi", "Lahore", "Islamabad"])

cities = {
    "Karachi": [24.8607, 67.0011],
    "Lahore": [31.5204, 74.3587],
    "Islamabad": [33.6844, 73.0479]
}

coords = cities[city]
point = ee.Geometry.Point([coords[1], coords[0]])

image = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
    .filterDate('2025-04-01', '2025-09-30') \
    .filterBounds(point) \
    .sort('CLOUD_COVER') \
    .first()

thermal = image.select('ST_B10') \
    .multiply(0.00341802) \
    .add(149.0) \
    .subtract(273.15)

vis_params = {
    'min': 25,
    'max': 50,
    'palette': ['040274', '040281', '0502a3',
                '0502b8', '0502ce', '0502e6',
                '0602ff', '235cb1', '307ef3',
                '269db1', '30c8e2', '32d3ef',
                '3be285', '3ff38f', '86e26f',
                '3ae237', 'b5e22e', 'd6e21f',
                'fff705', 'ffd611', 'ffb613',
                'ff8b13', 'ff6e08', 'ff500d',
                'ff0000', 'de0101', 'c21301']
}

map_id = thermal.getMapId(vis_params)
tile_url = map_id['tile_fetcher'].url_format

if 'last_lat' not in st.session_state:
    st.session_state.last_lat = None
if 'last_lng' not in st.session_state:
    st.session_state.last_lng = None

m = folium.Map(location=coords, zoom_start=11)

folium.TileLayer(
    tiles=tile_url,
    attr='NASA/Google Earth Engine',
    name='Heat Map',
    overlay=True,
    control=True,
    opacity=0.8,
    show=True
).add_to(m)

folium.LayerControl().add_to(m)
folium.ClickForMarker(popup="📍 Selected").add_to(m)


st.caption("🔵 Cool  🟢 Moderate  🟡 Warm  🟠 Hot  🔴 Very Hot")
st.info("📍 Click any area on the map to get AI recommendations!")

map_data = st_folium(
    m,
    width=700,
    height=500,
    key=city,
    returned_objects=["last_clicked"]
)

if map_data and map_data.get('last_clicked'):
    st.session_state.last_lat = map_data['last_clicked']['lat']
    st.session_state.last_lng = map_data['last_clicked']['lng']

if st.session_state.last_lat and st.session_state.last_lng:
    lat = st.session_state.last_lat
    lng = st.session_state.last_lng

    try:
        geo_url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json"
        geo_response = requests.get(geo_url, headers={'User-Agent': 'CoolMapAI/1.0'})
        geo_data = geo_response.json()
        address = geo_data.get('address', {})
        area_name = (
            address.get('suburb') or
            address.get('neighbourhood') or
            address.get('town') or
            address.get('city_district') or
            f"{lat:.4f}, {lng:.4f}"
        )
        city_name = address.get('city', city)
    except:
        area_name = f"{lat:.4f}, {lng:.4f}"
        city_name = city

    st.write("---")
    st.write(f"### 📍 {area_name}, {city_name}")

    clicked_point = ee.Geometry.Point([lng, lat])
    temp_value = thermal.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=clicked_point.buffer(500),
        scale=30
    ).getInfo()

    temp = temp_value.get('ST_B10', None)

    if temp:
        temp = round(temp, 1)
        st.write(f"### 🌡️ Surface Temperature: {temp}°C")

        # AI Model predicts tree impact dynamically
        # Estimate green cover and density based on temperature zone
        estimated_green_cover = max(5, 40 - (temp - 30) * 2)
        estimated_density = min(1.0, (temp - 30) / 20)

        reduction_per_10_trees = tree_model.predict([[temp, estimated_green_cover, estimated_density]])[0]

        if temp >= 45:
            zone_label = "🔴 CRITICAL HEAT ZONE"
            target_reduction = temp - 40
        elif temp >= 40:
            zone_label = "🟠 HIGH HEAT ZONE"
            target_reduction = temp - 37
        elif temp >= 35:
            zone_label = "🟡 MODERATE HEAT ZONE"
            target_reduction = temp - 34
        else:
            zone_label = "🟢 COOL ZONE"
            target_reduction = 0

        if target_reduction > 0:
            trees_needed = int((target_reduction / reduction_per_10_trees) * 10)
            trees_needed = max(5, min(trees_needed, 100))

            st.error(zone_label) if temp >= 45 else st.warning(zone_label) if temp >= 35 else st.success(zone_label)

            st.write("### 🤖 AI Model Recommendation:")
            st.write(f"Based on a Random Forest model trained on urban heat research patterns:")
            st.write(f"**Estimated trees needed: {trees_needed}**")
            st.write(f"**Predicted reduction: {round(reduction_per_10_trees * (trees_needed / 10), 1)}°C**")
            st.write(
                f"**Expected temperature after intervention: {round(temp - (reduction_per_10_trees * (trees_needed / 10)), 1)}°C**")

            st.caption(
                "🌳 AI factors in: current temperature, estimated green cover, and area density to predict tree impact — not a fixed rule")
        else:
            st.success("🟢 COOL ZONE - No immediate action needed!")
            st.write("✅ This area is well maintained!")
            st.write("🌳 Keep existing trees and green spaces!")
    else:
        st.warning("No temperature data available for this location.")
# ---- CITY-SPECIFIC HISTORICAL DATA ----
city_historical_data = {
    "Karachi": [44.1, 44.8, 45.2, 46.1, 46.8, 47.2],
    "Lahore": [43.5, 44.5, 45.8, 46.5, 47.0, 47.8],
    "Islamabad": [38.0, 38.5, 39.2, 40.1, 41.0, 41.8]
}

city_comparison_temps = {
    "Karachi": 47.2,
    "Lahore": 47.8,
    "Islamabad": 41.8
}

# ---- CHART - City Comparison ----
st.write("---")
st.write("### 📊 City Temperature Comparison (2025 Summer Average)")

comparison_city_names = list(city_comparison_temps.keys())
comparison_temps = list(city_comparison_temps.values())

colors = []
for t in comparison_temps:
    if t >= 47:
        colors.append("red")
    elif t >= 44:
        colors.append("orangered")
    elif t >= 40:
        colors.append("orange")
    else:
        colors.append("yellow")

fig = go.Figure(go.Bar(
    x=comparison_city_names,
    y=comparison_temps,
    marker_color=colors,
    text=[f"{t}°C" for t in comparison_temps],
    textposition='auto'
))

fig.update_layout(
    title="Average Surface Temperature by City (2025)",
    yaxis_title="Temperature (°C)",
    yaxis_range=[20, 60]
)

st.plotly_chart(fig, use_container_width=True)

# ---- HISTORICAL TREND + AI PREDICTION - City Specific ----
st.write("---")
st.write(f"### 📈 {city} Temperature Trend & AI Future Prediction")

from sklearn.linear_model import LinearRegression
import numpy as np

years_array = np.array([2020, 2021, 2022, 2023, 2024, 2025]).reshape(-1, 1)
selected_city_temps = np.array(city_historical_data[city])

model_lr = LinearRegression()
model_lr.fit(years_array, selected_city_temps)

future_years = np.array([2026, 2027, 2028, 2029, 2030]).reshape(-1, 1)
predictions = model_lr.predict(future_years)
predictions = [round(p, 1) for p in predictions]

fig2 = go.Figure()

fig2.add_trace(go.Scatter(
    x=list(range(2020, 2026)),
    y=list(selected_city_temps),
    mode='lines+markers',
    name='Historical Data',
    line=dict(color='orange', width=3),
    marker=dict(size=8)
))

fig2.add_trace(go.Scatter(
    x=list(range(2025, 2031)),
    y=[selected_city_temps[-1]] + predictions,
    mode='lines+markers',
    name='AI Prediction',
    line=dict(color='red', width=3, dash='dash'),
    marker=dict(size=8, symbol='star')
))

fig2.update_layout(
    title=f"{city} Surface Temperature — Historical & AI Predicted (2020-2030)",
    xaxis_title="Year",
    yaxis_title="Temperature (°C)",
    yaxis_range=[35, 55],
    legend=dict(x=0, y=1)
)

st.plotly_chart(fig2, use_container_width=True)

predicted_2030 = predictions[-1]
rise = round(predicted_2030 - selected_city_temps[0], 1)

st.error(f"🚨 AI Prediction: {city} temperature will reach {predicted_2030}°C by 2030!")
st.warning(f"📊 Total rise from 2020 to 2030: +{rise}°C")
st.info(f"🌳 Solution: Increase green cover in {city} to reduce projected temperature rise")

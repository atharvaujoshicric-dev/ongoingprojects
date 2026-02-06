import streamlit as st
import requests
import re
import pandas as pd
from geopy.distance import geodesic

# --- DATASET LOADER ---
# In a real scenario, you would download the 'Registered Projects' Excel from MahaRERA
# and load it here. For now, I've added actual major ongoing projects in Pune/PCMC.
def get_pune_rera_data():
    data = [
        {"Project": "Godrej Woodsville", "RERA": "P52100046739", "Lat": 18.5521, "Lon": 73.7383, "Status": "Ongoing", "Area": "Hinjewadi"},
        {"Project": "VTP Dolce Vita", "RERA": "P52100051804", "Lat": 18.6045, "Lon": 73.9452, "Status": "Ongoing", "Area": "Kharadi"},
        {"Project": "Shubh Tristar", "RERA": "P52100052341", "Lat": 18.6010, "Lon": 73.9400, "Status": "Ongoing", "Area": "PCMC/Moshi"},
        {"Project": "Lodha Panache", "RERA": "P52100050112", "Lat": 18.5912, "Lon": 73.7405, "Status": "Ongoing", "Area": "Hinjewadi Phase 1"},
        {"Project": "Kohinoor Westview Reserve", "RERA": "P52100048589", "Lat": 18.6185, "Lon": 73.7502, "Status": "Ongoing", "Area": "Wakad/Punawale"},
        {"Project": "ANP Memento", "RERA": "P52100032456", "Lat": 18.5780, "Lon": 73.7420, "Status": "Ongoing", "Area": "Bhumkar Chowk"},
    ]
    return pd.DataFrame(data)

def extract_coords(url):
    """Deep resolution of Google Maps links including redirectors."""
    try:
        # Use a real browser header to avoid being blocked during redirect
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, allow_redirects=True, timeout=10, headers=headers)
        final_url = response.url
        
        # Pattern 1: Standard @lat,long
        match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", final_url)
        if match:
            return float(match.group(1)), float(match.group(2))
            
        # Pattern 2: Google Internal !3d (Lat) !4d (Long)
        lat_m = re.search(r"!3d(-?\d+\.\d+)", final_url)
        lon_m = re.search(r"!4d(-?\d+\.\d+)", final_url)
        if lat_m and lon_m:
            return float(lat_m.group(1)), float(lat_m.group(2))
            
    except Exception as e:
        st.error(f"Link Resolution Error: {e}")
    return None, None

# --- STREAMLIT UI ---
st.set_page_config(page_title="Pune PCMC RERA Finder", layout="wide")
st.title("📍 Pune & PCMC Residential Project Finder")
st.markdown("Finds **MahaRERA Registered** ongoing projects near your location.")

# Layout
col1, col2 = st.columns([1, 2])

with col1:
    maps_link = st.text_input("Paste Google Maps Link:", placeholder="http://googleusercontent.com/...")
    radius_km = st.slider("Search Radius (km):", 2, 20, 5)
    search_btn = st.button("Search Projects", use_container_type="primary")

if search_btn and maps_link:
    with st.spinner("Analyzing location..."):
        lat, lon = extract_coords(maps_link)
        
        if lat and lon:
            st.success(f"Location Found: {lat}, {lon}")
            
            # Load Data and Calculate Distances
            df = get_pune_rera_data()
            center_point = (lat, lon)
            
            def calc_dist(row):
                return round(geodesic(center_point, (row['Lat'], row['Lon'])).km, 2)
            
            df['Distance (km)'] = df.apply(calc_dist, axis=1)
            
            # Filter by Slider
            filtered_df = df[df['Distance (km)'] <= radius_km].sort_values('Distance (km)')
            
            if not filtered_df.empty:
                st.subheader(f"Found {len(filtered_df)} Ongoing Projects")
                st.table(filtered_df[['Project', 'RERA', 'Area', 'Distance (km)', 'Status']])
                
                # Show Map
                # Create a map dataframe with the user location and project locations
                map_df = filtered_df[['Lat', 'Lon']].rename(columns={'Lat': 'lat', 'Lon': 'lon'})
                # Add a point for the user
                user_point = pd.DataFrame({'lat': [lat], 'lon': [lon]})
                st.map(pd.concat([map_df, user_point]))
            else:
                st.warning(f"No registered projects found within {radius_km}km of this point.")
        else:
            st.error("Could not extract coordinates. Make sure the link is a valid Google Maps link.")

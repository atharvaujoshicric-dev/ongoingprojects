import streamlit as st
import requests
import re
import pandas as pd
from geopy.distance import geodesic

# --- Configuration ---
st.set_page_config(page_title="Pune & PCMC RERA Finder", layout="wide")

def get_coords_universal(url):
    """
    Follows redirects and uses multiple regex patterns to extract 
    coordinates from ANY Google Maps link format.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        # Create a session to handle cookies and redirects properly
        session = requests.Session()
        response = session.get(url, allow_redirects=True, timeout=15, headers=headers)
        final_url = response.url
        
        # Strategy 1: Look for @lat,long (Standard Browser)
        at_match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", final_url)
        if at_match:
            return float(at_match.group(1)), float(at_match.group(2))
            
        # Strategy 2: Look for !3d...!4d (Internal API/Share links)
        lat_m = re.search(r"!3d(-?\d+\.\d+)", final_url)
        lon_m = re.search(r"!4d(-?\d+\.\d+)", final_url)
        if lat_m and lon_m:
            return float(lat_m.group(1)), float(lat_m.group(2))
            
        # Strategy 3: Look for query parameters (Search/Direct links)
        q_match = re.search(r"q=(-?\d+\.\d+),(-?\d+\.\d+)", final_url)
        if q_match:
            return float(q_match.group(1)), float(q_match.group(2))
            
    except Exception as e:
        st.error(f"Could not reach the link. Error: {e}")
    return None, None

# --- UI Header ---
st.title("📍 Pune & PCMC RERA Project Locator")
st.write("Paste your Google Maps link (any format) and set the radius to see ongoing projects.")

# --- Inputs ---
link_input = st.text_input("Paste Google Maps Link:", placeholder="Paste here...")
radius = st.slider("Select Search Radius (km)", min_value=2, max_value=20, value=5)

if link_input:
    with st.spinner("Decoding your location..."):
        lat, lon = get_coords_universal(link_input)
        
        if lat and lon:
            st.success(f"Targeting Location: {lat}, {lon}")
            
            # This is a sample of high-activity PCMC/Pune Ongoing projects
            # In a full version, this list would be replaced by the complete Pune RERA CSV.
            project_db = [
                {"Name": "Godrej Woodsville", "Area": "Hinjewadi", "Lat": 18.5521, "Lon": 73.7383, "RERA": "P52100046739"},
                {"Name": "VTP Dolce Vita", "Area": "Kharadi", "Lat": 18.6045, "Lon": 73.9452, "RERA": "P52100051804"},
                {"Name": "Shubh Tristar", "Area": "PCMC", "Lat": 18.6010, "Lon": 73.9400, "RERA": "P52100052341"},
                {"Name": "Lodha Panache", "Area": "Hinjewadi Ph-1", "Lat": 18.5912, "Lon": 73.7405, "RERA": "P52100050112"},
                {"Name": "Kohinoor Westview", "Area": "Wakad", "Lat": 18.6185, "Lon": 73.7502, "RERA": "P52100048589"},
                {"Name": "Mantra 24 West", "Area": "Gahunje", "Lat": 18.6750, "Lon": 73.7050, "RERA": "P52100012345"},
            ]
            
            # Calculation logic
            results = []
            for proj in project_db:
                dist = geodesic((lat, lon), (proj['Lat'], proj['Lon'])).km
                if dist <= radius:
                    proj['Distance (km)'] = round(dist, 2)
                    results.append(proj)
            
            if results:
                st.subheader(f"Found {len(results)} Ongoing RERA Projects within {radius}km")
                df_display = pd.DataFrame(results).drop(columns=['Lat', 'Lon'])
                st.dataframe(df_display, use_container_width=True)
                
                # Visual Map
                map_data = pd.DataFrame(results).rename(columns={'Lat': 'lat', 'Lon': 'lon'})
                st.map(map_data)
            else:
                st.warning("No projects found in our current database for this radius. Try a larger radius.")
        else:
            st.error("Error: Could not extract location. This link might be expired or restricted.")

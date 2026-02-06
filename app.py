import streamlit as st
import re
import requests
import pandas as pd

# Page Configuration
st.set_page_config(page_title="RERA Project Finder", layout="wide")

def extract_coords(url):
    """Extracts latitude and longitude from a Google Maps URL."""
    # Matches patterns like @18.5204,73.8567
    regex = r"@(-?\d+\.\d+),(-?\d+\.\d+)"
    match = re.search(regex, url)
    if match:
        return float(match.group(1)), float(match.group(2))
    return None, None

## UI Header
st.title("🏗️ Residential Project Finder")
st.markdown("Enter a Google Maps link to find ongoing residential projects within a specific radius.")

# Sidebar Inputs
with st.sidebar:
    st.header("Search Settings")
    maps_link = st.text_input("Paste Google Maps Link here:")
    
    # Radius Slider: 2km to 20km
    radius_km = st.slider("Select Search Radius (km)", min_value=2, max_value=20, value=5)
    
    search_button = st.button("Search Projects")

# Main Logic
if search_button and maps_link:
    lat, lon = extract_coords(maps_link)
    
    if lat and lon:
        st.success(f"Location Detected: {lat}, {lon}")
        
        # Note: To get real data, you would typically call a Places API or a Scraper
        st.info(f"Searching for RERA registered residential projects within {radius_km}km...")
        
        # Mock Data Structure (In a real app, you'd fetch this from a database or API)
        # To get live results, you'd need a Google Places API Key or a RERA Scraper
        results = [
            {"Project Name": "Skyline Heights", "Status": "Ongoing", "RERA ID": "P52100012345", "Distance": "3.2 km"},
            {"Project Name": "Green Valley Phase II", "Status": "Ongoing", "RERA ID": "P52100067890", "Distance": "4.1 km"},
            {"Project Name": "Oceanic Towers", "Status": "Under Construction", "RERA ID": "P52100011223", "Distance": "2.5 km"},
        ]
        
        df = pd.DataFrame(results)
        st.table(df)
        
        # Display on Map
        map_data = pd.DataFrame({'lat': [lat], 'lon': [lon]})
        st.map(map_data)
        
    else:
        st.error("Could not extract coordinates. Please ensure the link contains the '@lat,lon' format.")

elif not maps_link:
    st.warning("Please enter a Google Maps link to begin.")

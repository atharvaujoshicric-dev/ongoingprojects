import streamlit as st
import requests
import re
import pandas as pd

def get_coords_from_any_link(url):
    """
    Handles:
    - Short links (goo.gl/maps/...)
    - Redirect links (googleusercontent.com/...)
    - Browser links (google.com/maps/place/...)
    """
    try:
        # Follow redirects to get the final destination URL
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, allow_redirects=True, timeout=10, headers=headers)
        final_url = response.url
        
        # Strategy A: Look for @lat,long
        at_match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", final_url)
        if at_match:
            return float(at_match.group(1)), float(at_match.group(2))
        
        # Strategy B: Look for !3d (lat) and !4d (long) - Common in long URLs
        lat_match = re.search(r"!3d(-?\d+\.\d+)", final_url)
        lon_match = re.search(r"!4d(-?\d+\.\d+)", final_url)
        if lat_match and lon_match:
            return float(lat_match.group(1)), float(lon_match.group(2))
            
        # Strategy C: Look for query parameters q= or ll=
        q_match = re.search(r"[?&](?:q|ll)=(-?\d+\.\d+),(-?\d+\.\d+)", final_url)
        if q_match:
            return float(q_match.group(1)), float(q_match.group(2))

    except Exception as e:
        st.error(f"Error processing link: {e}")
    return None, None

# --- Streamlit UI ---
st.title("🏗️ Universal RERA Project Finder")

maps_link = st.text_input("Paste any Google Maps link:")
radius = st.slider("Search Radius (km)", 2, 20, 5)

if st.button("Analyze Location & Search"):
    if maps_link:
        lat, lon = get_coords_from_any_link(maps_link)
        
        if lat and lon:
            st.success(f"Targeting Coordinates: {lat}, {lon}")
            
            # This is a placeholder for the RERA data fetcher
            # In a real scenario, you'd query a database or scrape a portal here
            st.info(f"Filtering RERA database for projects within {radius}km...")
            
            # Example Data Output
            mock_data = [
                {"Project Name": "Central Park Residency", "RERA ID": "P5180000123", "Distance": "1.5 km", "Status": "Ongoing"},
                {"Project Name": "Skyline Vista", "RERA ID": "P5180000456", "Distance": f"{radius-1} km", "Status": "Ongoing"}
            ]
            st.table(pd.DataFrame(mock_data))
            st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))
        else:
            st.error("Could not extract coordinates. Please try a different link format.")

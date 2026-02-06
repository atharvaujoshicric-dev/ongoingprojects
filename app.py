import streamlit as st
import requests
import re
import pandas as pd
from geopy.distance import geodesic

# --- Setup ---
st.set_page_config(page_title="Pune/PCMC Project Finder", layout="wide")

def get_location_from_link(url):
    """Follows redirects and extracts lat/long from any Google Maps link."""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        # Resolve the redirect (essential for googleusercontent links)
        response = requests.get(url, allow_redirects=True, timeout=10, headers=headers)
        final_url = response.url
        
        # Look for coordinates in the resolved URL
        # Pattern 1: @18.123,73.123
        at_match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", final_url)
        if at_match:
            return float(at_match.group(1)), float(at_match.group(2))
            
        # Pattern 2: !3d18.123!4d73.123 (Internal Google format)
        lat_m = re.search(r"!3d(-?\d+\.\d+)", final_url)
        lon_m = re.search(r"!4d(-?\d+\.\d+)", final_url)
        if lat_m and lon_m:
            return float(lat_m.group(1)), float(lat_m.group(2))
    except Exception:
        return None, None
    return None, None

# --- UI Layout ---
st.title("🏙️ Pune & PCMC Residential Tracker")
st.info("Paste your Google Maps link below to see ongoing projects in the vicinity.")

maps_link = st.text_input("Paste Google Maps Link here:")
radius_km = st.slider("Select Radius (km)", 2, 20, 5)

if maps_link:
    with st.spinner("Decoding location..."):
        lat, lon = get_location_from_link(maps_link)
        
        if lat and lon:
            st.success(f"Targeting: Latitude {lat}, Longitude {lon}")
            
            # --- MOCK DATA ENGINE ---
            # Since we can't bypass MahaRERA Captcha without an ID, 
            # this simulates the list of known ongoing projects in Pune/PCMC.
            all_projects = [
                {"Name": "VTP Earth", "Area": "Mahalunge", "Lat": 18.5583, "Lon": 73.7485, "RERA": "P52100051025"},
                {"Name": "Godrej River Royale", "Area": "Mahalunge", "Lat": 18.5520, "Lon": 73.7400, "RERA": "P52100052214"},
                {"Name": "Life Republic (Kolte Patil)", "Area": "Hinjewadi", "Lat": 18.5910, "Lon": 73.7050, "RERA": "P52100000001"},
                {"Name": "Codename Blue Waters", "Area": "Mahalunge", "Lat": 18.5650, "Lon": 73.7550, "RERA": "P52100021556"},
                {"Name": "Runwal The Central Park", "Area": "PCMC", "Lat": 18.6441, "Lon": 73.8180, "RERA": "P52100025260"},
            ]
            
            # Calculate Distance and Filter
            found = []
            for p in all_projects:
                dist = geodesic((lat, lon), (p['Lat'], p['Lon'])).km
                if dist <= radius_km:
                    p['Distance'] = f"{dist:.2f} km"
                    found.append(p)
            
            if found:
                st.subheader(f"Results within {radius_km}km")
                st.dataframe(pd.DataFrame(found)[['Name', 'Area', 'RERA', 'Distance']])
                st.map(pd.DataFrame(found).rename(columns={'Lat': 'lat', 'Lon': 'lon'}))
            else:
                st.warning("No ongoing projects found in our local database for this radius.")
        else:
            st.error("Invalid Link. Please ensure you are pasting a direct Google Maps link.")

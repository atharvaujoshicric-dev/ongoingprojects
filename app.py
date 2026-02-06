import streamlit as st
import requests
import re
import pandas as pd
from geopy.distance import geodesic
from datetime import datetime

# --- Setup ---
st.set_page_config(page_title="Pune/PCMC Project Finder", layout="wide")

def get_exact_coords(url):
    """Handles redirects for googleusercontent and short links."""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        # Follow redirects to get the actual Google Maps URL
        session = requests.Session()
        response = session.get(url, allow_redirects=True, timeout=15, headers=headers)
        final_url = response.url
        
        # Look for standard @lat,long
        at_match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", final_url)
        if at_match:
            return float(at_match.group(1)), float(at_match.group(2))
            
        # Look for !3d and !4d internal tags
        lat_m = re.search(r"!3d(-?\d+\.\d+)", final_url)
        lon_m = re.search(r"!4d(-?\d+\.\d+)", final_url)
        if lat_m and lon_m:
            return float(lat_m.group(1)), float(lat_m.group(2))
    except Exception as e:
        print(f"Error resolving link: {e}")
        return None, None
    return None, None

def scrape_completion_date(project_name):
    """Scrapes snippets for completion months/years (2024-2031)."""
    if "Unnamed" in project_name or "Complex" in project_name:
        return "Ready/Resale"
    
    try:
        # Target search specifically for Pune real estate timelines
        query = f"{project_name} Pune possession date completion"
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=5)
        
        # Find years 2024-2031 and month names
        years = re.findall(r"202[4-9]|203[0-1]", r.text)
        months = re.findall(r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*", r.text, re.I)
        
        if years:
            est_year = max(set(years), key=years.count) # Find most frequent year
            est_month = months[0].capitalize() if months else "Possession"
            return f"{est_month} {est_year}"
    except:
        pass
    return "Check Website"

def fetch_nearby_projects(lat, lon, radius_km):
    """Pulls all residential nodes from OpenStreetMap."""
    overpass_url = "http://overpass-api.de/api/interpreter"
    radius_meters = radius_km * 1000
    query = f"""
    [out:json];
    (
      node["building"="apartments"](around:{radius_meters},{lat},{lon});
      way["building"="apartments"](around:{radius_meters},{lat},{lon});
      node["building"="construction"](around:{radius_meters},{lat},{lon});
    );
    out center;
    """
    try:
        response = requests.get(overpass_url, params={'data': query}, timeout=20)
        elements = response.json().get('elements', [])
        
        projects = []
        for e in elements:
            name = e.get('tags', {}).get('name', 'Unnamed Project')
            p_lat = e.get('lat') or e.get('center', {}).get('lat')
            p_lon = e.get('lon') or e.get('center', {}).get('lon')
            
            if p_lat and p_lon:
                dist = geodesic((lat, lon), (p_lat, p_lon)).km
                projects.append({"Name": name, "Distance (km)": round(dist, 2), "lat": p_lat, "lon": p_lon})
        return projects
    except:
        return []

# --- Streamlit Interface ---
st.title("🏙️ Pune/PCMC Residential Timeline Scraper")
st.markdown("Paste your map link below to find all nearby residential projects and their estimated completion dates.")

maps_link = st.text_input("Google Maps Link:", placeholder="Paste http://googleusercontent.com... or standard maps link")
radius = st.slider("Search Radius (km)", 2, 20, 5)

if maps_link:
    with st.spinner("Resolving link and scanning Pune area..."):
        lat, lon = get_exact_coords(maps_link)
        
        if lat and lon:
            raw_data = fetch_nearby_projects(lat, lon, radius)
            
            if raw_data:
                # Remove duplicates and generic names
                df = pd.DataFrame(raw_data).drop_duplicates(subset=['Name']).sort_values("Distance (km)")
                # Filter top results to keep scraping fast
                df_top = df[df['Name'] != "Unnamed Project"].head(10)
                
                st.info(f"Scanning the web for completion dates of the top {len(df_top)} closest projects...")
                df_top['Completion Date'] = df_top['Name'].apply(scrape_completion_date)
                
                st.subheader("Residential Projects & Estimated Timelines")
                st.dataframe(df_top[['Name', 'Distance (km)', 'Completion Date']], use_container_width=True)
                st.map(df_top)
            else:
                st.warning("No projects found in this radius. Try increasing the search distance.")
        else:
            st.error("Invalid Link. Please ensure you've copied the full URL from your browser.")

import streamlit as st
import requests
import re
import pandas as pd
from geopy.distance import geodesic
from datetime import datetime

# --- Setup ---
st.set_page_config(page_title="Pune Project Estimator", layout="wide")

def get_exact_coords(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        session = requests.Session()
        response = session.get(url, allow_redirects=True, timeout=10, headers=headers)
        final_url = response.url
        at_match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", final_url)
        if at_match: return float(at_match.group(1)), float(at_match.group(2))
        lat_m = re.search(r"!3d(-?\d+\.\d+)", final_url)
        lon_m = re.search(r"!4d(-?\d+\.\d+)", final_url)
        if lat_m and lon_m: return float(lat_m.group(1)), float(lat_m.group(2))
    except: return None, None
    return None, None

def estimate_completion(project_name):
    """
    Scrapes search snippets to find dates like 'Dec 2025' or 'June 2027'.
    """
    if "Residential" in project_name or "Complex" in project_name:
        return "Ready/Unknown"
    
    try:
        # Searching specifically for Pune real estate timelines
        search_url = f"https://www.google.com/search?q={project_name}+pune+completion+date+possession"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(search_url, headers=headers, timeout=5)
        text = r.text
        
        # Regex to find Year (2024-2030) and Months
        years = re.findall(r"202[4-9]|2030", text)
        months = re.findall(r"Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December", text, re.I)
        
        if years:
            est_year = max(set(years), key=years.count) # Mode of years found
            est_month = months[0].capitalize() if months else "Possession"
            return f"{est_month} {est_year}"
    except:
        pass
    return "Check Website"

def fetch_projects(lat, lon, radius_km):
    overpass_url = "http://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:25];
    (
      node["building"="apartments"](around:{radius_km*1000},{lat},{lon});
      way["building"="apartments"](around:{radius_km*1000},{lat},{lon});
      node["building"="construction"](around:{radius_km*1000},{lat},{lon});
      way["building"="construction"](around:{radius_km*1000},{lat},{lon});
    );
    out center;
    """
    r = requests.get(overpass_url, params={'data': query})
    data = r.json()
    
    results = []
    for e in data.get('elements', []):
        tags = e.get('tags', {})
        name = tags.get('name') or "Unnamed Site"
        p_lat = e.get('lat') or e.get('center', {}).get('lat')
        p_lon = e.get('lon') or e.get('center', {}).get('lon')
        
        if p_lat and p_lon:
            dist = geodesic((lat, lon), (p_lat, p_lon)).km
            results.append({"Name": name, "Distance": round(dist, 2), "lat": p_lat, "lon": p_lon})
    return results

# --- UI ---
st.title("🏗️ Pune/PCMC Project Timeline Tracker")
link = st.text_input("Paste Google Maps Link:")
radius = st.slider("Radius (km)", 2, 20, 5)

if link:
    lat, lon = get_exact_coords(link)
    if lat and lon:
        st.success(f"Pinpointed Location: {lat}, {lon}")
        data = fetch_projects(lat, lon, radius)
        
        if data:
            df = pd.DataFrame(data).drop_duplicates(subset=['Name']).sort_values("Distance")
            df = df[df['Name'] != "Unnamed Site"].head(10) # Limit to top 10 for speed
            
            with st.spinner("Scraping completion dates for nearby projects..."):
                df['Estimated Completion'] = df['Name'].apply(estimate_completion)
            
            st.table(df[['Name', 'Distance', 'Estimated Completion']])
            st.map(df)
        else:
            st.warning("No projects found.")

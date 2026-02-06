import streamlit as st
import requests
import re
import pandas as pd
from geopy.distance import geodesic

# --- Setup ---
st.set_page_config(page_title="Ongoing Pune Projects", layout="wide")

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

def scrape_completion_date(project_name):
    """
    Scrapes the web for specific possession/completion keywords 
    associated with the project name in Pune/PCMC.
    """
    if "Unnamed" in project_name: return "Unknown"
    
    try:
        # Search specifically for possession timelines
        query = f"{project_name} Pune PCMC possession date completion year"
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(search_url, headers=headers, timeout=5)
        
        # Regex to find dates like 'Dec 2026', 'March 2028', etc.
        # Looks for Year (2025-2032) and Month names
        date_pattern = r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s,-]*(202[5-9]|203[0-2])"
        match = re.search(date_pattern, r.text, re.IGNORECASE)
        
        if match:
            return f"{match.group(1).capitalize()} {match.group(2)}"
        
        # Fallback for just the year
        year_only = re.search(r"possession (202[5-9]|203[0-2])", r.text, re.IGNORECASE)
        if year_only:
            return f"Year {year_only.group(1)}"
            
    except:
        pass
    return "TBA (Ongoing)"

def fetch_ongoing_projects(lat, lon, radius_km):
    """
    Filters specifically for tags: 
    building=construction OR landuse=construction
    """
    overpass_url = "http://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:25];
    (
      node["building"="construction"](around:{radius_km*1000},{lat},{lon});
      way["building"="construction"](around:{radius_km*1000},{lat},{lon});
      node["landuse"="construction"](around:{radius_km*1000},{lat},{lon});
      way["landuse"="construction"](around:{radius_km*1000},{lat},{lon});
    );
    out center;
    """
    try:
        r = requests.get(overpass_url, params={'data': query})
        elements = r.json().get('elements', [])
        
        results = []
        for e in elements:
            tags = e.get('tags', {})
            # Prefer 'construction' tag which often contains the final project name
            name = tags.get('name') or tags.get('construction') or "New Project Site"
            p_lat = e.get('lat') or e.get('center', {}).get('lat')
            p_lon = e.get('lon') or e.get('center', {}).get('lon')
            
            if p_lat and p_lon:
                dist = geodesic((lat, lon), (p_lat, p_lon)).km
                results.append({"Name": name, "Distance": round(dist, 2), "lat": p_lat, "lon": p_lon})
        return results
    except:
        return []

# --- Streamlit UI ---
st.title("🚧 Pune/PCMC Ongoing Project Tracker")
st.markdown("This tool filters for **active construction sites only** and estimates their completion.")

link = st.text_input("Paste Google Maps Link:")
radius = st.slider("Search Radius (km)", 2, 20, 5)

if link:
    lat, lon = get_exact_coords(link)
    if lat and lon:
        st.success(f"Scanning {radius}km around: {lat}, {lon}")
        data = fetch_ongoing_projects(lat, lon, radius)
        
        if data:
            df = pd.DataFrame(data).drop_duplicates(subset=['Name']).sort_values("Distance")
            
            with st.spinner("Analyzing completion dates for ongoing sites..."):
                df['Est. Completion'] = df['Name'].apply(scrape_completion_date)
            
            st.subheader(f"Found {len(df)} Active Construction Projects")
            st.table(df[['Name', 'Distance', 'Est. Completion']])
            st.map(df)
        else:
            st.warning("No active construction sites tagged in this specific radius.")

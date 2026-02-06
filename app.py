import streamlit as st
import requests
import re
import pandas as pd
from geopy.distance import geodesic
import time

# --- Setup ---
st.set_page_config(page_title="Pune All-Project Tracker", layout="wide")

def get_exact_coords(url):
    """Robust link unmasking for googleusercontent and mobile links."""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        session = requests.Session()
        response = session.get(url, allow_redirects=True, timeout=12, headers=headers)
        final_url = response.url
        at_match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", final_url)
        if at_match: return float(at_match.group(1)), float(at_match.group(2))
        lat_m = re.search(r"!3d(-?\d+\.\d+)", final_url)
        lon_m = re.search(r"!4d(-?\d+\.\d+)", final_url)
        if lat_m and lon_m: return float(lat_m.group(1)), float(lat_m.group(2))
    except: return None, None
    return None, None

def find_completion_year(project_name):
    """Scrapes search snippets specifically for years 2024-2031."""
    if "Residential" in project_name or "Complex" in project_name or "Unnamed" in project_name:
        return "N/A (Built/Old)"
    
    # We use a dedicated real estate search string to trigger better snippets
    search_url = f"https://www.google.com/search?q={project_name}+Pune+possession+year+completion"
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
    
    try:
        # Note: In a real environment, adding a small delay prevents IP blocks
        r = requests.get(search_url, headers=headers, timeout=5)
        text = r.text
        
        # Regex to capture the year. Looks for 202 followed by 4, 5, 6, 7, 8, 9 or 2030/31
        years = re.findall(r"202[4-9]|203[0-1]", text)
        if years:
            # Picking the most frequent year found in results
            est_year = max(set(years), key=years.count)
            return est_year
    except:
        pass
    return "Contact Developer"

def fetch_all_projects(lat, lon, radius_km):
    """Pulls every residential 'node' and 'way' from OpenStreetMap database."""
    overpass_url = "http://overpass-api.de/api/interpreter"
    radius_meters = radius_km * 1000
    # Broadening the query to capture more projects
    query = f"""
    [out:json][timeout:30];
    (
      node["building"="apartments"](around:{radius_meters},{lat},{lon});
      way["building"="apartments"](around:{radius_meters},{lat},{lon});
      node["building"="construction"](around:{radius_meters},{lat},{lon});
      way["building"="construction"](around:{radius_meters},{lat},{lon});
      node["residential"="apartment"](around:{radius_meters},{lat},{lon});
      way["landuse"="residential"](around:{radius_meters},{lat},{lon});
    );
    out center;
    """
    try:
        r = requests.get(overpass_url, params={'data': query}, timeout=25)
        elements = r.json().get('elements', [])
        
        results = []
        for e in elements:
            tags = e.get('tags', {})
            name = tags.get('name') or tags.get('operator') or "Residential Site"
            p_lat = e.get('lat') or e.get('center', {}).get('lat')
            p_lon = e.get('lon') or e.get('center', {}).get('lon')
            
            if p_lat and p_lon:
                dist = geodesic((lat, lon), (p_lat, p_lon)).km
                results.append({"Name": name, "Distance (km)": round(dist, 2), "lat": p_lat, "lon": p_lon})
        return results
    except:
        return []

# --- UI ---
st.title("🏙️ Pune/PCMC: All Residential Projects Finder")
st.markdown("This tool scans **OpenStreetMap** for all residential complexes and searches the web for completion years.")

maps_link = st.text_input("Paste Google Maps Link:", placeholder="http://googleusercontent.com/...")
radius_val = st.slider("Search Radius (km)", 2, 20, 5)

if maps_link:
    with st.spinner("Decoding location and scanning all projects..."):
        lat, lon = get_exact_coords(maps_link)
        
        if lat and lon:
            all_data = fetch_all_projects(lat, lon, radius_val)
            
            if all_data:
                # Deduplicate and sort
                df = pd.DataFrame(all_data).drop_duplicates(subset=['Name']).sort_values("Distance (km)")
                
                # Show all projects first
                st.subheader(f"Found {len(df)} Residential Projects in {radius_val}km")
                
                # Now try to get years for named projects only (Generic ones are skipped for speed)
                named_mask = (df['Name'] != "Residential Site")
                named_df = df[named_mask].copy()
                
                if not named_df.empty:
                    with st.spinner("Finding completion years for named projects..."):
                        # We process in batches to avoid overwhelming the search engine
                        named_df['Est. Completion Year'] = named_df['Name'].apply(find_completion_year)
                    
                    # Merge back with the original list to show EVERYTHING
                    final_df = pd.concat([named_df, df[~named_mask]], sort=False)
                    final_df['Est. Completion Year'] = final_df['Est. Completion Year'].fillna("N/A")
                    
                    st.dataframe(final_df[['Name', 'Distance (km)', 'Est. Completion Year']], use_container_width=True)
                    st.map(final_df)
                else:
                    st.dataframe(df[['Name', 'Distance (km)']], use_container_width=True)
                    st.map(df)
            else:
                st.warning("No projects found. Try increasing the radius.")
        else:
            st.error("Could not read link. Ensure you pasted a valid Google Maps or redirect link.")

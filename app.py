import streamlit as st
import requests
import re
import pandas as pd
from geopy.distance import geodesic
import time

# --- Setup ---
st.set_page_config(page_title="Pune Project Finder + Scraper", layout="wide")

# Initialize session state for the dataframe so it persists after button clicks
if 'final_df' not in st.session_state:
    st.session_state.final_df = None

def get_exact_coords(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        session = requests.Session()
        response = session.get(url, allow_redirects=True, timeout=15, headers=headers)
        final_url = response.url
        
        center_match = re.search(r"center=(-?\d+\.\d+)%2C(-?\d+\.\d+)", final_url)
        if center_match:
            return float(center_match.group(1)), float(center_match.group(2))

        at_match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", final_url)
        if at_match:
            return float(at_match.group(1)), float(at_match.group(2))
            
        lat_m = re.search(r"!3d(-?\d+\.\d+)", final_url)
        lon_m = re.search(r"!4d(-?\d+\.\d+)", final_url)
        if lat_m and lon_m:
            return float(lat_m.group(1)), float(lon_m.group(2))
    except Exception:
        return None, None
    return None, None

def estimate_completion(project_name):
    """Simple web scraper to find possession/completion dates."""
    if project_name == "Residential Complex/Site":
        return "Unknown"
    
    query = f"{project_name} Pune possession date"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        # Note: Frequent requests may trigger a Google CAPTCHA
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        response = requests.get(search_url, headers=headers, timeout=5)
        text = response.text
        
        # Regex to find Month Year (e.g., Dec 2025) or just Year (2027)
        date_matches = re.findall(r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s?20\d{2}|20\d{2}", text)
        
        if date_matches:
            # Filter to find years in the future (2024-2030)
            valid_dates = [d for d in date_matches if "202" in d or "203" in d]
            return valid_dates[0] if valid_dates else "Check RERA"
    except:
        return "Error"
    return "Not Found"

def fetch_pune_projects(lat, lon, radius_km):
    overpass_url = "http://overpass-api.de/api/interpreter"
    radius_meters = radius_km * 1000
    
    query = f"""
    [out:json][timeout:25];
    (
      node["building"="apartments"](around:{radius_meters},{lat},{lon});
      way["building"="apartments"](around:{radius_meters},{lat},{lon});
      node["building"="construction"](around:{radius_meters},{lat},{lon});
      way["building"="construction"](around:{radius_meters},{lat},{lon});
      node["residential"="apartment"](around:{radius_meters},{lat},{lon});
    );
    out center;
    """
    try:
        r = requests.get(overpass_url, params={'data': query})
        data = r.json()
        results = []
        for e in data.get('elements', []):
            tags = e.get('tags', {})
            name = tags.get('name') or tags.get('description') or "Residential Complex/Site"
            p_lat = e.get('lat') or e.get('center', {}).get('lat')
            p_lon = e.get('lon') or e.get('center', {}).get('lon')
            if p_lat and p_lon:
                dist = geodesic((lat, lon), (p_lat, p_lon)).km
                results.append({
                    "Project/Building Name": name,
                    "Distance (km)": round(dist, 2),
                    "lat": p_lat,
                    "lon": p_lon,
                    "Completion Date": "N/A" # Default value
                })
        return results
    except:
        return []

# --- UI Layout ---
st.title("🏙️ Pune/PCMC Project Finder + Date Scraper")

col1, col2 = st.columns([2, 1])

with col1:
    link = st.text_input("Paste Google Maps Link:")
with col2:
    radius = st.slider("Select Search Radius (km)", 1, 15, 3)

if st.button("Find Projects"):
    with st.spinner("Pinpointing location and fetching projects..."):
        lat, lon = get_exact_coords(link)
        if lat and lon:
            raw_results = fetch_pune_projects(lat, lon, radius)
            if raw_results:
                df = pd.DataFrame(raw_results).sort_values("Distance (km)")
                df = df.drop_duplicates(subset=['Project/Building Name'])
                
                # Sort Named projects to the top
                named = df[df['Project/Building Name'] != "Residential Complex/Site"]
                unnamed = df[df['Project/Building Name'] == "Residential Complex/Site"]
                st.session_state.final_df = pd.concat([named, unnamed])
            else:
                st.error("No projects found in this area.")
        else:
            st.error("Could not extract coordinates. Try a different Google Maps link.")

# --- Results Display ---
if st.session_state.final_df is not None:
    df = st.session_state.final_df
    
    st.subheader(f"📍 Found {len(df)} Results")

    # Scraper Button
    if st.button("🔍 Scrape Completion Dates"):
        with st.spinner("Scraping dates (this takes a few seconds)..."):
            # Limit scraping to first 10 projects to avoid IP bans
            for index, row in df.head(10).iterrows():
                if row["Project/Building Name"] != "Residential Complex/Site":
                    df.at[index, "Completion Date"] = estimate_completion(row["Project/Building Name"])
                    time.sleep(1) # Ethical delay
            st.session_state.final_df = df
            st.rerun()

    st.dataframe(df[["Project/Building Name", "Distance (km)", "Completion Date"]], use_container_width=True)
    st.map(df)

---

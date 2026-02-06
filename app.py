import streamlit as st
import requests
import re
import pandas as pd
from geopy.distance import geodesic
import time

# --- Setup ---
st.set_page_config(page_title="Pune Project Finder", layout="wide")

# Initialize session state for persistence
if 'final_df' not in st.session_state:
    st.session_state.final_df = None

# --- Helper Functions ---

@st.cache_data
def convert_df_to_csv(df):
    """Caches the conversion to prevent re-computation on every rerun."""
    return df.to_csv(index=False).encode('utf-8')

def get_exact_coords(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        session = requests.Session()
        response = session.get(url, allow_redirects=True, timeout=15, headers=headers)
        final_url = response.url
        
        # Various patterns for Google Maps URLs
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
    """Free scraper: Extracts dates from Google search snippets."""
    if project_name == "Residential Complex/Site":
        return "Unknown"
    
    query = f"{project_name} Pune possession date completion"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        response = requests.get(search_url, headers=headers, timeout=5)
        text = response.text
        
        # Pattern to find 'Month 20XX' or just '20XX'
        date_matches = re.findall(r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s?20\d{2}|20\d{2}", text)
        
        if date_matches:
            # Prioritize future dates
            future_dates = [d for d in date_matches if "202" in d or "203" in d]
            return future_dates[0] if future_dates else date_matches[0]
    except:
        return "Error"
    return "TBD"

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
    );
    out center;
    """
    try:
        r = requests.get(overpass_url, params={'data': query})
        data = r.json()
        results = []
        for e in data.get('elements', []):
            tags = e.get('tags', {})
            name = tags.get('name') or "Residential Complex/Site"
            p_lat = e.get('lat') or e.get('center', {}).get('lat')
            p_lon = e.get('lon') or e.get('center', {}).get('lon')
            if p_lat and p_lon:
                dist = geodesic((lat, lon), (p_lat, p_lon)).km
                results.append({
                    "Project/Building Name": name,
                    "Distance (km)": round(dist, 2),
                    "lat": p_lat, "lon": p_lon,
                    "Completion Date": "N/A"
                })
        return results
    except:
        return []

# --- UI Interface ---
st.title("🏙️ Pune Project Finder & Data Exporter")

with st.sidebar:
    st.header("Search Parameters")
    link = st.text_input("Google Maps Link:")
    radius = st.slider("Radius (km)", 1, 15, 3)
    find_btn = st.button("🚀 Find Nearby Projects")

# Logic for finding projects
if find_btn:
    with st.spinner("Analyzing location..."):
        lat, lon = get_exact_coords(link)
        if lat and lon:
            raw_results = fetch_pune_projects(lat, lon, radius)
            if raw_results:
                df = pd.DataFrame(raw_results).sort_values("Distance (km)")
                df = df.drop_duplicates(subset=['Project/Building Name'])
                st.session_state.final_df = df
            else:
                st.warning("No project data found for this specific area.")
        else:
            st.error("Could not parse coordinates. Please provide a full Google Maps URL.")

# Logic for displaying and actions
if st.session_state.final_df is not None:
    df = st.session_state.final_df
    
    st.subheader(f"Results: {len(df)} projects found")

    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 Scrape Completion Dates"):
            with st.spinner("Gathering dates (takes ~15 seconds)..."):
                # Scraping only named projects to avoid spamming
                for idx, row in df.iterrows():
                    if row["Project/Building Name"] != "Residential Complex/Site":
                        df.at[idx, "Completion Date"] = estimate_completion(row["Project/Building Name"])
                        time.sleep(1.2) # Essential delay for free scraping
                st.session_state.final_df = df
                st.rerun()

    with col2:
        # --- DOWNLOAD FEATURE ---
        csv_data = convert_df_to_csv(df)
        st.download_button(
            label="📥 Download Data as CSV",
            data=csv_data,
            file_name=f"pune_projects_{int(time.time())}.csv",
            mime="text/csv",
        )

    st.dataframe(df[["Project/Building Name", "Distance (km)", "Completion Date"]], use_container_width=True)
    st.map(df)

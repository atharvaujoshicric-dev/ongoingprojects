import streamlit as st
import requests
import re
import pandas as pd
from geopy.distance import geodesic

# --- Setup ---
st.set_page_config(page_title="High-Accuracy Project Finder", layout="wide")

def get_exact_coords(url):
    """
    Ultra-robust coordinate extraction. 
    Follows redirects and checks multiple hidden patterns.
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        session = requests.Session()
        response = session.get(url, allow_redirects=True, timeout=15, headers=headers)
        final_url = response.url
        
        # Pattern 1: Look for the 'center' parameter in the URL (most accurate for area views)
        center_match = re.search(r"center=(-?\d+\.\d+)%2C(-?\d+\.\d+)", final_url)
        if center_match:
            return float(center_match.group(1)), float(center_match.group(2))

        # Pattern 2: Standard @lat,long
        at_match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", final_url)
        if at_match:
            return float(at_match.group(1)), float(at_match.group(2))
            
        # Pattern 3: Internal !3d !4d tags
        lat_m = re.search(r"!3d(-?\d+\.\d+)", final_url)
        lon_m = re.search(r"!4d(-?\d+\.\d+)", final_url)
        if lat_m and lon_m:
            return float(lat_m.group(1)), float(lon_m.group(2))
            
    except Exception:
        return None, None
    return None, None

def fetch_pune_projects(lat, lon, radius_km):
    """Pulls live residential data from OpenStreetMap for Pune/PCMC."""
    overpass_url = "http://overpass-api.de/api/interpreter"
    radius_meters = radius_km * 1000
    
    # Query targets: Apartments, Residential zones, and Construction sites
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
            
            # Get coords based on element type
            p_lat = e.get('lat') or e.get('center', {}).get('lat')
            p_lon = e.get('lon') or e.get('center', {}).get('lon')
            
            if p_lat and p_lon:
                # Calculate precise distance
                dist = geodesic((lat, lon), (p_lat, p_lon)).km
                results.append({
                    "Project/Building Name": name,
                    "Distance (km)": round(dist, 2),
                    "lat": p_lat,
                    "lon": p_lon
                })
        return results
    except:
        return []

# --- UI ---
st.title("🏙️ Accurate Pune/PCMC Project Finder")
st.markdown("Retrieves all residential developments within your chosen radius.")

link = st.text_input("Paste Google Maps Link:")
radius = st.slider("Select Search Radius (km)", 2, 20, 5)

if link:
    with st.spinner("Calculating exact location..."):
        lat, lon = get_exact_coords(link)
        
        if lat and lon:
            st.success(f"Pinpointed Location: {lat}, {lon}")
            
            raw_results = fetch_pune_projects(lat, lon, radius)
            
            if raw_results:
                # Clean up: Sort by distance and remove generic duplicates
                df = pd.DataFrame(raw_results).sort_values("Distance (km)")
                df = df.drop_duplicates(subset=['Project/Building Name'])
                
                # Filter out generic 'Unnamed' to show high-quality results first
                named_projects = df[df['Project/Building Name'] != "Residential Complex/Site"]
                unnamed_projects = df[df['Project/Building Name'] == "Residential Complex/Site"]
                final_df = pd.concat([named_projects, unnamed_projects])

                st.subheader(f"Found {len(final_df)} Results within {radius}km")
                st.dataframe(final_df[["Project/Building Name", "Distance (km)"]], use_container_width=True)
                st.map(final_df)
            else:
                st.warning("No residential sites found in this specific radius.")
        else:
            st.error("Invalid Link. Please ensure you've copied the full link from Google Maps.")

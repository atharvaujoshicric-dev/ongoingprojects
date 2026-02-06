from bs4 import BeautifulSoup
import time

def estimate_completion(project_name):
    """
    Attempts to find completion/possession date via a search query.
    Note: Real-estate sites have high bot protection; this is a simplified approach.
    """
    if project_name == "Residential Complex/Site":
        return "Unknown"

    query = f"{project_name} Pune possession date completion year"
    headers = {'User-Agent': 'Mozilla/5.0'} # Basic spoofing
    
    try:
        # Using a search proxy or direct search (Note: Google may rate-limit you)
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        response = requests.get(search_url, headers=headers, timeout=5)
        
        # Look for date patterns like "Dec 2025" or "2024" in the text
        text = response.text
        date_pattern = re.findall(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s\d{4}|\d{4}", text)
        
        if date_pattern:
            # Return the first year/date found that looks like a future or recent date
            return date_pattern[0] if isinstance(date_pattern[0], str) else "Check Online"
    except:
        return "N/A"
    
    return "TBD"

# --- Inside your UI logic after creating final_df ---
if st.button("🔍 Fetch Completion Dates (Takes longer)"):
    with st.spinner("Scraping data for projects..."):
        # We only scrape the top 10 named projects to avoid being blocked/slow performance
        final_df['Completion Date'] = final_df['Project/Building Name'].head(10).apply(estimate_completion)
        st.dataframe(final_df[["Project/Building Name", "Distance (km)", "Completion Date"]])

import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def scrape_nearby_projects(lat_long_query, radius_km=5):
    # Setup Selenium
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless') # Uncomment to run without opening window
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # Keshav Nagar Search Query
    search_query = f"ongoing residential projects within {radius_km}km of {lat_long_query}"
    url = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"
    
    driver.get(url)
    time.sleep(5)  # Let results load

    projects = []
    
    # Basic logic to find result cards
    # Note: Google Maps classes change often; these are common selectors
    results = driver.find_elements(By.CLASS_NAME, "hfpxzc") 
    
    for res in results[:15]: # Limit to top 15 for quick check
        try:
            name = res.get_attribute("aria-label")
            res.click()
            time.sleep(2)
            projects.append({"Project Name": name})
        except Exception as e:
            continue
            
    driver.quit()
    return pd.DataFrame(projects)

# Use the Keshav Nagar/Mundhwa coordinates
location = "18.5415,73.9392" 
df = scrape_nearby_projects(location)
print(df)

import os
import json
import time
from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)

# ------------------- Selenium Setup -------------------
def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=chrome_options
    )
    return driver

# ------------------- Scraper Functions -------------------
def login_linkedin(driver, username, password):
    driver.get("https://www.linkedin.com/uas/login")
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "session_key-login")))
    driver.find_element(By.ID, "session_key-login").send_keys(username)
    driver.find_element(By.ID, "session_password-login").send_keys(password + Keys.RETURN)
    time.sleep(3)

def search_jobs(driver, keyword, location):
    driver.get("https://www.linkedin.com/jobs/?trk=nav_responsive_sub_nav_jobs")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "keyword-search-box")))
    
    # enter keyword
    driver.find_element(By.ID, "keyword-search-box").send_keys(keyword)
    # clear location
    loc_box = driver.find_element(By.ID, "location-search-box")
    loc_box.clear()
    loc_box.send_keys(location + Keys.RETURN)
    time.sleep(3)

def get_job_links(driver, limit=5):
    """Get job post links from search results (limited)"""
    links = []
    try:
        jobs = driver.find_elements(By.CSS_SELECTOR, "a.job-title-link")[:limit]
        for job in jobs:
            links.append(job.get_attribute("href"))
    except:
        pass
    return links

def scrape_job(driver, job_url):
    driver.get(job_url)
    time.sleep(1.5)
    data = {}
    # job title
    try: data['job_title'] = driver.find_element(By.CSS_SELECTOR, "h1.title").text
    except: data['job_title'] = ""
    # company
    try: data['company'] = driver.find_element(By.CSS_SELECTOR, "span.company").text
    except: data['company'] = ""
    # location
    try: data['location'] = driver.find_element(By.CSS_SELECTOR, "h3.location").text
    except: data['location'] = ""
    # description
    try: data['description'] = driver.find_element(By.CSS_SELECTOR, "div.summary").text
    except: data['description'] = ""
    return data

# ------------------- Flask API -------------------
@app.route("/search_jobs", methods=["POST"])
def search_jobs_api():
    content = request.json
    username = content.get("username")
    password = content.get("password")
    keyword = content.get("keyword")
    location = content.get("location")

    if not username or not password or not keyword or not location:
        return jsonify({"error": "username, password, keyword, location required"}), 400

    driver = init_driver()
    try:
        login_linkedin(driver, username, password)
        search_jobs(driver, keyword, location)
        links = get_job_links(driver)
        results = [scrape_job(driver, link) for link in links]
    finally:
        driver.quit()
    return jsonify(results)

# ------------------- Run -------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

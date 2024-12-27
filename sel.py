import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from pymongo import MongoClient
import requests
from flask import Flask, render_template, jsonify


client = MongoClient('mongodb://localhost:27017')
db = client['stir'] 
collection = db['happening'] 

def get_driver():
    options = webdriver.ChromeOptions()
    options.headless = False
    driver = webdriver.Chrome(options=options)
    return driver

def login_to_twitter(driver, username, password):
    driver.get("https://twitter.com/login")
    time.sleep(5)

    wait = WebDriverWait(driver, 20)
    username_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@autocomplete='username']")))
    username_input.send_keys(username)
    username_input.send_keys(Keys.RETURN)
    time.sleep(5)
    
    password_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@autocomplete='current-password']")))
    password_input.send_keys(password)
    password_input.send_keys(Keys.RETURN)
    time.sleep(5)

def click_explore_button(driver):
    try:
        not_now_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Not now']"))
        )
        not_now_button.click()
    except TimeoutException:
        pass

    try:
        explore_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div/div[2]/header/div/div/div/div[1]/div[2]/nav/a[2]"))
        )
        explore_button.click()
        time.sleep(5)
    except TimeoutException:
        print("Explore button not found.")

def get_trending_topics(driver):
    time.sleep(10)
    trends = []
    xpaths = [
        '/html/body/div[1]/div/div/div[2]/main/div/div/div/div/div/div[3]/div/section/div/div/div[3]/div/div/div/div/div[2]',
        '/html/body/div[1]/div/div/div[2]/main/div/div/div/div/div/div[3]/div/section/div/div/div[4]/div/div/div/div/div[2]',
        '//*[@id="id__34dotb6j6sz"]/div[2]',
        '/html/body/div[1]/div/div/div[2]/main/div/div/div/div/div/div[3]/div/section/div/div/div[6]/div/div/div/div/div[2]',
        '/html/body/div[1]/div/div/div[2]/main/div/div/div/div/div/div[3]/div/section/div/div/div[7]/div/div/div/div/div[2]'
    ]

    for xpath in xpaths:
        try:
           element = driver.find_element(By.XPATH, xpath)
           trends.append(element.text)
        except NoSuchElementException as e:
           print(f"Error finding element for XPath {xpath}: {e}")

    return trends

def save_to_mongodb(trends, ip):
    unique_id = str(datetime.now().timestamp())
    data = {
        "_id": unique_id,
        "trend1": trends[0] if trends else None,
        "trend2": trends[1] if len(trends) > 1 else None,
        "trend3": trends[2] if len(trends) > 2 else None,
        "trend4": trends[3] if len(trends) > 3 else None,
        "trend5": trends[4] if len(trends) > 4 else None,
        "datetime": datetime.now(),
        "ip_address": ip
    }
    collection.insert_one(data)
    return data

def main(username, password):
    driver = get_driver()
    try:
        login_to_twitter(driver, username, password)
        click_explore_button(driver)
        trends = get_trending_topics(driver)
        ip = requests.get('https://api.ipify.org').text
        result = save_to_mongodb(trends, ip)
    finally:
        driver.quit()
    return result

app = Flask(__name__, template_folder='templates')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run-script')
def run_script():
    TWITTER_USERNAME = "prakash55225497"
    TWITTER_PASSWORD = "fastasaflash"
    result = main(TWITTER_USERNAME, TWITTER_PASSWORD)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)

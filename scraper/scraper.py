"""
scrapes from dsa website to a csv current zip codes associated with a chapter
cuz this is for some reason (???) the best way to determine constituency
"""

import csv
import json
import os
import random
import sys
import time
import logging
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.common.by import By

# maeve andersen
# 27 august 2023

# if you don't know exactly what this is doing and the consequences, you
# should really not be using this script! there is an inherent risk of
# overloading the API. do not adjust any sleep settings except to increase
# them! i have intentionally not included the proxy list, consider it a
# really basic "means test" of sorts for my conscience to ensure no one is
# running this out of the box.

# this will take several days to scrape depending on RNG, i suggest running it
# on an always-up server or VM.


logging.basicConfig(level=logging.WARNING, format="%(asctime)s : %(levelname)s : %(message)s")


def configure_browser_proxy(proxy: str):
    rand = random.randint(2, 5)
    logging.info("Waiting random time: %s", rand)
    time.sleep(rand)

    proxy_url = f"http://{proxy['host']}:{proxy['port']}"
    logging.info("Using proxy: %s", proxy_url)
    webdriver.DesiredCapabilities.CHROME["proxy"] = {
        "httpProxy": proxy_url,
        "ftpProxy": proxy_url,
        "sslProxy": proxy_url,
        "proxyType": "MANUAL",
    }
    # this sucks but prevents overload
    return rand


def scrape_zip_code(zip_code: str, proxy: dict) -> (str, str):
    """Checks a zip code to see what chapter it is part of, via provided web proxy dict"""
    url = f"view-source:https://chapters.dsausa.org/api/search?zip={zip_code}"
    logging.debug("API URL: %s", url)

    rand = configure_browser_proxy(proxy)
    driver.get(url)

    # ensure no server error
    i = 0
    while ("Internal Server Error" in driver.page_source) or ("Rate limit exceeded" in driver.page_source) or ("502: Bad gateway" in driver.page_source):
        i += rand

        rand = configure_browser_proxy(random.choice(proxy_list))
        driver.get(url)

        if i > 600:
            logging.critical("API timed out!")
            driver.quit()
            sys.exit("Data has been scraped and written.")

    content = driver.find_element(By.CLASS_NAME, "line-content").text

    try:
        data = json.loads(content)
        chapter_name = data.get("data", {}).get("chapter", "Chapter not found.")
    except json.JSONDecodeError:
        chapter_name = "Chapter not found."

    return zip_code, chapter_name


# load proxies
proxy_list = []
os.chdir(os.path.dirname(os.path.abspath(__file__)))
with open("proxy_list.csv", "r", encoding="utf-8") as proxy_csv:
    reader = csv.DictReader(proxy_csv)
    for row in reader:
        proxy_list.append(row)

# my laziness knows no bounds
all_zip_codes = [str(i).zfill(5) for i in range(501, 99951)]

# webdriver
driver = webdriver.Chrome()

# create the .csv
csv_path = os.path.join(os.path.split(os.path.dirname(__file__))[0], "chapter_zips.csv")
logging.info("Opening file at: %s", csv_path)
with open(csv_path, mode="w", newline="", encoding="UTF-8") as csvfile:
    fieldnames = ["zip", "chapter"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
    writer.writeheader()

    for iter_zip_code in tqdm(all_zip_codes, unit="zipcode", leave=False):
        logging.info("Checking chapter assignment of: %s", iter_zip_code)
        random_proxy = random.choice(proxy_list)
        scraped_zip, scraped_chapter = scrape_zip_code(iter_zip_code, random_proxy)
        if scraped_chapter != "Chapter not found.":
            writer.writerow({"zip": scraped_zip, "chapter": scraped_chapter})
            logging.info("%s assigned to: %s", iter_zip_code, scraped_chapter)
        else:
            logging.warning("%s is not assigned to a chapter", iter_zip_code)

driver.quit()
sys.exit("Data has been scraped and written.")

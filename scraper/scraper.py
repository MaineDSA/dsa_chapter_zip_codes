"""
scrapes from dsa website to a csv current zip codes associated with a chapter
cuz this is for some reason (???) the best way to determine constituency
"""

import csv
import json
import logging
import os
import random
import sys
import time

import zipcodes
from selenium import webdriver
from selenium.webdriver.common.by import By
from tqdm import tqdm


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


def configure_browser_proxy(proxy: dict) -> int:
    """wait a random amount of time, then set up chrome with the provided proxy"""
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


def scrape_chapter_from_zip_code(zip_code: str) -> str:
    """Checks a zip code to see what chapter it is part of, via provided web proxy dict"""
    logging.info("Checking chapter assignment of: %s", zip_code)
    url = f"view-source:https://chapters.dsausa.org/api/search?zip={zip_code}"
    logging.debug("API URL: %s", url)

    rand = configure_browser_proxy(random.choice(proxy_list))
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
        return data.get("data", {}).get("chapter", "Chapter not found.")
    except json.JSONDecodeError:
        logging.warning("JSONDecodeError: No valid JSON in content: %s", content)
        return "Chapter not found."

def get_all_zip_codes() -> list[str]:
    """Get all zip codes from the zipcodes library"""
    return [zip_data["zip_code"] for zip_data in zipcodes.list_all()]


def main():
    """Create test dataset for DSA membership list"""
    output_csv_path = os.path.join(os.path.split(os.path.dirname(__file__))[0], "chapter_zips.csv")
    logging.info("Opening file at: %s", output_csv_path)
    with open(output_csv_path, mode="w", newline="", encoding="UTF-8") as output_csv_file:
        writer = csv.DictWriter(output_csv_file, fieldnames=["zip", "chapter"], quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for iter_zip_code in tqdm(get_all_zip_codes(), unit="zipcode", leave=False):
            scraped_chapter = scrape_chapter_from_zip_code(iter_zip_code)
            if scraped_chapter != "Chapter not found.":
                writer.writerow({"zip": iter_zip_code, "chapter": scraped_chapter})
                logging.info("%s assigned to: %s", iter_zip_code, scraped_chapter)
            else:
                logging.info("%s is not assigned to a chapter", iter_zip_code)

    driver.quit()
    logging.info("Data has been scraped and written.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s : %(levelname)s : %(message)s")
    driver = webdriver.Chrome()
    with open(os.path.join(os.path.dirname(__file__), "proxy_list.csv"), "r", encoding="utf-8") as proxy_csv:
        proxy_list = list(csv.DictReader(proxy_csv))
    main()

"""
Scrape list of chapter zip code assignments from national DSA website to a csv.

Cuz this is for some reason (???) the best way to determine constituency.
"""

import csv
import json
import logging
import random
import sys
import time
from pathlib import Path

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


def configure_browser_proxy(proxy: dict) -> None:
    """Wait a random amount of time, then set up chrome with the provided proxy."""
    rand = random.randint(1, 5)
    logger.info("Waiting random time: %s", rand)
    time.sleep(rand)

    proxy_url = f"{proxy['host']}:{proxy['port']}"
    logger.info("Using proxy: %s", proxy_url)

    webdriver.DesiredCapabilities.CHROME["proxy"] = {
        "httpProxy": f"http://{proxy_url}",
        "ftpProxy": f"ftp://{proxy_url}",
        "sslProxy": f"https://{proxy_url}",
        "proxyType": "MANUAL",
    }


def scrape_chapter_from_zip_code(driver: webdriver.Chrome, zip_code: str) -> str:
    """Check a zip code to see what chapter it is part of, via provided web proxy dict."""
    logger.info("Checking chapter assignment of: %s", zip_code)
    url = f"view-source:https://chapters.dsausa.org/api/search?zip={zip_code}"
    logger.debug("API URL: %s", url)

    configure_browser_proxy(random.choice(proxy_list))
    driver.get(url)

    # ensure no server error
    i = 0
    while ("Internal Server Error" in driver.page_source) or ("Rate limit exceeded" in driver.page_source) or ("502: Bad gateway" in driver.page_source):
        configure_browser_proxy(random.choice(proxy_list))
        driver.get(url)

        if i > 600:
            logger.critical("API timed out!")
            driver.quit()
            sys.exit("Data has been scraped and written.")

    content = driver.find_element(By.CLASS_NAME, "line-content").text

    try:
        data = json.loads(content)
        return data.get("data", {}).get("chapter", "Chapter not found.")
    except json.JSONDecodeError:
        logger.warning("JSONDecodeError: No valid JSON in content: %s", content)
        return "Chapter not found."


def get_all_zip_codes() -> list[str]:
    """Get all zip codes from the zipcodes library."""
    return [zip_data["zip_code"] for zip_data in zipcodes.list_all()]


def main(driver: webdriver.Chrome) -> None:
    """Create test dataset for DSA membership list."""
    output_csv_path = Path(__file__).parent / "chapter_zips.csv"
    logger.info("Opening file at: %s", output_csv_path)
    with Path(output_csv_path).open(mode="w", newline="", encoding="UTF-8") as output_csv_file:
        writer = csv.DictWriter(output_csv_file, fieldnames=["zip", "chapter"], quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for iter_zip_code in tqdm(get_all_zip_codes(), unit="zipcode", leave=False):
            scraped_chapter = scrape_chapter_from_zip_code(driver, iter_zip_code)
            if scraped_chapter != "Chapter not found.":
                writer.writerow({"zip": iter_zip_code, "chapter": scraped_chapter})
                logger.info("%s assigned to: %s", iter_zip_code, scraped_chapter)
            else:
                logger.info("%s is not assigned to a chapter", iter_zip_code)

    driver.quit()
    logger.info("Data has been scraped and written.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s : %(levelname)s : %(message)s")
    logger = logging.getLogger(__name__)
    with (Path(__file__).parent / "proxy_list.csv").open(encoding="utf-8") as proxy_csv:
        proxy_list = list(csv.DictReader(proxy_csv))
    main(webdriver.Chrome())

import mysql.connector
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
import time
from datetime import datetime
import traceback
import logging

from sorter.filter import filter_project
from filterproject.db_utils import get_mysql_connection

logger = logging.getLogger("myjobs")


def row_exists_in_db(consultation_id):
    """
    Check if a consultation ID already exists in the tuneps_offers table.
    Returns True if it exists, False otherwise.
    """
    conn = get_mysql_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM tuneps_offers WHERE consultation_id = %s LIMIT 1", (consultation_id,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists


def run_web_scraper():
    logger.info("Running Tuneps web scraper...")

    # Configure Selenium to run headless
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--headless")

    driver = None

    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(60)
        driver.set_script_timeout(60)

        urls = [
            "https://www.tuneps.tn/portail/offres",
            "https://www.tuneps.tn/portail/consultations"
        ]

        today = datetime.today().strftime("%d/%m/%Y")
        headers = [
            'N° consultation', 'Client', 'Date Publication', 'Intitulé du projet',
            'Date Expiration', 'epBidMasterId', 'info', 'Lien'
        ]

        filtered_rows = []
        rows_added_total = 0

        for url in urls:
            stop_scraping = False  # Reset flag for each URL
            url_duplicates_found = False

            logger.info(f"Scraping data from: {url}")
            driver.get(url)
            WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.mat-table")))

            page_num = 0
            while not stop_scraping:
                page_num += 1
                logger.info(f"Scraping page {page_num} from {url}...")

                WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, "tr.mat-row")))
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                rows = soup.select('tbody .mat-row')

                rows_added = 0

                for row in rows:
                    columns = row.find_all('td')
                    row_data = [col.text.strip() for col in columns]

                    if len(row_data) >= 2:
                        consultation_id = row_data[0]
                        row_date = row_data[2]

                        if row_exists_in_db(consultation_id):
                            logger.info(f"Duplicate found in {url} (ID: {consultation_id}). Stopping this URL.")
                            url_duplicates_found = True
                            stop_scraping = True
                            break

                        if row_date != today:
                            logger.info(f"Found row dated {row_date} (not today). Stopping this URL.")
                            stop_scraping = True
                            break

                        id_number = row_data[0]
                        epBidMasterId = row_data[-2]

                        if "offres" in url:
                            details_link = f"{url}/details/{epBidMasterId}/{id_number}"
                        elif "consultations" in url:
                            details_link = f"{url}/consultationdetails/{epBidMasterId}/{id_number}"
                        else:
                            details_link = "N/A"

                        row_data.append(details_link)

                        if row_data not in filtered_rows:
                            rows_added += 1
                            filtered_rows.append(row_data)

                rows_added_total += rows_added

                if stop_scraping:
                    break 

                # Try to click "Next" if it exists
                try:
                    next_button = driver.find_element(By.CSS_SELECTOR, '.mat-paginator-navigation-next')
                    if "disabled" in next_button.get_attribute("class"):
                        logger.info(f"Reached last page on {url}.")
                        break
                    driver.execute_script("arguments[0].click();", next_button)
                    time.sleep(5)
                except Exception as e:
                    logger.error(f"Error clicking 'next' on {url}: {e}")
                    break

            # Log summary for this URL
            if url_duplicates_found:
                logger.info(f"Finished scraping {url} - duplicates found, moving to next URL.")
            else:
                logger.info(f"Finished scraping {url} - no duplicates found, all data collected.")

        logger.info(f"Web scraper completed. Total rows collected: {rows_added_total}")

        df = pd.DataFrame(filtered_rows, columns=headers)
        df.drop_duplicates(subset=['N° consultation'], inplace=True)

        #Save to database
        conn = get_mysql_connection()
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tuneps_offers (
            consultation_id VARCHAR(100) PRIMARY KEY,
            client TEXT,
            date_publication TEXT,
            intitule_projet TEXT,
            date_expiration TEXT,
            epBidMasterId TEXT,
            info TEXT,
            lien TEXT,
            is_filtered TINYINT DEFAULT 0
        )
        """)

        for _, row in df.iterrows():
            try:
                cursor.execute("""
                    INSERT IGNORE INTO tuneps_offers
                    (consultation_id, client, date_publication, intitule_projet, date_expiration, epBidMasterId, info, lien)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, tuple(row))
            except Exception as e:
                logger.error(f"Error inserting row: {e}")

        conn.commit()
        conn.close()

        logger.info('Data saved to MySQL database (table: tuneps_offers)')
        logger.info(f'Total rows added: {rows_added_total}')

        
        filter_project("tuneps_offers")

    except TimeoutException as te:
        logger.error(f"TimeoutException occurred: {te}")
    except WebDriverException as we:
        logger.error(f"WebDriverException occurred: {we}")
    except Exception as e:
        logger.error(f"Unexpected error: {traceback.format_exc()}")
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
        logger.info("Scraping attempt finished. Waiting for next scheduled run.")

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
import os
from sorter.filter import filter_project
import traceback
import logging


def run_web_scraper():
    print("Running Tuneps web scraper...")

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
        headers = ['N° consultation', 'Client', 'Date Publication', 'Intitulé du projet',
                'Date Expiration', 'epBidMasterId', 'info', 'Lien']

        filtered_rows = []
        rows_added_total = 0

        for url in urls:
            print(f"Scraping data from: {url}")
            driver.get(url)
            WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.mat-table")))

            page_num = 0
            while page_num < 10:
                page_num += 1
                print(f"Scraping page {page_num} from {url}...")
                WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, "tr.mat-row")))
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                rows = soup.select('tbody .mat-row')

                specific_date = "21/05/2025"
                rows_added = 0
                for row in rows:
                    columns = row.find_all('td')
                    row_data = [col.text.strip() for col in columns]

                    if len(row_data) >= 2:
                        row_date = row_data[2]
                        if row_date == today:
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

                try:
                    next_button = driver.find_element(By.CSS_SELECTOR, '.mat-paginator-navigation-next')
                    if "disabled" in next_button.get_attribute("class"):
                        print(f"Reached last page on {url}.")
                        break
                    driver.execute_script("arguments[0].click();", next_button)
                    time.sleep(5)
                except Exception as e:
                    print(f"Error clicking 'next' on {url}: {e}")
                    break

                    #create the dataframe
        df = pd.DataFrame(filtered_rows, columns=headers)
        df.drop_duplicates(subset=['N° consultation'], inplace=True)

        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="admin",
            database="filter_db"
        )
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
                print(f"Error inserting row: {e}")

        conn.commit()
        conn.close()

        print('Data saved to MySQL database (table: tuneps_offers)')
        print('Total rows added: ', rows_added_total)

        filter_project("tuneps_offers")

    except TimeoutException as te:
        logging.error("TimeoutException occurred: %s", te)
    except WebDriverException as we:
        logging.error("WebDriverException occurred: %s", we)
    except Exception as e:
        logging.error("Unexpected error: %s", traceback.format_exc())
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
        print("Scraping attempt finished. Waiting for next scheduled run.")

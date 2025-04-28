from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
from selenium.webdriver.chrome.options import Options
import time
from datetime import datetime
import os

def run_web_scraper():
    print("Running Tuneps web scraper...")

    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--headless")

    driver = webdriver.Chrome(options=options)

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
        while page_num < 20:
            page_num += 1
            print(f"Scraping page {page_num} from {url}...")
            WebDriverWait(driver, 40).until(EC.presence_of_element_located((By.CSS_SELECTOR, "tr.mat-row")))
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            rows = soup.select('tbody .mat-row')

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
                time.sleep(2)
            except Exception as e:
                print(f"Error clicking 'next' on {url}: {e}")
                break

    df = pd.DataFrame(filtered_rows, columns=headers)
    df.drop_duplicates(subset=['N° consultation'], inplace=True)

    # Save CSV in a predictable folder
    output_dir = os.path.join(os.path.dirname(__file__), "outputs")
    os.makedirs(output_dir, exist_ok=True)
    df.to_csv(os.path.join(output_dir, 'Tuneps.csv'), index=False)

    print('Total rows added: ', rows_added_total)
    print(df)

    driver.quit()

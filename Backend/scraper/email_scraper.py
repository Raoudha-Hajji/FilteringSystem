import mysql.connector
import os
import imaplib
import email
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re
from sorter.filter import filter_project
import logging

logger = logging.getLogger("myjobs")

def run_email_scraper():
    from filterproject.db_utils import get_mysql_connection
    conn = get_mysql_connection()
    cursor = conn.cursor()
    # Always create the table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tunisurf_offers(
            date_expiration TEXT,
            client TEXT,
            consultation_id VARCHAR(100) PRIMARY KEY,
            intitule_projet TEXT,
            lien TEXT,
            is_filtered TINYINT DEFAULT 0
        )
    """)
    conn.commit()

    EMAIL = "ha.raoudha@gmail.com"
    PASSWORD = "myhf kkst nmty bhoj"
    IMAP_SERVER = "imap.gmail.com"

    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)
    mail.select('inbox')

    subject = 'Fwd: PROGRESS ENGINEERING, vos appels d\'offres du'
    status, messages = mail.search(None, f'UNSEEN SUBJECT "{subject}"')
    email_ids = messages[0].split()

    if email_ids:
        # Set up DB connection once (already done above)
        for email_id in email_ids:
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            html_content = ""
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    html_content = part.get_payload(decode=True).decode('utf-8')
                    break

            soup = BeautifulSoup(html_content, 'html.parser')
            rows = soup.find_all('tr')

            dates, institutions, descriptions, links, consultation_numbers = [], [], [], [], []

            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 5:
                    date_text = cells[1].text.strip()
                    try:
                        date = datetime.strptime(date_text, '%Y-%m-%d').date()
                    except ValueError:
                        continue

                    institution = cells[2].text.strip()
                    description_cell = cells[4]
                    description = description_cell.text.strip()
                    link = description_cell.find('a')['href'] if description_cell.find('a') else None

                    match = re.match(r"([S\d]+) -", description)
                    if match:
                        consultation_number = match.group(1)
                        description = description.replace(f"{consultation_number} - ", "")
                    else:
                        consultation_number = "-"

                    dates.append(date)
                    institutions.append(institution)
                    descriptions.append(description)
                    links.append(link)
                    consultation_numbers.append(consultation_number)

            # Create and insert into database
            data = {
                'Date Expiration': dates,
                'Client': institutions,
                'N° consultation': consultation_numbers,
                'Intitulé du projet': descriptions,
                'Lien': links
            }
            df = pd.DataFrame(data)

            for _, row in df.iterrows():
                try:
                    cursor.execute("""
                        INSERT IGNORE INTO tunisurf_offers
                        (date_expiration, client, consultation_id, intitule_projet, lien, is_filtered)
                        VALUES (%s, %s, %s, %s, %s, 0)
                    """, tuple(row))
                except Exception as e:
                    logger.error(f"Error inserting row: {e}")

            # Mark email as seen
            mail.store(email_id, '+FLAGS', '\\Seen')

        conn.commit()
        conn.close()
        logger.info('All unseen matching emails processed and saved to MySQL')

    else:
        logger.info('No unseen emails with matching subject found.')

    filter_project("tunisurf_offers")
    mail.logout()


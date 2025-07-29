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
    logger.info("Running Tunisurf email scraper...")
    
    from filterproject.db_utils import get_mysql_connection
    conn = get_mysql_connection()
    cursor = conn.cursor()
    
    # Always create the table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tunisurf_offers(
            date_expiration TEXT,
            date_publication TEXT,
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

    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        mail.select('inbox')
        logger.info("Successfully connected to email server")

        subject = 'Fwd: PROGRESS ENGINEERING, vos appels d\'offres du'
        status, messages = mail.search(None, f'UNSEEN SUBJECT "{subject}"')
        email_ids = messages[0].split()

        logger.info(f"Found {len(email_ids)} unseen emails with matching subject")

        if email_ids:
            total_rows_added = 0
            
            for i, email_id in enumerate(email_ids):
                logger.info(f"Processing email {i+1}/{len(email_ids)}")
                
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                # Get the date of the email (date_publication)
                email_date_tuple = mail.fetch(email_id, '(BODY[HEADER.FIELDS (DATE)])')[1][0]
                email_date_str = None
                if email_date_tuple:
                    import email.utils
                    header = email.message_from_bytes(email_date_tuple[1])
                    email_date_str = header.get('Date')
                    if email_date_str:
                        email_parsed_date = email.utils.parsedate_to_datetime(email_date_str)
                        date_publication = email_parsed_date.strftime('%Y-%m-%d')
                    else:
                        date_publication = datetime.now().strftime('%Y-%m-%d')
                else:
                    date_publication = datetime.now().strftime('%Y-%m-%d')

                html_content = ""
                for part in msg.walk():
                    if part.get_content_type() == "text/html":
                        html_content = part.get_payload(decode=True).decode('utf-8')
                        break

                if not html_content:
                    logger.warning(f"No HTML content found in email {i+1}")
                    continue

                soup = BeautifulSoup(html_content, 'html.parser')
                rows = soup.find_all('tr')

                dates, institutions, descriptions, links, consultation_numbers = [], [], [], [], []

                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 5:
                        date_text = cells[1].text.strip()
                        try:
                            parsed_date = datetime.strptime(date_text, '%Y-%m-%d').date()
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

                        dates.append(parsed_date)
                        institutions.append(institution)
                        descriptions.append(description)
                        links.append(link)
                        consultation_numbers.append(consultation_number)

                logger.info(f"Found {len(dates)} rows in email {i+1}")

                # Create and insert into database
                if dates:  # Only process if we found data
                    data = {
                        'date_expiration': dates,
                        'date_publication': [date_publication] * len(dates),
                        'client': institutions,
                        'consultation_id': consultation_numbers,
                        'intitule_projet': descriptions,
                        'lien': links
                    }
                    df = pd.DataFrame(data)

                    email_rows_added = 0
                    for _, row in df.iterrows():
                        try:
                            cursor.execute("""
                                INSERT IGNORE INTO tunisurf_offers
                                (date_expiration, date_publication, client, consultation_id, intitule_projet, lien, is_filtered)
                                VALUES (%s, %s, %s, %s, %s, %s, 0)
                            """, tuple(row))
                            if cursor.rowcount > 0:
                                email_rows_added += 1
                        except Exception as e:
                            logger.error(f"Error inserting row: {e}")

                    total_rows_added += email_rows_added
                    logger.info(f"Added {email_rows_added} new rows from email {i+1}")

                # Mark email as seen
                mail.store(email_id, '+FLAGS', '\\Seen')

            conn.commit()
            conn.close()
            logger.info(f'Email scraper completed. Total rows added: {total_rows_added}')

        else:
            logger.info('No unseen emails with matching subject found.')
            conn.close()

        filter_project("tunisurf_offers")
        mail.logout()
        
    except Exception as e:
        logger.error(f"Error in email scraper: {e}")
        try:
            conn.close()
            mail.logout()
        except:
            pass


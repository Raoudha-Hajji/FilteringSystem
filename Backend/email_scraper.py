import imaplib
import email
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re

def run_email_scraper():
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
        latest_email_id = email_ids[-1]
        status, msg_data = mail.fetch(latest_email_id, '(RFC822)')
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        html_content = ""
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                html_content = part.get_payload(decode=True).decode('utf-8')
                break

        with open("html_content.txt", "w", encoding="utf-8") as f:
            f.write(html_content)

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

        data = {
            'Date Expiration': dates,
            'Client': institutions,
            'N° consultation': consultation_numbers,
            'Intitulé du projet': descriptions,
            'Lien': links
        }
        df = pd.DataFrame(data)
        df.to_csv('tunisurf.csv', index=False)

        mail.store(latest_email_id, '+FLAGS', '\\Seen')
        print(df)

    mail.logout()

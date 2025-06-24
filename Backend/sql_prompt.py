import sqlite3

# Connect to the running app's database
conn = sqlite3.connect("db.sqlite3")  # Make sure path is correct
cursor = conn.cursor()

# Create a new table (if it doesn't already exist)
cursor.execute('ALTER TABLE training_data RENAME COLUMN "Client" TO client')
cursor.execute('ALTER TABLE training_data RENAME COLUMN "N° Consultation" TO consultation_id')
cursor.execute('ALTER TABLE training_data RENAME COLUMN "Intitulé du projet" TO intitule_projet')
cursor.execute('ALTER TABLE training_data RENAME COLUMN "Lien" TO lien')


# Commit and close
conn.commit()
conn.close()

print(" Creation or Modification done successfully.")

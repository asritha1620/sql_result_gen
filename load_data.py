import sqlite3
import pandas as pd

# Connect to SQLite database (creates if doesn't exist)
conn = sqlite3.connect('business_data.db')
cursor = conn.cursor()

# Create tables
cursor.execute('''
CREATE TABLE IF NOT EXISTS quarterly_financial (
    year INTEGER,
    quarter TEXT,
    revenue REAL,
    net_income REAL,
    assets REAL,
    liabilities REAL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS annual_financial (
    year INTEGER,
    metric TEXT,
    value REAL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS operational_cargo (
    year INTEGER,
    quarter TEXT,
    port TEXT,
    volume REAL
)
''')

# Load data from CSVs
quarterly_df = pd.read_csv('financial_quarterly.csv')
annual_df = pd.read_csv('financial_annual.csv')
operational_df = pd.read_csv('operational_cargo.csv')

# Insert data
quarterly_df.to_sql('quarterly_financial', conn, if_exists='replace', index=False)
annual_df.to_sql('annual_financial', conn, if_exists='replace', index=False)
operational_df.to_sql('operational_cargo', conn, if_exists='replace', index=False)

# Commit and close
conn.commit()
conn.close()

print("Database created and data loaded successfully.")

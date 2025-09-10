import sqlite3
import pandas as pd

# Connect to SQLite database (creates if doesn't exist)
conn = sqlite3.connect('business_data.db')
cursor = conn.cursor()

# Drop old tables if exist
# cursor.execute('DROP TABLE IF EXISTS quarterly_financial')
# cursor.execute('DROP TABLE IF EXISTS annual_financial')
# cursor.execute('DROP TABLE IF EXISTS operational_cargo')

# Create new tables based on CSV structures
cursor.execute('''
CREATE TABLE IF NOT EXISTS balance_sheet (
    line_item VARCHAR(255),
    category VARCHAR(50),
    subcategory VARCHAR(100),
    subsubcategory VARCHAR(100),
    period VARCHAR(20),
    value REAL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS cash_flow_statement (
    item VARCHAR(255),
    category VARCHAR(100),
    period VARCHAR(20),
    value REAL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS roce_external (
    particular VARCHAR(100),
    period VARCHAR(20),
    value REAL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS roce_internal (
    category VARCHAR(50),
    port VARCHAR(50),
    line_item VARCHAR(100),
    period VARCHAR(20),
    value REAL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS quarterly_pnl (
    item VARCHAR(255),
    category VARCHAR(50),
    period VARCHAR(20),
    value REAL,
    period_type VARCHAR(20)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS consolidated_pnl (
    line_item VARCHAR(100),
    period VARCHAR(20),
    value REAL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS volumes (
    port VARCHAR(50),
    state VARCHAR(50),
    commodity VARCHAR(50),
    entity VARCHAR(50),
    type VARCHAR(20),
    period VARCHAR(20),
    value REAL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS containers (
    port VARCHAR(50),
    entity VARCHAR(50),
    type VARCHAR(20),
    period VARCHAR(20),
    value REAL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS roro (
    port VARCHAR(50),
    type VARCHAR(20),
    period VARCHAR(20),
    value REAL,
    number_of_cars INTEGER
)
''')

# Load data from CSVs
balance_df = pd.read_csv('csv_files/BalanceSheet.csv')
cashflow_df = pd.read_csv('csv_files/CashFlowStatement.csv')
roce_ext_df = pd.read_csv('csv_files/ROCE External.csv')
roce_int_df = pd.read_csv('csv_files/ROCE Internal.csv')
quarterly_df = pd.read_csv('csv_files/Quarterly PnL.csv')
consolidated_df = pd.read_csv('csv_files/Consolidated PnL.csv')
volumes_df = pd.read_csv('csv_files/Volumes.csv')
containers_df = pd.read_csv('csv_files/Containers.csv')
roro_df = pd.read_csv('csv_files/RORO.csv')

# Insert data
balance_df.to_sql('balance_sheet', conn, if_exists='replace', index=False)
cashflow_df.to_sql('cash_flow_statement', conn, if_exists='replace', index=False)
roce_ext_df.to_sql('roce_external', conn, if_exists='replace', index=False)
roce_int_df.to_sql('roce_internal', conn, if_exists='replace', index=False)
quarterly_df.to_sql('quarterly_pnl', conn, if_exists='replace', index=False)
consolidated_df.to_sql('consolidated_pnl', conn, if_exists='replace', index=False)
volumes_df.to_sql('volumes', conn, if_exists='replace', index=False)
containers_df.to_sql('containers', conn, if_exists='replace', index=False)
roro_df.to_sql('roro', conn, if_exists='replace', index=False)

# Add indexes for better joining performance
cursor.execute('CREATE INDEX IF NOT EXISTS idx_balance_sheet_period ON balance_sheet (period);')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_cash_flow_statement_period ON cash_flow_statement (period);')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_roce_external_period ON roce_external (period);')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_roce_internal_port_period ON roce_internal (port, period);')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_quarterly_pnl_period ON quarterly_pnl (period);')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_consolidated_pnl_period ON consolidated_pnl (period);')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_volumes_port_period ON volumes (port, period);')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_containers_port_period ON containers (port, period);')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_roro_port_period ON roro (port, period);')

# Commit and close
conn.commit()
conn.close()

print("Database updated with new tables, data loaded, and indexes created successfully.")


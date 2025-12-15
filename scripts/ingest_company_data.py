#!/usr/bin/env python3
"""
Ingest Kaggle company dataset into PostgreSQL database
Optimized for batch processing of 7 million records
"""
import os
import sys
import pandas as pd
from sqlalchemy import create_engine, text
from tqdm import tqdm
import time

# Add libs to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

DATABASE_URL = "postgresql://admin:secure_password@localhost:5432/job_tracker_prod"
DATASET_PATH = "/Users/nikunjshetye/.cache/kagglehub/datasets/peopledatalabssf/free-7-million-company-dataset/versions/1"
CSV_FILE = "companies_sorted.csv"
BATCH_SIZE = 10000  # Insert 10k rows at a time

def create_table_if_not_exists(engine):
    """Create the company_data table if it doesn't exist"""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS company_data (
        id SERIAL PRIMARY KEY,
        name VARCHAR NOT NULL,
        name_normalized VARCHAR,
        domain VARCHAR,
        year_founded INTEGER,
        industry VARCHAR,
        size_range VARCHAR,
        locality VARCHAR,
        country VARCHAR,
        linkedin_url VARCHAR,
        current_employee_estimate INTEGER,
        total_employee_estimate INTEGER,
        created_at TIMESTAMP DEFAULT NOW()
    );
    
    CREATE INDEX IF NOT EXISTS idx_company_name_normalized ON company_data(name_normalized);
    CREATE INDEX IF NOT EXISTS idx_company_industry ON company_data(industry);
    """
    
    with engine.connect() as conn:
        conn.execute(text(create_table_sql))
        conn.commit()
    print("✅ Table created/verified")

def get_row_count(engine):
    """Get current row count in company_data table"""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM company_data"))
        return result.scalar()

def ingest_data(limit=None):
    """
    Ingest company data from CSV into PostgreSQL
    
    Args:
        limit: Optional limit on number of rows to ingest (for testing)
    """
    print(f"🚀 Starting company data ingestion...")
    print(f"   Database: {DATABASE_URL.replace('secure_password', '****')}")
    print(f"   Dataset: {os.path.join(DATASET_PATH, CSV_FILE)}")
    
    # Create engine
    engine = create_engine(
        DATABASE_URL,
        pool_size=20,
        max_overflow=40,
        pool_pre_ping=True
    )
    
    # Create table
    create_table_if_not_exists(engine)
    
    # Check existing data
    existing_count = get_row_count(engine)
    print(f"📊 Existing records: {existing_count:,}")
    
    if existing_count > 0:
        response = input(f"⚠️  Table already contains {existing_count:,} records. Continue? (y/N): ")
        if response.lower() != 'y':
            print("❌ Aborted")
            return
    
    # Read and process CSV
    csv_path = os.path.join(DATASET_PATH, CSV_FILE)
    
    print(f"\n📖 Reading CSV file...")
    df = pd.read_csv(csv_path, nrows=limit)
    
    print(f"   Total rows to process: {len(df):,}")
    
    # Clean and prepare data
    print(f"\n🧹 Cleaning data...")
    df = df.rename(columns={
        'year founded': 'year_founded',
        'size range': 'size_range',
        'linkedin url': 'linkedin_url',
        'current employee estimate': 'current_employee_estimate',
        'total employee estimate': 'total_employee_estimate'
    })
    
    # Drop the unnamed index column
    if 'Unnamed: 0' in df.columns:
        df = df.drop('Unnamed: 0', axis=1)
    
    # Add normalized name for matching
    df['name_normalized'] = df['name'].str.lower().str.strip()
    
    # Convert year to integer
    df['year_founded'] = pd.to_numeric(df['year_founded'], errors='coerce').astype('Int64')
    
    # Handle NaN values
    df = df.where(pd.notnull(df), None)
    
    print(f"   Cleaned rows: {len(df):,}")
    
    # Insert in batches
    print(f"\n💾 Inserting data in batches of {BATCH_SIZE:,}...")
    start_time = time.time()
    
    total_inserted = 0
    errors = 0
    
    for i in tqdm(range(0, len(df), BATCH_SIZE)):
        batch = df.iloc[i:i+BATCH_SIZE]
        
        try:
            batch.to_sql(
                'company_data',
                engine,
                if_exists='append',
                index=False,
                method='multi'
            )
            total_inserted += len(batch)
        except Exception as e:
            errors += 1
            print(f"\n❌ Error inserting batch {i//BATCH_SIZE + 1}: {e}")
            if errors > 10:
                print("Too many errors, aborting...")
                break
    
    elapsed = time.time() - start_time
    
    print(f"\n{'='*80}")
    print(f"✅ Ingestion complete!")
    print(f"   Total rows inserted: {total_inserted:,}")
    print(f"   Errors: {errors}")
    print(f"   Time elapsed: {elapsed:.2f} seconds")
    print(f"   Rows per second: {total_inserted/elapsed:.2f}")
    print(f"{'='*80}")
    
    # Verify
    final_count = get_row_count(engine)
    print(f"\n📊 Final database record count: {final_count:,}")
    
    # Sample query
    print(f"\n🔍 Sample companies:")
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT name, industry, size_range, country 
            FROM company_data 
            LIMIT 5
        """))
        for row in result:
            print(f"   - {row[0]} | {row[1]} | {row[2]} | {row[3]}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Ingest Kaggle company dataset')
    parser.add_argument('--limit', type=int, help='Limit number of rows (for testing)')
    parser.add_argument('--test', action='store_true', help='Test mode with 1000 rows')
    
    args = parser.parse_args()
    
    if args.test:
        print("🧪 TEST MODE: Ingesting first 1,000 rows only")
        ingest_data(limit=1000)
    elif args.limit:
        print(f"📊 LIMITED MODE: Ingesting first {args.limit:,} rows")
        ingest_data(limit=args.limit)
    else:
        print("⚠️  FULL MODE: Ingesting ALL 7 million rows")
        print("   This will take approximately 10-20 minutes")
        response = input("   Continue? (y/N): ")
        if response.lower() == 'y':
            ingest_data()
        else:
            print("❌ Aborted")

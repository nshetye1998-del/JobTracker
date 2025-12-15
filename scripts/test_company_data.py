#!/usr/bin/env python3
"""
Test the enhanced fallback research with company database
"""
import os
import sys
import psycopg2

# Add libs to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

DATABASE_URL = "postgresql://admin:secure_password@localhost:5432/job_tracker_prod"

def test_company_lookup():
    """Test looking up companies from our database"""
    conn = psycopg2.connect(DATABASE_URL)
    
    test_companies = [
        "google",
        "microsoft",
        "amazon",
        "meta",
        "netflix",
        "ibm",
        "apple"
    ]
    
    print("🔍 Testing company data lookups:")
    print("="*80)
    
    cursor = conn.cursor()
    
    for company in test_companies:
        company_norm = company.lower().strip()
        
        cursor.execute("""
        SELECT name, domain, year_founded, industry, size_range, 
               locality, country, current_employee_estimate
        FROM company_data
        WHERE name_normalized = %s OR name_normalized LIKE %s
        ORDER BY current_employee_estimate DESC
        LIMIT 1
        """, (company_norm, f'%{company_norm}%'))
        
        row = cursor.fetchone()
        
        if row:
            print(f"\n✅ {company.upper()}")
            print(f"   Name: {row[0]}")
            print(f"   Domain: {row[1]}")
            print(f"   Founded: {row[2]}")
            print(f"   Industry: {row[3]}")
            print(f"   Size: {row[4]} employees")
            print(f"   Location: {row[5]}, {row[6]}")
            print(f"   Current Employees: {row[7]:,}")
        else:
            print(f"\n❌ {company.upper()} - Not found in database")
    
    print("\n" + "="*80)
    
    # Statistics
    cursor.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(DISTINCT industry) as industries,
        COUNT(DISTINCT country) as countries,
        SUM(current_employee_estimate) as total_employees
    FROM company_data
    """)
    
    row = cursor.fetchone()
    print(f"\n📊 Database Statistics:")
    print(f"   Total Companies: {row[0]:,}")
    print(f"   Unique Industries: {row[1]:,}")
    print(f"   Countries Represented: {row[2]:,}")
    print(f"   Total Employees Tracked: {row[3]:,}")
    
    # Top industries
    print(f"\n🏢 Top 10 Industries:")
    cursor.execute("""
    SELECT industry, COUNT(*) as count
    FROM company_data
    WHERE industry IS NOT NULL
    GROUP BY industry
    ORDER BY count DESC
    LIMIT 10
    """)
    
    for i, row in enumerate(cursor.fetchall(), 1):
        print(f"   {i}. {row[0]}: {row[1]:,} companies")
    
    conn.close()

if __name__ == "__main__":
    test_company_lookup()

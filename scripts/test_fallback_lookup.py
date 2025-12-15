#!/usr/bin/env python3
"""
Direct test of company lookup in fallback research
"""
import psycopg2
import re

DATABASE_URL = "postgresql://admin:secure_password@localhost:5432/job_tracker_prod"

def normalize(text):
    """Normalize text for matching"""
    if not text:
        return ""
    return re.sub(r'[^a-z0-9]', '', text.lower())

def get_company_info(company):
    """Fetch company data"""
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    company_norm = normalize(company)
    
    print(f"🔍 Looking up: {company}")
    print(f"   Normalized: {company_norm}")
    
    try:
        # Try exact match
        cursor.execute("""
        SELECT name, domain, year_founded, industry, size_range, 
               locality, country, linkedin_url, current_employee_estimate,
               total_employee_estimate
        FROM company_data
        WHERE name_normalized = %s
        LIMIT 1
        """, (company_norm,))
        
        row = cursor.fetchone()
        
        if not row:
            print(f"   ❌ No exact match, trying partial...")
            cursor.execute("""
            SELECT name, domain, year_founded, industry, size_range,
                   locality, country, linkedin_url, current_employee_estimate,
                   total_employee_estimate
            FROM company_data
            WHERE name_normalized LIKE %s
            ORDER BY current_employee_estimate DESC
            LIMIT 1
            """, (f'%{company_norm}%',))
            row = cursor.fetchone()
        
        if row:
            print(f"   ✅ FOUND!")
            company_data = {
                'name': row[0],
                'domain': row[1],
                'year_founded': row[2],
                'industry': row[3],
                'size_range': row[4],
                'locality': row[5],
                'country': row[6],
                'linkedin_url': row[7],
                'current_employees': row[8] or 0,
                'total_employees': row[9] or 0
            }
            
            print(f"\n📊 Company Data:")
            for key, value in company_data.items():
                print(f"   {key}: {value}")
            
            return company_data
        else:
            print(f"   ❌ Not found in database")
            return None
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None
    finally:
        conn.close()

# Test companies
test_companies = [
    "Microsoft",
    "Google", 
    "Amazon",
    "Apple",
    "Jayshree Infotech",
    "TechFlow",
    "wipro infotech"
]

print("="*80)
print("🧪 Testing Company Database Lookup")
print("="*80)

for company in test_companies:
    print()
    get_company_info(company)
    print("-"*80)

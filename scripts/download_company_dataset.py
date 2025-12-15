#!/usr/bin/env python3
"""
Download and explore Kaggle company dataset for research enhancement
"""
import kagglehub
import os
import pandas as pd

def download_dataset():
    """Download the 7 million company dataset from Kaggle"""
    print("🔄 Downloading company dataset from Kaggle...")
    
    try:
        # Download latest version
        path = kagglehub.dataset_download("peopledatalabssf/free-7-million-company-dataset")
        print(f"✅ Dataset downloaded to: {path}")
        
        # List files in the dataset
        print("\n📁 Files in dataset:")
        for file in os.listdir(path):
            file_path = os.path.join(path, file)
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            print(f"  - {file} ({size_mb:.2f} MB)")
        
        return path
    
    except Exception as e:
        print(f"❌ Error downloading dataset: {e}")
        print("\n💡 You may need to configure Kaggle API credentials:")
        print("   1. Go to https://www.kaggle.com/settings")
        print("   2. Click 'Create New API Token'")
        print("   3. Save kaggle.json to ~/.kaggle/kaggle.json")
        return None

def explore_dataset(path):
    """Explore the dataset structure and sample data"""
    if not path or not os.path.exists(path):
        print("❌ Dataset path not found")
        return
    
    print("\n🔍 Exploring dataset structure...")
    
    # Find CSV files
    csv_files = [f for f in os.listdir(path) if f.endswith('.csv')]
    
    for csv_file in csv_files:
        file_path = os.path.join(path, csv_file)
        print(f"\n📊 Analyzing: {csv_file}")
        
        try:
            # Read first few rows
            df = pd.read_csv(file_path, nrows=1000)
            
            print(f"   Rows (sample): {len(df):,}")
            print(f"   Columns: {len(df.columns)}")
            print(f"\n   Available fields:")
            for col in df.columns:
                non_null = df[col].notna().sum()
                print(f"     - {col}: {non_null}/{len(df)} non-null ({non_null/len(df)*100:.1f}%)")
            
            print(f"\n   Sample data (first 3 rows):")
            print(df.head(3).to_string())
            
            # Check for company name field
            name_fields = [col for col in df.columns if 'name' in col.lower()]
            if name_fields:
                print(f"\n   🏢 Company name fields found: {name_fields}")
                print(f"   Sample companies:")
                for name_field in name_fields[:3]:
                    samples = df[name_field].dropna().head(5).tolist()
                    print(f"     {name_field}: {samples}")
            
            # Check for useful fields for research
            useful_fields = {
                'industry': [col for col in df.columns if 'industry' in col.lower()],
                'size': [col for col in df.columns if 'size' in col.lower() or 'employee' in col.lower()],
                'location': [col for col in df.columns if 'location' in col.lower() or 'country' in col.lower() or 'city' in col.lower()],
                'description': [col for col in df.columns if 'description' in col.lower()],
                'website': [col for col in df.columns if 'website' in col.lower() or 'domain' in col.lower()],
                'founded': [col for col in df.columns if 'founded' in col.lower() or 'year' in col.lower()],
            }
            
            print(f"\n   🎯 Useful fields for research:")
            for category, fields in useful_fields.items():
                if fields:
                    print(f"     {category.upper()}: {fields}")
            
        except Exception as e:
            print(f"   ❌ Error reading {csv_file}: {e}")

if __name__ == "__main__":
    # Download dataset
    dataset_path = download_dataset()
    
    # Explore if download successful
    if dataset_path:
        explore_dataset(dataset_path)
        
        print("\n" + "="*80)
        print("✨ Next Steps:")
        print("  1. Review the dataset structure above")
        print("  2. Identify key fields for research enhancement")
        print("  3. Create database schema to store company data")
        print("  4. Build ingestion pipeline to load data")
        print("  5. Enhance fallback research with real company info")
        print("="*80)

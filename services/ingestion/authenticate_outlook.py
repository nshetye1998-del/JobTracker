#!/usr/bin/env python3
"""
One-time Outlook Authentication Setup
Uses Microsoft Device Code Flow - No Azure Portal needed!

Run this script once to authenticate with your Outlook account.
Token will be cached for future use.
"""
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from services.ingestion.src.outlook_client import OutlookClient

def main():
    print("\n" + "="*70)
    print("OUTLOOK AUTHENTICATION SETUP")
    print("="*70)
    print("This is a ONE-TIME setup to authenticate with your Outlook account.")
    print("You'll be prompted to visit a URL and enter a code.")
    print("Once authenticated, the token will be cached for future use.")
    print("="*70)
    
    try:
        # Create Outlook client
        client = OutlookClient()
        
        # Authenticate
        print("\nInitiating authentication...")
        token = client.authenticate()
        
        if token:
            print("\n" + "="*70)
            print("✅ AUTHENTICATION SUCCESSFUL!")
            print("="*70)
            print("Token cached in: outlook_token_cache.json")
            print("\nOutlook integration is now ready!")
            print("The ingestion service will automatically fetch emails from Outlook.")
            print("="*70)
            
            # Test fetch
            print("\nTesting email fetch...")
            emails = client.fetch_emails(since_hours=24)
            print(f"✅ Successfully fetched {len(emails)} emails from the last 24 hours")
            
            if emails:
                print("\nSample email:")
                email = emails[0]
                print(f"  From: {email['from']}")
                print(f"  Subject: {email['subject']}")
                print(f"  Received: {email['received_at']}")
            
        else:
            print("\n❌ Authentication failed. Please try again.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Authentication cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

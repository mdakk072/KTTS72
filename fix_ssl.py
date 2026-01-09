#!/usr/bin/env python3
"""
SSL Configuration Fix for Corporate Environments

This script helps resolve SSL certificate verification issues when downloading 
models from HuggingFace in corporate environments.
"""

import os
import sys
import ssl
import urllib3
from pathlib import Path

def configure_ssl_bypass():
    """Configure SSL bypass for the current session."""
    try:
        # Disable SSL verification warnings
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Create unverified SSL context
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Set environment variables to bypass SSL verification
        ssl_env_vars = {
            'CURL_CA_BUNDLE': '',
            'REQUESTS_CA_BUNDLE': '',
            'SSL_VERIFY': 'false',
            'PYTHONHTTPSVERIFY': '0',
        }
        
        for key, value in ssl_env_vars.items():
            os.environ[key] = value
            print(f"Set {key}={value}")
            
        print("\n[OK] SSL bypass configured for this session.")
        print("You can now run download_models.py or KTTS72")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to configure SSL bypass: {e}")
        return False

def check_ssl_status():
    """Check current SSL configuration."""
    print("Current SSL Configuration:")
    print("-" * 40)
    
    ssl_vars = ['CURL_CA_BUNDLE', 'REQUESTS_CA_BUNDLE', 'SSL_VERIFY', 'PYTHONHTTPSVERIFY']
    for var in ssl_vars:
        value = os.environ.get(var, 'Not Set')
        print(f"{var}: {value}")
    
    try:
        import requests
        print(f"\nRequests version: {requests.__version__}")
    except ImportError:
        print("\nRequests not available")
    
    try:
        import urllib3
        print(f"urllib3 version: {urllib3.__version__}")
    except ImportError:
        print("urllib3 not available")

def manual_download_instructions():
    """Show manual download instructions."""
    print("\nManual Download Instructions:")
    print("=" * 50)
    print("If SSL issues persist, you can manually download the models:")
    print()
    print("1. Go to: https://huggingface.co/hexgrad/Kokoro-82M")
    print("2. Download these files to your models/ folder:")
    print("   - config.json → models/kokoro-82m/")
    print("   - kokoro-v1_0.pth → models/kokoro-82m/")
    print("   - All .pt files from voices/ → models/voices/")
    print()
    print("Folder structure should be:")
    print("models/")
    print("├── kokoro-82m/")
    print("│   ├── config.json")
    print("│   └── kokoro-v1_0.pth")
    print("└── voices/")
    print("    ├── af_heart.pt")
    print("    └── ... (other voice files)")

def main():
    """Main function to handle SSL configuration."""
    if len(sys.argv) > 1 and sys.argv[1] == '--check':
        check_ssl_status()
        return
    
    if len(sys.argv) > 1 and sys.argv[1] == '--manual':
        manual_download_instructions()
        return
    
    print("KTTS72 SSL Configuration Tool")
    print("=" * 40)
    print()
    
    print("This tool helps fix SSL certificate issues in corporate environments.")
    print("Common in environments with proxy servers or custom certificates.")
    print()
    
    choice = input("Configure SSL bypass for this session? (y/n): ").lower().strip()
    
    if choice in ['y', 'yes']:
        success = configure_ssl_bypass()
        if success:
            print("\nTry running download_models.py again now!")
        else:
            print("\nSSL configuration failed. Try manual download instead.")
            manual_download_instructions()
    else:
        print("\nSkipping SSL configuration.")
        print("\nOther options:")
        print("  python fix_ssl.py --check     # Check current SSL settings") 
        print("  python fix_ssl.py --manual    # Show manual download instructions")

if __name__ == '__main__':
    main()
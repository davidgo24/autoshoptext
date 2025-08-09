#!/usr/bin/env python3
"""
Production Deployment Script for AutoShopText
Run this to start the application in production mode
"""

import os
import subprocess
import sys

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error: {description} failed")
        print(f"Error output: {result.stderr}")
        sys.exit(1)
    print(f"✅ {description} completed")
    return result.stdout

def check_environment():
    """Check if all required environment variables are set"""
    required_vars = [
        'DATABASE_URL',
        'TWILIO_ACCOUNT_SID', 
        'TWILIO_AUTH_TOKEN',
        'TWILIO_PHONE_NUMBER'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these in your .env file or environment")
        sys.exit(1)
    
    print("✅ All required environment variables are set")

def main():
    print("🚀 AutoShopText Production Deployment")
    print("=" * 50)
    
    # Check environment variables
    check_environment()
    
    # Install production requirements
    run_command("pip install -r requirements.prod.txt", "Installing production requirements")
    
    # Run database migrations/initialization
    print("🗄️  Initializing database...")
    
    # Start the application
    print("🚀 Starting application...")
    print("Application will be available on http://0.0.0.0:8001")
    print("Press Ctrl+C to stop")
    
    # Use gunicorn for production
    cmd = "gunicorn app.main:app -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8001"
    os.system(cmd)

if __name__ == "__main__":
    main()

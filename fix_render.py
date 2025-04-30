#!/usr/bin/env python3
"""
Comprehensive fix script for Render.com deployment.
This script handles:
1. Database migration and setup
2. Environment validation

Usage: python fix_render.py
"""

import os
import sys
import subprocess
import time

def run_command(cmd, description):
    """Run a command and print its output"""
    print(f"\n=== {description} ===")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error output: {e.stderr}")
        return False

def main():
    print("Starting Render.com fix script...")

    # Check Python version
    python_version = sys.version
    print(f"Using Python version: {python_version}")
    
    # Ensure correct directory structure
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Current directory: {current_dir}")
    
    # Run database fix script
    print("\n1. Running database fix script...")
    db_fix_success = run_command("python app/fix_db.py", "Database Fix")
    
    # Check for environment variables
    print("\n2. Checking environment variables...")
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        print("WARNING: SECRET_KEY environment variable not set. Using default (insecure) key.")
    else:
        print("SECRET_KEY environment variable is set.")
    
    # Summary
    print("\n=== Deployment Fix Summary ===")
    print(f"Database fix script: {'SUCCESS' if db_fix_success else 'FAILED'}")
    print(f"Environment variables: {'COMPLETE' if secret_key else 'INCOMPLETE'}")
    
    # Overall status
    if db_fix_success:
        print("\nDeployment fixes applied successfully!")
        return 0
    else:
        print("\nSome deployment fixes failed. Check the logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
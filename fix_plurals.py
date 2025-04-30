#!/usr/bin/env python3
"""
Fix script for pluralization inconsistencies in directory names.
This script handles:
1. Moving files from activitys → activities
2. Moving files from activity_categorys → activity_categories

Run this script if you're experiencing missing data for activities or activity categories.
"""

import os
import json
import shutil
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('fix_plurals')

# Define data directory
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

def fix_directory(incorrect_name, correct_name):
    """Fix a directory name inconsistency by moving files from incorrect to correct directory"""
    # Path to incorrect directory
    incorrect_dir = os.path.join(DATA_DIR, incorrect_name)
    
    # Path to correct directory
    correct_dir = os.path.join(DATA_DIR, correct_name)
    
    # Check if incorrect directory exists
    if not os.path.exists(incorrect_dir):
        logger.info(f"No incorrect directory found for {incorrect_name}, nothing to fix")
        return 0
    
    # Ensure correct directory exists
    if not os.path.exists(correct_dir):
        logger.info(f"Creating correct directory: {correct_dir}")
        os.makedirs(correct_dir)
    
    # Count of files moved
    files_moved = 0
    
    # Move files from incorrect to correct directory
    for filename in os.listdir(incorrect_dir):
        if filename.endswith('.json'):
            src_path = os.path.join(incorrect_dir, filename)
            dst_path = os.path.join(correct_dir, filename)
            
            logger.info(f"Moving {src_path} to {dst_path}")
            
            # Read file content
            with open(src_path, 'r') as f:
                try:
                    data = json.load(f)
                    
                    # Write to correct location
                    with open(dst_path, 'w') as f_out:
                        json.dump(data, f_out, indent=2)
                    
                    files_moved += 1
                    logger.info(f"Successfully moved {filename}")
                except json.JSONDecodeError:
                    logger.error(f"Error decoding JSON in {filename}, skipping")
    
    # Remove incorrect directory if empty or force removal
    if len(os.listdir(incorrect_dir)) == 0:
        logger.info(f"Removing empty incorrect directory: {incorrect_dir}")
        os.rmdir(incorrect_dir)
    else:
        logger.warning(f"Directory not empty, forcing removal: {incorrect_dir}")
        shutil.rmtree(incorrect_dir)
    
    logger.info(f"Fix completed for {incorrect_name} → {correct_name}: {files_moved} files moved")
    
    # Log contents of correct directory
    logger.info(f"Contents of {correct_name} directory:")
    for filename in os.listdir(correct_dir):
        logger.info(f" - {filename}")
        
    return files_moved

def main():
    """Fix all pluralization inconsistencies"""
    logger.info("Starting directory pluralization fixes")
    
    # Define the mapping of incorrect → correct directory names
    directories_to_fix = [
        ('activity_categorys', 'activity_categories'),
        ('activitys', 'activities')
    ]
    
    total_files_moved = 0
    
    # Fix each directory
    for incorrect, correct in directories_to_fix:
        files_moved = fix_directory(incorrect, correct)
        total_files_moved += files_moved
    
    logger.info(f"All fixes completed: {total_files_moved} files moved in total")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Fix script for activities directory inconsistency.
This script moves all JSON files from activitys to activities
and removes the incorrect directory.
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
logger = logging.getLogger('fix_activities')

# Define data directory
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

def fix_activities():
    """Fix activities directory inconsistency"""
    # Path to incorrect directory
    incorrect_dir = os.path.join(DATA_DIR, 'activitys')
    
    # Path to correct directory
    correct_dir = os.path.join(DATA_DIR, 'activities')
    
    # Check if incorrect directory exists
    if not os.path.exists(incorrect_dir):
        logger.info("No incorrect directory found, nothing to fix")
        return
    
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
    
    logger.info(f"Fix completed: {files_moved} files moved")
    
    # Log contents of correct directory
    logger.info("Contents of activities directory:")
    for filename in os.listdir(correct_dir):
        logger.info(f" - {filename}")

if __name__ == "__main__":
    logger.info("Starting activities directory fix")
    fix_activities()
    logger.info("Fix completed") 
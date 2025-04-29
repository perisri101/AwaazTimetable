#!/bin/bash

# Check if container is running
CONTAINER_ID=$(docker ps | grep -i awaazflexytimetable | awk '{print $1}')

if [ -z "$CONTAINER_ID" ]; then
    echo "Starting Docker container..."
    docker-compose up -d
    sleep 5
    CONTAINER_ID=$(docker ps | grep -i awaazflexytimetable | awk '{print $1}')
    
    if [ -z "$CONTAINER_ID" ]; then
        echo "Failed to detect Docker container. Looking for any Flask container..."
        CONTAINER_ID=$(docker ps | grep -i flask | awk '{print $1}')
    fi
    
    if [ -z "$CONTAINER_ID" ]; then
        echo "Failed to start Docker container!"
        exit 1
    fi
fi

echo "Using container: $CONTAINER_ID"

# Copy the migration script to ensure it's in the container
echo "Copying migration script to container..."
docker cp app/migrate_db.py $CONTAINER_ID:/app/

# Run the migration inside the container
echo "Running migration script in container..."
docker exec $CONTAINER_ID python /app/migrate_db.py

echo "Migration completed!" 
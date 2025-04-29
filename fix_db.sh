#!/bin/bash

# Get the container ID
CONTAINER_ID=$(docker ps | grep awaazflexytimetable | head -n 1 | awk '{print $1}')

if [ -z "$CONTAINER_ID" ]; then
    echo "Error: No running container found for AwaazFlexyTimetable"
    exit 1
fi

echo "Found container: $CONTAINER_ID"

# Copy the fix script to the container
echo "Copying fix script to container..."
docker cp app/fix_db.py $CONTAINER_ID:/app/fix_db.py

# Execute the script in the container
echo "Running fix script in container..."
docker exec $CONTAINER_ID python /app/fix_db.py

echo "Database fix completed!" 
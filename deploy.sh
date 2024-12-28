#!/bin/bash

# Exit on error
set -e

echo "Deploying JobBot..."

# Pull latest changes
echo "Pulling latest changes..."
git pull origin main

# Build and start containers
echo "Building and starting containers..."
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Initialize database if needed
echo "Initializing database..."
sleep 5  # Wait for database to be ready
docker-compose exec -T bot python -c "from database import Database; Database().create_tables()"

echo "Deployment complete! The bot should be running now."
echo "Check logs with: docker-compose logs -f bot"

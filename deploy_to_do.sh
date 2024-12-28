#!/bin/bash

# Exit on error
set -e

# Load environment variables
source .env

# Check if doctl is installed
if ! command -v doctl &> /dev/null; then
    echo "doctl is not installed. Installing..."
    # Download latest version
    curl -sL https://github.com/digitalocean/doctl/releases/latest/download/doctl-1.101.0-linux-amd64.tar.gz | tar -xzv
    sudo mv doctl /usr/local/bin
fi

# Create .do directory if it doesn't exist
mkdir -p .do

# Authenticate with DigitalOcean
echo "Authenticating with DigitalOcean..."
doctl auth init -t "${DO_ACCESS_TOKEN}"

# Create app if it doesn't exist
echo "Creating/Updating DigitalOcean App..."
if doctl apps list | grep -q "jobbot"; then
    echo "Updating existing app..."
    APP_ID=$(doctl apps list --format ID --no-header | head -n 1)
    doctl apps update $APP_ID --spec .do/app.yaml
else
    echo "Creating new app..."
    doctl apps create --spec .do/app.yaml
fi

# Deploy the app
echo "Deploying the app..."
APP_ID=$(doctl apps list --format ID --no-header | head -n 1)
doctl apps create-deployment $APP_ID

echo "Deployment initiated! Check the status in your DigitalOcean dashboard."
echo "App URL will be available in the dashboard once deployment is complete."

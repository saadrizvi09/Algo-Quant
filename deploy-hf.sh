#!/bin/bash

# AlgoQuant Backend - Hugging Face Deployment Script
# Run this script to quickly deploy your backend to Hugging Face Spaces

set -e  # Exit on error

echo "🚀 AlgoQuant Backend - Hugging Face Deployment"
echo "=============================================="
echo ""

# Check if huggingface-cli is installed
if ! command -v huggingface-cli &> /dev/null; then
    echo "❌ Hugging Face CLI not found. Installing..."
    pip install huggingface_hub
fi

# Login check
echo "Checking Hugging Face authentication..."
if ! huggingface-cli whoami &> /dev/null; then
    echo "Please login to Hugging Face:"
    huggingface-cli login
fi

# Get username
USERNAME=$(huggingface-cli whoami | grep 'username:' | awk '{print $2}')
echo "✅ Logged in as: $USERNAME"
echo ""

# Get space name
read -p "Enter Space name (default: algoquant-backend): " SPACE_NAME
SPACE_NAME=${SPACE_NAME:-algoquant-backend}

echo ""
echo "📦 Creating Space: $SPACE_NAME..."

# Create Space
huggingface-cli repo create $SPACE_NAME --type space --space_sdk docker || echo "Space already exists, continuing..."

# Clone Space repository
echo ""
echo "📥 Cloning Space repository..."
TEMP_DIR=$(mktemp -d)
git clone https://huggingface.co/spaces/$USERNAME/$SPACE_NAME $TEMP_DIR

# Copy backend files
echo ""
echo "📂 Copying backend files..."
cd backend
cp -r * $TEMP_DIR/
cp .gitignore $TEMP_DIR/ 2>/dev/null || true

# Rename README
cd $TEMP_DIR
if [ -f "README_HF.md" ]; then
    mv README_HF.md README.md
fi

# Commit and push
echo ""
echo "⬆️  Pushing to Hugging Face..."
git add .
git commit -m "Deploy AlgoQuant Backend to Hugging Face Spaces" || echo "No changes to commit"
git push

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Your API will be available at:"
echo "   https://$USERNAME-$SPACE_NAME.hf.space"
echo ""
echo "📚 API Documentation:"
echo "   https://$USERNAME-$SPACE_NAME.hf.space/docs"
echo ""
echo "⚙️  Don't forget to:"
echo "   1. Add DATABASE_URL secret in Space settings"
echo "   2. Add SECRET_KEY secret in Space settings"
echo "   3. Wait for Docker build to complete (check Logs tab)"
echo ""
echo "🎉 Happy trading!"

# Cleanup
cd ..
rm -rf $TEMP_DIR

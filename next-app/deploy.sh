#!/bin/bash
# Simple deployment script for Next.js frontend

# Exit on error
set -e

echo "Building Next.js app..."
npm install
npm run build

echo "Deployment build complete."
echo "To deploy, upload the .next, package.json, and .env.production to your Node.js host or use Vercel/Netlify."

#!/bin/bash
# Auto-generated release creation script

set -e

# Check arguments
if [ $# -eq 0 ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 1.2.3"
    exit 1
fi

VERSION=$1

# Validate version format (semantic versioning)
if ! [[ $VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: Version must be in format X.Y.Z (e.g., 1.2.3)"
    exit 1
fi

echo "Creating release v$VERSION..."

# Update version in files
echo "Updating version numbers..."
# Add version update commands here based on project type

# Create git tag
echo "Creating git tag..."
git tag -a "v$VERSION" -m "Release version $VERSION"

# Push tag
echo "Pushing tag to remote..."
git push origin "v$VERSION"

echo "✓ Release v$VERSION created successfully!"
echo "GitHub will automatically create a release from the tag."

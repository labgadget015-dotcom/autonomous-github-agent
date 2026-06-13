#!/bin/bash
# Auto-generated release tagger
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Release Creation Script${NC}"
echo ""

# Get current version from git tags
CURRENT_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
echo "Current version: $CURRENT_VERSION"

# Parse version numbers
VERSION=${CURRENT_VERSION#v}
IFS='.' read -ra VERSION_PARTS <<< "$VERSION"
MAJOR=${VERSION_PARTS[0]}
MINOR=${VERSION_PARTS[1]}
PATCH=${VERSION_PARTS[2]}

# Ask for version bump type
echo ""
echo "Select version bump type:"
echo "1) Patch (v$MAJOR.$MINOR.$((PATCH+1)))"
echo "2) Minor (v$MAJOR.$((MINOR+1)).0)"
echo "3) Major (v$((MAJOR+1)).0.0)"
echo "4) Custom"
read -r -p "Enter choice [1-4]: " choice

case $choice in
    1)
        NEW_VERSION="v$MAJOR.$MINOR.$((PATCH+1))"
        ;;
    2)
        NEW_VERSION="v$MAJOR.$((MINOR+1)).0"
        ;;
    3)
        NEW_VERSION="v$((MAJOR+1)).0.0"
        ;;
    4)
        read -r -p "Enter custom version (e.g., v1.2.3): " NEW_VERSION
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${YELLOW}Creating release: $NEW_VERSION${NC}"

# Get commit messages since last tag
echo ""
echo "Recent changes:"
git log "$CURRENT_VERSION"..HEAD --oneline --decorate

# Confirm
echo ""
read -r -p "Proceed with release $NEW_VERSION? [y/N]: " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "Release cancelled"
    exit 0
fi

# Create tag
git tag -a "$NEW_VERSION" -m "Release $NEW_VERSION"

# Push tag
git push origin "$NEW_VERSION"

echo ""
echo -e "${GREEN}✅ Release $NEW_VERSION created successfully!${NC}"
echo "View release: https://github.com/$(git remote get-url origin | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/releases/tag/$NEW_VERSION"

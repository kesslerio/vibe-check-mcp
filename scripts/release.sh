#!/bin/bash

# Publish Release Script
# This script handles the full release process for Vibe Check MCP

set -e

echo "🚀 Publishing Vibe Check MCP Release"
echo "===================================="

# Ensure we're on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "❌ Error: Must be on main branch to release"
    echo "   Current branch: $CURRENT_BRANCH"
    exit 1
fi

# Ensure working directory is clean
if [ -n "$(git status --porcelain)" ]; then
    echo "❌ Error: Working directory is not clean"
    echo "   Please commit or stash your changes"
    exit 1
fi

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull

# Run tests
echo "🧪 Running tests..."
PYTHONPATH=src:. pytest

# Run linting and type checking
echo "🔍 Running linting and type checks..."
if command -v black &> /dev/null; then
    black --check src/ tests/
fi
if command -v mypy &> /dev/null; then
    mypy src/
fi

# Get current version from VERSION file
if [ -f "VERSION" ]; then
    CURRENT_VERSION=$(cat VERSION)
else
    CURRENT_VERSION="0.0.0"
    echo "0.0.0" > VERSION
fi
echo "📌 Current version: $CURRENT_VERSION"

# Ask for new version
echo ""
echo "🔢 What type of release is this?"
echo "1) Patch (bug fixes) - e.g., 0.1.0 -> 0.1.1"
echo "2) Minor (new features) - e.g., 0.1.0 -> 0.2.0"  
echo "3) Major (breaking changes) - e.g., 0.1.0 -> 1.0.0"
echo "4) Custom version"
read -p "Enter choice (1-4): " RELEASE_TYPE

case $RELEASE_TYPE in
    1) 
        # Parse version and increment patch
        IFS='.' read -ra VERSION_PARTS <<< "$CURRENT_VERSION"
        MAJOR=${VERSION_PARTS[0]}
        MINOR=${VERSION_PARTS[1]}
        PATCH=$((${VERSION_PARTS[2]} + 1))
        NEW_VERSION="$MAJOR.$MINOR.$PATCH"
        ;;
    2) 
        # Parse version and increment minor
        IFS='.' read -ra VERSION_PARTS <<< "$CURRENT_VERSION"
        MAJOR=${VERSION_PARTS[0]}
        MINOR=$((${VERSION_PARTS[1]} + 1))
        NEW_VERSION="$MAJOR.$MINOR.0"
        ;;
    3) 
        # Parse version and increment major
        IFS='.' read -ra VERSION_PARTS <<< "$CURRENT_VERSION"
        MAJOR=$((${VERSION_PARTS[0]} + 1))
        NEW_VERSION="$MAJOR.0.0"
        ;;
    4)
        read -p "Enter custom version (e.g., 0.1.0): " NEW_VERSION
        ;;
    *) 
        echo "Invalid choice"; exit 1 
        ;;
esac

echo "🔄 Updating version to: $NEW_VERSION"

# Update version in VERSION file
echo "$NEW_VERSION" > VERSION

# Update changelog
echo ""
echo "📝 Please update CHANGELOG.md with the new version details"
echo "   New version: $NEW_VERSION"
if [ ! -f "CHANGELOG.md" ]; then
    echo "Creating CHANGELOG.md..."
    cat > CHANGELOG.md << EOF
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [${NEW_VERSION}] - $(date +%Y-%m-%d)

### Added
- Initial release of Vibe Check MCP
- Anti-pattern detection for code review
- GitHub integration for issues and PRs
- Educational coaching system

### Changed
- N/A

### Fixed
- N/A

EOF
fi
read -p "Press enter when CHANGELOG.md is updated..."

# Commit version bump and changelog
echo "📝 Committing version bump..."
git add VERSION CHANGELOG.md
git commit -m "Bump version to $NEW_VERSION"

# Create git tag
echo "🏷️  Creating git tag..."
git tag "v$NEW_VERSION"

# Push changes and tags
echo "⬆️  Pushing changes to GitHub..."
git push
git push --tags

# Create GitHub release
echo "📋 Creating GitHub release..."
if command -v gh &> /dev/null; then
    gh release create "v$NEW_VERSION" \
        --title "Vibe Check MCP v$NEW_VERSION" \
        --notes "See CHANGELOG.md for details" \
        --latest
else
    echo "⚠️  GitHub CLI not found. Please create the release manually at:"
    echo "   https://github.com/kesslerio/vibe-check-mcp/releases/new?tag=v$NEW_VERSION"
fi

echo ""
echo "✅ Release v$NEW_VERSION completed successfully!"
echo ""
echo "📋 Post-release checklist:"
echo "[ ] Test the MCP server with the new version"
echo "[ ] Update any documentation if needed"
echo "[ ] Announce the release if significant"
echo ""
echo "🔗 Installation command for users:"
echo "   git clone https://github.com/kesslerio/vibe-check-mcp.git"
echo "   cd vibe-check-mcp"
echo "   pip install -r requirements.txt"
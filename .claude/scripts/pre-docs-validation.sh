#!/bin/bash

# Pre-Documentation Validation Hook
# Ensures the three critical documentation files exist and are ready for updates
# Usage: Called automatically by project-docs-curator agent

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "🔍 Pre-Documentation Validation Starting..."

# Define the three critical files in order
DOCS=(
    "CLAUDE.md"
    "ProjectContextEngineering.md" 
    "ProjectTasks.md"
)

VALIDATION_ERRORS=0

# Function to check file existence and basic structure
check_file() {
    local file="$1"
    local position="$2"
    
    echo "[$position/3] Checking $file..."
    
    if [[ ! -f "$file" ]]; then
        echo "  ❌ ERROR: $file does not exist"
        ((VALIDATION_ERRORS++))
        return 1
    fi
    
    if [[ ! -r "$file" ]]; then
        echo "  ❌ ERROR: $file is not readable"
        ((VALIDATION_ERRORS++))
        return 1
    fi
    
    if [[ ! -s "$file" ]]; then
        echo "  ⚠️  WARNING: $file is empty"
    fi
    
    # Check if file has been modified in the last 30 days
    if [[ $(find "$file" -mtime +30 2>/dev/null) ]]; then
        echo "  ⚠️  WARNING: $file hasn't been updated in 30+ days"
    fi
    
    echo "  ✅ $file exists and is accessible"
    return 0
}

# Function to validate file headers and structure
validate_structure() {
    local file="$1"
    
    case "$file" in
        "CLAUDE.md")
            if ! grep -q "^# .*- Claude Context" "$file" 2>/dev/null; then
                echo "  ⚠️  WARNING: $file missing expected header format"
            fi
            if ! grep -q "Version:" "$file" 2>/dev/null; then
                echo "  ⚠️  WARNING: $file missing version information"
            fi
            ;;
        "ProjectContextEngineering.md")
            if ! grep -q "^# Project Context" "$file" 2>/dev/null; then
                echo "  ⚠️  WARNING: $file missing expected header format"
            fi
            if ! grep -q "Date:" "$file" 2>/dev/null; then
                echo "  ⚠️  WARNING: $file missing date information"
            fi
            ;;
        "ProjectTasks.md")
            if ! grep -q "^# Project Tasks" "$file" 2>/dev/null; then
                echo "  ⚠️  WARNING: $file missing expected header format"
            fi
            if ! grep -q "Session Date:" "$file" 2>/dev/null; then
                echo "  ⚠️  WARNING: $file missing session date"
            fi
            ;;
    esac
}

# Main validation loop
echo ""
echo "📋 Validating Three Critical Documentation Files (in order):"
echo "   1. CLAUDE.md → 2. ProjectContextEngineering.md → 3. ProjectTasks.md"
echo ""

for i in "${!DOCS[@]}"; do
    file="${DOCS[$i]}"
    position=$((i + 1))
    
    if check_file "$file" "$position"; then
        validate_structure "$file"
    fi
    echo ""
done

# Check for .claude directory structure
echo "🏗️  Checking .claude directory structure..."
if [[ ! -d ".claude" ]]; then
    echo "  ❌ ERROR: .claude directory missing"
    ((VALIDATION_ERRORS++))
else
    echo "  ✅ .claude directory exists"
    
    if [[ ! -d ".claude/agents" ]]; then
        echo "  ❌ ERROR: .claude/agents directory missing"
        ((VALIDATION_ERRORS++))
    else
        echo "  ✅ .claude/agents directory exists"
    fi
    
    if [[ ! -d ".claude/scripts" ]]; then
        echo "  ❌ ERROR: .claude/scripts directory missing"
        ((VALIDATION_ERRORS++))
    else
        echo "  ✅ .claude/scripts directory exists"
    fi
fi

# Check project type and architecture
echo ""
echo "🏛️  Detecting project architecture..."
if [[ -f "package.json" ]] && [[ -f "next.config.js" ]]; then
    echo "  ✅ React/Next.js project detected"
    ARCHITECTURE="React/Next.js"
elif [[ -f "package.json" ]]; then
    echo "  ✅ Node.js project detected"
    ARCHITECTURE="Node.js"
elif [[ -f "app.py" ]] || [[ -f "main.py" ]]; then
    echo "  ✅ Python project detected"
    ARCHITECTURE="Python"
else
    echo "  ⚠️  WARNING: Unable to detect project architecture"
    ARCHITECTURE="Unknown"
fi

# Store architecture for post-validation
echo "$ARCHITECTURE" > ".claude/tmp_architecture" 2>/dev/null || true

# Final validation summary
echo ""
echo "📊 Pre-Validation Summary:"
echo "   Architecture: $ARCHITECTURE"
echo "   Critical Files: ${#DOCS[@]}/3 required files checked"
echo "   Errors: $VALIDATION_ERRORS"

if [[ $VALIDATION_ERRORS -eq 0 ]]; then
    echo ""
    echo "✅ PRE-VALIDATION PASSED"
    echo "   Ready for documentation workflow: CLAUDE.md → ProjectContextEngineering.md → ProjectTasks.md"
    exit 0
else
    echo ""
    echo "❌ PRE-VALIDATION FAILED"
    echo "   Please fix $VALIDATION_ERRORS error(s) before proceeding"
    exit 1
fi
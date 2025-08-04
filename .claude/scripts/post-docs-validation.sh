#!/bin/bash

# Post-Documentation Validation Hook
# Validates that all three critical documentation files are updated and consistent
# Usage: Called automatically by project-docs-curator agent after documentation updates

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "🔍 Post-Documentation Validation Starting..."

# Define the three critical files in order
DOCS=(
    "CLAUDE.md"
    "ProjectContextEngineering.md" 
    "ProjectTasks.md"
)

VALIDATION_ERRORS=0
VALIDATION_WARNINGS=0

# Get architecture from pre-validation (if available)
ARCHITECTURE="Unknown"
if [[ -f ".claude/tmp_architecture" ]]; then
    ARCHITECTURE=$(cat ".claude/tmp_architecture")
fi

# Function to check if file was recently updated (within last 5 minutes)
check_recent_update() {
    local file="$1"
    local position="$2"
    
    echo "[$position/3] Validating $file updates..."
    
    if [[ ! -f "$file" ]]; then
        echo "  ❌ ERROR: $file disappeared during documentation update"
        ((VALIDATION_ERRORS++))
        return 1
    fi
    
    # Check if file was modified in the last 5 minutes
    if ! find "$file" -mmin -5 2>/dev/null | grep -q .; then
        echo "  ⚠️  WARNING: $file was not updated in this session"
        ((VALIDATION_WARNINGS++))
    else
        echo "  ✅ $file was recently updated"
    fi
    
    return 0
}

# Function to validate content consistency
validate_content() {
    local file="$1"
    
    case "$file" in
        "CLAUDE.md")
            # Check for outdated Flask references if this is a React project
            if [[ "$ARCHITECTURE" == "React/Next.js" ]] && grep -qi "flask" "$file" 2>/dev/null; then
                echo "  ❌ ERROR: $file contains outdated Flask references in React project"
                ((VALIDATION_ERRORS++))
            fi
            
            # Check for required sections
            if ! grep -q "Version:" "$file" 2>/dev/null; then
                echo "  ❌ ERROR: $file missing version information"
                ((VALIDATION_ERRORS++))
            fi
            
            if ! grep -q "Last Updated:" "$file" 2>/dev/null; then
                echo "  ❌ ERROR: $file missing last updated date"
                ((VALIDATION_ERRORS++))
            fi
            ;;
            
        "ProjectContextEngineering.md")
            # Check for architecture consistency
            if [[ "$ARCHITECTURE" == "React/Next.js" ]] && ! grep -qi "react\|next.js" "$file" 2>/dev/null; then
                echo "  ❌ ERROR: $file missing React/Next.js architecture details"
                ((VALIDATION_ERRORS++))
            fi
            
            # Check for required sections
            if ! grep -q "Date:" "$file" 2>/dev/null; then
                echo "  ❌ ERROR: $file missing date information"
                ((VALIDATION_ERRORS++))
            fi
            ;;
            
        "ProjectTasks.md")
            # Check for session information
            if ! grep -q "Session Date:" "$file" 2>/dev/null; then
                echo "  ❌ ERROR: $file missing session date"
                ((VALIDATION_ERRORS++))
            fi
            
            # Warn about potential historical content - check for task completion patterns
            if grep -qi "(completed)\|(finished)\|(done):" "$file" 2>/dev/null; then
                echo "  ⚠️  WARNING: $file may contain historical completed tasks (should be current/future only)"
                ((VALIDATION_WARNINGS++))
            fi
            ;;
    esac
}

# Function to check cross-document consistency
check_consistency() {
    echo ""
    echo "🔗 Checking cross-document consistency..."
    
    # Extract version/date information
    CLAUDE_VERSION=""
    if [[ -f "CLAUDE.md" ]]; then
        CLAUDE_VERSION=$(grep "Version:" "CLAUDE.md" 2>/dev/null | head -1 | sed 's/.*Version:\s*//' | sed 's/\s.*//' || echo "")
    fi
    
    CONTEXT_DATE=""
    if [[ -f "ProjectContextEngineering.md" ]]; then
        CONTEXT_DATE=$(grep "Date:" "ProjectContextEngineering.md" 2>/dev/null | head -1 | sed 's/.*Date:\s*//' | sed 's/\s.*//' || echo "")
    fi
    
    TASKS_DATE=""
    if [[ -f "ProjectTasks.md" ]]; then
        TASKS_DATE=$(grep "Session Date:" "ProjectTasks.md" 2>/dev/null | head -1 | sed 's/.*Session Date:\s*//' | sed 's/\s.*//' || echo "")
    fi
    
    # Check for architecture consistency across files - allow transformation context
    if [[ "$ARCHITECTURE" == "React/Next.js" ]]; then
        for file in "${DOCS[@]}"; do
            if [[ -f "$file" ]] && grep -qi "flask" "$file" 2>/dev/null; then
                # Allow Flask references in transformation/migration context
                if ! grep -qi "flask.*to.*react\|react.*transformation\|migrated.*from.*flask\|flask.*transformation" "$file" 2>/dev/null; then
                    echo "  ❌ ERROR: $file contains inappropriate Flask references in React project"
                    ((VALIDATION_ERRORS++))
                fi
            fi
        done
    fi
    
    echo "  📅 Detected versions/dates:"
    echo "     CLAUDE.md Version: ${CLAUDE_VERSION:-'Not found'}"
    echo "     ProjectContextEngineering.md Date: ${CONTEXT_DATE:-'Not found'}"
    echo "     ProjectTasks.md Session Date: ${TASKS_DATE:-'Not found'}"
}

# Function to validate file sizes (prevent empty files)
check_file_sizes() {
    echo ""
    echo "📏 Checking file completeness..."
    
    for file in "${DOCS[@]}"; do
        if [[ -f "$file" ]]; then
            size=$(wc -c < "$file" 2>/dev/null || echo "0")
            lines=$(wc -l < "$file" 2>/dev/null || echo "0")
            
            if [[ $size -lt 100 ]]; then
                echo "  ❌ ERROR: $file is too small ($size bytes) - likely incomplete"
                ((VALIDATION_ERRORS++))
            elif [[ $lines -lt 10 ]]; then
                echo "  ⚠️  WARNING: $file has few lines ($lines) - may be incomplete"
                ((VALIDATION_WARNINGS++))
            else
                echo "  ✅ $file has adequate content ($lines lines, $size bytes)"
            fi
        fi
    done
}

# Main validation process
echo ""
echo "📋 Post-Validating Three Critical Documentation Files:"
echo "   Architecture: $ARCHITECTURE"
echo ""

# Check each file for updates and content
for i in "${!DOCS[@]}"; do
    file="${DOCS[$i]}"
    position=$((i + 1))
    
    if check_recent_update "$file" "$position"; then
        validate_content "$file"
    fi
    echo ""
done

# Run consistency checks
check_consistency
check_file_sizes

# Final validation summary
echo ""
echo "📊 Post-Validation Summary:"
echo "   Architecture: $ARCHITECTURE"
echo "   Files Validated: ${#DOCS[@]}/3"
echo "   Errors: $VALIDATION_ERRORS"
echo "   Warnings: $VALIDATION_WARNINGS"

# Clean up temporary files
rm -f ".claude/tmp_architecture" 2>/dev/null || true

# Determine exit status
if [[ $VALIDATION_ERRORS -eq 0 ]]; then
    if [[ $VALIDATION_WARNINGS -eq 0 ]]; then
        echo ""
        echo "✅ POST-VALIDATION PASSED (Perfect)"
        echo "   All three documentation files are updated and consistent"
        echo "   Workflow completed: CLAUDE.md → ProjectContextEngineering.md → ProjectTasks.md ✅"
    else
        echo ""
        echo "✅ POST-VALIDATION PASSED (With Warnings)"
        echo "   Documentation workflow completed with $VALIDATION_WARNINGS warning(s)"
        echo "   Consider addressing warnings in next update cycle"
    fi
    exit 0
else
    echo ""
    echo "❌ POST-VALIDATION FAILED"
    echo "   $VALIDATION_ERRORS error(s) found in documentation workflow"
    echo "   Please fix errors and re-run validation"
    exit 1
fi
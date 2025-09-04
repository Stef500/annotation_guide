#!/bin/bash

# Test script for CI/CD pipeline validation
# Tests multiple LaTeX documents to ensure pipeline robustness

set -e

echo "🧪 Starting CI/CD Pipeline Test Suite..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run a test
run_test() {
    local test_name="$1"
    local tex_file="$2"
    local expected_pdf="$3"
    
    echo -e "\n${YELLOW}Testing: $test_name${NC}"
    
    # Clean previous output
    rm -f "output/$expected_pdf"
    
    # Try to compile
    if xelatex -output-directory=output -interaction=nonstopmode "$tex_file" >/dev/null 2>&1; then
        if [ -f "output/$expected_pdf" ]; then
            echo -e "${GREEN}✓ PASSED: $test_name${NC}"
            ((TESTS_PASSED++))
            return 0
        else
            echo -e "${RED}✗ FAILED: $test_name - PDF not generated${NC}"
            ((TESTS_FAILED++))
            return 1
        fi
    else
        echo -e "${RED}✗ FAILED: $test_name - Compilation error${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Create output directory
mkdir -p output

echo "Setting up test environment..."

# Test 1: Basic pipeline test document
echo -e "\n${YELLOW}=== Test 1: Pipeline Validation Document ===${NC}"
run_test "Pipeline Test Document" "templates/test-pipeline.tex" "test-pipeline.pdf"

# Test 2: Main template (if it exists and has required sections)
if [ -f "templates/main.tex" ]; then
    echo -e "\n${YELLOW}=== Test 2: Main Template ===${NC}"
    
    # Check if all required section files exist
    missing_sections=()
    for section in "sections/title-page.tex" "sections/introduction.tex" "sections/annotation-guidelines.tex" "sections/examples.tex"; do
        if [ ! -f "templates/$section" ]; then
            missing_sections+=("$section")
        fi
    done
    
    if [ ${#missing_sections[@]} -eq 0 ]; then
        run_test "Main Template" "templates/main.tex" "main.pdf"
    else
        echo -e "${YELLOW}⚠ SKIPPED: Main template - Missing sections: ${missing_sections[*]}${NC}"
    fi
fi

# Test 3: Test document (if it exists)
if [ -f "templates/test-document.tex" ]; then
    echo -e "\n${YELLOW}=== Test 3: Test Document ===${NC}"
    run_test "Test Document" "templates/test-document.tex" "test-document.pdf"
fi

# Summary
echo -e "\n${YELLOW}=== Test Results Summary ===${NC}"
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All tests passed! Pipeline is ready for production.${NC}"
    
    # List generated PDFs
    echo -e "\n${YELLOW}Generated PDFs:${NC}"
    ls -la output/*.pdf 2>/dev/null || echo "No PDFs found in output/"
    
    exit 0
else
    echo -e "\n${RED}💥 Some tests failed. Check the compilation logs.${NC}"
    
    # Show any log files
    echo -e "\n${YELLOW}Available log files:${NC}"
    ls -la output/*.log 2>/dev/null || echo "No log files found"
    
    exit 1
fi
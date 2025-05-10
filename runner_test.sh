#!/bin/bash

show_help() {
    echo "Usage: ./runner_test.sh [OPTIONS]"
    echo "Options:"
    echo "  -h, --help           Show this help message"
    echo "  -v, --verbose        Run tests in verbose mode"
    echo "  -f, --file FILE      Run specific test file"
    echo "  -t, --test TEST      Run specific test function"
    echo "  -m, --marker MARKER  Run tests with specific marker"
    echo "  -c, --coverage       Run tests with coverage report"
    echo "  -w, --watch         Run tests in watch mode (rerun on file changes)"
    echo ""
    echo "Examples:"
    echo "  ./runner_test.sh                    # Run all tests"
    echo "  ./runner_test.sh -v                 # Run tests in verbose mode"
    echo "  ./runner_test.sh -f test_main.py    # Run specific test file"
    echo "  ./runner_test.sh -t test_create_vpn_config  # Run specific test"
    echo "  ./runner_test.sh -c                 # Run with coverage"
}

VERBOSE=""
FILE=""
TEST=""
MARKER=""
COVERAGE=""
WATCH=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--verbose)
            VERBOSE="-v"
            shift
            ;;
        -f|--file)
            FILE="test/$2"
            shift 2
            ;;
        -t|--test)
            TEST="::$2"
            shift 2
            ;;
        -m|--marker)
            MARKER="-m $2"
            shift 2
            ;;
        -c|--coverage)
            COVERAGE="--cov=. --cov-report=term-missing"
            shift
            ;;
        -w|--watch)
            WATCH="--watch"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

CMD="pytest"

[[ -n "$VERBOSE" ]] && CMD="$CMD $VERBOSE"
[[ -n "$COVERAGE" ]] && CMD="$CMD $COVERAGE"
[[ -n "$MARKER" ]] && CMD="$CMD $MARKER"
[[ -n "$WATCH" ]] && CMD="$CMD $WATCH"

if [[ -n "$FILE" ]]; then
    CMD="$CMD $FILE"
    [[ -n "$TEST" ]] && CMD="$CMD$TEST"
fi

echo "Running: $CMD"
$CMD

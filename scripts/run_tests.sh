#!/bin/bash

# Run tests with coverage
echo "Running tests with coverage..."
pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html

# Run only unit tests
# pytest tests/unit/ -v

# Run only integration tests
# pytest tests/integration/ -v

# Run specific test
# pytest tests/integration/test_auth_api.py -v
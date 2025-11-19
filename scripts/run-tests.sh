#!/usr/bin/env bash
set -euo pipefail
echo "Run tests for each package under packages/*"

for pkg in packages/*; do
  if [ -d "$pkg" ]; then
    echo "=== Package: $pkg ==="
    pushd "$pkg" >/dev/null
    if [ -f "pyproject.toml" ] || [ -f "setup.py" ]; then
      python -m pip install --upgrade pip
      python -m pip install -e .
    elif [ -f "requirements.txt" ]; then
      python -m pip install --upgrade pip
      python -m pip install -r requirements.txt
    else
      echo "No install file for $pkg"
    fi

    if [ -d "tests" ] || ls *_test.py >/dev/null 2>&1 || ls tests.py >/dev/null 2>&1; then
      python -m pytest -q || { echo "Tests failed in $pkg"; exit 1; }
    else
      echo "No tests found for $pkg"
    fi
    popd >/dev/null
  fi
done

echo "All package tests completed."

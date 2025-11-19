#!/usr/bin/env bash
set -euo pipefail

# Configuration — modifiez si besoin
OWNER="kabir308"
NEW_REPO_NAME="github-clients"
REPO1="https://github.com/kabir308/RepoForgeX.git"
REPO1_PREFIX="packages/RepoForgeX"
REPO1_BRANCH="main"
REPO2="https://github.com/kabir308/-GitHub-Innovation-Promoter-Agent-Agent-Promoteur-d-Innovation-GitHub.git"
REPO2_PREFIX="packages/GitHub-Innovation-Promoter-Agent"
REPO2_BRANCH="main"

# Temp workspace
TMPDIR="$(mktemp -d)"
echo "Workspace: $TMPDIR"
cd "$TMPDIR"

echo "Initializing empty git repo for monorepo..."
git init "$NEW_REPO_NAME"
cd "$NEW_REPO_NAME"

# Add first repo as subtree
echo "Adding first repo as subtree: $REPO1 -> $REPO1_PREFIX"
git remote add repo1 "$REPO1"
git fetch repo1
git subtree add --prefix="$REPO1_PREFIX" repo1 "$REPO1_BRANCH"

# Add second repo as subtree
echo "Adding second repo as subtree: $REPO2 -> $REPO2_PREFIX"
git remote add repo2 "$REPO2"
git fetch repo2
git subtree add --prefix="$REPO2_PREFIX" repo2 "$REPO2_BRANCH"

# Create standard files
echo "Adding standard files (README, CI, scripts, .gitignore)..."

# README
cat > README.md <<'EOF'
# github-clients — Monorepo (RepoForgeX + GitHub Innovation Promoter Agent)

But
Ce dépôt centralise deux projets existants :
- packages/RepoForgeX
- packages/GitHub-Innovation-Promoter-Agent

Il conserve l'historique Git de chaque projet (import via git subtree).

Structure
- packages/
  - RepoForgeX/
  - GitHub-Innovation-Promoter-Agent/

Commandes locales
- Créer et activer un virtualenv (par package) :
  cd packages/<package>
  python -m venv .venv && source .venv/bin/activate
  pip install -r requirements.txt  # ou pip install -e . si le package est packagé

- Lancer tous les tests depuis la racine :
  ./scripts/run-tests.sh

CI
- GitHub Actions exécute les tests pour chaque package sous packages/* (matrix Python 3.10, 3.11).

Notes
- Ce monorepo est public selon votre demande.
- Les sources importées conservent leur historique (git subtree add sans --squash).
EOF

# .gitignore
cat > .gitignore <<'EOF'
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/

# Editor
.vscode/
.idea/
*.swp

# OS
.DS_Store

# Optional backup
repo-backup/
EOF

# scripts/run-tests.sh
mkdir -p scripts
cat > scripts/run-tests.sh <<'EOF'
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
EOF
chmod +x scripts/run-tests.sh

# GitHub Actions CI
mkdir -p .github/workflows
cat > .github/workflows/monorepo-ci.yml <<'EOF'
name: Monorepo CI (Python packages)

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.10, 3.11]
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies & run tests for each package
        run: |
          set -euo pipefail
          for pkg in packages/*; do
            if [ -d "$pkg" ]; then
              echo "=== Package: $pkg ==="
              cd "$pkg"
              if [ -f "pyproject.toml" ] || [ -f "setup.py" ]; then
                python -m pip install --upgrade pip
                python -m pip install -e .
              elif [ -f "requirements.txt" ]; then
                python -m pip install --upgrade pip
                python -m pip install -r requirements.txt
              else
                echo "No install file (pyproject/setup/requirements). Skipping install for $pkg"
              fi
              if [ -d "tests" ] || ls *_test.py >/dev/null 2>&1 || ls tests.py >/dev/null 2>&1; then
                python -m pytest -q || exit 1
              else
                echo "No tests found for $pkg"
              fi
              cd - >/dev/null
            fi
          done
        shell: bash
EOF

# Commit changes
git add .
git commit -m "Create monorepo skeleton and import subtrees: RepoForgeX + GitHub Innovation Promoter Agent"

echo "Creating GitHub repo via gh CLI: $OWNER/$NEW_REPO_NAME (public)"
# Create repo on GitHub and push
gh repo create "${OWNER}/${NEW_REPO_NAME}" --public --source=. --remote=origin --push --confirm

echo "Monorepo created and pushed: https://github.com/${OWNER}/${NEW_REPO_NAME}"
echo "Workspace content at: $(pwd)"
echo "Done."

# RepoForgeX — Hardened, Dockerized & GitHub App ready 🚀

[![CI Status](https://github.com/kabir308/RepoForgeX/workflows/CI%20-%20tests%20%26%20lint/badge.svg)](https://github.com/kabir308/RepoForgeX/actions)
[![codecov](https://codecov.io/gh/kabir308/RepoForgeX/branch/main/graph/badge.svg)](https://codecov.io/gh/kabir308/RepoForgeX)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

RepoForgeX automatise la création, l'initialisation, le scaffolding et la synchronisation de nombreux repositories GitHub.

## ✨ Version 0.3.0 - Revolutionary Features!

Cette version ajoute des **fonctionnalités révolutionnaires**:
- 🤖 **AI-powered repository naming suggestions** - Get intelligent name suggestions based on descriptions
- 📝 **Auto-template generation** - Automatically create issue templates, PR templates, security policies, and code of conduct
- 📊 **Repository health scoring** - Instant health assessments with actionable recommendations
- 📈 **Advanced analytics & insights** - Track patterns, get smart recommendations, export reports
- 🔄 **Batch operations with rollback** - Transaction-like operations with automatic rollback on failure

### Plus les fonctionnalités existantes:
- Validation stricte de la configuration (pydantic).
- Support d'authentification via GitHub App (JWT -> installation token).
- Dockerfile & docker-compose pour exécution en conteneur.
- Logs rotatifs et configuration d'environnement.
- Tests unitaires (pytest) et CI GitHub Actions.
- Mode dry-run, force, push parallèle.

📚 **[Read the Revolutionary Features Guide](REVOLUTIONARY_FEATURES.md)** for detailed documentation!

## Quickstart
1. Copier .env.example -> .env et renseigner :
   - GITHUB_TOKEN (optionnel si vous utilisez GitHub Token)
   - ou GITHUB_APP_ID, GITHUB_APP_PRIVATE_KEY (PEM), INSTALLATION_ID pour GitHub App auth
   - GITHUB_USER
   - REPOFORGEX_USE_SSH (0/1)
2. Installer dépendances & tests:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   pytest
   ```
3. Dry-run:
   ```bash
   export GITHUB_TOKEN=ghp_xxx
   python -m repoforgex.cli --config repos.yml --dry-run
   ```
4. **Try revolutionary features:**
   ```bash
   # Get name suggestions, auto-generate templates, check health, and get analytics
   python -m repoforgex.cli --config repos.yml \
     --suggest-names \
     --auto-templates \
     --health-check \
     --analytics
   ```
5. Docker:
   ```bash
   docker compose up --build
   ```

## Revolutionary Features Quick Examples

```bash
# AI-powered name suggestions
python -m repoforgex.cli --config repos.yml --suggest-names

# Auto-generate standard templates (issue, PR, security, code of conduct)
python -m repoforgex.cli --config repos.yml --auto-templates

# Check repository health and get recommendations
python -m repoforgex.cli --config repos.yml --health-check

# Get comprehensive analytics and insights
python -m repoforgex.cli --config repos.yml --analytics

# Combine all features for maximum benefit!
python -m repoforgex.cli --config repos.yml \
  --suggest-names --auto-templates --health-check --analytics
```

## Security notes
- Ne placez jamais vos clefs / tokens dans le code. Utilisez secrets GitHub Actions ou un secret manager.
- Préférez GitHub App pour org-wide automation (meilleure gouvernance).

Voir les fichiers ajoutés/modifiés pour plus de détails.

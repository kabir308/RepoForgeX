# RepoForgeX — Hardened, Dockerized & GitHub App ready

RepoForgeX automatise la création, l'initialisation, le scaffolding et la synchronisation de nombreux repositories GitHub.
Cette version ajoute :
- Validation stricte de la configuration (pydantic).
- Support d'authentification via GitHub App (JWT -> installation token).
- Dockerfile & docker-compose pour exécution en conteneur.
- Logs rotatifs et configuration d'environnement.
- Tests unitaires (pytest) et CI GitHub Actions.
- Mode dry-run, force, push parallèle (déjà existants).

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
4. Docker:
   ```bash
   docker compose up --build
   ```

## Security notes
- Ne placez jamais vos clefs / tokens dans le code. Utilisez secrets GitHub Actions ou un secret manager.
- Préférez GitHub App pour org-wide automation (meilleure gouvernance).

Voir les fichiers ajoutés/modifiés pour plus de détails.

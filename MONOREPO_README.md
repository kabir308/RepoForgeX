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

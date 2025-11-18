# Examples

This directory contains usage examples for RepoForgeX.

## Basic Usage

### Example 1: Create a Single Repository

Create a `repos.yml` file:

```yaml
repos:
  - name: my-awesome-project
    description: "My awesome new project"
    private: true

options:
  default_branch: main
  commit_message: "Initial commit from RepoForgeX"
  use_ssh: false
```

Run in dry-run mode to test:
```bash
export GITHUB_TOKEN=your_token_here
export GITHUB_USER=your_username
python -m repoforgex.cli --config repos.yml --dry-run
```

Run for real:
```bash
python -m repoforgex.cli --config repos.yml
```

### Example 2: Create Multiple Repositories with Templates

```yaml
repos:
  - name: python-service-1
    description: "Python microservice 1"
    private: true
    template: python-basic

  - name: python-service-2
    description: "Python microservice 2"
    private: true
    template: python-basic

  - name: frontend-app
    description: "Frontend application"
    private: true
    template: node-basic

options:
  default_branch: main
  commit_message: "Initial commit"
  use_ssh: false
```

### Example 3: Using GitHub App Authentication

Set up environment variables:
```bash
export GITHUB_APP_ID=123456
export GITHUB_APP_PRIVATE_KEY="/path/to/private-key.pem"
export INSTALLATION_ID=78910
export GITHUB_USER=your-org
```

Run the CLI:
```bash
python -m repoforgex.cli --config repos.yml
```

### Example 4: Using with Docker

Create a `.env` file:
```
GITHUB_TOKEN=ghp_your_token
GITHUB_USER=your_username
REPOFORGEX_USE_SSH=0
```

Run with Docker Compose:
```bash
docker compose up --build
```

The web API will be available at `http://localhost:5000`

### Example 5: Web API Usage

Start the web server:
```bash
python -m repoforgex.web
```

Check status:
```bash
curl http://localhost:5000/
curl http://localhost:5000/health
curl http://localhost:5000/repos
curl http://localhost:5000/status
```

## Advanced Configuration

### Custom Repository Paths

```yaml
repos:
  - name: project-1
    path: /path/to/local/project-1

  - name: project-2
    path: ./relative/path/project-2
```

### Override Owner (for Organizations)

```yaml
repos:
  - name: org-repo
    owner: my-organization
    description: "Repository in organization"
```

Or use the CLI flag:
```bash
python -m repoforgex.cli --owner my-organization
```

### Force Re-initialization

```bash
python -m repoforgex.cli --force
```

This will reinitialize local repositories even if they already exist.

### Parallel Processing

Control the number of parallel workers:
```bash
python -m repoforgex.cli --parallel 8
```

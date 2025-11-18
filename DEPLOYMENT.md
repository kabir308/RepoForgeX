# Deployment Guide

This guide explains how to deploy RepoForgeX in different environments.

## Local Development

1. Install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Set environment variables:
```bash
cp .env.example .env
# Edit .env with your GitHub credentials
```

3. Run tests:
```bash
pytest
```

4. Run CLI:
```bash
python -m repoforgex.cli --config repos.yml --dry-run
```

5. Run web server:
```bash
python -m repoforgex.web
```

## Docker Deployment

### Single Container

Build and run:
```bash
docker build -t repoforgex:latest .
docker run -p 5000:5000 \
  -e GITHUB_TOKEN=your_token \
  -e GITHUB_USER=your_user \
  -e REPOFORGEX_USE_SSH=0 \
  repoforgex:latest
```

### Docker Compose

1. Create `.env` file with your credentials
2. Start the service:
```bash
docker compose up -d
```

3. View logs:
```bash
docker compose logs -f
```

4. Stop the service:
```bash
docker compose down
```

## GitHub App Setup

### Creating a GitHub App

1. Go to Settings → Developer settings → GitHub Apps → New GitHub App
2. Set the following:
   - **Name**: RepoForgeX (or your preferred name)
   - **Homepage URL**: Your application URL
   - **Webhook URL**: Your webhook endpoint (optional)

3. Set permissions:
   - **Repository permissions**:
     - Contents: Read & Write
     - Metadata: Read-only

4. Generate a private key and download it

5. Install the app to your user/organization

6. Note the following values:
   - App ID
   - Installation ID (from the installation URL)
   - Private key (PEM file)

### Using GitHub App in RepoForgeX

Set environment variables:
```bash
export GITHUB_APP_ID=123456
export GITHUB_APP_PRIVATE_KEY="$(cat /path/to/private-key.pem)"
export INSTALLATION_ID=78910
export GITHUB_USER=your-org
```

Or in `.env` file:
```
GITHUB_APP_ID=123456
GITHUB_APP_PRIVATE_KEY=/path/to/private-key.pem
INSTALLATION_ID=78910
GITHUB_USER=your-org
```

## Production Deployment

### Using a WSGI Server

For production, use gunicorn instead of Flask's development server:

1. Install gunicorn:
```bash
pip install gunicorn
```

2. Run the web server:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 repoforgex.web:app
```

### Kubernetes Deployment

Example Kubernetes manifest:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: repoforgex
spec:
  replicas: 2
  selector:
    matchLabels:
      app: repoforgex
  template:
    metadata:
      labels:
        app: repoforgex
    spec:
      containers:
      - name: repoforgex
        image: repoforgex:latest
        ports:
        - containerPort: 5000
        env:
        - name: GITHUB_TOKEN
          valueFrom:
            secretKeyRef:
              name: repoforgex-secrets
              key: github-token
        - name: GITHUB_USER
          value: "your-user"
---
apiVersion: v1
kind: Service
metadata:
  name: repoforgex
spec:
  selector:
    app: repoforgex
  ports:
  - port: 80
    targetPort: 5000
  type: LoadBalancer
```

### Environment Variables

Required:
- `GITHUB_TOKEN` or `GITHUB_APP_ID` + `GITHUB_APP_PRIVATE_KEY` + `INSTALLATION_ID`
- `GITHUB_USER`: GitHub username or organization

Optional:
- `REPOFORGEX_USE_SSH`: Use SSH for git operations (0 or 1, default: 0)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `PORT`: Port for web server (default: 5000)
- `CONFIG_PATH`: Path to repos.yml (default: repos.yml)

## Security Considerations

1. **Never commit secrets**: Use environment variables or secret managers
2. **Use GitHub App**: Preferred for organization-wide automation
3. **Rotate tokens**: Regularly rotate access tokens
4. **Limit permissions**: Only grant necessary permissions
5. **Use HTTPS**: Always use HTTPS in production
6. **Container security**: Scan Docker images for vulnerabilities
7. **Network security**: Use firewalls and network policies

## Monitoring

The web API provides health check endpoints:

- `GET /`: Service information
- `GET /health`: Health check
- `GET /status`: Authentication status

Use these for monitoring and load balancer health checks.

## Troubleshooting

### Authentication Issues

If you get authentication errors:
1. Verify your token/credentials are correct
2. Check token permissions
3. Ensure the token hasn't expired
4. For GitHub App, verify installation ID is correct

### Network Issues

If repositories fail to create/push:
1. Check network connectivity
2. Verify GitHub API is accessible
3. Check firewall rules
4. Review logs for specific errors

### Docker Issues

If Docker build fails:
1. Ensure Docker is installed and running
2. Check Dockerfile syntax
3. Verify base image is available
4. Review build logs

## Support

For issues and questions:
- GitHub Issues: https://github.com/kabir308/repoforgex/issues
- Documentation: See README.md and EXAMPLES.md

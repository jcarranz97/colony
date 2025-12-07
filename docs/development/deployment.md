# Deployment Guide

This guide covers how Colony's components are deployed to various environments.

## Documentation Deployment

Colony's documentation is automatically deployed to GitHub Pages using GitHub Actions.

### GitHub Pages Setup

The documentation is built with MkDocs Material and deployed to GitHub Pages at:
`https://your-username.github.io/colony/`

### Automatic Deployment

Every push to the `main` branch automatically triggers a documentation build and deployment via GitHub Actions.

#### GitHub Actions Workflow

The deployment is handled by `.github/workflows/docs.yml`:

```yaml
name: Deploy Documentation
on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure Git Credentials
        run: |
          git config user.name github-actions[bot]
          git config user.email 41898282+github-actions[bot]@users.noreply.github.com
      
      - uses: actions/setup-python@v4
        with:
          python-version: 3.x
      
      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          key: ${{ github.ref }}
          path: .cache
      
      - name: Install dependencies
        run: pip install mkdocs-material
      
      - name: Deploy to GitHub Pages
        run: mkdocs gh-deploy --force
```

### Manual Deployment

To deploy documentation manually:

```bash
# Install dependencies
pip install mkdocs-material

# Deploy to GitHub Pages
mkdocs gh-deploy
```

### Repository Settings

Ensure your GitHub repository has the following settings:

1. **Go to Settings > Pages**
2. **Source**: Deploy from a branch
3. **Branch**: `gh-pages` 
4. **Folder**: `/ (root)`

The `gh-deploy` command automatically creates and manages the `gh-pages` branch.

### Local Preview

To preview documentation locally before deployment:

```bash
# Install dependencies
pip install mkdocs-material

# Serve locally
mkdocs serve

# Access at http://localhost:8000
```

### Troubleshooting

**Common Issues:**

- **Permission denied**: Ensure GitHub Actions has write permissions
- **Build fails**: Check that all referenced files exist in the docs folder
- **Pages not updating**: GitHub Pages can take a few minutes to reflect changes

**Debug Steps:**

1. Check GitHub Actions logs in the Actions tab
2. Verify all documentation files are committed
3. Ensure `mkdocs.yml` configuration is valid
4. Test build locally with `mkdocs build`

## Application Deployment

### Backend Deployment

*Coming soon - Docker containerization and deployment strategies*

### Frontend Deployment  

*Coming soon - Static site deployment options*

### Full Stack Deployment

*Coming soon - Complete deployment with Docker Compose*
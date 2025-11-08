# GitHub Actions Setup

This repository uses GitHub Actions for CI/CD. The workflow automatically runs on every push and pull request.

## Workflow Overview

The CI/CD pipeline consists of 4 jobs:

1. **Lint** - Runs flake8 and pylint to check code quality
2. **Test** - Runs pytest with coverage reporting
3. **Build Docker** - Builds and pushes Docker image to Docker Hub
4. **Create Pre-Release** - Creates a pre-release on main branch pushes

## Required Setup

The workflow uses **GitHub Container Registry (GHCR)** to store Docker images. No additional secrets are required!

### Automatic Authentication

The workflow automatically authenticates with GHCR using the built-in `GITHUB_TOKEN`. This means:

- ✅ No Docker Hub account needed
- ✅ No manual secret configuration required
- ✅ Images stored at `ghcr.io/YOUR_USERNAME/letterbox-list-generator`
- ✅ Integrated with GitHub Packages

### Making Images Public (Optional)

By default, GHCR packages are private. To make your images public:

1. Go to your GitHub profile
2. Click on **Packages**
3. Find **letterbox-list-generator**
4. Click **Package settings**
5. Scroll to **Danger Zone**
6. Click **Change visibility** → **Public**

## Workflow Triggers

The workflow runs on:

- **Push to main/develop branches** - Runs full pipeline
- **Pull requests to main/develop** - Runs lint and test only (no Docker push)
- **Manual trigger** - Can be triggered manually from Actions tab

## Pre-Release Strategy

When code is pushed to the `main` branch:

1. Tests pass ✅
2. Docker image is built and pushed ✅
3. A pre-release is automatically created with:
   - Auto-incremented version tag (e.g., `v0.0.1-pre.123`)
   - Changelog generated from git commits (all commits if no previous tag, or changes since last tag)
   - Docker images tagged as `latest-pre` and version tag

**First Release**: When there are no existing tags, the workflow will create `v0.0.1-pre.1` and show the last 20 commits in the changelog.

## Creating a Full Release

To create a full (non-pre) release:

1. Go to **Releases** in your GitHub repository
2. Click **Draft a new release**
3. Choose a tag (e.g., `v1.0.0`)
4. Fill in the release notes
5. Uncheck **Set as a pre-release**
6. Click **Publish release**

## Disabling Pre-Releases

If you don't want automatic pre-releases, you can:

1. Remove the `create-prerelease` job from `.github/workflows/ci-cd.yml`
2. Or change the condition to only run on tags:
   ```yaml
   if: startsWith(github.ref, 'refs/tags/')
   ```

## Monitoring Workflow Runs

1. Go to the **Actions** tab in your repository
2. Click on any workflow run to see details
3. View logs for each job
4. Download artifacts (if any)

## Troubleshooting

### Docker Push Fails

- Ensure the workflow has `packages: write` permission
- Check that the image name is correct: `ghcr.io/YOUR_USERNAME/REPO_NAME`
- Verify the GitHub Actions runner can access GHCR
- Check if the package visibility needs to be changed to public

### Tests Fail

- Check the test logs in the Actions tab
- Run tests locally: `make test`
- Ensure all dependencies are in `requirements.txt`

### Linting Fails

- Run linters locally:
  - `flake8 .`
  - `pylint $(git ls-files '*.py')`
- Fix any errors before pushing

## Local Testing

Before pushing, test locally:

```bash
# Run tests
make test

# Run linting
flake8 .
pylint $(git ls-files '*.py')

# Build Docker image
docker build -t letterbox-list-generator:test .

# Run Docker container
docker run --rm letterbox-list-generator:test
```

## Coverage Reports

Test coverage is automatically uploaded to Codecov (if configured). To view coverage locally:

```bash
make test-cov-html
open htmlcov/index.html
```

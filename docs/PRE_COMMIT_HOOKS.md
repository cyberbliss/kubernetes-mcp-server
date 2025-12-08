# Pre-commit Hooks Setup

This repository uses [pre-commit](https://pre-commit.com/) to ensure code quality and prevent secrets from being committed.

## Installation

### 1. Install pre-commit

```bash
# Using pip (recommended)
pip install pre-commit

# Or using Homebrew (macOS)
brew install pre-commit

# Or use the Makefile target
make pre-commit-install
```

### 2. Install the git hooks

```bash
# Using pre-commit directly
pre-commit install

# Or using the Makefile target
make pre-commit-install
```

## Usage

### Automatic checks on commit

Once installed, pre-commit will automatically run on `git commit`. If any hooks fail, the commit will be blocked.

### Manual execution

Run all hooks on all files:

```bash
pre-commit run --all-files

# Or using the Makefile target
make pre-commit-run
```

Run hooks on specific files:

```bash
pre-commit run --files path/to/file1.go path/to/file2.go
```

## Hooks Included

### General File Checks
- **trailing-whitespace**: Removes trailing whitespace
- **end-of-file-fixer**: Ensures files end with a newline
- **check-yaml**: Validates YAML syntax
- **check-json**: Validates JSON syntax
- **check-added-large-files**: Prevents large files from being committed (>1MB)
- **check-merge-conflict**: Detects merge conflict markers
- **detect-private-key**: Detects private keys

### Secret Detection
- **detect-secrets**: Scans for secrets using Yelp's detect-secrets
  - Uses `.secrets.baseline` to track known false positives
  - Excludes lock files and minified assets

### Go-Specific
- **golangci-lint**: Runs comprehensive Go linting
- **go-fmt**: Formats Go code
- **go-mod-tidy**: Tidies go.mod and go.sum
- **go-vet**: Runs go vet
- **go-imports**: Organizes imports
- **go-build**: Ensures code builds

### Other
- **hadolint**: Lints Dockerfiles
- **markdownlint**: Lints and fixes Markdown files
- **yamllint**: Lints YAML files

## Working with Secrets Detection

### Updating the secrets baseline

If you need to add legitimate secrets or tokens (e.g., test fixtures):

```bash
# Scan and update the baseline
make secrets-scan

# Review and audit the findings
make secrets-audit
```

During the audit:
- Press `s` to skip a secret (won't be flagged again)
- Press `n` to mark as a real secret
- Press `q` to quit

### Bypassing pre-commit

**Not recommended**, but if you absolutely need to bypass pre-commit:

```bash
git commit --no-verify
```

## Updating Hooks

To update all hooks to their latest versions:

```bash
pre-commit autoupdate

# Or using the Makefile target
make pre-commit-update
```

## Troubleshooting

### Hooks fail on first run

Some hooks need to download dependencies on first run. This is normal and subsequent runs will be faster.

### golangci-lint timeout

If golangci-lint times out, you can increase the timeout in `.pre-commit-config.yaml`:

```yaml
- id: golangci-lint
  args: ['--timeout=10m']  # Increase from 5m to 10m
```

### Skipping specific hooks

To skip a specific hook for all commits:

```bash
SKIP=golangci-lint git commit -m "message"
```

To permanently disable a hook, comment it out in `.pre-commit-config.yaml`.

## Integration with CI/CD

Consider adding this to your CI pipeline to ensure pre-commit checks run on all PRs:

```yaml
# GitHub Actions example
- name: Run pre-commit
  uses: pre-commit/action@v3.0.0
```

## Makefile Targets

- `make pre-commit-install` - Install pre-commit and git hooks
- `make pre-commit-run` - Run all pre-commit hooks on all files
- `make pre-commit-update` - Update hooks to latest versions
- `make secrets-scan` - Scan for secrets and update baseline
- `make secrets-audit` - Audit detected secrets

## References

- [pre-commit documentation](https://pre-commit.com/)
- [detect-secrets documentation](https://github.com/Yelp/detect-secrets)
- [golangci-lint documentation](https://golangci-lint.run/)

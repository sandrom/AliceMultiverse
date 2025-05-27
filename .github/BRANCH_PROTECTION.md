# Branch Protection Settings

This document describes the recommended branch protection rules for the AliceMultiverse repository.

## Main Branch Protection

Apply these settings to the `main` branch:

### 1. Require a pull request before merging
- ✅ Require approvals: 1
- ✅ Dismiss stale pull request approvals when new commits are pushed
- ✅ Require review from CODEOWNERS

### 2. Require status checks to pass before merging
- ✅ Require branches to be up to date before merging
- Required status checks:
  - `test` (all OS/Python combinations)
  - `security / secrets-scan`
  - `security / security-scan`
  - `security / sensitive-data-scan`
  - `security / codeql-analysis`

### 3. Require conversation resolution before merging
- ✅ All conversations must be resolved

### 4. Require signed commits
- ✅ Require signed commits (optional but recommended)

### 5. Include administrators
- ⚠️ Do not bypass these settings for administrators

### 6. Restrict who can push to matching branches
- Add team/users who can merge PRs

### 7. Rules for force pushes
- ❌ Do not allow force pushes
- ❌ Do not allow deletions

## How to Enable

1. Go to Settings → Branches
2. Add rule for `main` branch
3. Configure all settings above
4. Save changes

## Additional Security

1. Enable "Security" tab in repository settings
2. Enable Dependabot security updates
3. Enable secret scanning
4. Enable push protection for secrets

## PR Workflow

All changes must follow this workflow:

```bash
# Create feature branch
git checkout -b feat/your-feature

# Make changes and commit
git add .
git commit -m "feat: add new feature"  # pre-commit hooks run here

# Push to GitHub
git push origin feat/your-feature

# Create PR
gh pr create --title "feat: add new feature" --body "Description of changes"

# After approval and checks pass, merge via GitHub UI
```
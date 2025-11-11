# Branch Protection Rules

## Overview

This document describes the branch protection rules for the WWMAA repository. These rules ensure code quality, prevent accidental deletions, and enforce a proper review process.

## Table of Contents

1. [Main Branch Protection](#main-branch-protection)
2. [Setting Up Branch Protection](#setting-up-branch-protection)
3. [Required Status Checks](#required-status-checks)
4. [Pull Request Requirements](#pull-request-requirements)
5. [Bypass Permissions](#bypass-permissions)
6. [Troubleshooting](#troubleshooting)

---

## Main Branch Protection

The `main` branch is the production branch and requires the strictest protection rules.

### Protection Rules Summary

```
┌─────────────────────────────────────────────────────────────┐
│                Main Branch Protection Rules                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ✅ Require pull request reviews (1 approval)               │
│  ✅ Require status checks to pass                           │
│  ✅ Require branches to be up to date                       │
│  ✅ Require conversation resolution                         │
│  ✅ Require linear history                                  │
│  ✅ Require signed commits (recommended)                    │
│  ❌ Allow force pushes                                      │
│  ❌ Allow deletions                                         │
│  ❌ Allow bypassing settings                                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Setting Up Branch Protection

### Step-by-Step Guide

#### 1. Navigate to Branch Protection Settings

1. Go to your GitHub repository
2. Click on **Settings** tab
3. Click on **Branches** in the left sidebar
4. Click **Add branch protection rule**

#### 2. Specify Branch Name Pattern

- **Branch name pattern:** `main`
- This will apply rules to the main branch only

#### 3. Configure Protection Rules

##### Require Pull Request Reviews

- ✅ **Require a pull request before merging**
  - ✅ **Require approvals:** `1`
  - ✅ **Dismiss stale pull request approvals when new commits are pushed**
  - ✅ **Require review from Code Owners** (if CODEOWNERS file exists)
  - ⬜ **Restrict who can dismiss pull request reviews** (optional)
  - ✅ **Allow specified actors to bypass required pull requests** (for CI/CD bots only)

##### Require Status Checks

- ✅ **Require status checks to pass before merging**
  - ✅ **Require branches to be up to date before merging**

  **Status checks to require:**
  ```
  ✅ backend-lint
  ✅ backend-unit-tests
  ✅ backend-integration-tests
  ✅ frontend-lint
  ✅ frontend-build-test
  ✅ ci-status
  ⬜ security-scan (optional - currently set to continue-on-error)
  ```

##### Require Conversation Resolution

- ✅ **Require conversation resolution before merging**
  - All PR comments must be resolved before merge
  - Ensures no feedback is overlooked

##### Require Signed Commits

- ✅ **Require signed commits** (recommended)
  - Ensures commit authenticity
  - See [GitHub GPG signing guide](https://docs.github.com/en/authentication/managing-commit-signature-verification)

##### Require Linear History

- ✅ **Require linear history**
  - Prevents merge commits
  - Enforces rebase or squash merging
  - Keeps commit history clean

##### Additional Settings

- ✅ **Require deployments to succeed before merging** (if using GitHub Deployments)
- ✅ **Lock branch** (for critical releases only)
- ❌ **Do not allow bypassing the above settings**
- ❌ **Allow force pushes** (disabled for main)
- ❌ **Allow deletions** (disabled for main)

#### 4. Save Changes

- Scroll to bottom and click **Create** or **Save changes**

---

## Required Status Checks

### Backend Checks

#### 1. backend-lint
- **Purpose:** Ensure code quality and style consistency
- **Checks:**
  - Flake8 linting
  - Black code formatting
  - isort import sorting
  - MyPy type checking (advisory)
- **Duration:** ~5-10 minutes
- **Blocking:** Yes

#### 2. backend-unit-tests
- **Purpose:** Verify core functionality
- **Checks:**
  - Pytest unit tests
  - Code coverage (80% minimum)
- **Duration:** ~10-20 minutes
- **Blocking:** Yes

#### 3. backend-integration-tests
- **Purpose:** Verify external integrations
- **Checks:**
  - Integration with Redis
  - API integration tests
  - Database integration tests
- **Duration:** ~10-20 minutes
- **Blocking:** Yes

### Frontend Checks

#### 4. frontend-lint
- **Purpose:** Ensure frontend code quality
- **Checks:**
  - ESLint
  - TypeScript type checking
- **Duration:** ~5-10 minutes
- **Blocking:** Yes

#### 5. frontend-build-test
- **Purpose:** Verify frontend builds and tests
- **Checks:**
  - Next.js build
  - Jest unit tests
  - Code coverage (75% minimum)
- **Duration:** ~10-20 minutes
- **Blocking:** Yes

### Aggregate Checks

#### 6. ci-status
- **Purpose:** Aggregate all check results
- **Checks:**
  - Verifies all required checks passed
  - Posts summary comment on PR
- **Duration:** ~1 minute
- **Blocking:** Yes

### Optional Checks

#### security-scan
- **Purpose:** Detect security vulnerabilities
- **Checks:**
  - Python dependency scanning (pip-audit)
  - Node dependency scanning (npm audit)
- **Duration:** ~5-10 minutes
- **Blocking:** No (continue-on-error)
- **Note:** Should be reviewed but doesn't block merge

---

## Pull Request Requirements

### Creating a Pull Request

1. **Branch from main:**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/your-feature-name
   ```

2. **Make changes and commit:**
   ```bash
   git add .
   git commit -m "feat: add your feature"
   git push origin feature/your-feature-name
   ```

3. **Create PR on GitHub:**
   - Navigate to repository
   - Click **Pull requests** > **New pull request**
   - Select your branch
   - Fill in PR template
   - Assign reviewers

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests pass locally
- [ ] Coverage maintained/improved
```

### Review Process

1. **Automated checks run:**
   - CI pipeline executes
   - Status checks appear on PR

2. **Code review:**
   - Reviewer assigned
   - Review comments added
   - Changes requested (if needed)

3. **Address feedback:**
   - Fix requested changes
   - Push new commits
   - Request re-review

4. **Approval:**
   - Reviewer approves PR
   - All checks pass
   - Ready to merge

5. **Merge:**
   - Choose merge strategy:
     - **Squash and merge** (recommended for feature branches)
     - **Rebase and merge** (for clean history)
     - **Create merge commit** (for release branches)
   - Click **Merge pull request**
   - Delete branch after merge

### Merge Strategies

#### Squash and Merge (Recommended)
- Combines all commits into one
- Keeps main branch history clean
- Best for feature branches with many small commits

```bash
# Results in single commit on main
feat: add user authentication (PR #123)
```

#### Rebase and Merge
- Applies commits individually
- Maintains commit history
- Best for well-structured commits

```bash
# Preserves individual commits
feat: add login endpoint
feat: add logout endpoint
test: add auth tests
```

#### Create Merge Commit
- Creates merge commit with all changes
- Preserves branch history
- Best for release branches

```bash
# Creates merge commit
Merge pull request #123 from feature/auth
```

---

## Bypass Permissions

### When to Allow Bypassing

Branch protection rules should rarely be bypassed. However, there are legitimate scenarios:

1. **Emergency hotfixes**
   - Critical production bugs
   - Security vulnerabilities
   - Must be fixed immediately

2. **CI/CD automation**
   - Automated releases
   - Dependency updates
   - Bot accounts

3. **Repository administration**
   - Fixing broken main branch
   - Resolving merge conflicts

### How to Allow Bypassing

1. Go to **Branch protection rules** for `main`
2. Scroll to **Allow specified actors to bypass required pull requests**
3. Add specific users/teams/apps:
   - Repository administrators
   - CI/CD bot accounts (e.g., Dependabot)
4. **Never** allow "Anyone" to bypass

### Best Practices for Bypassing

- **Document the reason** in commit message
- **Notify the team** via Slack/email
- **Create follow-up PR** for proper review
- **Minimize frequency** of bypasses

---

## Troubleshooting

### Problem: Status Check Never Completes

**Symptoms:**
- Check shows "Expected" but never runs
- PR cannot be merged

**Solutions:**

1. **Re-run failed workflows:**
   - Go to Actions tab
   - Click on failed workflow
   - Click "Re-run all jobs"

2. **Check workflow syntax:**
   ```bash
   # Validate workflow YAML
   yamllint .github/workflows/ci.yml
   ```

3. **Verify branch is up to date:**
   ```bash
   git fetch origin main
   git rebase origin/main
   git push --force-with-lease
   ```

### Problem: Cannot Merge Despite Passing Checks

**Symptoms:**
- All checks pass
- "Merge" button disabled

**Solutions:**

1. **Check if branch is up to date:**
   - Update branch with latest main
   - Click "Update branch" on PR

2. **Resolve all conversations:**
   - Ensure no unresolved comments
   - Resolve or reply to all feedback

3. **Check for missing approvals:**
   - Verify required number of approvals
   - Request review if needed

### Problem: Check Fails but Should Pass

**Symptoms:**
- Test passes locally
- Fails in CI

**Solutions:**

1. **Environment differences:**
   ```bash
   # Match CI environment
   docker run -it python:3.11-slim bash
   pip install -r requirements.txt
   pytest
   ```

2. **Caching issues:**
   - Clear GitHub Actions cache
   - Update cache keys in workflow

3. **Secrets missing:**
   - Verify GitHub Secrets configured
   - Check secret names match workflow

### Problem: Force Push Needed but Blocked

**Symptoms:**
- Need to force push to PR branch
- Force push blocked

**Solutions:**

1. **Force push is allowed on feature branches:**
   ```bash
   git push --force-with-lease origin feature/branch
   ```

2. **If still blocked, check:**
   - Branch protection rules
   - You're not pushing to main
   - You have write permissions

### Problem: Too Many Status Checks Required

**Symptoms:**
- Some checks are redundant
- Slowing down merge process

**Solutions:**

1. **Review required checks:**
   - Remove non-essential checks
   - Combine related checks
   - Make some checks non-blocking

2. **Optimize workflow:**
   - Run checks in parallel
   - Cache dependencies
   - Skip checks for docs-only changes

---

## Code Owners (Optional)

### Setting Up CODEOWNERS

Create `.github/CODEOWNERS` file:

```
# CODEOWNERS file

# Global owners
* @your-org/core-team

# Backend code
/backend/ @your-org/backend-team

# Frontend code
/app/ @your-org/frontend-team
/components/ @your-org/frontend-team

# Documentation
/docs/ @your-org/tech-writers

# CI/CD
/.github/ @your-org/devops-team

# Security sensitive
/backend/auth.py @your-org/security-team
/backend/payment.py @your-org/security-team
```

### Benefits

- Automatic reviewer assignment
- Required approval from code owners
- Clear ownership boundaries
- Better code quality

---

## Advanced Configuration

### Rulesets (GitHub Enterprise)

For organizations with GitHub Enterprise:

1. **Create organization-level rulesets**
2. **Apply to multiple repositories**
3. **Inherit and extend rules**
4. **Centralized management**

### Required Workflows

For consistent CI across repositories:

```yaml
# .github/workflows/required-workflow.yml
name: Required CI
on:
  pull_request:
  push:
    branches: [main]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run security scan
        run: ./scripts/security-scan.sh
```

---

## Summary Checklist

When setting up branch protection:

- ✅ Main branch protected
- ✅ Require PR reviews (1 approval)
- ✅ Require status checks (all critical checks listed)
- ✅ Require branches up to date
- ✅ Require conversation resolution
- ✅ Require linear history
- ✅ Require signed commits (recommended)
- ✅ Disable force pushes
- ✅ Disable deletions
- ✅ Disable bypassing rules
- ✅ Configure CODEOWNERS (optional)
- ✅ Test with a sample PR

---

## Additional Resources

- [GitHub Branch Protection Documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub Required Status Checks](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches#require-status-checks-before-merging)
- [GitHub CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- [Signing Commits](https://docs.github.com/en/authentication/managing-commit-signature-verification/signing-commits)

---

**Last Updated:** November 10, 2025
**Maintainer:** WWMAA Development Team

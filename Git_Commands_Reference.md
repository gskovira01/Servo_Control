# Git Commands Quick Reference

## Basic Workflow
```bash
git status          # Check file changes
git add .           # Stage all files
git commit -m "msg" # Save changes
git push            # Upload to GitHub
git pull            # Download updates
```

## Setup
```bash
git init            # Create new repo
git clone <url>     # Download repo
```

## Branches
```bash
git branch          # List branches
git checkout -b new # Create branch
git merge branch    # Combine branches
```

## History
```bash
git log             # View commits
git diff            # See changes
```

## Fixes
```bash
git stash           # Save changes temporarily
git stash pop       # Restore saved changes
git reset --hard    # Discard all changes
```

## Config
```bash
git config user.name "Name"      # Set name
git config user.email "email"    # Set email
```

## Most Common Pattern
```bash
git add .
git commit -m "Your description here"
git push
```

---
*Quick reference for Servo Control project*
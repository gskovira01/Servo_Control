# Git Setup Guide for Servo Control Project

This guide will help you set up Git version control for your servo control project, eliminating the need for memory stick transfers.

## Step 1: Install Git (Required)

### Windows Installation
1. **Download Git**: Go to https://git-scm.com/download/win
2. **Run installer**: Accept default settings
3. **Verify installation**: Open PowerShell and type `git --version`

### Alternative: Install via Windows Package Manager
```powershell
winget install Git.Git
```

## Step 2: Configure Git (First Time Only)
```powershell
git config --global user.name "Greg Skovira"
git config --global user.email "your-email@example.com"
```

## Step 3: Initialize Local Repository
```powershell
# You're already in the correct directory (D:\Python)
git init
git add .
git commit -m "Initial commit: 8-axis servo control system Rev 31"
```

## Step 4: Create Remote Repository

### Option A: GitHub (Recommended)
1. Go to https://github.com and sign in/create account
2. Click "New Repository" (+ icon)
3. Name: `servo-control-8-axis`
4. Description: `Professional 8-axis servo control with dual ClearCore controllers`
5. Set to **Private** (for internal use)
6. Do NOT initialize with README (you already have files)
7. Click "Create Repository"

### Option B: GitLab or Azure DevOps
Similar process on gitlab.com or dev.azure.com

## Step 5: Connect Local Repository to Remote
```powershell
# Replace <your-username> with your actual GitHub username
git remote add origin https://github.com/<your-username>/servo-control-8-axis.git
git branch -M main
git push -u origin main
```

## Step 6: Daily Development Workflow

### Windows Development
```powershell
# After making changes to code
git add .
git commit -m "Description of your changes"
git push
```

### Raspberry Pi Deployment
```bash
# First time deployment
git clone https://github.com/<your-username>/servo-control-8-axis.git
cd servo-control-8-axis

# Future updates (no memory stick needed!)
git pull
```

## Benefits You'll Get

### ✅ No More Memory Stick Transfers
- Direct network deployment to Raspberry Pi
- Instant code synchronization
- No more forgotten or lost memory sticks

### ✅ Professional Version Control
- Complete history of all changes
- Easy rollback to previous working versions
- Track what changed and when

### ✅ Backup & Safety
- Your code is safely stored in cloud
- Multiple copies (local + remote)
- Never lose work due to hardware failure

### ✅ Collaboration Ready
- Share with team members easily
- Track individual contributions
- Merge changes from multiple developers

## Example Commands After Setup

```powershell
# Daily development cycle
git status                          # See what files changed
git add Servo_Control_8_Axis.py     # Stage specific file
git add .                           # Stage all changes
git commit -m "Fixed servo timing"  # Commit with description
git push                           # Upload to repository

# Check history
git log --oneline                  # See commit history
git diff                          # See current changes

# Raspberry Pi updates
git pull                          # Download latest changes
```

## Troubleshooting

### If git command not found:
1. Restart PowerShell after installing Git
2. Check if Git was added to PATH during installation
3. Try: `refreshenv` (if using Chocolatey)

### If repository already exists:
```powershell
git remote -v                     # Check current remotes
git remote set-url origin <new-url>  # Update remote URL
```

### If authentication issues:
- Use GitHub Desktop app for easier authentication
- Or set up SSH keys for command line access

## Next Steps After Setup

1. **Test the workflow**: Make a small change and push it
2. **Deploy to Pi**: Clone the repository on Raspberry Pi
3. **Update Pi**: Use `git pull` instead of memory stick
4. **Enjoy**: Professional development workflow achieved!

---

**Need Help?** 
- Git documentation: https://git-scm.com/docs
- GitHub guides: https://guides.github.com
- Pro tip: Use VS Code's built-in Git integration for visual interface
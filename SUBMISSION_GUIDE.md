# OpenEnv Hackathon - Complete Submission Guide

## 📋 Table of Contents
1. [Pre-Submission Setup](#pre-submission-setup)
2. [Local Testing](#local-testing)
3. [GitHub Setup](#github-setup)
4. [HuggingFace Spaces Deployment](#huggingface-spaces-deployment)
5. [Final Validation](#final-validation)
6. [Submission](#submission)

---

## Pre-Submission Setup

### Time Required: 30 minutes

### Step 1: Ensure Python 3.10+ is Installed

```bash
python --version
# Output should be: Python 3.10.x, 3.11.x, or 3.12.x
```

If not, download from https://www.python.org/downloads/

### Step 2: Extract Project Files

The project is in the `inventory-management-env/` directory with this structure:

```
inventory-management-env/
├── inventory_env.py
├── inference.py
├── openenv.yaml
├── requirements.txt
├── Dockerfile
├── README.md
├── .env.example
├── .gitignore
├── graders/
│   ├── __init__.py
│   ├── easy_grader.py
│   ├── medium_grader.py
│   └── hard_grader.py
└── .github/
    └── workflows/
        └── ci.yml
```

### Step 3: Get Your HuggingFace Token

1. Go to: https://huggingface.co/settings/tokens
2. Click **"New token"**
3. Set **Name:** "openenv-hackathon"
4. Set **Type:** "Read"
5. Click **Create token**
6. Copy the token (starts with `hf_`)
7. **Save it somewhere safe** - you'll need it multiple times

---

## Local Testing

### Time Required: 20 minutes

### Step 1: Create Virtual Environment

```bash
cd inventory-management-env

# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows (PowerShell):
venv\Scripts\Activate.ps1

# On Windows (Command Prompt):
venv\Scripts\activate.bat
```

**Check:** You should see `(venv)` at the start of your command line.

### Step 2: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Check:** Should complete without errors.

### Step 3: Create .env File

```bash
# Copy the example
cp .env.example .env

# Edit .env with your values
# For macOS/Linux, use:
nano .env

# For Windows, use:
notepad .env
```

Add your HuggingFace token:

```
HF_TOKEN=hf_your_token_here
API_BASE_URL=https://router.huggingface.co/v1
MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
MY_ENV_TASK=easy
MY_ENV_BENCHMARK=inventory-management
```

**Alternative:** Export as environment variables:

```bash
export HF_TOKEN="hf_your_token_here"
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
export MY_ENV_TASK="easy"
```

### Step 4: Test Environment Installation

```bash
# Test that the environment module works
python -c "from inventory_env import InventoryEnv; env = InventoryEnv(task='easy'); print('✓ Environment OK')"

# Test graders
python -m graders.easy_grader
python -m graders.medium_grader
python -m graders.hard_grader

# Expected output: "Easy Task Score: 0.XX" etc.
```

**If you get import errors:**
```bash
pip install -r requirements.txt --force-reinstall
```

### Step 5: Run First Inference (Easy Task)

```bash
# Make sure .env is loaded
source .env  # (On Windows: type .env in PowerShell to view)

# Run inference
MY_ENV_TASK=easy python inference.py 2>/dev/null | head -20
```

**Expected output:**
```
[START] task=easy env=inventory-management model=Qwen/Qwen2.5-72B-Instruct
[STEP]  step=1 action=observe reward=0.00 done=false error=null
[STEP]  step=2 action=reorder(SKU001, qty=50) reward=0.10 done=false error=null
...
[END]   success=true steps=30 score=0.75 rewards=0.00,0.10,0.15,...
```

**What to check:**
- ✓ Exactly ONE `[START]` line
- ✓ Multiple `[STEP]` lines (one per step)
- ✓ Exactly ONE `[END]` line
- ✓ All rewards in format: `0.00` (2 decimals)
- ✓ `done` is `true` or `false` (lowercase)
- ✓ `score` in range `0.0-1.0`

**If it fails:**
- Check `HF_TOKEN` is correct
- Check internet connection
- Try a different model: `MODEL_NAME="mistralai/Mistral-7B-Instruct-v0.2"`

### Step 6: Test All Three Tasks

```bash
echo "Testing EASY..."
MY_ENV_TASK=easy python inference.py 2>/dev/null | grep "^\["

echo "Testing MEDIUM..."
MY_ENV_TASK=medium python inference.py 2>/dev/null | grep "^\["

echo "Testing HARD..."
MY_ENV_TASK=hard python inference.py 2>/dev/null | grep "^\["
```

**Success criteria:**
- Each task produces valid `[START]`, `[STEP]`, `[END]` lines
- Completes in <5 minutes each
- No errors in output

---

## GitHub Setup

### Time Required: 10 minutes

### Step 1: Initialize Git Repository

```bash
cd inventory-management-env

# Initialize git
git init

# Configure git (one time)
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Add all files
git add .

# Commit
git commit -m "Initial commit: Inventory management OpenEnv environment"
```

### Step 2: Create GitHub Repository

1. Go to https://github.com/new
2. **Repository name:** `inventory-management-env`
3. **Description:** "OpenEnv inventory optimization environment for hackathon"
4. **Public:** Yes (for evaluation)
5. **Initialize with:** Nothing (skip)
6. Click **Create repository**

### Step 3: Push to GitHub

Copy the commands from GitHub and run them:

```bash
git remote add origin https://github.com/YOUR_USERNAME/inventory-management-env.git
git branch -M main
git push -u origin main

# Verify
git remote -v
# Should show your repo URL
```

**Success:** You should see files on GitHub at `https://github.com/YOUR_USERNAME/inventory-management-env`

---

## HuggingFace Spaces Deployment

### Time Required: 15 minutes

### Step 1: Create HF Space

1. Go to https://huggingface.co/spaces
2. Click **Create new Space**

Fill in:
- **Space name:** `inventory-management-env`
- **License:** Apache 2.0
- **Space SDK:** Docker
- **Visibility:** Public
- Click **Create Space**

Wait for the blank space to be created (1-2 minutes).

### Step 2: Configure Space Secrets

1. In your Space, go to **Settings** (gear icon top-right)
2. Click **Repository secrets**
3. Add these secrets:

| Name | Value |
|------|-------|
| `HF_TOKEN` | Your HuggingFace token |
| `API_BASE_URL` | `https://router.huggingface.co/v1` |
| `MODEL_NAME` | `Qwen/Qwen2.5-72B-Instruct` |

Click **Save** after each.

### Step 3: Link GitHub Repository

1. In Space settings, scroll to **Repository**
2. Under **Sync from repo**, click **Connect a repository**
3. Select your GitHub repo: `inventory-management-env`
4. **Branch:** `main`
5. **Private code:** No (must be public for evaluation)
6. Click **Save**

This will trigger an auto-sync. The Space will rebuild whenever you push to GitHub.

### Step 4: Monitor Deployment

The Space will start building. Check progress:

1. Click **Logs** tab in the Space
2. Watch for build status (should see "Docker build" messages)
3. Wait for "Space is running" message

**If build fails:**
- Check the error message in Logs
- Most common: Docker timeout (try again)
- Check that `Dockerfile` is in repo root
- Verify `requirements.txt` syntax

### Step 5: Get Your Space URL

Once deployed, your Space URL is:
```
https://huggingface.co/spaces/YOUR_USERNAME/inventory-management-env
```

**Save this URL** - you'll need it for submission.

### Step 6: Test Space Accessibility

```bash
# Check space is accessible
curl -I https://huggingface.co/spaces/YOUR_USERNAME/inventory-management-env

# Should return: HTTP/1.1 200 OK
```

---

## Final Validation

### Time Required: 30 minutes

### Validation Checklist

Use this checklist to verify everything works:

```bash
# 1. Code syntax check
echo "Checking Python syntax..."
python -m py_compile inventory_env.py
python -m py_compile inference.py
python -m py_compile graders/*.py
# Expected: No output = success

# 2. Test environment
echo "Testing environment..."
python inventory_env.py
# Expected: test output with scores

# 3. Test each task
echo "Testing tasks..."
for TASK in easy medium hard; do
  echo "=== $TASK ==="
  MY_ENV_TASK=$TASK python inference.py 2>/dev/null | grep "^\[" | head -3
done

# 4. Validate openenv.yaml
echo "Checking openenv.yaml..."
python -c "import yaml; yaml.safe_load(open('openenv.yaml'))" && echo "✓ YAML valid"

# 5. Test Docker build
echo "Building Docker image..."
docker build -t inventory-env . --quiet && echo "✓ Docker build OK"

# 6. Check git
echo "Checking git status..."
git status
git log --oneline | head -5
```

**All should show ✓ (checkmarks) or success messages.**

### Required Files Checklist

- [ ] `inventory_env.py` - Main environment
- [ ] `inference.py` - Inference script (in root!)
- [ ] `openenv.yaml` - OpenEnv specification
- [ ] `requirements.txt` - Dependencies
- [ ] `Dockerfile` - Container config
- [ ] `README.md` - Documentation
- [ ] `graders/easy_grader.py` - Easy task grader
- [ ] `graders/medium_grader.py` - Medium task grader
- [ ] `graders/hard_grader.py` - Hard task grader
- [ ] `.gitignore` - Git ignore rules
- [ ] `.env.example` - Env template
- [ ] `.github/workflows/ci.yml` - CI/CD (optional but good)

### Environment Variables Checklist

Must have these set when running inference:

```bash
# Check they're set
env | grep -E "HF_TOKEN|API_BASE_URL|MODEL_NAME|MY_ENV_TASK"

# Should show all 4 variables
```

### Log Format Checklist

Run inference and verify output format:

```bash
MY_ENV_TASK=easy python inference.py 2>/dev/null > output.txt
cat output.txt

# Verify:
# ✓ First line: [START] task=... env=... model=...
# ✓ Middle lines: [STEP]  step=... action=... reward=0.00 done=false error=null
# ✓ Last line: [END]   success=... steps=... score=0.00 rewards=...
```

---

## Submission

### Time Required: 10 minutes

### Step 1: Final Push to GitHub

```bash
# Make sure everything is committed
git status
# Should show: "On branch main, nothing to commit"

# If not:
git add -A
git commit -m "Final submission ready"
git push origin main
```

### Step 2: Verify GitHub and HF Space

1. Check GitHub: https://github.com/YOUR_USERNAME/inventory-management-env
   - Should have all files
   - Should see recent commits

2. Check HF Space: https://huggingface.co/spaces/YOUR_USERNAME/inventory-management-env
   - Should be running (green status)
   - Should see "Built from repo" 
   - Should show your code files

### Step 3: Complete Submission Form

Go to the OpenEnv Hackathon portal (provided by organizers).

**Form fields:**

| Field | Value |
|-------|-------|
| **Problem Statement** | Select "Inventory Restocking Decision System" |
| **Round** | Round 1 |
| **GitHub Repository URL** | `https://github.com/YOUR_USERNAME/inventory-management-env` |
| **HuggingFace Space URL** | `https://huggingface.co/spaces/YOUR_USERNAME/inventory-management-env` |
| **Team Leader** | Your name (only team leader submits) |
| **Team Members** | List other team members (if any) |

### Step 4: Submit

1. Review all fields are correct
2. Click **Submit**
3. You should get a confirmation message

**Keep the confirmation number/email.**

### Step 5: Wait for Validation

The hackathon team will:
1. ✓ Ping your HF Space (verify it's running)
2. ✓ Validate `openenv.yaml`
3. ✓ Build your Docker image
4. ✓ Run `inference.py` on each task
5. ✓ Check log format
6. ✓ Run graders

You'll receive an email with results within 24 hours.

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'openai'"

```bash
# Install openai library
pip install openai --upgrade

# Verify
python -c "import openai; print(openai.__version__)"
```

### "HF_TOKEN is not set"

```bash
# Option 1: Set in .env file
echo 'HF_TOKEN=hf_your_token' > .env
source .env

# Option 2: Export in shell
export HF_TOKEN="hf_your_token"

# Verify
echo $HF_TOKEN  # Should print your token
```

### "Connection error / timeout"

```bash
# Check internet
ping huggingface.co

# Check token is valid
curl -H "Authorization: Bearer $HF_TOKEN" https://api-inference.huggingface.co/status

# Try different model (faster)
MODEL_NAME="mistralai/Mistral-7B-Instruct-v0.2" python inference.py
```

### "Docker build fails"

```bash
# Check Docker is installed
docker --version

# Check syntax error in Dockerfile
docker build -t test . --progress=plain 2>&1 | tail -20

# Clean and retry
docker system prune
docker build -t inventory-env .
```

### "HF Space doesn't deploy"

1. Check **Logs** tab in Space settings
2. Look for build errors (usually timeout or permission)
3. Try pushing a new commit to trigger rebuild:
   ```bash
   git commit --allow-empty -m "Retry deployment"
   git push origin main
   ```
4. Wait 5 minutes for rebuild

### "Inference takes too long"

```bash
# Try a faster model
MODEL_NAME="mistralai/Mistral-7B-Instruct-v0.2" \
  MY_ENV_TASK=easy \
  python inference.py

# Or reduce steps in inference.py (line 213)
# Change: while step < max_steps:
# To:     while step < 15:  # Only 15 steps for testing
```

---

## Success Indicators

✓ **You're ready to submit when:**

1. Local testing:
   - `python inventory_env.py` runs without errors
   - `MY_ENV_TASK=easy python inference.py` produces valid logs
   - All 3 tasks complete in <5 min each

2. GitHub:
   - Repository is public
   - All files visible
   - Latest commit is recent

3. HF Space:
   - Space is running (green status)
   - Files visible in Space
   - URL is accessible

4. Validation:
   - `[START]`, `[STEP]`, `[END]` format is correct
   - All rewards in 0.0-1.0 range
   - No parsing errors in output

---

## Quick Reference Commands

```bash
# Activate environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Test environment
python inventory_env.py

# Run inference (easy)
MY_ENV_TASK=easy python inference.py

# Test specific task
MY_ENV_TASK=medium python inference.py 2>/dev/null | grep "^\["

# Build Docker
docker build -t inventory-env .

# Push to GitHub
git add -A && git commit -m "message" && git push origin main

# Check HF Space URL
echo "https://huggingface.co/spaces/YOUR_USERNAME/inventory-management-env"
```

---

## Timeline

| Task | Time | Deadline |
|------|------|----------|
| Setup & Testing | 60 min | Before submission |
| GitHub repo | 10 min | Before HF sync |
| HF Spaces deploy | 15 min | Before submission |
| Final validation | 30 min | Day before |
| **SUBMISSION** | 10 min | **8 Apr 11:59 PM IST** |

**Total time: ~2 hours**

---

## Getting Help

- **Technical issues:** GitHub Issues on your repo
- **Hackathon questions:** help_openenvhackathon@scaler.com
- **HF Spaces docs:** https://huggingface.co/docs/hub/spaces
- **OpenEnv docs:** https://github.com/openenv-hackathon/openenv

---

Good luck! 🚀

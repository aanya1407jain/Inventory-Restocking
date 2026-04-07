# Inventory Restocking Decision System - OpenEnv Environment

A complete OpenEnv implementation for AI agent-based inventory optimization. The environment simulates a multi-SKU warehouse where agents learn to make optimal restocking decisions while minimizing costs and preventing stockouts.

## Quick Start

### Prerequisites
- Python 3.10+ (3.10, 3.11, or 3.12 recommended)
- Git
- HuggingFace account (for model API access)
- Docker (optional, for deployment to HF Spaces)

### 1. Local Setup (15 minutes)

```bash
# Clone or download the project
git clone <your-repo-url> inventory-management-env
cd inventory-management-env

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python inventory_env.py  # Should output test results
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# HuggingFace API
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx
API_BASE_URL=https://router.huggingface.co/v1
MODEL_NAME=Qwen/Qwen2.5-72B-Instruct

# Environment task
MY_ENV_TASK=easy  # Can be: easy, medium, hard
MY_ENV_BENCHMARK=inventory-management
```

Or export them in your shell:

```bash
export HF_TOKEN="hf_xxxxxxxxxxxxxxxxxxxx"
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
export MY_ENV_TASK="easy"
```

**Get your HF_TOKEN:**
1. Go to https://huggingface.co/settings/tokens
2. Create a new token (read access is sufficient)
3. Copy the token

### 3. Test Locally

```bash
# Test environment
python -c "from inventory_env import InventoryEnv; env = InventoryEnv(); print('Environment works!')"

# Run a single inference episode (Easy task, ~5 minutes)
MY_ENV_TASK=easy python inference.py

# Expected output format:
# [START] task=easy env=inventory-management model=Qwen/Qwen2.5-72B-Instruct
# [STEP]  step=1 action=observe reward=0.00 done=false error=null
# [STEP]  step=2 action=reorder(SKU001, qty=100) reward=0.25 done=false error=null
# ...
# [END]   success=true steps=30 score=0.75 rewards=0.00,0.25,0.20,...
```

### 4. Test All Three Tasks

```bash
# Easy task (simplest - just detect low stock)
MY_ENV_TASK=easy python inference.py 2>/dev/null | grep "^\[" > easy_results.txt

# Medium task (forecast demand - 5 min)
MY_ENV_TASK=medium python inference.py 2>/dev/null | grep "^\[" > medium_results.txt

# Hard task (optimize cost - 5 min)
MY_ENV_TASK=hard python inference.py 2>/dev/null | grep "^\[" > hard_results.txt
```

### 5. Test Graders Locally

```bash
# Test each grader
python -m graders.easy_grader
python -m graders.medium_grader
python -m graders.hard_grader

# Expected: "Easy Task Score: 0.XX", etc.
```

---

## Environment Details

### Action Space

```json
{
  "product_id": "SKU001|SKU002|SKU003",
  "quantity": 0-200,
  "reorder": true|false
}
```

**Example Actions:**
- `{"product_id": "SKU001", "quantity": 100, "reorder": true}` - Order 100 units of SKU001
- `{"product_id": "SKU002", "quantity": 0, "reorder": false}` - Just observe (no action)

### Observation Space

```json
{
  "products": {
    "SKU001": 80,
    "SKU002": 50,
    "SKU003": 120
  },
  "demand_history": [12, 10, 14, 11, 9, 13, 12],
  "lead_time": 3,
  "current_day": 5,
  "total_cost": 175.50,
  "stockouts_count": 1
}
```

### SKU Configurations

| SKU | Initial Stock | Mean Demand/Day | Std Dev | Holding Cost | Order Cost |
|-----|---------------|-----------------|---------|--------------|-----------|
| SKU001 | 80 | 12 | 3 | $0.50 | $15 |
| SKU002 | 50 | 8 | 2 | $0.80 | $20 |
| SKU003 | 120 | 18 | 4 | $0.30 | $12 |

### Tasks

#### Easy Task: Reactive Reordering
**Objective:** Recognize low stock and place orders before stockouts occur.

**Scoring:**
- Minimize number of stockouts
- Reorder efficiency (not too early, not too late)
- Score: 0.0-1.0

**Strategy Hint:**
Monitor `products` dict. If any SKU drops below 50% of expected 7-day demand, place an order for 100 units.

#### Medium Task: Demand Forecasting
**Objective:** Predict demand patterns and maintain >95% service level.

**Scoring:**
- Service level (demand fulfilled): target >95%
- Cost efficiency: minimize cost-per-unit
- Score: service_level * 0.7 + cost_efficiency * 0.3

**Strategy Hint:**
Use `demand_history` to calculate rolling average. Order proactively when forecast shows demand spike, adjusting 2-3 days ahead of predicted peak.

#### Hard Task: Multi-Objective Optimization
**Objective:** Minimize total cost (ordering + holding) while maintaining 99% service level.

**Scoring:**
- Service level: >99% (critical)
- Cost efficiency: minimize daily costs
- Stockout penalty: severe (each costs 0.2 points)
- Score: service_level * 0.5 + cost_efficiency * 0.3 + no_stockouts * 0.2

**Strategy Hint:**
Calculate Economic Order Quantity (EOQ) for each SKU. Factor in lead time (3 days), demand variance, and SKU-specific costs.

---

## File Structure

```
inventory-management-env/
├── inventory_env.py           # Main environment implementation
├── inference.py               # Baseline LLM agent (MUST be root dir)
├── openenv.yaml              # OpenEnv spec
├── requirements.txt          # Python dependencies
├── Dockerfile                # Container configuration
├── README.md                 # This file
├── .github/
│   └── workflows/
│       └── ci.yml           # (Optional) CI/CD
├── graders/
│   ├── __init__.py
│   ├── easy_grader.py       # Easy task evaluation
│   ├── medium_grader.py     # Medium task evaluation
│   └── hard_grader.py       # Hard task evaluation
└── .env                      # (Optional) Local env vars
```

---

## Deploying to HuggingFace Spaces

### Step 1: Create GitHub Repository

```bash
# Initialize git (if not already done)
git init
git add .
git commit -m "Initial commit: inventory management environment"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/inventory-management-env.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy to HF Spaces

1. Go to https://huggingface.co/spaces
2. Click "Create new Space"
3. **Space name:** `inventory-management-env`
4. **License:** Apache 2.0
5. **Space SDK:** Docker
6. **Private/Public:** Public (for evaluation)

### Step 3: Configure Space

After space is created, go to **Settings** → **Repository** and add secrets:

```
HF_TOKEN: hf_xxxxxxxxxxxxxxxxxxxx
API_BASE_URL: https://router.huggingface.co/v1
MODEL_NAME: Qwen/Qwen2.5-72B-Instruct
MY_ENV_TASK: easy
MY_ENV_BENCHMARK: inventory-management
```

### Step 4: Link GitHub Repository

In HF Spaces settings:
- **Repository:** Link your GitHub repo
- **Repo sync:** Enable auto-sync
- **Private code:** Disable (for evaluation)

Push a commit to trigger deployment:

```bash
git commit --allow-empty -m "Trigger HF Spaces deployment"
git push origin main
```

The space will build automatically. Check **Logs** tab for build status.

### Step 5: Verify Deployment

```bash
# Test the deployed space
curl -X GET "https://huggingface.co/spaces/YOUR_USERNAME/inventory-management-env/file=openenv.yaml"

# Should see your openenv.yaml file served
```

---

## Validation Checklist

Before submitting, verify ALL of these:

### Code Quality
- [ ] `python -m py_compile inventory_env.py` passes
- [ ] `python -m py_compile inference.py` passes
- [ ] `python -m py_compile graders/*.py` passes
- [ ] `openenv.yaml` is valid YAML

### Local Testing
- [ ] `python inventory_env.py` runs without errors
- [ ] `MY_ENV_TASK=easy python inference.py` completes in <5 min
- [ ] `MY_ENV_TASK=medium python inference.py` completes in <5 min
- [ ] `MY_ENV_TASK=hard python inference.py` completes in <5 min
- [ ] Output contains exactly one `[START]`, multiple `[STEP]`, one `[END]`
- [ ] All scores in `[0.0, 1.0]` range with 2 decimal places

### Docker
- [ ] `docker build -t inventory-env .` succeeds
- [ ] `docker run inventory-env` runs inference.py
- [ ] Docker image < 2GB in size

### HF Spaces Deployment
- [ ] Space is public and deployed
- [ ] Space URL is accessible
- [ ] `curl <SPACE_URL>/file=openenv.yaml` returns 200
- [ ] Files visible in Space's "Files" tab

### Documentation
- [ ] README.md is complete and clear
- [ ] Environment description explains all SKUs
- [ ] Action/observation spaces are well-documented
- [ ] Setup instructions are step-by-step

### Compliance
- [ ] `inference.py` uses OpenAI client (not direct API calls)
- [ ] Environment variables: `API_BASE_URL`, `MODEL_NAME`, `HF_TOKEN`
- [ ] Log format strictly matches: `[START]`, `[STEP]`, `[END]`
- [ ] All fields in specified order, no extra fields
- [ ] Rewards always 2 decimal places (0.00, not 0)
- [ ] Booleans lowercase (true, false, not True, False)

---

## Submission Steps

### 1. Final Testing (30 minutes)

```bash
# Clean environment
rm -rf venv __pycache__ .env

# Fresh install + test
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run all tasks
for TASK in easy medium hard; do
  echo "Testing $TASK..."
  MY_ENV_TASK=$TASK python inference.py 2>&1 | grep "^\["
done
```

### 2. Push to GitHub

```bash
git add -A
git commit -m "Final submission: inventory management OpenEnv"
git push origin main

# Wait for HF Spaces to auto-deploy (2-5 minutes)
```

### 3. Get Your Space URL

Your space URL is: `https://huggingface.co/spaces/YOUR_USERNAME/inventory-management-env`

### 4. Submit via Hackathon Portal

1. Go to OpenEnv Hackathon submission page
2. **Round 1 Problem Statement:** Select "Inventory Restocking Decision System"
3. **HuggingFace Space URL:** Paste your space URL
4. **GitHub Repository:** Paste your GitHub repo URL
5. **Team Leader:** Only team leaders can submit
6. Click **Submit**

### 5. Post-Submission Verification

Hackathon judges will:
1. ✓ Ping your HF Space URL (must return 200)
2. ✓ Validate `openenv.yaml` format
3. ✓ Build your Docker image
4. ✓ Run `python inference.py` on each task
5. ✓ Verify log format (3 lines per task)
6. ✓ Check grader outputs

You'll receive confirmation within 24 hours.

---

## Troubleshooting

### Problem: "openai library not found"
```bash
pip install --upgrade openai
```

### Problem: HF_TOKEN error
```bash
# Verify token works
curl -H "Authorization: Bearer $HF_TOKEN" https://api-inference.huggingface.co/status

# Should return 200 OK
```

### Problem: Docker build fails
```bash
# Check Python version
python --version  # Must be 3.10+

# Rebuild with verbose output
docker build -t inventory-env . --progress=plain
```

### Problem: HF Space doesn't deploy
- Check **Logs** tab in Space settings
- Ensure all secrets are set correctly
- Try pushing an empty commit: `git commit --allow-empty -m "Retry" && git push`

### Problem: Inference times out
- Reduce `max_steps` in `inference.py` to 10 for testing
- Check `MODEL_NAME` is correct (list at huggingface.co)
- Verify internet connectivity

### Problem: JSON parse errors
```bash
# Check inference output format
MY_ENV_TASK=easy python inference.py 2>/dev/null | head -5

# Should show:
# [START] task=easy env=inventory-management model=...
# [STEP]  step=1 action=...
```

---

## Performance Tips

### Faster Inference
```bash
# Use a smaller model (but still perform reasonably)
MODEL_NAME="mistralai/Mistral-7B-Instruct-v0.2" python inference.py

# Or a smaller quantized version
MODEL_NAME="TheBloke/Mistral-7B-Instruct-v0.2-GPTQ" python inference.py
```

### Reduce Inference Steps
Edit `inference.py`, line 213:
```python
while step < max_steps and not done:
    # Change max_steps from 30 to 15 for quicker testing
```

### Batch Testing
```bash
# Run all 3 tasks and save results
for TASK in easy medium hard; do
  echo "=== $TASK ===" | tee -a results.log
  MY_ENV_TASK=$TASK timeout 600 python inference.py 2>&1 | grep "^\[" | tee -a results.log
done
```

---

## Support & Contact

- **Documentation:** See `openenv.yaml` for full spec
- **Hackathon Help:** help_openenvhackathon@scaler.com
- **GitHub Issues:** Submit issues on your repo
- **Discord:** [OpenEnv Community](https://discord.gg/openenv)

---

## License

Apache License 2.0 - See LICENSE file (if included)

---

## Changelog

### v1.0 (2025-04-07)
- Initial release
- Three tasks: easy, medium, hard
- Full grader implementations
- Complete documentation
- Docker + HF Spaces ready

---

**Good luck with the hackathon! 🚀**

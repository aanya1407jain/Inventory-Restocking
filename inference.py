#!/usr/bin/env python3
"""
Baseline inference script for inventory management environment.
Uses OpenAI-compatible client to control the agent.

Required environment variables:
- API_BASE_URL: LLM API endpoint (default: HuggingFace router)
- MODEL_NAME: Model identifier (default: Qwen/Qwen2.5-72B-Instruct)
- HF_TOKEN: API key for authentication
"""

import os
import sys
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime

# Try to import OpenAI client
try:
    from openai import OpenAI
except ImportError:
    print("ERROR: openai library not found. Install with: pip install openai")
    sys.exit(1)

from inventory_env import InventoryEnv, InventoryAction, InventoryState


# ============================================================================
# Configuration from environment
# ============================================================================
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")
TASK = os.getenv("MY_ENV_TASK", "easy")
BENCHMARK = os.getenv("MY_ENV_BENCHMARK", "inventory-management")

# Validate credentials
if not HF_TOKEN:
    print("ERROR: HF_TOKEN not set. Set it with: export HF_TOKEN=your_token")
    sys.exit(1)

# Initialize OpenAI client
client = OpenAI(api_key=HF_TOKEN, base_url=API_BASE_URL)

# ============================================================================
# LLM Agent Logic
# ============================================================================

def build_prompt(state: InventoryState, task: str, step: int) -> str:
    """Build the prompt for the LLM agent based on current state."""
    
    products_str = json.dumps(state.products, indent=2)
    demand_str = json.dumps(state.demand_history, indent=2)
    
    base_prompt = f"""
You are managing inventory for an e-commerce warehouse. Your goal is to optimize restocking decisions.

CURRENT STATE (Day {state.current_day}/30):
- Current Inventory: {products_str}
- Demand History (last 7 days): {demand_str}
- Total Cost So Far: ${state.total_cost:.2f}
- Stockouts: {state.stockouts_count}

SKU INFORMATION:
- SKU001: Mean demand 12/day, holding cost $0.5/unit, order cost $15
- SKU002: Mean demand 8/day, holding cost $0.8/unit, order cost $20
- SKU003: Mean demand 18/day, holding cost $0.3/unit, order cost $12

TASK: {task.upper()}
"""
    
    if task == "easy":
        prompt = base_prompt + """
Your goal: Avoid stockouts by reordering when inventory gets low.
Strategy: Monitor current inventory. If stock is below 50% of expected weekly demand, place an order.

DECISION:
Choose which SKU to check (if any), and whether to reorder.
Respond ONLY with valid JSON (no markdown, no extra text):
{"product_id": "SKU001", "quantity": 100, "reorder": true}

Where:
- product_id: which SKU to act on
- quantity: how many units (0-200), or 0 to skip ordering
- reorder: true to place order, false to just observe
"""
    
    elif task == "medium":
        prompt = base_prompt + """
Your goal: Predict upcoming demand and maintain 95% service level.
Strategy: Analyze demand_history to forecast demand. Reorder proactively.

Calculate rolling average demand and standard deviation. Place orders 2-3 days ahead of expected peaks.

DECISION:
Based on the demand pattern, choose whether to reorder and how much.
Respond ONLY with valid JSON (no markdown, no extra text):
{"product_id": "SKU001", "quantity": 100, "reorder": true}
"""
    
    else:  # hard
        prompt = base_prompt + """
Your goal: Minimize total cost (order + holding) while maintaining 99% service level.
Strategy: Balance order costs against holding costs. Use demand forecasts to optimize timing.

Consider:
- Cost of placing an order vs cost of holding extra inventory
- SKU-specific demand patterns and costs
- Lead time (3 days) - order now to receive in 3 days

DECISION:
Optimize across all three SKUs. Choose which to reorder and how much.
Respond ONLY with valid JSON (no markdown, no extra text):
{"product_id": "SKU001", "quantity": 100, "reorder": true}
"""
    
    return prompt


def parse_action(response_text: str) -> Optional[InventoryAction]:
    """Parse LLM response into InventoryAction."""
    try:
        # Try to extract JSON from response
        response_text = response_text.strip()
        
        # If response contains markdown code blocks, extract the JSON
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()
        
        # Parse JSON
        action_dict = json.loads(response_text)
        
        # Validate required fields
        if "product_id" not in action_dict:
            return None
        
        action = InventoryAction(
            product_id=action_dict.get("product_id", "SKU001"),
            quantity=int(action_dict.get("quantity", 0)),
            reorder=bool(action_dict.get("reorder", False))
        )
        return action
    
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        return None


def run_episode(task: str, max_steps: int = 30) -> Dict[str, Any]:
    """Run one complete episode and return metrics."""
    
    env = InventoryEnv(task=task, seed=42)
    state = env.reset()
    
    # Log episode start
    print(f"[START] task={task} env={BENCHMARK} model={MODEL_NAME}")
    sys.stdout.flush()
    
    step = 0
    total_reward = 0.0
    rewards = []
    done = False
    last_error = None
    
    while step < max_steps and not done:
        step += 1
        
        try:
            # Build prompt
            prompt = build_prompt(state, task, step)
            
            # Call LLM
            response = client.messages.create(
                model=MODEL_NAME,
                max_tokens=300,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = response.content[0].text
            action = parse_action(response_text)
            
            # If parsing failed, take default action
            if action is None:
                action = InventoryAction(product_id="SKU001", quantity=0, reorder=False)
                last_error = "parse_error"
            else:
                last_error = None
            
            # Execute action
            next_state, reward, done, info = env.step(action)
            
            total_reward += reward
            rewards.append(reward)
            
            # Format action string
            action_str = f"reorder({action.product_id}, qty={action.quantity})" if action.reorder else "observe"
            
            # Log step (CRITICAL FORMAT - no deviations)
            error_field = f'"{last_error}"' if last_error else "null"
            print(f"[STEP]  step={step} action={action_str} reward={reward:.2f} done={'true' if done else 'false'} error={error_field}")
            sys.stdout.flush()
            
            state = next_state
        
        except Exception as e:
            # Log error and continue
            error_msg = str(e)[:50]
            print(f"[STEP]  step={step} action=error reward=0.00 done=true error=\"{error_msg}\"")
            sys.stdout.flush()
            done = True
            last_error = error_msg
    
    # Calculate final score
    final_score = env.get_task_score()
    success = final_score >= 0.5
    
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    
    # Log episode end (CRITICAL FORMAT - no deviations)
    print(f"[END]   success={'true' if success else 'false'} steps={step} score={final_score:.2f} rewards={rewards_str}")
    sys.stdout.flush()
    
    return {
        "task": task,
        "success": success,
        "score": final_score,
        "steps": step,
        "total_reward": total_reward,
        "rewards": rewards,
        "final_state": state,
        "env_metrics": {
            "total_cost": env.total_cost,
            "stockouts": env.stockouts_count,
            "demand_satisfaction": env.total_sold / max(env.total_demand, 1)
        }
    }


def main():
    """Main entry point."""
    
    try:
        print(f"Starting inventory management inference", file=sys.stderr)
        print(f"Task: {TASK}", file=sys.stderr)
        print(f"Model: {MODEL_NAME}", file=sys.stderr)
        print(f"API Base URL: {API_BASE_URL}", file=sys.stderr)
        print("", file=sys.stderr)
        
        # Run the episode
        result = run_episode(TASK, max_steps=30)
        
        print(f"", file=sys.stderr)
        print(f"Episode Complete", file=sys.stderr)
        print(f"Final Score: {result['score']:.2f}", file=sys.stderr)
        print(f"Success: {result['success']}", file=sys.stderr)
        
        return 0 if result['success'] else 1
    
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

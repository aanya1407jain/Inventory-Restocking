#!/usr/bin/env python3
"""
Baseline inference script for inventory management environment.
"""

import os
import sys
import json
from typing import Dict, Any, Optional
from openai import OpenAI
from huggingface_hub import InferenceClient
from inventory_env import InventoryEnv, InventoryAction, InventoryState

# ============================================================================
# Configuration
# ============================================================================
API_BASE_URL = "https://api-inference.huggingface.co/v1" # Standard Serverless API
MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"
HF_TOKEN = os.getenv("HF_TOKEN")
TASK = os.getenv("MY_ENV_TASK", "easy")
BENCHMARK = os.getenv("MY_ENV_BENCHMARK", "inventory-management")

if not HF_TOKEN:
    print("ERROR: HF_TOKEN not set.")
    sys.exit(1)

client = InferenceClient(api_key=os.getenv("HF_TOKEN"))

# ============================================================================
# Logic
# ============================================================================

def build_prompt(state: InventoryState, task: str) -> str:
    products_str = json.dumps(state.products, indent=2)
    demand_str = json.dumps(state.demand_history, indent=2)
    
    prompt = f"""You are managing inventory for an e-commerce warehouse. 
CURRENT STATE (Day {state.current_day}/30):
- Inventory: {products_str}
- Demand History: {demand_str}
- Task: {task.upper()}
Goal: Avoid stockouts. If stock is low (< 50% weekly demand), reorder.
Respond ONLY with valid JSON:
{{"product_id": "SKU001", "quantity": 100, "reorder": true}}"""
    return prompt

def parse_action(response_text: str) -> Optional[InventoryAction]:
    """Extracts JSON from the LLM response even if it contains markdown."""
    try:
        response_text = response_text.strip()
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        data = json.loads(response_text)
        return InventoryAction(
            product_id=data.get("product_id", "SKU001"),
            quantity=int(data.get("quantity", 0)),
            reorder=bool(data.get("reorder", False))
        )
    except Exception:
        return None

def run_episode(task: str, max_steps: int = 30):
    env = InventoryEnv(task=task, seed=42)
    state = env.reset()
    
    print(f"[START] task={task} env={BENCHMARK} model={MODEL_NAME}")
    sys.stdout.flush()

    step = 0
    done = False
    
    while step < max_steps and not done:
        step += 1
        try:
            prompt = build_prompt(state, task)
            
            # 2. Use the native chat_completion method
            response = client.chat_completion(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300
            )
            
            raw_content = response.choices[0].message.content
            action = parse_action(raw_content)
            if not action:
                action = InventoryAction(product_id="SKU001", quantity=0, reorder=False)

            state, reward, done, info = env.step(action)
            
            action_str = f"reorder({action.product_id}, qty={action.quantity})" if action.reorder else "observe"
            print(f"[STEP]  step={step} action={action_str} reward={reward:.2f} done={'true' if done else 'false'} error=null")
            sys.stdout.flush()

        except Exception as e:
            print(f"[STEP]  step={step} action=error reward=0.00 done=true error=\"{str(e)[:50]}\"")
            sys.stdout.flush()
            break

    final_score = env.get_task_score()
    print(f"[END]   success={'true' if final_score >= 0.5 else 'false'} steps={step} score={final_score:.2f}")

if __name__ == "__main__":
    run_episode(TASK)

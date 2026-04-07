import streamlit as st
import json
import pandas as pd
from huggingface_hub import InferenceClient
from inventory_env import InventoryEnv, InventoryAction

# --- PAGE SETUP ---
st.set_page_config(page_title="OpenEnv | Inventory Dashboard", layout="wide")

# Cyberpunk Styling
# --- CUSTOM CSS (Cyberpunk Style) ---
st.markdown("""
    <style>
    .main { background-color: #0a0c0f; color: #e6edf3; }
    .stMetric { background-color: #161b22; border: 1px solid #21262d; padding: 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True) # Changed from unsafe_allow_value

# --- SESSION STATE (The simulation memory) ---
if 'env' not in st.session_state:
    st.session_state.env = InventoryEnv(task="easy", seed=42)
    st.session_state.state = st.session_state.env.reset()
    st.session_state.history = []
    st.session_state.done = False

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.title("📦 INVTRACK Engine")
    st.subheader("Configuration")
    task_mode = st.selectbox("Task Difficulty", ["easy", "medium", "hard"])
    agent_type = st.radio("Control Logic", ["AI Agent (LLM)", "Heuristic (Rules)", "Manual"])
    
    if st.button("Reset Simulation"):
        st.session_state.env = InventoryEnv(task=task_mode, seed=42)
        st.session_state.state = st.session_state.env.reset()
        st.session_state.history = []
        st.session_state.done = False
        st.rerun()

# --- HELPER FUNCTIONS ---
def get_llm_action(state, task):
    """Calls the LLM via InferenceClient (Warning: Will hit 402 if credits empty)"""
    client = InferenceClient(api_key=st.secrets.get("HF_TOKEN"))
    prompt = f"Current Inventory: {state.products}. Task: {task}. Return JSON: {{'product_id': 'SKU001', 'quantity': 100, 'reorder': true}}"
    try:
        response = client.chat_completion(
            model="Qwen/Qwen2.5-7B-Instruct",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )
        data = json.loads(response.choices[0].message.content)
        return InventoryAction(product_id=data['product_id'], quantity=data['quantity'], reorder=data['reorder'])
    except Exception as e:
        st.error(f"AI Error: {str(e)}")
        return None

def heuristic_logic(state):
    """Fall back logic to test the environment without using AI credits"""
    for sku, qty in state.products.items():
        if qty < 40: # Reorder if stock is low
            return InventoryAction(product_id=sku, quantity=100, reorder=True)
    return InventoryAction(product_id="SKU001", quantity=0, reorder=False)

# --- MAIN DASHBOARD ---
st.header(f"Day {st.session_state.state.current_day} / 30")

# Metric Row
m1, m2, m3, m4 = st.columns(4)
m1.metric("Current Cost", f"${st.session_state.state.total_cost:.2f}")
m2.metric("Stockouts", st.session_state.state.stockouts_count)
m3.metric("Step Reward", f"{st.session_state.history[-1]['reward'] if st.session_state.history else 0.0:.2f}")
m4.metric("Status", "FINISHED" if st.session_state.done else "RUNNING")

# Inventory Visualization
st.subheader("Live Stock Levels")
cols = st.columns(3)
for i, (sku, qty) in enumerate(st.session_state.state.products.items()):
    with cols[i]:
        st.write(f"**{sku}**")
        color = "red" if qty < 20 else "green"
        st.markdown(f"<h2 style='color:{color};'>{qty}</h2>", unsafe_allow_html=True)
        st.progress(min(qty / 200, 1.0))

# --- EXECUTION ---
st.divider()

if not st.session_state.done:
    if st.button("▶ Execute Next Step"):
        # Select action based on radio button
        if agent_type == "AI Agent (LLM)":
            action = get_llm_action(st.session_state.state, task_mode)
        elif agent_type == "Heuristic (Rules)":
            action = heuristic_logic(st.session_state.state)
        else: # Manual
            action = InventoryAction(product_id="SKU001", quantity=50, reorder=True)

        if action:
            next_state, reward, done, info = st.session_state.env.step(action)
            
            # Update History
            st.session_state.history.append({
                "day": st.session_state.state.current_day,
                "action": action.product_id if action.reorder else "None",
                "qty": action.quantity,
                "reward": reward
            })
            
            st.session_state.state = next_state
            st.session_state.done = done
            st.rerun()

# Display History Table
if st.session_state.history:
    st.subheader("Action Log")
    df = pd.DataFrame(st.session_state.history)
    st.dataframe(df.tail(10), use_container_width=True)

if st.session_state.done:
    st.balloons()
    st.success(f"Simulation Complete! Final OpenEnv Score: {st.session_state.env.get_task_score():.2f}")

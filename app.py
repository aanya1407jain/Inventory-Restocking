
Copy

"""
Inventory Restocking Decision System — Web Application
Flask app with interactive UI to run and visualize inventory simulations.
"""
 
import json
import sys
import os
from flask import Flask, render_template_string, request, jsonify, session
from inventory_env import InventoryEnv, InventoryAction, InventoryState
from graders.easy_grader import EasyGrader
from graders.medium_grader import MediumGrader
from graders.hard_grader import HardGrader
 
app = Flask(__name__)
app.secret_key = os.urandom(24)
 
# ============================================================================
# HTML Template (single-file, embedded)
# ============================================================================
 
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Inventory Restocking Decision System</title>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Barlow+Condensed:wght@300;400;600;700;900&family=Barlow:wght@300;400;500&display=swap" rel="stylesheet"/>
  <style>
    :root {
      --bg: #0a0c0f;
      --surface: #111318;
      --panel: #161b22;
      --border: #21262d;
      --accent: #00ff88;
      --accent2: #00bfff;
      --warn: #ffb800;
      --danger: #ff4560;
      --text: #e6edf3;
      --muted: #7d8590;
      --mono: 'Share Tech Mono', monospace;
      --sans: 'Barlow', sans-serif;
      --display: 'Barlow Condensed', sans-serif;
    }
 
    * { margin: 0; padding: 0; box-sizing: border-box; }
 
    body {
      background: var(--bg);
      color: var(--text);
      font-family: var(--sans);
      min-height: 100vh;
      overflow-x: hidden;
    }
 
    /* Scanline overlay */
    body::before {
      content: '';
      position: fixed;
      inset: 0;
      background: repeating-linear-gradient(
        0deg, transparent, transparent 2px, rgba(0,255,136,0.015) 2px, rgba(0,255,136,0.015) 4px
      );
      pointer-events: none;
      z-index: 9999;
    }
 
    /* Header */
    header {
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      padding: 0 2rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      height: 60px;
      position: sticky;
      top: 0;
      z-index: 100;
    }
 
    .logo {
      font-family: var(--display);
      font-weight: 900;
      font-size: 1.4rem;
      letter-spacing: 0.15em;
      text-transform: uppercase;
      color: var(--accent);
    }
 
    .logo span {
      color: var(--muted);
      font-weight: 300;
    }
 
    .status-bar {
      display: flex;
      gap: 1.5rem;
      font-family: var(--mono);
      font-size: 0.75rem;
      color: var(--muted);
    }
 
    .status-item {
      display: flex;
      align-items: center;
      gap: 0.4rem;
    }
 
    .dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--accent);
      animation: pulse 2s infinite;
    }
 
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.3; }
    }
 
    /* Main layout */
    .layout {
      display: grid;
      grid-template-columns: 280px 1fr 300px;
      height: calc(100vh - 60px);
    }
 
    /* Sidebar */
    .sidebar {
      background: var(--surface);
      border-right: 1px solid var(--border);
      padding: 1.5rem;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }
 
    .section-label {
      font-family: var(--display);
      font-size: 0.65rem;
      letter-spacing: 0.25em;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 0.75rem;
    }
 
    /* Task selector */
    .task-cards {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }
 
    .task-card {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 1rem;
      cursor: pointer;
      transition: all 0.2s;
      position: relative;
      overflow: hidden;
    }
 
    .task-card::before {
      content: '';
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      width: 3px;
      background: transparent;
      transition: background 0.2s;
    }
 
    .task-card:hover { border-color: var(--accent); }
 
    .task-card.active {
      border-color: var(--accent);
      background: rgba(0,255,136,0.05);
    }
 
    .task-card.active::before { background: var(--accent); }
 
    .task-card.medium.active::before { background: var(--warn); }
    .task-card.hard.active::before { background: var(--danger); }
 
    .task-card.medium.active { border-color: var(--warn); background: rgba(255,184,0,0.05); }
    .task-card.hard.active { border-color: var(--danger); background: rgba(255,69,96,0.05); }
 
    .task-name {
      font-family: var(--display);
      font-size: 1rem;
      font-weight: 700;
      letter-spacing: 0.1em;
      text-transform: uppercase;
    }
 
    .task-desc {
      font-size: 0.75rem;
      color: var(--muted);
      margin-top: 0.3rem;
      line-height: 1.4;
    }
 
    .task-badge {
      display: inline-block;
      font-family: var(--mono);
      font-size: 0.6rem;
      padding: 0.15rem 0.4rem;
      border-radius: 3px;
      margin-top: 0.4rem;
    }
    .badge-easy { background: rgba(0,255,136,0.15); color: var(--accent); }
    .badge-medium { background: rgba(255,184,0,0.15); color: var(--warn); }
    .badge-hard { background: rgba(255,69,96,0.15); color: var(--danger); }
 
    /* Config section */
    .config-row {
      display: flex;
      flex-direction: column;
      gap: 0.3rem;
      margin-bottom: 0.75rem;
    }
 
    .config-label {
      font-size: 0.72rem;
      color: var(--muted);
      font-family: var(--mono);
    }
 
    input[type="number"], select {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 4px;
      color: var(--text);
      padding: 0.5rem 0.75rem;
      font-family: var(--mono);
      font-size: 0.8rem;
      width: 100%;
      outline: none;
      transition: border-color 0.2s;
    }
 
    input[type="number"]:focus, select:focus { border-color: var(--accent); }
 
    /* Buttons */
    .btn {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      padding: 0.6rem 1rem;
      border-radius: 4px;
      border: none;
      font-family: var(--display);
      font-weight: 700;
      font-size: 0.85rem;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      cursor: pointer;
      transition: all 0.2s;
      width: 100%;
    }
 
    .btn-primary {
      background: var(--accent);
      color: #000;
    }
 
    .btn-primary:hover {
      background: #00ffaa;
      box-shadow: 0 0 20px rgba(0,255,136,0.4);
    }
 
    .btn-primary:disabled {
      opacity: 0.4;
      cursor: not-allowed;
      box-shadow: none;
    }
 
    .btn-secondary {
      background: transparent;
      color: var(--muted);
      border: 1px solid var(--border);
    }
 
    .btn-secondary:hover { border-color: var(--muted); color: var(--text); }
 
    .btn-danger {
      background: transparent;
      color: var(--danger);
      border: 1px solid var(--danger);
    }
 
    .btn-danger:hover { background: rgba(255,69,96,0.1); }
 
    /* Main content */
    .main {
      overflow-y: auto;
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }
 
    /* Inventory Grid */
    .inventory-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 1rem;
    }
 
    .sku-card {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1.25rem;
      position: relative;
      overflow: hidden;
      transition: border-color 0.3s;
    }
 
    .sku-card.critical { border-color: var(--danger); }
    .sku-card.warning { border-color: var(--warn); }
    .sku-card.healthy { border-color: var(--accent); }
 
    .sku-id {
      font-family: var(--mono);
      font-size: 0.7rem;
      color: var(--muted);
      letter-spacing: 0.1em;
    }
 
    .sku-stock {
      font-family: var(--display);
      font-size: 2.5rem;
      font-weight: 900;
      line-height: 1;
      margin: 0.3rem 0;
    }
 
    .sku-stock.critical { color: var(--danger); }
    .sku-stock.warning { color: var(--warn); }
    .sku-stock.healthy { color: var(--accent); }
 
    .sku-label { font-size: 0.72rem; color: var(--muted); }
 
    .sku-bar-bg {
      height: 4px;
      background: var(--border);
      border-radius: 2px;
      margin-top: 1rem;
      overflow: hidden;
    }
 
    .sku-bar {
      height: 100%;
      border-radius: 2px;
      transition: width 0.5s ease;
    }
    .sku-bar.critical { background: var(--danger); }
    .sku-bar.warning { background: var(--warn); }
    .sku-bar.healthy { background: var(--accent); }
 
    .sku-meta {
      display: flex;
      justify-content: space-between;
      margin-top: 0.6rem;
      font-family: var(--mono);
      font-size: 0.65rem;
      color: var(--muted);
    }
 
    .on-order-badge {
      position: absolute;
      top: 0.75rem;
      right: 0.75rem;
      background: rgba(0,191,255,0.15);
      color: var(--accent2);
      font-family: var(--mono);
      font-size: 0.6rem;
      padding: 0.1rem 0.4rem;
      border-radius: 3px;
    }
 
    /* Metrics row */
    .metrics-row {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 1rem;
    }
 
    .metric-card {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1rem;
    }
 
    .metric-value {
      font-family: var(--display);
      font-size: 1.8rem;
      font-weight: 900;
      line-height: 1;
    }
 
    .metric-value.good { color: var(--accent); }
    .metric-value.warn { color: var(--warn); }
    .metric-value.bad { color: var(--danger); }
 
    .metric-name {
      font-size: 0.7rem;
      color: var(--muted);
      margin-top: 0.3rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
 
    /* Action panel */
    .action-panel {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1.25rem;
    }
 
    .action-form {
      display: grid;
      grid-template-columns: 1fr 1fr 1fr auto;
      gap: 0.75rem;
      align-items: end;
    }
 
    .form-group { display: flex; flex-direction: column; gap: 0.3rem; }
 
    .step-btn {
      background: var(--accent);
      color: #000;
      border: none;
      border-radius: 4px;
      font-family: var(--display);
      font-weight: 900;
      font-size: 0.9rem;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      padding: 0.5rem 1.5rem;
      cursor: pointer;
      height: 36px;
      transition: all 0.2s;
    }
 
    .step-btn:hover { background: #00ffaa; box-shadow: 0 0 20px rgba(0,255,136,0.4); }
    .step-btn:disabled { opacity: 0.4; cursor: not-allowed; }
 
    /* Log panel */
    .log-container {
      background: #080a0d;
      border: 1px solid var(--border);
      border-radius: 8px;
      height: 220px;
      overflow-y: auto;
      padding: 1rem;
      font-family: var(--mono);
      font-size: 0.72rem;
    }
 
    .log-entry {
      display: flex;
      gap: 0.75rem;
      padding: 0.2rem 0;
      border-bottom: 1px solid rgba(255,255,255,0.03);
      animation: slideIn 0.2s ease;
    }
 
    @keyframes slideIn {
      from { opacity: 0; transform: translateX(-8px); }
      to { opacity: 1; transform: translateX(0); }
    }
 
    .log-day { color: var(--muted); min-width: 40px; }
    .log-action { color: var(--accent2); flex: 1; }
    .log-reward { min-width: 60px; text-align: right; }
    .log-reward.pos { color: var(--accent); }
    .log-reward.neg { color: var(--danger); }
    .log-reward.zero { color: var(--muted); }
    .log-stockout { color: var(--danger); }
 
    /* Right panel */
    .right-panel {
      background: var(--surface);
      border-left: 1px solid var(--border);
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
      overflow-y: auto;
    }
 
    /* Progress ring */
    .progress-section {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.75rem;
    }
 
    .day-progress {
      position: relative;
      width: 120px;
      height: 120px;
    }
 
    .day-progress svg { transform: rotate(-90deg); }
 
    .day-progress-text {
      position: absolute;
      inset: 0;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
    }
 
    .day-num {
      font-family: var(--display);
      font-size: 2rem;
      font-weight: 900;
      line-height: 1;
      color: var(--accent);
    }
 
    .day-label { font-size: 0.6rem; color: var(--muted); letter-spacing: 0.1em; }
 
    /* Demand chart */
    .demand-chart {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1rem;
    }
 
    .bar-chart {
      display: flex;
      align-items: flex-end;
      gap: 4px;
      height: 60px;
    }
 
    .bar-col {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      height: 100%;
      justify-content: flex-end;
    }
 
    .bar-fill {
      width: 100%;
      background: var(--accent2);
      border-radius: 2px 2px 0 0;
      opacity: 0.7;
      transition: height 0.4s ease;
      min-height: 2px;
    }
 
    .bar-fill.latest { opacity: 1; background: var(--accent); }
 
    .bar-label {
      font-family: var(--mono);
      font-size: 0.55rem;
      color: var(--muted);
      margin-top: 2px;
    }
 
    /* Score display */
    .score-card {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1rem;
      text-align: center;
    }
 
    .score-value {
      font-family: var(--display);
      font-size: 3rem;
      font-weight: 900;
      line-height: 1;
    }
 
    .score-value.high { color: var(--accent); }
    .score-value.mid { color: var(--warn); }
    .score-value.low { color: var(--danger); }
 
    .score-label { font-size: 0.7rem; color: var(--muted); margin-top: 0.3rem; }
 
    /* Grade buttons */
    .grade-section {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }
 
    .grade-result {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 0.75rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-family: var(--mono);
      font-size: 0.75rem;
    }
 
    .grade-task { color: var(--muted); }
    .grade-score { font-weight: bold; }
    .grade-score.high { color: var(--accent); }
    .grade-score.mid { color: var(--warn); }
    .grade-score.low { color: var(--danger); }
 
    /* Toast */
    .toast {
      position: fixed;
      bottom: 1.5rem;
      right: 1.5rem;
      background: var(--panel);
      border: 1px solid var(--accent);
      border-radius: 6px;
      padding: 0.75rem 1.25rem;
      font-family: var(--mono);
      font-size: 0.8rem;
      color: var(--accent);
      z-index: 200;
      opacity: 0;
      transform: translateY(10px);
      transition: all 0.3s;
      pointer-events: none;
    }
 
    .toast.show { opacity: 1; transform: translateY(0); }
    .toast.error { border-color: var(--danger); color: var(--danger); }
 
    /* Scrollbar */
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--muted); }
 
    /* Episode complete */
    .episode-complete {
      background: rgba(0,255,136,0.05);
      border: 1px solid var(--accent);
      border-radius: 8px;
      padding: 1.5rem;
      text-align: center;
      display: none;
    }
 
    .episode-complete.show { display: block; animation: fadeIn 0.5s ease; }
 
    @keyframes fadeIn {
      from { opacity: 0; transform: scale(0.97); }
      to { opacity: 1; transform: scale(1); }
    }
 
    .episode-title {
      font-family: var(--display);
      font-size: 1.5rem;
      font-weight: 900;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: var(--accent);
      margin-bottom: 0.5rem;
    }
 
    .episode-subtitle { font-size: 0.8rem; color: var(--muted); }
 
    /* Loading spinner */
    .spinner {
      display: inline-block;
      width: 12px;
      height: 12px;
      border: 2px solid rgba(0,0,0,0.3);
      border-top-color: #000;
      border-radius: 50%;
      animation: spin 0.6s linear infinite;
    }
 
    @keyframes spin { to { transform: rotate(360deg); } }
 
    /* Highlight flash */
    @keyframes flash {
      0% { background: rgba(0,255,136,0.15); }
      100% { background: transparent; }
    }
 
    .flash { animation: flash 0.6s ease; }
  </style>
</head>
<body>
 
<header>
  <div class="logo">INVTRACK <span>/ Decision Engine</span></div>
  <div class="status-bar">
    <div class="status-item"><div class="dot"></div> ENV ONLINE</div>
    <div class="status-item" id="hdr-task">TASK: —</div>
    <div class="status-item" id="hdr-day">DAY: —/30</div>
  </div>
</header>
 
<div class="layout">
  <!-- ── LEFT SIDEBAR ── -->
  <aside class="sidebar">
    <div>
      <div class="section-label">Mission</div>
      <div class="task-cards">
        <div class="task-card easy active" data-task="easy" onclick="selectTask('easy')">
          <div class="task-name">Easy</div>
          <div class="task-desc">Monitor inventory and reorder before stockouts occur.</div>
          <div class="task-badge badge-easy">Stockout Avoidance</div>
        </div>
        <div class="task-card medium" data-task="medium" onclick="selectTask('medium')">
          <div class="task-name">Medium</div>
          <div class="task-desc">Predict demand patterns and maintain 95% service level.</div>
          <div class="task-badge badge-medium">Demand Prediction</div>
        </div>
        <div class="task-card hard" data-task="hard" onclick="selectTask('hard')">
          <div class="task-name">Hard</div>
          <div class="task-desc">Minimize total cost while hitting 99% service level.</div>
          <div class="task-badge badge-hard">Cost Optimization</div>
        </div>
      </div>
    </div>
 
    <div>
      <div class="section-label">Configuration</div>
      <div class="config-row">
        <span class="config-label">Random Seed</span>
        <input type="number" id="seed-input" value="42" min="0" max="9999"/>
      </div>
      <div class="config-row">
        <span class="config-label">Auto-Play Speed (ms)</span>
        <input type="number" id="speed-input" value="500" min="100" max="3000" step="100"/>
      </div>
    </div>
 
    <div style="display:flex;flex-direction:column;gap:0.5rem;">
      <button class="btn btn-primary" id="start-btn" onclick="startEpisode()">
        ▶ Start Episode
      </button>
      <button class="btn btn-secondary" id="auto-btn" onclick="toggleAuto()" disabled>
        ⚡ Auto-Play
      </button>
      <button class="btn btn-danger" id="reset-btn" onclick="resetEpisode()">
        ↺ Reset
      </button>
    </div>
 
    <div>
      <div class="section-label">Benchmark Grader</div>
      <div class="grade-section">
        <button class="btn btn-secondary" onclick="runGrader('easy')" style="color:var(--accent);border-color:var(--accent)">
          Grade Easy
        </button>
        <button class="btn btn-secondary" onclick="runGrader('medium')" style="color:var(--warn);border-color:var(--warn)">
          Grade Medium
        </button>
        <button class="btn btn-secondary" onclick="runGrader('hard')" style="color:var(--danger);border-color:var(--danger)">
          Grade Hard
        </button>
        <div id="grade-results"></div>
      </div>
    </div>
 
    <div style="margin-top:auto;">
      <div class="section-label">SKU Reference</div>
      <div style="font-family:var(--mono);font-size:0.65rem;color:var(--muted);line-height:1.8;">
        <div>SKU001 · μ=12/day · $0.50/u · $15 order</div>
        <div>SKU002 · μ=8/day  · $0.80/u · $20 order</div>
        <div>SKU003 · μ=18/day · $0.30/u · $12 order</div>
        <div style="margin-top:0.5rem;">Lead Time: 3 days · Max: 200 units</div>
      </div>
    </div>
  </aside>
 
  <!-- ── MAIN ── -->
  <main class="main">
    <!-- SKU Cards -->
    <div>
      <div class="section-label">Inventory Status</div>
      <div class="inventory-grid">
        <div class="sku-card" id="card-SKU001">
          <div class="sku-id">SKU001</div>
          <div class="sku-stock" id="stock-SKU001">—</div>
          <div class="sku-label">units in stock</div>
          <div class="sku-bar-bg"><div class="sku-bar" id="bar-SKU001" style="width:0%"></div></div>
          <div class="sku-meta">
            <span>demand: 12/day</span>
            <span id="coverage-SKU001">— days</span>
          </div>
        </div>
        <div class="sku-card" id="card-SKU002">
          <div class="sku-id">SKU002</div>
          <div class="sku-stock" id="stock-SKU002">—</div>
          <div class="sku-label">units in stock</div>
          <div class="sku-bar-bg"><div class="sku-bar" id="bar-SKU002" style="width:0%"></div></div>
          <div class="sku-meta">
            <span>demand: 8/day</span>
            <span id="coverage-SKU002">— days</span>
          </div>
        </div>
        <div class="sku-card" id="card-SKU003">
          <div class="sku-id">SKU003</div>
          <div class="sku-stock" id="stock-SKU003">—</div>
          <div class="sku-label">units in stock</div>
          <div class="sku-bar-bg"><div class="sku-bar" id="bar-SKU003" style="width:0%"></div></div>
          <div class="sku-meta">
            <span>demand: 18/day</span>
            <span id="coverage-SKU003">— days</span>
          </div>
        </div>
      </div>
    </div>
 
    <!-- Metrics -->
    <div>
      <div class="section-label">Episode Metrics</div>
      <div class="metrics-row">
        <div class="metric-card">
          <div class="metric-value good" id="m-cost">$0.00</div>
          <div class="metric-name">Total Cost</div>
        </div>
        <div class="metric-card">
          <div class="metric-value" id="m-stockouts">0</div>
          <div class="metric-name">Stockouts</div>
        </div>
        <div class="metric-card">
          <div class="metric-value good" id="m-reward">0.00</div>
          <div class="metric-name">Cumulative Reward</div>
        </div>
        <div class="metric-card">
          <div class="metric-value good" id="m-score">—</div>
          <div class="metric-name">Episode Score</div>
        </div>
      </div>
    </div>
 
    <!-- Manual Action -->
    <div>
      <div class="section-label">Manual Action</div>
      <div class="action-panel">
        <div class="action-form">
          <div class="form-group">
            <span class="config-label">Product SKU</span>
            <select id="action-sku">
              <option value="SKU001">SKU001</option>
              <option value="SKU002">SKU002</option>
              <option value="SKU003">SKU003</option>
            </select>
          </div>
          <div class="form-group">
            <span class="config-label">Quantity (0–200)</span>
            <input type="number" id="action-qty" value="50" min="0" max="200"/>
          </div>
          <div class="form-group">
            <span class="config-label">Reorder?</span>
            <select id="action-reorder">
              <option value="true">Yes — Place Order</option>
              <option value="false">No — Observe Only</option>
            </select>
          </div>
          <button class="step-btn" id="step-btn" onclick="takeStep()" disabled>
            STEP →
          </button>
        </div>
      </div>
    </div>
 
    <!-- Episode complete banner -->
    <div class="episode-complete" id="episode-complete">
      <div class="episode-title">Episode Complete</div>
      <div class="episode-subtitle" id="complete-subtitle">—</div>
    </div>
 
    <!-- Log -->
    <div>
      <div class="section-label">Step Log</div>
      <div class="log-container" id="log-container">
        <div style="color:var(--muted);font-family:var(--mono);font-size:0.72rem;">
          Select a task and press Start to begin the simulation...
        </div>
      </div>
    </div>
  </main>
 
  <!-- ── RIGHT PANEL ── -->
  <aside class="right-panel">
    <!-- Day progress -->
    <div>
      <div class="section-label">Simulation Progress</div>
      <div class="progress-section">
        <div class="day-progress">
          <svg width="120" height="120" viewBox="0 0 120 120">
            <circle cx="60" cy="60" r="52" fill="none" stroke="var(--border)" stroke-width="8"/>
            <circle cx="60" cy="60" r="52" fill="none" stroke="var(--accent)" stroke-width="8"
              stroke-dasharray="326.7" stroke-dashoffset="326.7"
              id="progress-ring" stroke-linecap="round"/>
          </svg>
          <div class="day-progress-text">
            <div class="day-num" id="day-num">0</div>
            <div class="day-label">OF 30 DAYS</div>
          </div>
        </div>
      </div>
    </div>
 
    <!-- Demand history chart -->
    <div>
      <div class="section-label">Demand History (7 days)</div>
      <div class="demand-chart">
        <div class="bar-chart" id="demand-bars">
          <div style="color:var(--muted);font-size:0.7rem;font-family:var(--mono);">No data yet</div>
        </div>
      </div>
    </div>
 
    <!-- Score card -->
    <div>
      <div class="section-label">Live Score</div>
      <div class="score-card">
        <div class="score-value" id="score-display">—</div>
        <div class="score-label" id="score-label">Start an episode to evaluate</div>
      </div>
    </div>
 
    <!-- Last action info -->
    <div>
      <div class="section-label">Last Action</div>
      <div class="demand-chart">
        <div id="last-action-info" style="font-family:var(--mono);font-size:0.72rem;color:var(--muted);">—</div>
      </div>
    </div>
 
    <!-- On-order status -->
    <div>
      <div class="section-label">Orders In Transit</div>
      <div id="on-order-panel" style="font-family:var(--mono);font-size:0.72rem;color:var(--muted);">
        No active orders
      </div>
    </div>
  </aside>
</div>
 
<div class="toast" id="toast"></div>
 
<script>
  // ── State ──
  let currentTask = 'easy';
  let running = false;
  let autoPlay = false;
  let autoTimer = null;
  let cumulativeReward = 0;
  let episodeDone = false;
 
  const DEMANDS = { SKU001: 12, SKU002: 8, SKU003: 18 };
 
  // ── Task selection ──
  function selectTask(task) {
    currentTask = task;
    document.querySelectorAll('.task-card').forEach(c => c.classList.remove('active'));
    document.querySelector(`.task-card[data-task="${task}"]`).classList.add('active');
    document.getElementById('hdr-task').textContent = `TASK: ${task.toUpperCase()}`;
  }
 
  // ── Start episode ──
  async function startEpisode() {
    const seed = parseInt(document.getElementById('seed-input').value) || 42;
    const res = await fetch('/api/reset', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task: currentTask, seed })
    });
    const data = await res.json();
 
    running = true;
    episodeDone = false;
    cumulativeReward = 0;
 
    document.getElementById('episode-complete').classList.remove('show');
    document.getElementById('step-btn').disabled = false;
    document.getElementById('auto-btn').disabled = false;
    document.getElementById('log-container').innerHTML = '';
    document.getElementById('m-score').textContent = '—';
    document.getElementById('score-display').textContent = '—';
    document.getElementById('score-display').className = 'score-value';
    document.getElementById('score-label').textContent = 'Episode in progress...';
 
    updateUI(data.state, null, null);
    showToast(`Episode started · Task: ${currentTask.toUpperCase()} · Seed: ${seed}`);
  }
 
  // ── Reset ──
  async function resetEpisode() {
    stopAuto();
    running = false;
    episodeDone = false;
    cumulativeReward = 0;
    document.getElementById('step-btn').disabled = true;
    document.getElementById('auto-btn').disabled = true;
    document.getElementById('auto-btn').textContent = '⚡ Auto-Play';
    document.getElementById('episode-complete').classList.remove('show');
    document.getElementById('log-container').innerHTML =
      '<div style="color:var(--muted);font-family:var(--mono);font-size:0.72rem;">Select a task and press Start to begin...</div>';
 
    // Reset displays
    ['SKU001','SKU002','SKU003'].forEach(sku => {
      document.getElementById(`stock-${sku}`).textContent = '—';
      document.getElementById(`bar-${sku}`).style.width = '0%';
      document.getElementById(`coverage-${sku}`).textContent = '— days';
      setSkuStatus(sku, 'neutral');
    });
 
    document.getElementById('day-num').textContent = '0';
    document.getElementById('progress-ring').style.strokeDashoffset = '326.7';
    document.getElementById('demand-bars').innerHTML = '<div style="color:var(--muted);font-size:0.7rem;font-family:var(--mono);">No data yet</div>';
    document.getElementById('m-cost').textContent = '$0.00';
    document.getElementById('m-stockouts').textContent = '0';
    document.getElementById('m-reward').textContent = '0.00';
    document.getElementById('m-score').textContent = '—';
    document.getElementById('score-display').textContent = '—';
    document.getElementById('score-label').textContent = 'Start an episode to evaluate';
    document.getElementById('hdr-day').textContent = 'DAY: —/30';
    document.getElementById('last-action-info').textContent = '—';
    document.getElementById('on-order-panel').textContent = 'No active orders';
 
    await fetch('/api/reset_session', { method: 'POST' });
  }
 
  // ── Take step ──
  async function takeStep() {
    if (!running || episodeDone) return;
 
    const sku = document.getElementById('action-sku').value;
    const qty = parseInt(document.getElementById('action-qty').value) || 0;
    const reorder = document.getElementById('action-reorder').value === 'true';
 
    document.getElementById('step-btn').disabled = true;
 
    const res = await fetch('/api/step', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ product_id: sku, quantity: qty, reorder })
    });
 
    const data = await res.json();
    if (data.error) { showToast(data.error, true); document.getElementById('step-btn').disabled = false; return; }
 
    cumulativeReward += data.reward;
    updateUI(data.state, data, data.info);
    addLog(data.state.current_day - 1, sku, qty, reorder, data.reward, data.info);
 
    if (data.done) {
      episodeDone = true;
      stopAuto();
      showEpisodeComplete(data.score);
    } else {
      document.getElementById('step-btn').disabled = false;
    }
  }
 
  // ── Auto-play ──
  function toggleAuto() {
    if (autoPlay) {
      stopAuto();
    } else {
      autoPlay = true;
      document.getElementById('auto-btn').textContent = '⏹ Stop Auto';
      runAuto();
    }
  }
 
  function stopAuto() {
    autoPlay = false;
    clearTimeout(autoTimer);
    document.getElementById('auto-btn').textContent = '⚡ Auto-Play';
  }
 
  async function runAuto() {
    if (!autoPlay || episodeDone) { stopAuto(); return; }
 
    // Simple heuristic: pick lowest stock SKU and reorder if below threshold
    const res = await fetch('/api/state');
    const stateData = await res.json();
    if (!stateData.state) { stopAuto(); return; }
 
    const state = stateData.state;
    let bestSku = 'SKU001';
    let minCoverage = Infinity;
    for (const [sku, qty] of Object.entries(state.products)) {
      const cov = qty / DEMANDS[sku];
      if (cov < minCoverage) { minCoverage = cov; bestSku = sku; }
    }
    const shouldOrder = minCoverage < 5;
    const qty = shouldOrder ? Math.min(200, Math.round(DEMANDS[bestSku] * 10)) : 0;
 
    document.getElementById('action-sku').value = bestSku;
    document.getElementById('action-qty').value = qty;
    document.getElementById('action-reorder').value = shouldOrder ? 'true' : 'false';
 
    await takeStep();
 
    if (!episodeDone && autoPlay) {
      const speed = parseInt(document.getElementById('speed-input').value) || 500;
      autoTimer = setTimeout(runAuto, speed);
    }
  }
 
  // ── Run grader ──
  async function runGrader(task) {
    showToast(`Running ${task} grader...`);
    const res = await fetch('/api/grade', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task })
    });
    const data = await res.json();
    const score = data.score;
    const cls = score >= 0.7 ? 'high' : score >= 0.4 ? 'mid' : 'low';
 
    const existing = document.getElementById(`grade-${task}`);
    const div = existing || document.createElement('div');
    div.id = `grade-${task}`;
    div.className = 'grade-result';
    div.innerHTML = `
      <span class="grade-task">${task.toUpperCase()}</span>
      <span class="grade-score ${cls}">${(score * 100).toFixed(1)}%</span>
    `;
    if (!existing) document.getElementById('grade-results').appendChild(div);
 
    showToast(`${task.toUpperCase()} grade: ${(score * 100).toFixed(1)}%`);
  }
 
  // ── UI Updates ──
  function updateUI(state, stepData, info) {
    if (!state) return;
 
    // Day progress
    const day = state.current_day;
    document.getElementById('day-num').textContent = day;
    document.getElementById('hdr-day').textContent = `DAY: ${day}/30`;
    const pct = day / 30;
    const circumference = 326.7;
    document.getElementById('progress-ring').style.strokeDashoffset = circumference * (1 - pct);
 
    // SKU cards
    for (const [sku, qty] of Object.entries(state.products)) {
      const el = document.getElementById(`stock-${sku}`);
      el.textContent = qty;
      const pctFill = Math.min(100, (qty / 200) * 100);
      const coverage = (qty / DEMANDS[sku]).toFixed(1);
      document.getElementById(`coverage-${sku}`).textContent = `${coverage}d cover`;
 
      let status = 'healthy';
      if (qty / DEMANDS[sku] < 2) status = 'critical';
      else if (qty / DEMANDS[sku] < 5) status = 'warning';
 
      setSkuStatus(sku, status);
      const bar = document.getElementById(`bar-${sku}`);
      bar.style.width = pctFill + '%';
      bar.className = `sku-bar ${status}`;
      el.className = `sku-stock ${status}`;
      document.getElementById(`card-${sku}`).className = `sku-card ${status}`;
    }
 
    // Metrics
    document.getElementById('m-cost').textContent = `$${state.total_cost.toFixed(2)}`;
    const so = state.stockouts_count;
    const soEl = document.getElementById('m-stockouts');
    soEl.textContent = so;
    soEl.className = `metric-value ${so === 0 ? 'good' : so < 3 ? 'warn' : 'bad'}`;
 
    const rwEl = document.getElementById('m-reward');
    rwEl.textContent = cumulativeReward.toFixed(2);
    rwEl.className = `metric-value ${cumulativeReward >= 0 ? 'good' : 'bad'}`;
 
    if (stepData && stepData.score !== undefined) {
      const sc = stepData.score;
      document.getElementById('m-score').textContent = (sc * 100).toFixed(1) + '%';
      const scCls = sc >= 0.7 ? 'high' : sc >= 0.4 ? 'mid' : 'low';
      document.getElementById('score-display').textContent = (sc * 100).toFixed(0) + '%';
      document.getElementById('score-display').className = `score-value ${scCls}`;
    }
 
    // Demand bars
    if (state.demand_history && state.demand_history.length > 0) {
      const hist = state.demand_history;
      const maxD = Math.max(...hist, 1);
      let barsHtml = '';
      hist.forEach((d, i) => {
        const h = Math.max(4, Math.round((d / maxD) * 60));
        const isLatest = i === hist.length - 1;
        barsHtml += `
          <div class="bar-col">
            <div class="bar-fill ${isLatest ? 'latest' : ''}" style="height:${h}px"></div>
            <div class="bar-label">${d}</div>
          </div>`;
      });
      document.getElementById('demand-bars').innerHTML = barsHtml;
    }
 
    // Last action
    document.getElementById('last-action-info').textContent = state.last_action || '—';
 
    // On-order (from stepData extras if available)
    if (info && info.order_placed) {
      document.getElementById('on-order-panel').innerHTML =
        `<span style="color:var(--accent2)">Order placed · arrives in 3 days</span>`;
    }
  }
 
  function setSkuStatus(sku, status) {
    // handled inline in updateUI
  }
 
  function addLog(day, sku, qty, reorder, reward, info) {
    const container = document.getElementById('log-container');
    const entry = document.createElement('div');
    entry.className = 'log-entry';
 
    const action = reorder ? `order(${sku}, qty=${qty})` : 'observe';
    const rwCls = reward > 0 ? 'pos' : reward < 0 ? 'neg' : 'zero';
    const stockoutMark = info && info.stockout ? '<span class="log-stockout"> ⚠ STOCKOUT</span>' : '';
 
    entry.innerHTML = `
      <span class="log-day">D${String(day + 1).padStart(2,'0')}</span>
      <span class="log-action">${action}${stockoutMark}</span>
      <span class="log-reward ${rwCls}">${reward >= 0 ? '+' : ''}${reward.toFixed(2)}</span>
    `;
    container.appendChild(entry);
    container.scrollTop = container.scrollHeight;
  }
 
  function showEpisodeComplete(score) {
    const el = document.getElementById('episode-complete');
    const pct = score !== undefined ? (score * 100).toFixed(1) : '—';
    const pass = score >= 0.5;
    document.getElementById('complete-subtitle').textContent =
      `Final Score: ${pct}% · ${pass ? 'PASSED ✓' : 'FAILED ✗'} · Task: ${currentTask.toUpperCase()}`;
    el.style.borderColor = pass ? 'var(--accent)' : 'var(--danger)';
    el.style.background = pass ? 'rgba(0,255,136,0.05)' : 'rgba(255,69,96,0.05)';
    document.querySelector('.episode-title').style.color = pass ? 'var(--accent)' : 'var(--danger)';
    el.classList.add('show');
    stopAuto();
    document.getElementById('step-btn').disabled = true;
    showToast(`Episode complete! Score: ${pct}%`);
  }
 
  function showToast(msg, isError = false) {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.className = `toast ${isError ? 'error' : ''} show`;
    setTimeout(() => t.classList.remove('show'), 3000);
  }
</script>
</body>
</html>
"""
 
 
# ============================================================================
# In-memory session store (single-user; for multi-user use Flask-Session)
# ============================================================================
 
_env_store: dict = {}  # Holds the InventoryEnv instance
 
 
def get_env() -> InventoryEnv | None:
    return _env_store.get("env")
 
 
# ============================================================================
# Routes
# ============================================================================
 
@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)
 
 
@app.route("/api/reset", methods=["POST"])
def api_reset():
    data = request.get_json(force=True)
    task = data.get("task", "easy")
    seed = int(data.get("seed", 42))
 
    env = InventoryEnv(task=task, seed=seed)
    state = env.reset()
    _env_store["env"] = env
 
    return jsonify({"state": state.model_dump(), "task": task})
 
 
@app.route("/api/reset_session", methods=["POST"])
def api_reset_session():
    _env_store.clear()
    return jsonify({"ok": True})
 
 
@app.route("/api/state", methods=["GET"])
def api_state():
    env = get_env()
    if env is None:
        return jsonify({"error": "No active episode. Call /api/reset first."}), 400
    return jsonify({"state": env.state().model_dump()})
 
 
@app.route("/api/step", methods=["POST"])
def api_step():
    env = get_env()
    if env is None:
        return jsonify({"error": "No active episode. Start one first."}), 400
 
    data = request.get_json(force=True)
 
    try:
        action = InventoryAction(
            product_id=data.get("product_id", "SKU001"),
            quantity=int(data.get("quantity", 0)),
            reorder=bool(data.get("reorder", False)),
        )
    except Exception as e:
        return jsonify({"error": f"Invalid action: {e}"}), 400
 
    next_state, reward, done, info = env.step(action)
    score = env.get_task_score() if done else None
 
    return jsonify({
        "state": next_state.model_dump(),
        "reward": round(reward, 4),
        "done": done,
        "info": info,
        "score": score,
    })
 
 
@app.route("/api/grade", methods=["POST"])
def api_grade():
    data = request.get_json(force=True)
    task = data.get("task", "easy")
 
    try:
        if task == "easy":
            grader = EasyGrader()
        elif task == "medium":
            grader = MediumGrader()
        elif task == "hard":
            grader = HardGrader()
        else:
            return jsonify({"error": f"Unknown task: {task}"}), 400
 
        score = grader.grade()
        metrics = grader.get_metrics()
 
        return jsonify({"task": task, "score": round(score, 4), "metrics": metrics})
 
    except Exception as e:
        return jsonify({"error": str(e)}), 500
 
 
# ============================================================================
# Entry point
# ============================================================================
 
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
 
    print(f"")
    print(f"  ╔══════════════════════════════════════════╗")
    print(f"  ║   Inventory Restocking Decision System   ║")
    print(f"  ║   http://localhost:{port}                    ║")
    print(f"  ╚══════════════════════════════════════════╝")
    print(f"")
 
    app.run(host="0.0.0.0", port=port, debug=debug)
 
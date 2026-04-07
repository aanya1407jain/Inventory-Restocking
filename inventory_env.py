"""
Inventory Restocking Decision Environment
OpenEnv-compliant environment for AI agent inventory management
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Tuple, Any
import json
import random
from datetime import datetime


class InventoryState(BaseModel):
    """Observable state of the inventory system"""
    products: Dict[str, int] = Field(description="Current inventory by SKU")
    demand_history: List[int] = Field(description="Last 7 days of demand")
    lead_time: int = Field(description="Days until next order arrives")
    current_day: int = Field(description="Simulation day (0-30)")
    total_cost: float = Field(description="Cumulative order + holding costs")
    stockouts_count: int = Field(description="Number of stockouts so far")
    last_action: Optional[str] = Field(default=None)


class InventoryAction(BaseModel):
    """Action space: agent decides what to order"""
    product_id: str = Field(description="SKU to reorder (SKU001, SKU002, SKU003)")
    quantity: int = Field(default=0, ge=0, le=200, description="Units to order")
    reorder: bool = Field(default=False, description="Place order?")


class InventoryEnv:
    """
    Inventory management simulation environment.
    
    State: Current stock levels, demand history, costs
    Action: Reorder decisions (which product, how much)
    Reward: Based on cost efficiency and service level
    """
    
    # SKU configurations: (initial_stock, daily_demand_mean, holding_cost, order_cost)
    SKU_CONFIG = {
        "SKU001": {"initial": 80, "demand_mean": 12, "demand_std": 3, "holding_cost": 0.5, "order_cost": 15},
        "SKU002": {"initial": 50, "demand_mean": 8, "demand_std": 2, "holding_cost": 0.8, "order_cost": 20},
        "SKU003": {"initial": 120, "demand_mean": 18, "demand_std": 4, "holding_cost": 0.3, "order_cost": 12},
    }
    
    def __init__(self, task: str = "easy", seed: int = 42):
        """
        Initialize environment.
        
        Args:
            task: "easy", "medium", or "hard"
            seed: Random seed for reproducibility
        """
        self.task = task
        self.seed = seed
        random.seed(seed)
        
        self.max_days = 30
        self.max_inventory = 200
        self.lead_time_base = 3
        
        # Initialize products
        self.products: Dict[str, int] = {
            sku: config["initial"] 
            for sku, config in self.SKU_CONFIG.items()
        }
        self.products_on_order: Dict[str, int] = {sku: 0 for sku in self.products}
        self.lead_time_remaining: Dict[str, int] = {sku: 0 for sku in self.products}
        
        # Metrics
        self.current_day = 0
        self.total_cost = 0.0
        self.stockouts_count = 0
        self.total_demand = 0
        self.total_sold = 0
        self.demand_history: List[int] = []
        self.last_action = None
        
    def reset(self) -> InventoryState:
        """Reset environment for new episode"""
        random.seed(self.seed)
        
        self.products = {
            sku: config["initial"] 
            for sku, config in self.SKU_CONFIG.items()
        }
        self.products_on_order = {sku: 0 for sku in self.products}
        self.lead_time_remaining = {sku: 0 for sku in self.products}
        
        self.current_day = 0
        self.total_cost = 0.0
        self.stockouts_count = 0
        self.total_demand = 0
        self.total_sold = 0
        self.demand_history = []
        self.last_action = None
        
        return self.state()
    
    def state(self) -> InventoryState:
        """Get current observable state"""
        return InventoryState(
            products=self.products.copy(),
            demand_history=self.demand_history[-7:] if self.demand_history else [0] * 7,
            lead_time=self.lead_time_remaining.get(list(self.products.keys())[0], 0),
            current_day=self.current_day,
            total_cost=round(self.total_cost, 2),
            stockouts_count=self.stockouts_count,
            last_action=self.last_action
        )
    
    def _generate_demand(self, sku: str) -> int:
        """Generate stochastic daily demand for SKU"""
        config = self.SKU_CONFIG[sku]
        demand = max(0, int(random.gauss(config["demand_mean"], config["demand_std"])))
        return demand
    
    def step(self, action: InventoryAction) -> Tuple[InventoryState, float, bool, Dict[str, Any]]:
        """
        Execute one step of the environment.
        
        Args:
            action: InventoryAction specifying reorder decision
            
        Returns:
            (next_state, reward, done, info)
        """
        if self.current_day >= self.max_days:
            return self.state(), 0.0, True, {"error": "Episode finished"}
        
        reward = 0.0
        info = {
            "day": self.current_day,
            "stockout": False,
            "order_placed": False,
            "demand": {}
        }
        
        # Process incoming orders
        for sku in self.products:
            if self.lead_time_remaining[sku] > 0:
                self.lead_time_remaining[sku] -= 1
                if self.lead_time_remaining[sku] == 0 and self.products_on_order[sku] > 0:
                    self.products[sku] = min(
                        self.products[sku] + self.products_on_order[sku],
                        self.max_inventory
                    )
                    self.products_on_order[sku] = 0
        
        # Process agent action (reorder)
        if action.reorder and action.product_id in self.products:
            if action.quantity > 0:
                order_cost = self.SKU_CONFIG[action.product_id]["order_cost"]
                self.total_cost += order_cost
                self.products_on_order[action.product_id] = action.quantity
                self.lead_time_remaining[action.product_id] = self.lead_time_base
                info["order_placed"] = True
                self.last_action = f"order({action.product_id}, qty={action.quantity})"
        
        if not info["order_placed"]:
            self.last_action = "observe"
        
        # Simulate demand for all products
        for sku in self.products:
            demand = self._generate_demand(sku)
            info["demand"][sku] = demand
            self.total_demand += demand
            
            if self.products[sku] >= demand:
                self.products[sku] -= demand
                self.total_sold += demand
            else:
                # Stockout: sell what's available, lose the rest
                self.total_sold += self.products[sku]
                self.products[sku] = 0
                self.stockouts_count += 1
                info["stockout"] = True
                reward -= 0.3  # Penalty for stockout
        
        # Holding cost (cost of keeping inventory)
        for sku in self.products:
            holding_cost = self.SKU_CONFIG[sku]["holding_cost"]
            self.total_cost += holding_cost * self.products[sku]
        
        # Reward logic depends on task
        if self.task == "easy":
            # Simple: reward for no stockout, penalty for stockout
            if not info["stockout"]:
                reward += 0.1
        elif self.task == "medium":
            # Reward for demand satisfaction (service level)
            service_level = self.total_sold / max(self.total_demand, 1)
            reward += service_level * 0.1
        elif self.task == "hard":
            # Multi-objective: cost efficiency + service level
            service_level = self.total_sold / max(self.total_demand, 1)
            cost_ratio = self.total_cost / (self.current_day * 50 + 1)  # Normalize by days
            reward += (service_level * 0.9 - cost_ratio * 0.1)
        
        self.current_day += 1
        done = (self.current_day >= self.max_days)
        
        return self.state(), round(reward, 2), done, info
    
    def get_task_score(self) -> float:
        """
        Calculate final score based on task type.
        Score is normalized to [0, 1].
        """
        if self.current_day == 0:
            return 0.0
        
        service_level = self.total_sold / max(self.total_demand, 1)
        cost_per_day = self.total_cost / self.current_day
        
        if self.task == "easy":
            # Easy: just measure if we avoided stockouts
            score = max(0, 1.0 - (self.stockouts_count / self.max_days))
        elif self.task == "medium":
            # Medium: service level with some cost penalty
            score = service_level * max(0, 1.0 - (cost_per_day / 100))
        elif self.task == "hard":
            # Hard: optimize both cost and service
            baseline_cost = 50  # Expected cost per day
            cost_efficiency = max(0, 1.0 - (cost_per_day / baseline_cost))
            score = (service_level * 0.6 + cost_efficiency * 0.4)
        else:
            score = 0.0
        
        return round(min(1.0, max(0.0, score)), 2)


def test_env():
    """Quick test of environment"""
    env = InventoryEnv(task="easy")
    state = env.reset()
    print(f"Initial state: {state}")
    
    # Take 5 steps
    for i in range(5):
        action = InventoryAction(product_id="SKU001", quantity=50, reorder=i % 2 == 0)
        next_state, reward, done, info = env.step(action)
        print(f"Step {i+1}: reward={reward}, done={done}, stockout={info.get('stockout')}")
        if done:
            break
    
    score = env.get_task_score()
    print(f"Final score: {score}")


if __name__ == "__main__":
    test_env()

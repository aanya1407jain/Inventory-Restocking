"""
Hard Task Grader: Multi-objective optimization (cost + service)
Grades: Can the agent minimize total cost while maintaining 99% service?
"""

from inventory_env import InventoryEnv, InventoryAction


class HardGrader:
    """
    Hard task grader: Minimize cost while maintaining 99% service level.
    
    Metrics:
    - Service level (critical): Must maintain >99% demand satisfaction
    - Cost efficiency (primary): Minimize total ordering + holding costs
    - Stockout penalty (severe): Heavily penalizes any stockouts
    
    Score formula:
    service_score = min(1.0, actual_service / 0.99)
    cost_score = max(0.0, 1.0 - cost_per_day / baseline_cost)
    stockout_penalty = max(0.0, 1.0 - stockouts / 10)
    score = service_score * 0.5 + cost_score * 0.3 + stockout_penalty * 0.2
    """
    
    def __init__(self, task_name: str = "hard"):
        self.task_name = task_name
        self.metrics = {
            "total_demand": 0,
            "total_satisfied": 0,
            "total_cost": 0.0,
            "orders_placed": 0,
            "stockouts": 0,
            "service_level": 0.0,
            "cost_per_day": 0.0,
            "cost_per_unit": 0.0,
            "steps_taken": 0,
        }
    
    def _calculate_optimal_order(self, sku: str, current_qty: int, history: list) -> int:
        """
        Calculate optimal order quantity for a SKU.
        
        Uses Economic Order Quantity (EOQ) approximation:
        EOQ = sqrt(2 * D * S / H)
        Where:
        - D = annual demand
        - S = cost per order
        - H = holding cost per unit
        """
        sku_config = {
            "SKU001": {"demand_mean": 12, "order_cost": 15, "holding_cost": 0.5},
            "SKU002": {"demand_mean": 8, "order_cost": 20, "holding_cost": 0.8},
            "SKU003": {"demand_mean": 18, "order_cost": 12, "holding_cost": 0.3},
        }
        
        config = sku_config.get(sku, sku_config["SKU001"])
        
        # Average daily demand
        avg_demand = config["demand_mean"]
        
        # If current inventory < 3 days of demand, reorder
        days_of_stock = current_qty / max(avg_demand, 1)
        
        if days_of_stock < 3:
            # Order for 7 days ahead
            order_qty = avg_demand * 7
            return min(200, order_qty)
        
        return 0
    
    def grade(self, seed: int = 42) -> float:
        """
        Run environment with optimization heuristic.
        
        Returns:
            score (float): Grade from 0.0 to 1.0
        """
        env = InventoryEnv(task=self.task_name, seed=seed)
        state = env.reset()
        
        done = False
        step = 0
        
        # Strategy: Optimize all three SKUs together
        # Track which SKU needs ordering most urgently
        last_ordered_day = {"SKU001": -10, "SKU002": -10, "SKU003": -10}
        
        while not done and step < 30:
            step += 1
            
            # Find the most urgent SKU to reorder
            product_to_order = None
            min_score = float('inf')
            
            for sku in state.products.keys():
                qty = state.products[sku]
                mean_demand_map = {"SKU001": 12, "SKU002": 8, "SKU003": 18}
                expected_demand = mean_demand_map.get(sku, 10)
                
                # Score: days of stock remaining
                days_of_stock = qty / max(expected_demand, 1)
                
                # Urgency: which one is running out soonest?
                if days_of_stock < min_score:
                    min_score = days_of_stock
                    product_to_order = sku
            
            # Reorder decision
            should_reorder = False
            order_qty = 0
            
            # If stock is critically low (< 2 days), order aggressively
            if min_score < 2:
                should_reorder = True
                order_qty = self._calculate_optimal_order(
                    product_to_order,
                    state.products[product_to_order],
                    state.demand_history
                )
                if order_qty > 0:
                    last_ordered_day[product_to_order] = step
                    self.metrics["orders_placed"] += 1
            
            # Also consider: if we haven't ordered in a while and stock is moderate, preorder
            elif min_score < 5 and (step - last_ordered_day.get(product_to_order, -10)) > 7:
                should_reorder = True
                order_qty = self._calculate_optimal_order(
                    product_to_order,
                    state.products[product_to_order],
                    state.demand_history
                )
                if order_qty > 0:
                    last_ordered_day[product_to_order] = step
                    self.metrics["orders_placed"] += 1
            
            action = InventoryAction(
                product_id=product_to_order or "SKU001",
                quantity=order_qty,
                reorder=should_reorder
            )
            
            state, reward, done, info = env.step(action)
            
            if info.get("stockout"):
                self.metrics["stockouts"] += 1
            
            self.metrics["steps_taken"] = step
        
        # Calculate metrics from final environment state
        self.metrics["total_demand"] = env.total_demand
        self.metrics["total_satisfied"] = env.total_sold
        self.metrics["total_cost"] = env.total_cost
        
        # Service level (must be >99% for hard task)
        service_level = env.total_sold / max(env.total_demand, 1)
        self.metrics["service_level"] = round(service_level, 4)
        
        # Cost metrics
        cost_per_day = env.total_cost / max(step, 1)
        cost_per_unit = env.total_cost / max(env.total_sold, 1)
        
        self.metrics["cost_per_day"] = round(cost_per_day, 2)
        self.metrics["cost_per_unit"] = round(cost_per_unit, 2)
        
        # Scoring
        # Service level: must be >99%
        service_score = min(1.0, service_level / 0.99)
        
        # Cost efficiency: baseline is ~50/day for 3 SKUs
        baseline_daily_cost = 50
        cost_ratio = cost_per_day / baseline_daily_cost
        cost_score = max(0.0, 1.0 - cost_ratio)
        
        # Stockout penalty: each stockout is severe
        stockout_penalty = max(0.0, 1.0 - (self.metrics["stockouts"] / 5))
        
        # Combined score: weighted multi-objective
        # Service is most critical (50%), cost is secondary (30%), no stockouts (20%)
        score = (
            (service_score * 0.50) +
            (cost_score * 0.30) +
            (stockout_penalty * 0.20)
        )
        
        score = min(1.0, max(0.0, score))
        
        return score
    
    def get_metrics(self) -> dict:
        """Return grading metrics."""
        return self.metrics.copy()


def test_grader():
    """Quick test of the grader."""
    grader = HardGrader()
    score = grader.grade()
    print(f"Hard Task Score: {score:.2f}")
    print(f"Metrics: {grader.get_metrics()}")


if __name__ == "__main__":
    test_grader()

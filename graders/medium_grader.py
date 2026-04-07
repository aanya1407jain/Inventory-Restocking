"""
Medium Task Grader: Predict demand and maintain service level
Grades: Can the agent forecast demand patterns and maintain >95% service?
"""

from inventory_env import InventoryEnv, InventoryAction


class MediumGrader:
    """
    Medium task grader: Predict demand and maintain service level.
    
    Metrics:
    - Service level (primary): % of demand satisfied (target: >95%)
    - Cost efficiency (secondary): Cost per unit served
    - Forecast accuracy: How close predicted vs actual demand
    
    Score formula:
    service_score = min(1.0, actual_service / 0.95)
    cost_score = max(0.0, 1.0 - cost_per_unit / baseline_cost)
    score = service_score * 0.7 + cost_score * 0.3
    """
    
    def __init__(self, task_name: str = "medium"):
        self.task_name = task_name
        self.metrics = {
            "total_demand": 0,
            "total_satisfied": 0,
            "total_cost": 0.0,
            "orders_placed": 0,
            "stockouts": 0,
            "service_level": 0.0,
            "steps_taken": 0,
        }
    
    def _forecast_demand(self, history: list) -> int:
        """Simple demand forecast using moving average."""
        if not history:
            return 10  # default
        return sum(history[-7:]) // len(history[-7:]) if history else 10
    
    def grade(self, seed: int = 42) -> float:
        """
        Run environment with forecasting heuristic.
        
        Returns:
            score (float): Grade from 0.0 to 1.0
        """
        env = InventoryEnv(task=self.task_name, seed=seed)
        state = env.reset()
        
        done = False
        step = 0
        
        # Strategy: Use moving average to forecast, order when forecast demand > current inventory
        while not done and step < 30:
            step += 1
            
            # Forecast demand for next week
            history = state.demand_history if state.demand_history else [10] * 7
            forecasted_demand = self._forecast_demand(history)
            
            # Find SKU with lowest inventory relative to forecast
            product_to_order = None
            min_coverage = float('inf')
            
            for sku, qty in state.products.items():
                mean_demand_map = {"SKU001": 12, "SKU002": 8, "SKU003": 18}
                expected_demand = mean_demand_map.get(sku, 10)
                
                # Days of inventory available
                coverage = qty / max(expected_demand, 1)
                
                if coverage < min_coverage:
                    min_coverage = coverage
                    product_to_order = sku
            
            # Reorder decision: if coverage < 5 days, order enough for 10 days
            should_reorder = False
            order_qty = 0
            
            if min_coverage < 5:
                mean_demand_map = {"SKU001": 12, "SKU002": 8, "SKU003": 18}
                expected_demand = mean_demand_map.get(product_to_order, 10)
                order_qty = expected_demand * 10  # Order for 10 days ahead
                order_qty = min(200, order_qty)  # Cap at max inventory
                should_reorder = True
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
        
        # Service level
        service_level = env.total_sold / max(env.total_demand, 1)
        self.metrics["service_level"] = round(service_level, 3)
        
        # Cost per unit served
        cost_per_unit = env.total_cost / max(env.total_sold, 1)
        
        # Scoring
        # Service level component: how close to 95% target?
        service_score = min(1.0, service_level / 0.95)
        
        # Cost efficiency: baseline is ~50/day
        baseline_daily_cost = 50
        daily_cost = env.total_cost / max(step, 1)
        cost_ratio = daily_cost / baseline_daily_cost
        cost_score = max(0.0, 1.0 - cost_ratio)
        
        # Combined score
        score = (service_score * 0.7) + (cost_score * 0.3)
        score = min(1.0, max(0.0, score))
        
        return score
    
    def get_metrics(self) -> dict:
        """Return grading metrics."""
        return self.metrics.copy()


def test_grader():
    """Quick test of the grader."""
    grader = MediumGrader()
    score = grader.grade()
    print(f"Medium Task Score: {score:.2f}")
    print(f"Metrics: {grader.get_metrics()}")


if __name__ == "__main__":
    test_grader()

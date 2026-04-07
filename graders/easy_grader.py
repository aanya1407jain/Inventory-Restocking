"""
Easy Task Grader: Recognize and respond to low stock levels
Grades: How well does the agent avoid stockouts through reactive ordering?
"""

from inventory_env import InventoryEnv, InventoryAction


class EasyGrader:
    """
    Easy task grader: Detect low stock and order before stockout.
    
    Metrics:
    - Stockout avoidance (primary): Minimize number of stockouts
    - Order efficiency (secondary): Reorder at reasonable times, not too late
    
    Score formula:
    score = (1 - stockout_ratio) * (1 - late_order_ratio)
    
    Where:
    - stockout_ratio = stockouts / max_days
    - late_order_ratio = orders_placed_too_late / total_orders
    """
    
    def __init__(self, task_name: str = "easy"):
        self.task_name = task_name
        self.metrics = {
            "stockouts": 0,
            "late_orders": 0,
            "total_orders": 0,
            "days_below_threshold": 0,
            "steps_taken": 0,
        }
    
    def grade(self, seed: int = 42) -> float:
        """
        Run environment and calculate grade.
        
        Returns:
            score (float): Grade from 0.0 to 1.0
        """
        env = InventoryEnv(task=self.task_name, seed=seed)
        state = env.reset()
        
        done = False
        step = 0
        
        # Baseline: simple reactive policy
        # Strategy: If any SKU drops below 40 units, order 100 units
        while not done and step < 30:
            step += 1
            
            # Simple heuristic: if inventory is low, order
            product_to_order = None
            order_qty = 0
            should_reorder = False
            
            # Find the product with lowest inventory
            min_stock = float('inf')
            for sku, qty in state.products.items():
                if qty < min_stock:
                    min_stock = qty
                    product_to_order = sku
            
            # If stock is below threshold (rough heuristic), order
            mean_demand_map = {"SKU001": 12, "SKU002": 8, "SKU003": 18}
            threshold = mean_demand_map.get(product_to_order, 10) * 3  # 3 days worth
            
            if min_stock < threshold:
                should_reorder = True
                order_qty = 100
                self.metrics["total_orders"] += 1
            
            if min_stock < threshold / 2:
                # Too late - we're at critical level
                self.metrics["late_orders"] += 1
            
            if min_stock < 0.5 * threshold:
                self.metrics["days_below_threshold"] += 1
            
            action = InventoryAction(
                product_id=product_to_order or "SKU001",
                quantity=order_qty,
                reorder=should_reorder
            )
            
            state, reward, done, info = env.step(action)
            
            if info.get("stockout"):
                self.metrics["stockouts"] += 1
            
            self.metrics["steps_taken"] = step
        
        # Calculate score
        max_days = 30
        stockout_ratio = self.metrics["stockouts"] / max_days
        
        # Penalty for ordering too late or inefficiently
        late_order_ratio = 0.0
        if self.metrics["total_orders"] > 0:
            late_order_ratio = self.metrics["late_orders"] / self.metrics["total_orders"]
        
        # Base score: 1.0 - stockout_ratio
        base_score = max(0.0, 1.0 - stockout_ratio)
        
        # Apply efficiency penalty
        efficiency_penalty = late_order_ratio * 0.2
        score = max(0.0, base_score - efficiency_penalty)
        
        return min(1.0, score)
    
    def get_metrics(self) -> dict:
        """Return grading metrics."""
        return self.metrics.copy()


def test_grader():
    """Quick test of the grader."""
    grader = EasyGrader()
    score = grader.grade()
    print(f"Easy Task Score: {score:.2f}")
    print(f"Metrics: {grader.get_metrics()}")


if __name__ == "__main__":
    test_grader()

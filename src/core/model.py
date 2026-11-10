from dataclasses import dataclass, field
from typing import Optional
from src.core.config import STATUS_OK
import numpy as np

@dataclass(eq=False)
class MKPProblem:
    name: str 
    n: int  # so mat hang
    m: int  # so rang buoc
    profits: np.ndarray      # Loi nhuan 
    weights: np.ndarray      # Ma tran MxN
    capacities: np.ndarray   # Gioi hang 
    z_ref: Optional[float] = None # Gia tri tham chieu
    
    def __post_init__(self):
        self.profits = np.asarray(self.profits)
        self.weights = np.asarray(self.weights)
        self.capacities = np.asarray(self.capacities)

        if (self.profits.shape != (self.n,)):
            raise ValueError("profits phai co n phan tu")
        if (self.weights.shape != (self.m, self.n)):
            raise ValueError("weights phai la ma tran m x n")
        if (self.capacities.shape != (self.m,)):
            raise ValueError("capacities phai co m phan tu")

@dataclass
class MKPResult:
    """Ket qua cua mot lan chay thuat toan"""
    selected_items: list            
    total_profit: float           
    resource_usage: list          
    feasible: bool                 
    runtime: float = 0.0           
    optimality_gap: Optional[float] = None   
    history: list = field(default_factory=list)   
    status: str = STATUS_OK        
    peak_memory: float = 0.0    
    
    def to_dict(self) -> dict:
        return {
            "selected_items": self.selected_items,
            "total_profit": self.total_profit,
            "resource_usage": self.resource_usage,
            "feasible": self.feasible,
            "runtime": self.runtime,
            "optimality_gap": self.optimality_gap,
            "history": self.history,
            "status": self.status,
        }      
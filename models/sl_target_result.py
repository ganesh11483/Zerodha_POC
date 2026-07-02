from dataclasses import dataclass

@dataclass
class SLTargetResult:
    stop_loss: float = 0.0
    target: float = 0.0


def clamp(x, min_value: float=0, max_value: float=0) -> float:
    return max(min(x, max_value), min_value)

    
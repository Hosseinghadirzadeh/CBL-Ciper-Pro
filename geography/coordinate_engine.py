def format_coordinate(value: float) -> str:
    if not -180.0 <= value <= 180.0:
        raise ValueError("Coordinate is outside the valid range")
    return f"{value:.6f}"


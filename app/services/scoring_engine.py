def calculate_score(base_score: int = 0, hints_used: int = 0, commands_executed: int = 0, attempts: int = 1):
    penalty = hints_used * 5 + max(0, attempts - 1) * 2
    score = max(0, base_score + commands_executed * 10 - penalty)
    return score

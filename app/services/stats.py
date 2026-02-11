stats = {"requests": 0}

def increment_requests():
    stats["requests"] += 1

def get_stats():
    return stats

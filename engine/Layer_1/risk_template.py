STATUS_RANK = {
    "SAFE": 0,
    "WARNING": 1,
    "CRITICAL": 2,
}


def worst_status(statuses: list[str]) -> str:
    if not statuses:
        return "SAFE"

    normalized = [status.upper() for status in statuses]
    return max(normalized, key=lambda status: STATUS_RANK.get(status, -1))

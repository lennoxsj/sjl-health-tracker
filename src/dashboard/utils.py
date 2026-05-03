def pace_to_seconds(pace_str):
    """Convert 'M:SS' pace string to total seconds."""
    m, s = pace_str.split(":")
    return int(m) * 60 + int(s)


def two_way_pct(current, baseline, target, higher_is_better=True):
    """
    Progress from baseline toward target as 0.0–1.0.
    Exceeding target clamps to 1.0; moving away from target gives 0.0.
    Accepts numeric values or 'M:SS' pace strings.
    """
    if isinstance(current, str):
        current  = pace_to_seconds(current)
        baseline = pace_to_seconds(baseline)
        target   = pace_to_seconds(target)
        higher_is_better = False  # faster pace = lower seconds

    if higher_is_better:
        span = target - baseline
        pct = (current - baseline) / span if span != 0 else 1.0
    else:
        span = baseline - target
        pct = (baseline - current) / span if span != 0 else 1.0

    return max(0.0, min(1.0, pct))

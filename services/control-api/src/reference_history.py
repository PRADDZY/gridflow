MAX_REFERENCE_OBSERVATION_HISTORY = 60


def record_reference_history(history: list[dict], observation: dict) -> list[dict]:
    return [observation, *history][:MAX_REFERENCE_OBSERVATION_HISTORY]

def values_match(predicted, expected, tolerance=1e-6):
    # Compare floats with tolerance because normalized numeric values may pass
    # through parsing and serialization steps.
    if isinstance(expected, float):
        return isinstance(predicted, (int, float)) and abs(predicted - expected) <= tolerance
    return predicted == expected


def accuracy(pred, truth):
    # Accuracy measures how many target fields were predicted exactly as expected.
    correct = 0
    total = 0

    for key, expected in truth.items():
        total += 1
        if key in pred and values_match(pred[key], expected):
            correct += 1

    return correct / total if total else 0.0


def completeness(pred, truth):
    # Completeness checks whether expected fields are present, even when the correct
    # value is explicitly null in the ground truth.
    filled = 0
    total = len(truth)

    for key, expected in truth.items():
        # Treat explicit nulls as complete when the target schema expects no value.
        if key in pred and (pred[key] is not None or expected is None):
            filled += 1

    return filled / total if total else 0.0


def exact_match(pred, truth):
    # Exact match is intentionally strict: every ground-truth field must match.
    return 1.0 if all(key in pred and values_match(pred[key], value) for key, value in truth.items()) else 0.0

def merge_missingness(total_rows, placeholder_out, validity_out):
    actual_nan = placeholder_out["missing_component"]["actual_nan"]
    placeholder = placeholder_out["missing_component"]["placeholder"]
    invalid = validity_out["invalid_component"]

    total_missing = actual_nan + placeholder + invalid
    missing_ratio = round(total_missing / total_rows, 4)

    status = "valid"
    if missing_ratio > 0.8:
        status = "broken"
    elif missing_ratio > 0:
        status = "weak"

    return {
        "missingness": {
            "status": status,
            "value": missing_ratio,
            "components": {
                "actual_nan": round(actual_nan / total_rows, 4),
                "placeholder": round(placeholder / total_rows, 4),
                "invalid": round(invalid / total_rows, 4)
            },
            "violations": (
                placeholder_out["violations"] +
                validity_out["violations"]
            )
        }
    }

if __name__ == "__main__":
    merge_missingness()
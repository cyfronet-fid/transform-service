from typing import Any, Dict


def infer_schema(data: Any) -> Any:
    if isinstance(data, dict):
        return {key: infer_schema(value) for key, value in data.items()}

    elif isinstance(data, list):
        if not data:
            return "List[Unknown]"
        return [infer_schema(data[0])]

    else:
        return type(data).__name__


def print_schema(data: Dict[str, Any]) -> None:
    import json

    schema = infer_schema(data)
    print("\n=== Inferred Schema ===")
    print(json.dumps(schema, indent=2))

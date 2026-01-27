import json


def load_ndjson(path):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def chunk_iterable(iterable, size):
    for i in range(0, len(iterable), size):
        yield iterable[i : i + size]

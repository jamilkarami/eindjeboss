import json


def load_json_file(path):
    with open(path, "rb") as f:
        try:
            return json.loads(f.read())
        except:
            return dict()


def save_json_file(data, path):
    f = open(path, "w")
    output = json.dumps(data, indent=4)
    print(output, file=f)


def get_file(path):
    return f"files/{path}"


def check_limit(command: str):
    limits = load_json_file(get_file("limits.json"))
    current = limits[command]["current"]
    max = limits[command]["max"]
    if current < max:
        limits[command]["current"] = current + 1
        save_json_file(limits, "limits.json")
        return True
    return False

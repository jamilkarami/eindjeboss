
import json

def load_json_file(path):
    with open(path, "rb") as f:
        try:
            return json.loads(f.read())
        except:
            return dict()

def save_json_file(data, path):
    f = open(path, 'w')
    output = json.dumps(data, indent=4)
    print(output, file=f)

def get_file(path):
    return f"files/{path}"
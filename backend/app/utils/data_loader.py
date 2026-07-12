import json
import os

# data_loader.py is at backend/app/utils/data_loader.py
# data/ is at backend/data/
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(_THIS_DIR))  # go from utils/ -> app/ -> backend/
DATA_DIR = os.path.join(BASE_DIR, 'data')

_cache = {}

def load_json(filename):
    if filename in _cache:
        return _cache[filename]
    path = os.path.join(DATA_DIR, filename)
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    _cache[filename] = data
    return data

def load_dev_library():
    return load_json('dev_std_library.json')

def load_ops_library():
    return load_json('ops_std_library.json')

def load_csbmk():
    return load_json('csbmk_data.json')

def load_city_price():
    return load_json('city_price.json')

def load_industry_template(template_key):
    path = os.path.join(DATA_DIR, 'industry_templates', f'{template_key}.json')
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_all_templates():
    templates_dir = os.path.join(DATA_DIR, 'industry_templates')
    templates = {}
    for fname in os.listdir(templates_dir):
        if fname.endswith('.json'):
            key = fname.replace('.json', '')
            with open(os.path.join(templates_dir, fname), 'r', encoding='utf-8') as f:
                templates[key] = json.load(f)
    return templates

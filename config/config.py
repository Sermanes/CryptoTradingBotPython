import json

CONFIG_FILE = "config.json"

def get_json_data():
    f = open(CONFIG_FILE)
    data = json.load(f)
    f.close()

    return data

def get_coin():
    return get_json_data()['coin']


def getList(dict):
    return dict.keys()

def get_symbols():
    data = get_json_data()['symbols']
    symbols = []

    for x in data:
        symbols.append(list(x.keys())[0])
        
    return symbols

def get_decimals():
    data = get_json_data()['symbols']
    decimals = []

    for x in data:
        decimals.append(list(x.values())[0])
        
    return decimals

def get_leverage():
    return get_json_data()['leverage']


def get_data_file():
    return get_json_data()['data_file']


def get_exception_file():
    return get_json_data()['exception_file']
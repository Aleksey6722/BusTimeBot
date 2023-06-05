import json
import requests


def get_stops():
    a_dict = {'Point1': {'Latitude': 49.935127, 'Longitude': 82.666678}, 'Point2': {'Latitude': 49.89085, 'Longitude': 82.718598}}
    resp = requests.post('https://oskemenbus.kz/api/GetStops', json=a_dict)
    t = resp.text
    l = ''
    c = 0
    for i in resp.text.split('\n')[:-1]:
        result = json.loads(i)
        name = result.get('result').get('StopName')
        id = result.get('result').get('StopId')
        l += id + ', ' + name + '\n'
        c += 1
    return l

st = get_stops()
print(st)
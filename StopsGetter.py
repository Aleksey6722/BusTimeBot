import json
import requests


def get_stops():
    a_dict = {'Point1': {'Latitude': 50.007318, 'Longitude': 82.55763}, 'Point2': {'Latitude': 49.947647, 'Longitude':  82.643141}}
    resp = requests.post('https://oskemenbus.kz/api/GetStops', json=a_dict)
    l = []
    for i in resp.text.split('\n')[:-1]:
        result = json.loads(i)
        name = result.get('result').get('StopName')
        id = result.get('result').get('StopId')
        resp1 = requests.post('https://oskemenbus.kz/api/GetScoreboard', json={"StopId": id})
        st = resp1.text.split('\n')[0]
        obj = json.loads(st)
        stop_type = obj.get('result').get('Type')
        if stop_type == 2:
            l.append((name, id, stop_type))
    return l

st = get_stops()
print(st)
import json
import requests


def get_stops():
    a_dict = {'Point1': {'Latitude': 50.007577, 'Longitude': 82.557241}, 'Point2': {'Latitude': 49.944862, 'Longitude':  82.650906}}
    resp = requests.post('https://oskemenbus.kz/api/GetStops', json=a_dict)

    l = []
    а = resp.text.split('\n')[:-1]
    for i in resp.text.split('\n')[:-1]:
        result = json.loads(i)
        name = result.get('result').get('StopName')
        id = result.get('result').get('StopId')
        resp1 = requests.post('https://oskemenbus.kz/api/GetScoreboard', json={"StopId": id})
        st = resp1.text.split('\n')[0]
        if not st:
            continue
        obj = json.loads(st)
        stop_type = obj.get('result').get('Type')
        if stop_type == 2:
            l.append((name, id, stop_type))
        l.sort(key=lambda x: x[0])
    return l

st = get_stops()
print(st)
print(len(st))
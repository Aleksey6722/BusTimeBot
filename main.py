import telebot
from telebot import types
import requests
import json

from models import session, Region, TramStop

bot = telebot.TeleBot('5865105516:AAGLxWHqTXwH2rBABDNx3xqw969LW_boFqA')
message_choose_transport = 'Выберите транспорт'
message_choose_busstop = 'Выберите автобусную остановку'
message_choose_tramstop = 'Выберите трамвайную остановку'
message_choose_region = 'Выберите район'


def sum_duplicates(sorted_list):
    a_list = []
    i = 0
    for item in sorted_list:
        if len(a_list) > 0 and item[0] == a_list[i - 1][0]:
            a_list[i - 1][1] = a_list[i - 1][1] + ',' + item[1]
            continue
        a_list.append(item)
        i += 1
    return list(map(lambda x: ','.join(x), a_list))


def sort_function(elem):
    if elem[0].isdigit():
        return int(elem[0])
    return int(elem[0][:-1])


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Автобусы', callback_data='bus_region')
    btn2 = types.InlineKeyboardButton('Трамваи', callback_data='trams')
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, message_choose_transport, reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.data == 'bus_region')
def bus(callback):
    data = session.query(Region).all()
    markup = types.InlineKeyboardMarkup()
    for elem in data:
        i = elem.name
        markup.add(types.InlineKeyboardButton(elem.name, callback_data=elem.name))
    bot.send_message(callback.message.chat.id, message_choose_region, reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.data == 'trams')
def tram(callback):
    data = session.query(TramStop).all()
    a_list = []
    for elem in data:
        a_list.append([elem.name.strip(), str(elem.id)])
    stop_list = sum_duplicates(a_list)
    markup = types.InlineKeyboardMarkup()
    for item in stop_list:
        name = item.split(',')[0]
        markup.add(types.InlineKeyboardButton(name, callback_data=item))
    bot.send_message(callback.message.chat.id, message_choose_tramstop, reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.message.text == message_choose_region)
def get_busstops(callback):
    data = session.query(Region).filter(Region.name == callback.data).first()
    tram_stops_id = [x[0] for x in session.query(TramStop.id).all()]
    data_to_send = {
        'Point1': {'Latitude': data.latitude1, 'Longitude': data.longitude1},
        'Point2': {'Latitude': data.latitude2, 'Longitude': data.longitude2}
    }
    resp = requests.post('https://oskemenbus.kz/api/GetStops', json=data_to_send)
    a_list = []
    for row in resp.text.split('\n')[:-1]:
        obj = json.loads(row)
        name = obj.get('result').get('StopName')
        stop_id = obj.get('result').get('StopId')
        if stop_id not in tram_stops_id:
            a_list.append([name.strip(), stop_id])

    a_list.sort(key=lambda x: x[0])
    stops_list = sum_duplicates(a_list)
    markup = types.InlineKeyboardMarkup()
    i = 0
    for item in stops_list:
        name = item.split(',')[0]
        ids = item.split(',')[1:]
        print(item)
        print(type(item))
        markup.add(types.InlineKeyboardButton(name, callback_data=','.join(ids)))
    bot.send_message(callback.message.chat.id, message_choose_busstop, reply_markup=markup)


def func(x, callback=None):
    var = x[0].callback_data == callback.data
    return var


@bot.callback_query_handler(func=lambda callback: callback.message.text ==
                            message_choose_busstop or message_choose_tramstop or 'Обновить')
def get_buses(callback):
    for i in callback.message.reply_markup.keyboard:
        if i[0].callback_data == callback.data:
            name = i[0].text
            break
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Автобусы', callback_data='bus_region')
    btn2 = types.InlineKeyboardButton('Трамваи', callback_data='trams')
    markup.add(types.InlineKeyboardButton('Обновить', callback_data=callback.data))
    markup.add(btn1, btn2)
    id = callback.data.split(',')
    a_list = []
    for elem in id:
        resp = requests.post('https://oskemenbus.kz/api/GetScoreboard', json={"StopId": elem})
        for row in resp.text.split('\n')[:-1]:
            obj = json.loads(row)
            number = obj.get('result').get('Number')
            destination = obj.get('result').get('EndStop')
            time_from_server = obj.get('result').get('InfoM')[0]
            time = time_from_server if time_from_server > 0 else '<1'
            a_list.append((number, destination, str(time)+'мин'))

    if len(a_list) == 0:
        bot.send_message(callback.message.chat.id, 'Нет ни одного автобуса/трамвая', reply_markup=markup)
        return

    a_list.sort(key=sort_function)
    result = f'Остановка: {name}\n\nНомер (направление) время \n\n'
    for elem in a_list:
        result += f' {elem[0]}   ({elem[1]})   {elem[2]}\n'
    bot.send_message(callback.message.chat.id, result, reply_markup=markup)


bot.infinity_polling()

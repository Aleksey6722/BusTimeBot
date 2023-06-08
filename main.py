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
    return a_list


def sort_function(elem):
    if elem[0].isdigit():
        return int(elem[0])
    return int(elem[0][:-1])


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Автобусы', callback_data='region')
    btn2 = types.InlineKeyboardButton('Трамваи', callback_data='trams')
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, message_choose_transport, reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.data == 'region')
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
    for i in stop_list:
        markup.add(types.InlineKeyboardButton(i[0], callback_data=i[1]))
    bot.send_message(callback.message.chat.id, message_choose_tramstop, reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.message.text == message_choose_region)
def get_busstops(callback):
    data = session.query(Region).filter(Region.name == callback.data).first()
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
        a_list.append([name.strip(), stop_id])

    a_list.sort(key=lambda x: x[0])
    stops_list = sum_duplicates(a_list)
    markup = types.InlineKeyboardMarkup()
    for item in stops_list:
        markup.add(types.InlineKeyboardButton(item[0], callback_data=','.join(item)))
    bot.send_message(callback.message.chat.id, message_choose_busstop, reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.message.text ==
                            message_choose_busstop or message_choose_tramstop or 'Обновить')
def get_buses(callback):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Автобусы', callback_data='region')
    btn2 = types.InlineKeyboardButton('Трамваи', callback_data='trams')
    markup.add(types.InlineKeyboardButton('Обновить', callback_data=callback.data))
    markup.add(btn1, btn2)
    name = callback.data.split(',')[0]
    id = callback.data.split(',')[1:]
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
    result = f'Остановка: {name}\n\nНомер (направление) время \n\n'  # Сделать отображение названия остановки из будущей БД
    for elem in a_list:
        result += f' {elem[0]}   ({elem[1]})   {elem[2]}\n'
    bot.send_message(callback.message.chat.id, result, reply_markup=markup)


bot.infinity_polling()

import telebot
from telebot import types
import requests
import json

from models import session, Region

bot = telebot.TeleBot('5865105516:AAGLxWHqTXwH2rBABDNx3xqw969LW_boFqA')
message_choose_transport = 'Выберите транспорт'
message_choose_busstop = 'Выберите автобусную остановку'
message_choose_tramstop = 'Выберите трамвайную остановку'
message_choose_region = 'Выберите район'

regions = [
    {'Point1': {'Latitude': 49.935127, 'Longitude': 82.666678}, 'Point2': {'Latitude': 49.89085, 'Longitude': 82.718598}},
    {'Point1': {'Latitude': 49.950912, 'Longitude': 82.643208}, 'Point2': {'Latitude': 49.941789, 'Longitude':  82.657945}},
    {'Point1': {'Latitude': 49.951872, 'Longitude': 82.659318}, 'Point2': {'Latitude': 49.941294, 'Longitude':  82.675867}},
    {'Point1': {'Latitude': 49.962677, 'Longitude': 82.62226}, 'Point2': {'Latitude': 49.947134, 'Longitude':  82.64557}},
]


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Автобусы', callback_data='region')
    btn2 = types.InlineKeyboardButton('Трамваи', callback_data='trams')
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, message_choose_transport, reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.data == 'region')
def bus(callback):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Аблакетка', callback_data='ablaketka'))
    markup.add(types.InlineKeyboardButton('Пристань', callback_data='pristan'))
    markup.add(types.InlineKeyboardButton('Посёлок Красина', callback_data='krasina'))
    markup.add(types.InlineKeyboardButton('Центральный рынок', callback_data='rynok_centr'))

    bot.send_message(callback.message.chat.id, message_choose_region, reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.data == 'trams')
def tram(callback):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Библиотека Пушкина', callback_data='142337,141313'))
    markup.add(types.InlineKeyboardButton('Рынок', callback_data='143361,144385'))
    markup.add(types.InlineKeyboardButton('Дворец спорта', callback_data='543745,544769'))
    markup.add(types.InlineKeyboardButton('Дом связи (Больничный комплекс)', callback_data='156673,590849'))
    markup.add(types.InlineKeyboardButton('Смирнова', callback_data='562177pip,561153'))
    bot.send_message(callback.message.chat.id, message_choose_tramstop, reply_markup=markup)


def sum_duplicates(sorted_list):
    a_list = []
    i = 0
    for item in sorted_list:
        if len(a_list) > 0 and item[1] == a_list[i - 1][1]:
            a_list[i - 1][0] = a_list[i - 1][0] + ',' + item[0]
            continue
        a_list.append(item)
        i += 1
    return a_list


def sort_function(elem):
    if elem[0].isdigit():
        return int(elem[0])
    return int(elem[0][:-1])


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
        a_list.append([stop_id, name.strip()])

    a_list.sort(key=lambda x: x[1])
    stops_list = sum_duplicates(a_list)
    markup = types.InlineKeyboardMarkup()
    for item in stops_list:
        markup.add(types.InlineKeyboardButton(item[1], callback_data=item[0]))
    bot.send_message(callback.message.chat.id, message_choose_busstop, reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.message.text ==
                            message_choose_busstop or message_choose_tramstop or 'Обновить')
def get_buses(callback):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Автобусы', callback_data='region')
    btn2 = types.InlineKeyboardButton('Трамваи', callback_data='trams')
    markup.add(types.InlineKeyboardButton('Обновить', callback_data=callback.data))
    markup.add(btn1, btn2)

    a_list = []
    for id in callback.data.split(','):
        resp = requests.post('https://oskemenbus.kz/api/GetScoreboard', json={"StopId": id})
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
    result = 'номер (направление) время \n\n' # Сделать отображение названия остановки из будущей БД
    for elem in a_list:
        result += f'  {elem[0]}   ({elem[1]})   {elem[2]}\n'
    bot.send_message(callback.message.chat.id, result, reply_markup=markup)


bot.infinity_polling()

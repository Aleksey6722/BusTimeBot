import telebot
from telebot import types
import requests
from sqlalchemy import or_

import json
import os
import time
from datetime import datetime
from threading import Thread
import uuid
import re

from models import session, Region, TramStop, Button, Notice

TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)
message_choose_transport = 'Выберите транспорт'
message_choose_busstop = 'Выберите автобусную остановку'
message_choose_tramstop = 'Выберите трамвайную остановку'
message_choose_region = 'Выберите район'
message_choose_day_of_week = 'Выберите день недели'
message_choose_number_of_vehicle = 'Выберите номер транспорта'
message_set_time = 'Введите время уведомления в 24-х часовом формате ЧЧ:ММ'
DAYS = {'Monday': 'Понедельник', 'Tuesday': 'Вторник', 'Wednesday': 'Среда', 'Thursday': 'Четверг',
            'Friday': 'Пятница', 'Saturday': 'Суббота', 'Sunday': 'Воскресенье', 'Everyday': 'Каждый день'}


def sum_duplicates(sorted_list):
    a_list = []
    i = 0
    for item in sorted_list:
        if len(a_list) > 0 and item[0] == a_list[i - 1][0]:
            a_list[i - 1][1] = a_list[i - 1][1] + '-' + item[1]
            continue
        a_list.append(item)
        i += 1
    return list(map(lambda x: ','.join(x), a_list))


def sort_function(elem):
    if elem[0].isdigit():
        return int(elem[0])
    return int(elem[0][:-1])


def get_scoreboard(data):
    ids = data.split('-')
    a_list = []
    for elem in ids:
        resp = requests.post('https://oskemenbus.kz/api/GetScoreboard', json={"StopId": elem})
        for row in resp.text.split('\n')[:-1]:
            obj = json.loads(row)
            number = obj.get('result').get('Number')
            destination = obj.get('result').get('EndStop')
            time_from_server = obj.get('result').get('InfoM')[0]
            time = time_from_server if time_from_server > 0 else '<1'
            a_list.append((number, destination, str(time) + 'мин'))
    return a_list


def generate_callback(**kwargs):
    fixed_time = time.time()-60*60*24
    session.query(Button).filter(Button.date < datetime.fromtimestamp(fixed_time)).delete()
    key = str(uuid.uuid4())
    new_button = Button(key=key, **kwargs)
    try:
        session.add(new_button)
        session.commit()
        return key
    except Exception as e:
        print('Ошибка создания кнопки, неверные данные')
        print(e)


def get_callback_by_id(key):
    data = session.query(Button).filter(Button.key == key).first()
    return data


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Автобусы', callback_data='bus_region')
    btn2 = types.InlineKeyboardButton('Трамваи', callback_data='trams')
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, message_choose_transport, reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.data == 'bus_region')
def bus_regions(callback):
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
    for item in stops_list:
        name = item.split(',')[0]
        stop_id = item.split(',')[1]
        markup.add(types.InlineKeyboardButton(name, callback_data=generate_callback(name=name, stop_id=stop_id)))
    bot.send_message(callback.message.chat.id, message_choose_busstop, reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.data.split(',')[0] == 'notice')
def choose_vehicle(callback):
    markup = types.InlineKeyboardMarkup(row_width=5)
    list_of_buttons = []
    key = callback.data.split(',')[-1]
    current_stop = get_callback_by_id(key)
    routs = set()
    for id in current_stop.stop_id.split('-'):
        resp = requests.post('https://oskemenbus.kz/api/GetStopRouts', json={"StopId": id})
        for row in resp.text.split('\n')[:-1]:
            row = json.loads(row)
            number = row.get('result').get('Number')
            routs.add(number)
            if (len(list_of_buttons) == 0) or (number not in [x.text for x in list_of_buttons]):
                key = generate_callback(name=current_stop.name,
                                        stop_id=current_stop.stop_id,
                                        bus_number=number)
                list_of_buttons.append(types.InlineKeyboardButton(number, callback_data=key))
    markup.add(*list_of_buttons)
    bot.send_message(callback.message.chat.id, message_choose_number_of_vehicle, reply_markup=markup)
    print(markup.keyboard)


@bot.callback_query_handler(func=lambda callback: callback.message.text == message_choose_number_of_vehicle)
def choose_day(callback):
    markup = types.InlineKeyboardMarkup()
    current_data = get_callback_by_id(callback.data)
    for day, name in DAYS.items():
        key = generate_callback(name=current_data.name,
                                stop_id=current_data.stop_id,
                                bus_number=current_data.bus_number,
                                day=day)
        markup.add(types.InlineKeyboardButton(f"{name}", callback_data=key))
    bot.send_message(callback.message.chat.id, message_choose_day_of_week, reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.message.text == message_choose_day_of_week)
def choose_time(callback):
    # data = get_callback_by_id(callback.data)
    bot.send_message(callback.message.chat.id, message_set_time,)
    bot.register_next_step_handler(callback.message, callback=set_time, call=callback)


re_time = re.compile(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$')


def set_time(message, call):
    data = get_callback_by_id(call.data)
    if re.fullmatch(re_time, message.text):
        notice_time = datetime.strptime(message.text, '%H:%M').time()
        params = {
            'username': message.chat.first_name,
            'chat_id': message.chat.id,
            'stop_id': data.stop_id,
            'stop_name': data.name,
            'bus_number': data.bus_number,
            'day': data.day,
            'notice_time': notice_time
        }
        check = session.query(Notice).filter_by(**params).first()
        if check:
            bot.send_message(message.chat.id, 'Такое уведомление уже существует! Для управления уведомлениями '
                                              'введите команду /my_notice')
            return
        notice = Notice(**params)
        session.add(notice)
        session.commit()
        bot.send_message(message.chat.id, 'Уведомление создано! Для управления уведомлениями '
                                       'введите команду /my_notice')
        return
    bot.send_message(message.chat.id, 'Некорректное время')
    choose_time(call)


@bot.callback_query_handler(func=lambda callback: callback.message.text ==
                                                  (message_choose_busstop or message_choose_tramstop) or
                                                  callback.message.reply_markup.keyboard[1][0].text == 'Обновить')
def get_vehicle(callback):
    current_busstop = get_callback_by_id(callback.data)
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Автобусы', callback_data='bus_region')
    btn2 = types.InlineKeyboardButton('Трамваи', callback_data='trams')
    markup.add(types.InlineKeyboardButton('Установить уведомление', callback_data='notice,'+callback.data))
    markup.add(types.InlineKeyboardButton('Обновить', callback_data=callback.data))
    markup.add(btn1, btn2)
    list_of_buses = get_scoreboard(current_busstop.stop_id)
    if len(list_of_buses) == 0:
        bot.send_message(callback.message.chat.id, f'На остановке {current_busstop.name} '
                                                   f'нет ни одного автобуса/трамвая', reply_markup=markup)
        return

    list_of_buses.sort(key=sort_function)
    result = f'Остановка: {current_busstop.name}\n\nНомер (направление) время \n\n'
    for elem in list_of_buses:
        result += f' {elem[0]}   ({elem[1]})   {elem[2]}\n'
    bot.send_message(callback.message.chat.id, result, reply_markup=markup)


def check_notify():
    while True:
        today = datetime.today().strftime('%A')
        nowtime = datetime.today().strftime('%H:%M')
        # g = datetime.strptime('6:00', '%H:%M').time()
        notices = session.query(Notice).filter(or_(Notice.day == 'Everyday',
                                                  Notice.day == today)).filter(Notice.notice_time == nowtime).all()
        if notices:
            for a_notice in notices:
                bus_info = get_scoreboard(a_notice.stop_id)
                a_list = [x for x in bus_info if x[0] == a_notice.bus_number]
                if not a_list:
                    bot.send_message(notice.chat_id, f'Уведомление!\n\nОстановка: {a_notice.stop_name}\n\n'
                                                     f'Автобус {a_notice.bus_number} в данный момент не на маршруте')
                message_text = ''
                for bus in a_list:
                    message_text += f' {bus[0]}   ({bus[1]})   {bus[2]}\n'
                bot.send_message(a_notice.chat_id, f'Уведомление!\n\nОстановка: {a_notice.stop_name}\n\n'
                                                 f'Номер (направление) время \n\n'+message_text)
        time.sleep(60)
        print(datetime.today().strftime('%A'))
        print(datetime.today().strftime('%H:%M'))

notifier = Thread(target=check_notify)
notifier.start()

bot.infinity_polling()


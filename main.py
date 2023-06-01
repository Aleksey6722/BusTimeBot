import telebot
from telebot import types
import requests
import json

bot = telebot.TeleBot('5865105516:AAGLxWHqTXwH2rBABDNx3xqw969LW_boFqA')


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Автобусы', callback_data='buses')
    btn2 = types.InlineKeyboardButton('Трамваи', callback_data='trams')
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, 'Выберите транспорт', reply_markup=markup)

#
# @bot.callback_query_handler(func=lambda callback: callback.data == 'Выберите транспорт')
# def transport_handler(callback):
#     print(callback.data)
#     markup = types.InlineKeyboardMarkup()
#     btn1 = types.InlineKeyboardButton('Остановка Мир', callback_data='16385')
#     btn2 = types.InlineKeyboardButton('Остановка Казахстан', callback_data='kazakhstan')
#     markup.add(btn1, btn2)
#     bot.send_message(callback.message.chat.id, 'Выберите остановку', reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.data == 'buses')
def bus(callback):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Мир', callback_data='16385,51201'))
    markup.add(types.InlineKeyboardButton('Казахстан', callback_data='44033,23553,667649'))

    bot.send_message(callback.message.chat.id, 'Выберите автобусную остановку', reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.data == 'trams')
def tram(callback):
    bot.send_message(callback.message.chat.id, 'Выберите трамвайную остановку')
    # btn1 = types.InlineKeyboardButton('Остановка Мир', callback_data='16385')
    # btn2 = types.InlineKeyboardButton('Остановка Казахстан', callback_data='kazakhstan')
    # markup.add(btn1, btn2)
    # bot.send_message(callback.message.chat.id, 'Выберите остановку', reply_markup=markup)

@bot.callback_query_handler(func=lambda callback: True)
def get_buses(callback):
    a_list = []
    for id in callback.data.split(','):
        resp = requests.post('https://oskemenbus.kz/api/GetScoreboard', json={"StopId": id})
        for row in resp.text.split('\n')[:-1]:
            obj = json.loads(row)
            number = obj.get('result').get('Number')
            destination = obj.get('result').get('EndStop')
            time = obj.get('result').get('InfoM')[0]
            a_list.append((number, destination, str(time)+' мин'))

    print(a_list)
    bot.send_message(callback.message.chat.id, str(a_list))


bot.polling(none_stop=True)

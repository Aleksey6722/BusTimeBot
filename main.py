import telebot
from telebot import types
import requests
import json

bot = telebot.TeleBot('5865105516:AAGLxWHqTXwH2rBABDNx3xqw969LW_boFqA')
message_choose_transport = 'Выберите транспорт'
message_choose_busstop = 'Выберите автобусную остановку'
message_choose_tramstop = 'Выберите трамвайную остановку'


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Автобусы', callback_data='buses')
    btn2 = types.InlineKeyboardButton('Трамваи', callback_data='trams')
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, message_choose_tramstop, reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.data == 'buses')
def bus(callback):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Мир', callback_data='16385,51201'))
    markup.add(types.InlineKeyboardButton('Казахстан', callback_data='44033,23553,667649'))
    markup.add(types.InlineKeyboardButton('Дворец спорта', callback_data='20481,47105'))
    markup.add(types.InlineKeyboardButton('Автовокзал', callback_data='152577,151553'))
    markup.add(types.InlineKeyboardButton('Конденсаторный завод', callback_data='334849,336897'))
    markup.add(types.InlineKeyboardButton('Т/ц Евразия', callback_data='62465,'))
    markup.add(types.InlineKeyboardButton('Рынок', callback_data='17409,50177'))
    bot.send_message(callback.message.chat.id, message_choose_busstop, reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.data == 'trams')
def tram(callback):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Библиотека Пушкина', callback_data='142337,141313'))
    markup.add(types.InlineKeyboardButton('Рынок', callback_data='143361,144385'))
    markup.add(types.InlineKeyboardButton('Дворец спорта', callback_data='543745,544769'))
    markup.add(types.InlineKeyboardButton('Дом связи (Больничный комплекс)', callback_data='156673,590849'))
    markup.add(types.InlineKeyboardButton('Смирнова', callback_data='562177pip,561153'))
    bot.send_message(callback.message.chat.id, message_choose_tramstop, reply_markup=markup)


def sort_function(elem):
    if elem[0].isdigit():
        return int(elem[0])
    return int(elem[0][:-1])


@bot.callback_query_handler(func=lambda callback: callback.message.text ==
                            message_choose_busstop or message_choose_tramstop or 'Обновить')
def get_buses(callback):
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

    a_list.sort(key=sort_function)
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Автобусы', callback_data='buses')
    btn2 = types.InlineKeyboardButton('Трамваи', callback_data='trams')
    markup.add(types.InlineKeyboardButton('Обновить', callback_data=callback.data))
    t = callback.data
    markup.add(btn1, btn2)
    result = 'номер (направление) время \n\n' # Сделать отображение названия остановки из будущей БД
    for elem in a_list:
        result += f'  {elem[0]}   ({elem[1]})   {elem[2]}\n'
    bot.send_message(callback.message.chat.id, result, reply_markup=markup)


bot.polling(none_stop=True)

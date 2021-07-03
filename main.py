from pyowm import OWM
from telegram.ext import Updater, MessageHandler, Filters, ConversationHandler
from telegram.ext import CallbackContext, CommandHandler
from pyowm.utils.config import get_default_config
from pyowm.utils import timestamps
from lists import if_cloudly, if_sunny_and_hot, if_sunny, if_rainy, if_snowy, if_fogy, if_not, if_no, if_yes, if_wrong
import random
from questions import for_ask
from telegram import ReplyKeyboardMarkup


ask = for_ask.copy()
right_answers = 0
quest = ''
already_asked = []

city = 'Москва'
TOKEN = '1757315846:AAGClNPT4jjxzEREPGzdAjP_Vb7x3kuUhCM'

reply_keyboard = [['/change_city', '/start_play'],
                  ['/daily', '/now', '/h3', '/start'],
                  ['/will_have_snow', '/will_have_fog', '/will_have_rain']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

play_keyboard = [['а', 'б', 'с'],
                 ['продолжить', '/stop_play']]
markup2 = ReplyKeyboardMarkup(play_keyboard, one_time_keyboard=False)

yes_or_no = [['да'], ['нет']]
markup3 = ReplyKeyboardMarkup(yes_or_no, one_time_keyboard=True)


def change_city(update, context):
    global city
    try:
        city = update.message.text.split()[1]
        update.message.reply_text(f'Город по умолчанию: {city}')
    except IndexError:
        update.message.reply_text(f'Введите в формате /change_city "город" или /start для возврата.')


def stickers(w):
    if 'облачно' in w.detailed_status or 'пасмурно' in w.detailed_status:
        return random.choice(if_cloudly)
    elif ('солнечно' in w.detailed_status or 'ясно' in w.detailed_status) and \
            int(w.temperature("celsius")["temp"]) >= 25:
        return random.choice(if_sunny_and_hot)
    elif 'солнечно' in w.detailed_status or 'ясно' in w.detailed_status:
        return random.choice(if_sunny)
    elif 'дождь' in w.detailed_status or 'дождливо' in w.detailed_status:
        return random.choice(if_rainy)
    elif 'снег' in w.detailed_status:
        return random.choice(if_snowy)
    elif 'дымка' in w.detailed_status or 'туман' in w.detailed_status or 'мгла' in w.detailed_status:
        return random.choice(if_fogy)
    else:
        return random.choice(if_yes)


def start(update, context):
    update.message.reply_text(f'Привет, узнаем погоду для города {city}?\n'
                              '/change_city для смены города по умолчанию\n'
                              '/daily для прогноза на завтра в определенное время в формате 00.00\n'
                              '/now для прогноза прямо сейчас\n'
                              '/h3 для прогноза через 3 часа\n'
                              '/will_have_snow узнать будет ли снег в ближайшие три часа\n'
                              '/will_have_rain узнать будет ли дождь в ближайшие три часа\n'
                              '/will_have_fog узнать будет ли туман в ближайшие три часа\n'
                              '/start_play для начала игры',
                              reply_markup=markup)


def now(update, context):
    place = city
    config_dict = get_default_config()
    config_dict['language'] = 'ru'
    owm = OWM('3c55bbaac015f0a173e15d6345bf3970', config_dict)
    mgr = owm.weather_manager()
    observation = mgr.weather_at_place(place)
    w = observation.weather
    update.message.reply_text("\n".join([
            f'Кратко если: {w.detailed_status}',
            f'А ветер.. Скорость: {w.wind()["speed"]}м/с',
            f'Влажность: {w.humidity}%',
            f't°: {int(w.temperature("celsius")["temp"])}°, ощущается как: '
            f'{int(w.temperature("celsius")["feels_like"])}°']))
    update.message.reply_sticker(stickers(w))


def daily(update, context):
    place = city
    config_dict = get_default_config()
    config_dict['language'] = 'ru'

    owm = OWM('3c55bbaac015f0a173e15d6345bf3970', config_dict)
    try:
        time = list(map(int, (update.message.text.split()[1]).split('.')))
        if time[1] > 60:
            time[1], time[0] = time[1] % 60, time[0] + time[1] // 60
        elif time[1] < 60:
            time[1], time[0] = time[1] % 60, time[0] - abs(time[1] // 60)
        if time[0] > 24 or time[0] < 0:
            time[0] = abs(time[0] % 24)
    except IndexError:
        time = [12, 00]
    mgr = owm.weather_manager()
    three_h_forecaster = mgr.forecast_at_place(place, '3h')
    tomorrow_at_five = timestamps.tomorrow(*time)  # datetime object for tomorrow at 5 PM
    w = three_h_forecaster.get_weather_at(tomorrow_at_five)
    if time[1] == 0:
        time[1] = '00'
    update.message.reply_text("\n".join([
        f'Погода завтра в {":".join(map(str, time))}\n'
        f'Кратко если: {w.detailed_status}',
        f'А ветер.. Скорость: {w.wind()["speed"]}м/с',
        f'Влажность: {w.humidity}%',
        f't°: {int(w.temperature("celsius")["temp"])}°, ощущается как: '
        f'{int(w.temperature("celsius")["feels_like"])}°']))
    update.message.reply_sticker(stickers(w))


def h3(update, context):
    place = city
    config_dict = get_default_config()
    config_dict['language'] = 'ru'

    owm = OWM('3c55bbaac015f0a173e15d6345bf3970', config_dict)

    mgr = owm.weather_manager()

    three_h_forecaster = mgr.forecast_at_place(place, '3h')
    tomorrow_at_five = timestamps.next_three_hours()
    w = three_h_forecaster.get_weather_at(tomorrow_at_five)
    update.message.reply_text("\n".join([
        f'Кратко если: {w.detailed_status}',
        f'А ветер.. Скорость: {w.wind()["speed"]}м/с',
        f'Влажность: {w.humidity}%',
        f't°: {int(w.temperature("celsius")["temp"])}°, ощущается как: {int(w.temperature("celsius")["feels_like"])}°'
    ]))
    update.message.reply_sticker(stickers(w))


def default_city(update, context):
    global city
    city = update.message.text

    update.message.reply_text(f'Город по умолчанию: {city}')


def will_have_snow(update, context):
    place = city
    config_dict = get_default_config()
    config_dict['language'] = 'ru'

    owm = OWM('3c55bbaac015f0a173e15d6345bf3970', config_dict)
    mgr = owm.weather_manager()
    three_h_forecaster = mgr.forecast_at_place(place, '3h')
    if three_h_forecaster.will_have_snow():
        update.message.reply_text(random.choice(if_yes))
        update.message.reply_sticker(random.choice(if_snowy))
    else:
        update.message.reply_text(random.choice(if_no))
        update.message.reply_sticker(random.choice(if_not))


def will_have_rain(update, context):
    place = city
    config_dict = get_default_config()
    config_dict['language'] = 'ru'
    owm = OWM('3c55bbaac015f0a173e15d6345bf3970', config_dict)
    mgr = owm.weather_manager()
    three_h_forecaster = mgr.forecast_at_place(place, '3h')
    if three_h_forecaster.will_have_rain():
        update.message.reply_text(random.choice(if_yes))
        update.message.reply_sticker(random.choice(if_rainy))
    else:
        update.message.reply_text(random.choice(if_no))
        update.message.reply_sticker(random.choice(if_not))


def will_have_fog(update, context):
    place = city
    config_dict = get_default_config()
    config_dict['language'] = 'ru'

    owm = OWM('3c55bbaac015f0a173e15d6345bf3970', config_dict)
    mgr = owm.weather_manager()
    three_h_forecaster = mgr.forecast_at_place(place, '3h')
    if three_h_forecaster.will_have_fog():
        update.message.reply_text(random.choice(if_yes))
        update.message.reply_sticker(random.choice(if_fogy))
    else:
        update.message.reply_text(random.choice(if_no))
        update.message.reply_sticker(random.choice(if_not))


def start_play(update, context):
    update.message.reply_text('Начнем игру?', reply_markup=markup3)
    global already_asked
    already_asked = []
    return 1


def q1(update, context):
    global quest, already_asked, ask
    if update.message.text != '/stop_play':
        if update.message.text.lower() != 'нет':
            if len(ask) == 0:
                ask = for_ask.copy()
                update.message.reply_text(f'Вопросы закончились. Вы решили {right_answers} из 7. Поздравляю!')
                update.message.reply_sticker(random.choice(if_not))
                update.message.reply_text(f'Привет, узнаем погоду для города {city}?\n'
                                          '/change_city для смены города по умолчанию\n'
                                          '/daily для прогноза на завтра в определенное время в формате 00.00\n'
                                          '/now для прогноза прямо сейчас\n'
                                          '/h3 для прогноза через 3 часа\n'
                                          '/will_have_snow узнать будет ли снег в ближайшие три часа\n'
                                          '/will_have_rain узнать будет ли дождь в ближайшие три часа\n'
                                          '/will_have_fog узнать будет ли туман в ближайшие три часа\n'
                                          '/start_play для начала игры',
                                          reply_markup=markup)
                return ConversationHandler.END
            else:
                quest = random.choice([i for i in (ask.keys())])
                already_asked.append(quest)
                update.message.reply_photo(quest)
                update.message.reply_text('Введите букву', reply_markup=markup2)
            return 2
        else:
            update.message.reply_text(f'Вопросы закончились. Вы решили {right_answers} из 7. Поздравляю!')
            update.message.reply_sticker(random.choice(if_not))
            update.message.reply_text(f'Привет, узнаем погоду для города {city}?\n'
                                      '/change_city для смены города по умолчанию\n'
                                      '/daily для прогноза на завтра в определенное время в формате 00.00\n'
                                      '/now для прогноза прямо сейчас\n'
                                      '/h3 для прогноза через 3 часа\n'
                                      '/will_have_snow узнать будет ли снег в ближайшие три часа\n'
                                      '/will_have_rain узнать будет ли дождь в ближайшие три часа\n'
                                      '/will_have_fog узнать будет ли туман в ближайшие три часа\n'
                                      '/start_play для начала игры',
                                      reply_markup=markup)
            return ConversationHandler.END
    elif update.message.text == '/stop_play':
        update.message.reply_text(f'Вопросы закончились. Вы решили {right_answers} из 7. Поздравляю!')
        update.message.reply_sticker(random.choice(if_not))
        update.message.reply_text(f'Привет, узнаем погоду для города {city}?\n'
                                  '/change_city для смены города по умолчанию\n'
                                  '/daily для прогноза на завтра в определенное время в формате 00.00\n'
                                  '/now для прогноза прямо сейчас\n'
                                  '/h3 для прогноза через 3 часа\n'
                                  '/will_have_snow узнать будет ли снег в ближайшие три часа\n'
                                  '/will_have_rain узнать будет ли дождь в ближайшие три часа\n'
                                  '/will_have_fog узнать будет ли туман в ближайшие три часа\n'
                                  '/start_play для начала игры',
                                  reply_markup=markup)
        return ConversationHandler.END
    else:
        update.message.reply_text('Нажмите "продолжить" или любую букву для продолжения,'
                                  ' или команду /stop_play для завершения игры.')


def q2(update, context):
    global ask, right_answers
    if update.message.text != '/stop_play':
        if update.message.text.lower() == ask[quest]:
            update.message.reply_text('Верно!\n'
                                      'Нажмите "продолжить" для продолжения или команду '
                                      '/stop_play для завершения игры.')
            update.message.reply_sticker(random.choice(if_not))
            right_answers += 1
        else:

            update.message.reply_text('Ошибка!\n'
                                      'Нажмите "продолжить" для продолжения или команду '
                                      '/stop_play для завершения игры.')
            update.message.reply_sticker(random.choice(if_wrong))
        del ask[quest]
        return 1
    elif update.message.text == '/stop_play':
        update.message.reply_text(f'Вопросы закончились. Вы решили {right_answers} из 7. Поздравляю!')
        update.message.reply_sticker(random.choice(if_not))
        update.message.reply_text(f'Привет, узнаем погоду для города {city}?\n'
                                  '/change_city для смены города по умолчанию\n'
                                  '/daily для прогноза на завтра в определенное время в формате 00.00\n'
                                  '/now для прогноза прямо сейчас\n'
                                  '/h3 для прогноза через 3 часа\n'
                                  '/will_have_snow узнать будет ли снег в ближайшие три часа\n'
                                  '/will_have_rain узнать будет ли дождь в ближайшие три часа\n'
                                  '/will_have_fog узнать будет ли туман в ближайшие три часа\n'
                                  '/start_play для начала игры',
                                  reply_markup=markup)
        return ConversationHandler.END
    else:
        update.message.reply_text('Нажмите "продолжить" для продолжения или команду /stop_play для завершения игры.')


def stop_play(update, context):
    update.message.reply_text(f'Вопросы закончились. Вы решили {right_answers} из 7. Поздравляю!')
    update.message.reply_sticker(random.choice(if_not))
    update.message.reply_text(f'Привет, узнаем погоду для города {city}?\n'
                              '/change_city для смены города по умолчанию\n'
                              '/daily для прогноза на завтра в определенное время в формате 00.00\n'
                              '/now для прогноза прямо сейчас\n'
                              '/h3 для прогноза через 3 часа\n'
                              '/will_have_snow узнать будет ли снег в ближайшие три часа\n'
                              '/will_have_rain узнать будет ли дождь в ближайшие три часа\n'
                              '/will_have_fog узнать будет ли туман в ближайшие три часа\n'
                              '/start_play для начала игры',
                              reply_markup=markup)
    return ConversationHandler.END


def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    updater.start_polling()
    dp = updater.dispatcher
    updater.start_polling()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start_play', start_play)],

        # Состояние внутри диалога.
        states={
            1: [MessageHandler(Filters.text, q1)],
            2: [MessageHandler(Filters.text, q2)]
        },

        fallbacks=[CommandHandler('stop_play', stop_play)]
    )
    dp.add_handler(conv_handler)

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler('now', now))
    dp.add_handler(CommandHandler('change_city', change_city))
    dp.add_handler(CommandHandler('daily', daily))
    dp.add_handler(CommandHandler('h3', h3))
    dp.add_handler(CommandHandler('will_have_snow', will_have_snow))
    dp.add_handler(CommandHandler('will_have_fog', will_have_fog))
    dp.add_handler(CommandHandler('will_have_rain', will_have_rain))
    dp.add_handler(CommandHandler('start_play', start_play))

    updater.idle()


if __name__ == '__main__':
    print('start')
    main()

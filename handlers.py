"""
Handler - функция, которая принимает на вход text (текст входящего сообщения) и контекст (dict), а возвращает bool:
 True если шаг пройден, False если данные введены неправильно.
"""

import settings
import re
import datetime
import calendar

from generate_ticket import generate_ticket


def handler_from_city(text, context):
    try:
        cities = []
        text = text.lower()
        if any(from_city == text for from_city in settings.FLIGHTS['fly_from']):
            context['from_city'] = text
            return True
        else:
            for from_city, to_city in settings.FLIGHTS['fly_from'].items():
                cities.append(from_city)
            context['options'] = ', '.join(cities).title()
            return False
    except ValueError:
        return False


def handler_to_city(text, context):
    cities = []
    text = text.lower()
    if any(from_city == text for from_city in settings.FLIGHTS['fly_from'][context['from_city']]):
        context['to_city'] = text
        context['timetable'] = settings.FLIGHTS['fly_from'][context['from_city']][context['to_city']]['timetable']
        return True
    else:
        for to_city, timetable in settings.FLIGHTS['fly_from'][context['from_city']].items():
            cities.append(to_city)
        context['options'] = ', '.join(cities).title()
        return False


def handler_date(text, context):
    today = datetime.datetime.now().date()
    try:
        date_to_fly = datetime.datetime.strptime(text, '%d-%m-%Y').date()
    except ValueError:
        return False
    if date_to_fly and today < date_to_fly:
        context['date_to_fly'] = str(date_to_fly)
        context['today'] = str(today)
        handler_flight_options(text, context)
        return True
    else:
        return False


def handler_flight_options(text, context):
    handler_flight_search(text, context)
    options = ''
    for i, option in enumerate(context['times_to_fly']):
        options += f'\n* {i + 1} ** дата: {option[:10]} *** время отправления: {option[10:]}'

    context['options'] = options
    return True


def handler_flight_search(text, context):
    delta_day = datetime.timedelta(days=1)
    times_to_fly = []
    day_to_fly = datetime.datetime.strptime(context['date_to_fly'], '%Y-%m-%d').date()
    data = context['timetable']['data']
    times = context['timetable']['time'].replace(' ', '').split(',')
    if data == 'по нечетным':
        while len(times_to_fly) < 5:
            while day_to_fly.day % 2 != 0:
                day_to_fly = day_to_fly + delta_day
            for time in times:
                hour, minute = time.split(':')
                time_to_fly = datetime.time(hour=int(hour), minute=int(minute), second=00)
                next_flight = datetime.datetime.combine(day_to_fly, time_to_fly)
                times_to_fly.append(str(next_flight))
            day_to_fly += delta_day
        context['times_to_fly'] = times_to_fly[:5]

    elif data == 'по будням':
        while len(times_to_fly) < 5:
            if calendar.weekday(day_to_fly.year, day_to_fly.month, day_to_fly.day) < 5:
                for time in times:
                    hour, minute = time.split(':')
                    time_to_fly = datetime.time(hour=int(hour), minute=int(minute), second=00)
                    next_flight = datetime.datetime.combine(day_to_fly, time_to_fly)
                    times_to_fly.append(str(next_flight))
            day_to_fly += delta_day
        context['times_to_fly'] = times_to_fly[:5]
    else:
        while len(times_to_fly) < 5:
            for time in times:
                hour, minute = time.split(':')
                time_to_fly = datetime.time(hour=int(hour), minute=int(minute), second=00)
                next_flight = datetime.datetime.combine(day_to_fly, time_to_fly)
                times_to_fly.append(str(next_flight))
            day_to_fly += delta_day
        context['times_to_fly'] = times_to_fly[:5]


def handler_choose_flight(text, context):
    try:
        if 0 < int(text) < 6:
            selected_flight = context['times_to_fly'][int(text) - 1]
            context['selected_flight'] = selected_flight
            context['options'] = None
            return True
        else:
            return False
    except ValueError:
        return False


def handler_number_of_passengers(text, context):
    try:
        if 0 < int(text) < 6:
            context['number_of_passengers'] = int(text)
            return True
        else:
            return False
    except ValueError:
        return False


def handler_comments(text, context):
    context['comments'] = text
    handler_data(text, context)
    return True


def handler_data(text, context):
    options = f'\n\n*Город отправления: {context["from_city"].title()}' \
              f'\n*Город прибытия: {context["to_city"].title()}' \
              f'\n*Дата вылета: {context["selected_flight"]}' \
              f'\n*Время вылета: {context["selected_flight"]}' \
              f'\n*Колличество пасажиров: {context["number_of_passengers"]}' \
              f'\n*Комментарий: {context["comments"]}' \
              f'\n\nНапишите "да" или "нет"'
    context['options'] = options
    return True


def handler_check_data(text, context):
    text = text.lower()
    if text == 'да':
        context['options'] = None
        return True
    else:
        return False


def handler_check_tell(text, context):
    text = re.sub(r"[-:*\\ ]", "", text)
    re_tel = re.compile(r'[+][379]\w{11}')
    matches = re.findall(re_tel, text)
    if matches:
        context['tell'] = matches
        return True
    else:
        return False


def handler_generate_ticket(text, context):
    return generate_ticket(context)

# def list_for_odd_dates(context):
#     while len(times_to_fly) < 5:
#         while day_to_fly.day % 2 != 0:
#             day_to_fly = day_to_fly + delta_day
#         for time in times:
#             hour, minute = time.split(':')
#             time_to_fly = datetime.time(hour=int(hour), minute=int(minute), second=00)
#             next_flight = datetime.datetime.combine(day_to_fly, time_to_fly)
#             times_to_fly.append(next_flight)
#         day_to_fly += delta_day
#     print(len(times_to_fly), times_to_fly)
#     context['times_to_fly'] = times_to_fly[:5]
#
# def list_for_weekdays(context):
#     while len(times_to_fly) < 5:
#         if calendar.weekday(day_to_fly.year, day_to_fly.month, day_to_fly.day) < 5:
#             for time in times:
#                 hour, minute = time.split(':')
#                 time_to_fly = datetime.time(hour=int(hour), minute=int(minute), second=00)
#                 next_flight = datetime.datetime.combine(day_to_fly, time_to_fly)
#                 times_to_fly.append(next_flight)
#         day_to_fly += delta_day
#     print(len(times_to_fly), times_to_fly)
#     context['times_to_fly'] = times_to_fly[:5]
#
# def list_for_everyday(context):
#     while len(times_to_fly) < 5:
#         for time in times:
#             hour, minute = time.split(':')
#             print(hour, minute, type(hour))
#             time_to_fly = datetime.time(hour=int(hour), minute=int(minute), second=00)
#             next_flight = datetime.datetime.combine(day_to_fly, time_to_fly)
#             times_to_fly.append(next_flight)
#         day_to_fly += delta_day
#     print(len(times_to_fly), times_to_fly)
#     context['times_to_fly'] = times_to_fly[:5]

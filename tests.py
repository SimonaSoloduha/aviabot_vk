import datetime
from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch, Mock
from pony.orm import db_session, rollback
from vk_api.bot_longpoll import VkBotMessageEvent

from bot import Bot
from aviabot import settings
from generate_ticket import generate_ticket


def isolate_db(test_func):
    def wrapper(*args, **kwargs):
        with db_session:
            test_func(*args, **kwargs)
            rollback()

    return wrapper


def generate_data_for_test():
    today = datetime.date.today()
    try:
        data_for_test = today.replace(today.year, today.month + 1, 1)
    except ValueError:
        data_for_test = today.replace(today.year + 1, 1, 1)
    return data_for_test


class Test1(TestCase):
    RAW_EVENT = {'type': 'message_new',
                 'object': {
                     'message': {
                         'date': 1604150900, 'from_id': 611951744, 'id': 2520, 'out': 0, 'peer_id': 611951744,
                         'text': 'dafreweda', 'conversation_message_id': 2520, 'fwd_messages': [],
                         'important': False, 'random_id': 0, 'attachments': [], 'is_hidden': False
                     },
                     'client_info': {
                         'button_actions': ['text', 'vkpay', 'open_app', 'location', 'open_link'], 'keyboard': True,
                         'inline_keyboard': True, 'carousel': False, 'lang_id': 0}
                 },
                 'group_id': 199292054,
                 'event_id': '1e2d414455da1e27098186cfb759bdc8c32f6217'
                 }

    DATA_FOR_TEST = generate_data_for_test()

    def test_ok(self):
        count = 5
        obj = {'a': 1}
        events = [obj] * count
        long_poller_mock = Mock(return_value=events)
        long_poller_listen_mock = Mock()
        long_poller_listen_mock.listen = long_poller_mock

        with patch('bot.vk_api.VkApi'):
            with patch('bot.VkBotLongPoll', return_value=long_poller_listen_mock):
                bot = Bot("", "")
                bot.on_event = Mock()
                bot.run()
                bot.on_event.assert_called()
                bot.on_event.assert_any_call(obj)
                assert bot.on_event.call_count == count

    INPUTS = [
        'Привет',
        'Старт',
        'Киев',
        'Одесса',
        f'{DATA_FOR_TEST.strftime("%d-%m-%Y")}',
        '3',
        '4',
        'нет',
        'да',
        '+380506218337',
    ]

    EXPECTED_OUTPUTS = [
        settings.DEFAULT_ANSWER,
        settings.SCENARIOS['searching']['steps']['step1']['text'],
        settings.SCENARIOS['searching']['steps']['step2']['text'],
        settings.SCENARIOS['searching']['steps']['step3']['text'],
        settings.SCENARIOS['searching']['steps']['step4']['text'] + str(f'\n* 1 ** дата: {DATA_FOR_TEST} *** время '
                                                                        'отправления:  08:00:00\n* 2 ** дата: '
                                                                        f'{DATA_FOR_TEST} *** время отправления:  '
                                                                        f'13:00:00\n* 3 ** дата: {DATA_FOR_TEST} '
                                                                        f'*** время '
                                                                        'отправления:  22:00:00\n* 4 ** дата: '
                                                                        f'{DATA_FOR_TEST + datetime.timedelta(days=1)} '
                                                                        f'*** время отправления: '
                                                                        f' 08:00:00\n* 5 ** дата: '
                                                                        f'{DATA_FOR_TEST + datetime.timedelta(days=1)}'
                                                                        f' *** время '
                                                                        'отправления:  13:00:00'),
        settings.SCENARIOS['searching']['steps']['step5']['text'],
        settings.SCENARIOS['searching']['steps']['step6']['text'],
        settings.SCENARIOS['searching']['steps']['step7']['text'] + str('\n\n*Город отправления: Киев\n*Город '
                                                                        f'прибытия: Одесса\n*Дата вылета:'
                                                                        f' {DATA_FOR_TEST} '
                                                                        f'22:00:00\n*Время вылета: {DATA_FOR_TEST} '
                                                                        '22:00:00\n*Колличество пасажиров: '
                                                                        '4\n*Комментарий: нет\n\nНапишите "да" или '
                                                                        '"нет"'),
        settings.SCENARIOS['searching']['steps']['step8']['text'],
        # settings.SCENARIOS['searching']['steps']['step8']['image'],
        settings.SCENARIOS['searching']['steps']['step9']['text']
    ]

    CONTEXT_AVATAR = {'today': f'{DATA_FOR_TEST}', 'options': None, 'to_city': 'одесса', 'comments': 'нет',
                      'from_city': 'киев', 'timetable': {'data': 'каждый день', 'time': '08:00, 13:00, 22:00'},
                      'date_to_fly': f'{DATA_FOR_TEST}',
                      'selected_flight': f'{DATA_FOR_TEST} 22:00:00',
                      'number_of_passengers': 4, 'tell': ['+999999999999'],
                      'photo_100': 'https://sun6-22.userapi.com/impg/Uug82dJrTXnWY8CXzeinj56jwZw0j5D6RU8q6w'
                                   '/rXIofVNKaYY.jpg?size=100x0&quality=88&crop=0,31,929,'
                                   '929&sign=46646cbf1404c2da88698262cb151b2c&c_uniq_tag'
                                   '=HFoX1kUIoN_8EhnTo6TkPNmjwHCKZ-U2cdFPJomQ4MI&ava=1', 'first_name': 'Simona',
                      'last_name': 'Soloduha'}

    @isolate_db
    def test_run_ok(self):
        send_mock = Mock()
        api_mock = Mock()
        api_mock.messages.send = send_mock

        events = []
        for input_text in self.INPUTS:
            event = deepcopy(self.RAW_EVENT)
            event['object']['message']['text'] = input_text
            events.append(VkBotMessageEvent(event))

        long_poller_mock = Mock()
        long_poller_mock.listen = Mock(return_value=events)

        with patch('bot.VkBotLongPoll', return_value=long_poller_mock):
            bot = Bot('', '')
            bot.api = api_mock
            bot.send_image = Mock()
            bot.run()
        assert send_mock.call_count == len(self.INPUTS)

        real_outputs = []
        for call in send_mock.call_args_list:
            args, kwargs = call
            real_outputs.append(kwargs['message'])

        for real, expec in zip(real_outputs, self.EXPECTED_OUTPUTS):
            print(real)
            print('-' * 50)
            print(expec)
            print('-' * 50)
            print(real == expec)
            print('_' * 50)
        assert real_outputs == self.EXPECTED_OUTPUTS

    def test_image_generation(self):

        with open('files/avatar_for_test.png', 'rb') as avatar_file:
            avatar_mock = Mock()
            avatar_mock.content = avatar_file.read()

        with patch('requests.get', return_value=avatar_mock):
            ticket_file = generate_ticket(self.CONTEXT_AVATAR)

        with open('files/ticket_for_test.png', 'rb') as expected_file:
            expected_bytes = expected_file.read()

        assert ticket_file.read() == expected_bytes

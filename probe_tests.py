from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch, Mock
from pony.orm import db_session, rollback
from vk_api.bot_longpoll import VkBotMessageEvent

from bot import Bot
from aviabot import settings


def isolate_db(test_func):
    def wrapper(*args, **kwargs):
        with db_session:
            test_func(*args, **kwargs)
            rollback()
    return wrapper


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
        '01-05-2021',
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
        settings.SCENARIOS['searching']['steps']['step4']['text'] + str('\n* 1 ** дата: 2021-05-01 *** время '
                                                                        'отправления:  08:00:00\n* 2 ** дата: '
                                                                        '2021-05-01 *** время отправления:  '
                                                                        '13:00:00\n* 3 ** дата: 2021-05-01 *** время '
                                                                        'отправления:  22:00:00\n* 4 ** дата: '
                                                                        '2021-05-02 *** время отправления:  '
                                                                        '08:00:00\n* 5 ** дата: 2021-05-02 *** время '
                                                                        'отправления:  13:00:00'),
        settings.SCENARIOS['searching']['steps']['step5']['text'],
        settings.SCENARIOS['searching']['steps']['step6']['text'],
        settings.SCENARIOS['searching']['steps']['step7']['text'] + str('\n\n*Город отправления: Киев\n*Город '
                                                                        'прибытия: Одесса\n*Дата вылета: 2021-05-01 '
                                                                        '22:00:00\n*Время вылета: 2021-05-01 '
                                                                        '22:00:00\n*Колличество пасажиров: '
                                                                        '4\n*Комментарий: нет\n\nНапишите "да" или '
                                                                        '"нет"'),
        settings.SCENARIOS['searching']['steps']['step8']['text'],
        settings.SCENARIOS['searching']['steps']['step9']['text'],
    ]

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
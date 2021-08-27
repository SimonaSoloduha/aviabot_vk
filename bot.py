import random
import logging
import handlers
import requests

import vk_api
from vk_api.bot_longpoll import VkBotLongPoll
from pony.orm import db_session

from models import UserState, BaseApplications

try:
    import settings
except ImportError:
    exit('Добавьте файл config.py и определите в нем my_token my_group_id!!!')

log = logging.getLogger("bot")
log.setLevel(logging.DEBUG)


def configure_logging():
    steam_handler = logging.StreamHandler()
    steam_handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    steam_handler.setLevel(logging.DEBUG)
    log.addHandler(steam_handler)

    file_handler = logging.FileHandler("bot.log")
    format_file_handler = '%(asctime)-15s %(levelname)-6s %(message)s'
    date_format_file_handler = '%d-%m-%Y %H:%M'
    formatter_file = logging.Formatter(fmt=format_file_handler, datefmt=date_format_file_handler)
    file_handler.setFormatter(formatter_file)
    file_handler.setLevel(logging.DEBUG)
    log.addHandler(file_handler)


class Bot:
    """
    Use python3.8
    """

    def __init__(self, group_id, token):
        """

        :param group_id: group_id из группы vk
        :param token: секретный токен
        """
        self.token = token
        self.group_id = group_id
        self.vk = vk_api.VkApi(token=token)
        self.long_poller = VkBotLongPoll(self.vk, self.group_id)
        self.api = self.vk.get_api()
        self.users = self.api.users.get
        self.user_guests = []

    def run(self):
        """
        Запуск бота
        """
        for event in self.long_poller.listen():
            try:
                self.on_event(event)
            except Exception:
                log.exception("ошибка в обработке события")

    @db_session
    def on_event(self, event):
        """
        Отправляем сообщение назад, если это текст
        :param event: VkBotMessageEvent object
        :return None
        """

        if event.type == vk_api.bot_longpoll.VkBotEventType.MESSAGE_TYPING_STATE:
            log.info("Есть событие :%s", event.type)

            user_id = event.object['from_id']

            if user_id not in self.user_guests:
                text_to_send = settings.GREETING
                self.user_guests.append(user_id)
                self.api.messages.send(
                    message=text_to_send,
                    random_id=random.randint(0, 2 ** 20),
                    peer_id=user_id,
                )

        if event.type == vk_api.bot_longpoll.VkBotEventType.MESSAGE_NEW:
            log.info("Есть событие :%s", event.type)

            user_id = event.object.message["peer_id"]
            text = event.object.message["text"]

            state = UserState.get(user_id=str(user_id))

            if state:
                state.context['options'] = None

            if state is not None and text != '/start' and text != '/help':
                self.continue_scenario(text, state, user_id)
            elif text == '/help':
                text_to_send = settings.DEFAULT_ANSWER
                self.send_text(user_id, text_to_send)
            else:
                for intent in settings.INTENTS:
                    log.debug(f'User gets {intent}')
                    if any(token in text.lower() for token in intent['tokens']):
                        if intent['answer']:
                            text_to_send = intent['answer']
                            self.send_text(user_id, text_to_send)
                        else:
                            self.start_scenario(str(user_id), intent['scenario'], text)
                            # self.send_text(str(user_id), text_to_send)
                        break
                else:
                    text_to_send = settings.DEFAULT_ANSWER
                    self.send_text(user_id, text_to_send)


    def send_text(self, user_id, text_to_send):
        self.api.messages.send(
            message=text_to_send,
            random_id=random.randint(0, 2 ** 20),
            peer_id=user_id,
        )

    def send_image(self, step, user_id, text, context):
        response = self.api.users.get(user_id=str(user_id), fields='photo_100')
        first_name = response[0]['first_name']
        last_name = response[0]['last_name']
        photo_100 = response[0]['photo_100']
        context['photo_100'] = photo_100

        context['first_name'] = first_name
        context['last_name'] = last_name
        handler = getattr(handlers, step['image'])
        image = handler(text, context)

        upload_url = self.api.photos.getMessagesUploadServer()['upload_url']
        # print('upload_url', upload_url)
        upload_data = requests.post(url=upload_url, files={'photo': ('image.png', image, 'image/png')}).json()
        # print('upload_data', upload_data)
        image_data = self.api.photos.saveMessagesPhoto(**upload_data)
        # print('image_data', image_data)

        owner_id = image_data[0]['owner_id']
        media_id = image_data[0]['id']
        attachment = f'photo{owner_id}_{media_id}'
        self.api.messages.send(
            attachment=attachment,
            random_id=random.randint(0, 2 ** 20),
            peer_id=user_id,
        )

    def send_step(self, step, user_id, text, context):
        if 'text' in step:
            self.send_text(user_id, step['text'].format(**context))
        if 'image' in step:
            self.send_image(step, user_id, text, context)

    def start_scenario(self, user_id, scenario_name, text):
        scenario = settings.SCENARIOS[scenario_name]
        first_step = scenario['first_step']
        step = scenario['steps'][first_step]
        text_to_send = step['text']
        UserState(user_id=str(user_id), scenario_name=scenario_name, step_name=first_step, context={})
        self.send_text(user_id, text_to_send)

    def continue_scenario(self, text, state, user_id):
        steps = settings.SCENARIOS[state.scenario_name]['steps']
        step = steps[state.step_name]

        handler = getattr(handlers, step['handler'])
        if handler(text=text, context=state.context):
            next_step = steps[step['next_step']]
            if state.context['options'] is not None:
                text_to_send = next_step['text'] + state.context['options'].format(**state.context)
                self.send_text(user_id, text_to_send)
            else:
                text_to_send = next_step['text'].format(**state.context)
                self.send_step(next_step, user_id, text, state.context)
            if next_step['next_step']:
                state.step_name = step['next_step']
            else:
                BaseApplications(today=state.context['today'], to_city=state.context['to_city'],
                                 from_city=state.context['from_city'], comments=state.context['comments'],
                                 selected_flight=state.context['selected_flight'],
                                 number_of_passengers=state.context['number_of_passengers'],
                                 tell=''.join(state.context['tell']))

                state.delete()
        else:
            if state.context['options'] is not None:
                text_to_send = step['failure_text'] + state.context['options'].format(**state.context)
                self.send_text(user_id, text_to_send)
                state.context['options'] = None
            else:
                text_to_send = step['failure_text'].format(**state.context)
                self.send_text(user_id, text_to_send)


if __name__ == "__main__":
    configure_logging()
    bot = Bot(settings.GROUP_ID, settings.TOKEN)
    bot.run()

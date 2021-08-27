from io import BytesIO

import requests
from PIL import Image, ImageDraw, ImageFont

TEMPLATE_PATH = "files/ticket_template.png"
FONT_PATH = "files/OpenSans-Regular.ttf"
FONT_SIZE = 16
BLACK = (0, 0, 0, 255)
NAME_OFFSET = (50, 118)
AVATAR_OFFSET = (290, 70)
FROM_OFFSET = (50, 188)
TO_OFFSET = (50, 255)
DATA_OFFSET = (290, 255)
TIME_DEPARTURE = (400, 255)


def generate_ticket(context):
    print(context)
    base = Image.open(TEMPLATE_PATH).convert("RGBA")
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    draw = ImageDraw.Draw(base)
    draw.text(NAME_OFFSET, f"{context['first_name']} {context['last_name']}", font=font, fill=BLACK)
    draw.text(FROM_OFFSET, context['from_city'].title(), font=font, fill=BLACK)
    draw.text(TO_OFFSET, context['to_city'].title(), font=font, fill=BLACK)
    draw.text(DATA_OFFSET, context['selected_flight'][:10], font=font, fill=BLACK)
    draw.text(TIME_DEPARTURE, context['selected_flight'][10:], font=font, fill=BLACK)

    response = requests.get(url=context['photo_100'])

    avatar_file_like = BytesIO(response.content)
    avatar = Image.open(avatar_file_like)
    avatar.save('files/avatar_for_test.png', 'png')

    base.paste(avatar, AVATAR_OFFSET)
    base.save('files/ticket_for_test.png', 'png')

    temp_file = BytesIO()
    base.save(temp_file, 'png')
    temp_file.seek(0)

    return temp_file


if __name__ == "__main__":
    generate_ticket()

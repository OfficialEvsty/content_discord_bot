import datetime
import os
import random

import discord
from django.db.models import Value

def get_random_image(directory):
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    images = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    if not images:
        raise ValueError("В указанной директории нет изображений")
    return random.choice(images)

class ManagerEmbed(discord.Embed):
    def __init__(self, user: discord.User, content=None, is_formatted=False):
        title = f""
        if content is None:
            content = ""
        if is_formatted:
            description = content
        else:
            description = f"```{content}```"
        super().__init__(title=title, description=description, timestamp=datetime.datetime.now())
        self.set_author(name=user.name, icon_url=user.avatar.url)
        self.set_footer(text="ПАНЕЛЬ УПРАВЛЕНИЯ")
        self.image_directory = "ui/design/backgrounds"
        image_file = get_random_image(self.image_directory)
        image_path = os.path.join(self.image_directory, image_file)
        self.file = discord.File(image_path)
        self.set_image(url=f"attachment://{image_file}")

class ActivityViewerEmbed(discord.Embed):
    def __init__(self, start, page_size, content, chosen_bosses, dates: ()):
        super().__init__(title=f"Активность участников {start}-{start+page_size}",
                         description=f"```{content}```", timestamp=datetime.datetime.now())
        self.add_field(name="ДАТА", value=f">>> `с  {dates[0].date()}\nпо {dates[1].date()}`")
        self.add_field(name="БОССЫ", value=f">>> `{chosen_bosses}`")
        self.set_footer(text=f"Ходят на праймисы?")

class SalaryViewerEmbed(discord.Embed):
    def __init__(self, start, page_size, content, chosen_bosses, dates: (), bank):
        super().__init__(title=f"Зарплата участников {start}-{start+page_size}",
                         description=f"```{content}```", timestamp=datetime.datetime.now())
        self.add_field(name="ДАТА", value=f">>> `с  {dates[0].date()}\nпо {dates[1].date()}`")
        self.add_field(name="БОССЫ", value=f">>> `{chosen_bosses}`")
        self.set_footer(text=f"Пришло в казну: {bank} $")

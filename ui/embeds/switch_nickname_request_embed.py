from datetime import datetime

import discord


class SwitchNicknameEmbed(discord.Embed):
    def __init__(self, user: discord.User, nickname: str, color = None):
        title = f"Запрос на присвоение никнейма в Archeage"
        description = f"Подтвердите свое разрешение на присвоение/смены никнейма для пользователя `{user.name}`"
        if color:
            super().__init__(title=title, description=description, timestamp=datetime.now(), color=color)
        else:
            super().__init__(title=title, description=description, timestamp=datetime.now())
        self.set_author(name=user.name, icon_url=user.avatar.url)
        self.add_field(name=f"Никнейм", value=f"`{nickname}`")
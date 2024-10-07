import random
from datetime import datetime
from typing import List

import discord

from data.models.event import Activity
from utilities.custom.emoji import EMOJIS


class BoundingNicknamesEmbed(discord.Embed):
    def __init__(self, user: discord.Member, current: str, previous: List[str]):
        author = ""
        author_icon = ""
        if user:
            author = user.name
            author_icon = user.avatar.url
        timestamp = datetime.now()
        content = f"{EMOJIS['Emblem_Active']}|{current}\n"
        content += f"\n".join([f"{EMOJIS['Emblem_Inactive']}|{prev}" for prev in previous])

        super().__init__(title="Никнеймы", description=f">>> {content}",
                         timestamp=timestamp,
                         color=discord.Color.from_rgb(random.randint(0, 255),
                                                      random.randint(0, 255),
                                                      random.randint(0, 255)))
        if user:
            self.set_author(name=author, icon_url=author_icon)
            self.set_thumbnail(url=author_icon)

# Extended for admins
class BoundingNicknameAndActivityEmbed(BoundingNicknamesEmbed):
    def __init__(self, user: discord.Member, current: str, previous: List[str], activity: float, salary: float):
        super().__init__(user, current, previous)
        self.add_field(name="Активность", value=f"`{activity}%`", inline=True)
        self.add_field(name="Зарплата", value=f"`{salary}` :coin:", inline=True)
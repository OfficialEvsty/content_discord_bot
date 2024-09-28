import random
from datetime import datetime
from typing import List

import discord

from utilities.custom.emoji import EMOJIS


class BoundingNicknamesEmbed(discord.Embed):
    def __init__(self, caller: discord.Member, user: discord.Member, current: str, previous: List[str]):
        author = user.name
        author_icon = user.avatar.url
        caller_name = caller.name
        caller_icon = caller.avatar.url
        timestamp = datetime.now()
        content = f"{EMOJIS['Emblem_Active']}|{current}\n"
        content += f"\n".join([f"{EMOJIS['Emblem_Inactive']}|{prev}" for prev in previous])

        super().__init__(title="Никнеймы", description=f">>> {content}",
                         timestamp=timestamp,
                         color=discord.Color.from_rgb(random.randint(0, 255),
                                                      random.randint(0, 255),
                                                      random.randint(0, 255)))
        self.set_author(name=author, icon_url=author_icon)
        self.set_footer(text=f"{caller_name} использовал /профиль", icon_url=caller_icon)
        self.set_thumbnail(url=author_icon)
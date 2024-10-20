import discord


class RedirectedScreenshotEmbed(discord.Embed):
    def __init__(self, events, image_url, datetime, size, author, icon_url, collisions, manual):
        events_name_txt = ", ".join(events)
        super().__init__(title=f"РЕЙД НА: ***{events_name_txt}***", description=f"Размер рейда: `{size}`", timestamp=datetime)
        if collisions is not None:
            if len(collisions) > 0:
                self.add_field(name=f'Коллизии `{len(collisions)}`', value='```\n'+'\n'.join(collisions) + '```', inline=True)
        if manual is not None:
            if len(manual) > 0:
                self.add_field(name=f'Ручной ввод: `{len(manual)}`', value='```\n' + '\n'.join(manual) + '```')
        self.set_image(url=image_url)
        self.set_footer(text=f"Предоставил(а) {author}", icon_url=icon_url)
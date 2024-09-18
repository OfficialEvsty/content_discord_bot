import discord


class NicknameTableEmbed(discord.Embed):
    def __init__(self, names_list: []):
        # Создаем Embed
        content = "\n".join(names_list)
        super().__init__(title=f"Добавленные никнеймы: {len(names_list)}", description=f"```\n{content}```", color=discord.Color.green())

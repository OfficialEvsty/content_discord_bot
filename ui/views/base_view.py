import json
import logging

import discord.ui

with open("config.json") as file:
    config = json.load(file)

logger = logging.getLogger("app.ui")
class BaseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=config['SLASH_COMMANDS']['Timeout'])
        self.message = None
        self.is_timeout = False

    async def on_timeout(self) -> None:
        self.is_timeout = True
        # Проверяем, связано ли сообщение с view
        if self.message:
            try:
                # Удаляем сообщение при срабатывании тайм-аута
                await self.message.delete()
            except discord.NotFound:
                # Сообщение уже было удалено
                pass
            except discord.HTTPException as e:
                # Ловим другие ошибки
                logger.error(f"Ошибка во время работы on_timeout: {e}")

class CancelButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Закрыть", style=discord.ButtonStyle.danger, row=1)

    async def callback(self, interaction: discord.Interaction):
        view: CancelledView = self.view  # Получаем представление (View), к которому относится кнопка
        if view and hasattr(view, 'message') and view.message:
            view.cancelled = True
            await view.message.delete()  # Удаляем сообщение
            view.stop()  # Останавливаем представление
            raise TimeoutError(view)
        else:
            logger.error(f"Сообщение {view.message if view else 'None'} не найдено")

class CancelledView(BaseView):
    cnl_button: CancelButton
    def __init__(self):
        super().__init__()
        self.cnl_button = CancelButton()
        self.cancelled = False
        self.add_item(self.cnl_button)


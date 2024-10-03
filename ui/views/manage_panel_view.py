import discord
from discord import SelectOption
from discord.ui import Button, Select

from commands.calculating.activity_commands import calculate_activity
from commands.calculating.salary_commands import calculate_salary_by_nickname
from data.models.event import EventType
from ui.embeds.manage_embed import ActivityViewerEmbed, ManagerEmbed, SalaryViewerEmbed
from ui.modals.activity_modal import DateInputModal
from ui.views.base_view import BaseView, CancelledView


class ManagerPanelView(CancelledView):
    def __init__(self, controller, message = None):
        super().__init__()
        self.message = message
        self.controller = controller
        self.dates = (None, None)
        self.nickname_activities_percent = None
        self.activity_button = Button(label="Активка")
        self.salary_button = Button(label="Зарплата")
        self.input_dates_modal_button = Button(label="Выбрать даты")
        self.activity_button.callback = self.activity_callback
        self.salary_button.callback = self.salary_callback
        self.input_dates_modal_button.callback = self.input_dates_modal
        self.add_item(self.activity_button)
        self.add_item(self.salary_button)
        self.add_item(self.input_dates_modal_button)
        self.update_buttons()

    async def on_timeout(self) -> None:
        if self.message:
            updated_view = ManagerPanelView(self.controller, self.message)
            self.update_buttons()
            await self.message.edit(view=updated_view)

    async def input_dates_modal(self, interaction: discord.Interaction):
        modal = DateInputModal()
        modal_msg = await interaction.response.send_modal(modal)
        await modal.wait()
        self.dates = (modal.start, modal.end)
        self.update_buttons()
        self.nickname_activities_percent = await self.controller.get_nickname_activities(interaction, self.dates[0],
                                                                                    self.dates[1])
        return await self.message.edit(view=self)



    def update_buttons(self):
        self.salary_button.disabled = True
        self.activity_button.disabled = True
        if self.dates[0] and self.dates[1]:
            self.clear_items()
            self.salary_button.disabled = False
            self.activity_button.disabled = False
            self.add_item(self.activity_button)
            self.add_item(self.salary_button)
            self.add_item(self.input_dates_modal_button)

    async def activity_callback(self, interaction: discord.Interaction):
        if self.dates[0] and self.dates[1]:
            activity_viewer = PaginatorView(self.nickname_activities_percent, (self.dates[0], self.dates[1]), True,
                                            self.controller, self.message)
            await interaction.followup.edit_message(message_id=self.message.id, view=activity_viewer, attachments=[])
            self.stop()

    async def salary_callback(self, interaction: discord.Interaction):
        if self.dates[0] and self.dates[1]:
            activity_viewer = PaginatorView(self.nickname_activities_percent, (self.dates[0], self.dates[1]), False,
                                            self.controller, self.message)

            await interaction.followup.edit_message(message_id=self.message.id, view=activity_viewer, attachments=[])
            self.stop()



class PaginatorView(BaseView):
    def __init__(self, items, dates, is_activity, controller, msg):
        super().__init__()
        self.is_activity = is_activity
        self.message = msg
        self.bank = 0
        self.controller = controller
        self.items = items
        self.dates = dates
        self.current_page = 0
        self.page_size = 25
        self.max_chars_count = 0
        self.items_list = []
        self.bosses = [SelectOption(label=etype.value) for etype in EventType]
        self.chosen = None


        self.select = discord.ui.Select(placeholder=f"Выберите боссов",
                                        options=self.bosses, max_values=len(self.bosses))

        self.embed = None
        self.select.callback = self.select_callback
        self.add_item(self.select)

        self.prev_button = discord.ui.Button(label="◀️", style=discord.ButtonStyle.primary)
        self.prev_button.callback = self.prev_page
        self.add_item(self.prev_button)

        self.next_button = discord.ui.Button(label="▶️", style=discord.ButtonStyle.primary)
        self.next_button.callback = self.next_page
        self.add_item(self.next_button)

        self.back_button = discord.ui.Button(label="Назад", style=discord.ButtonStyle.danger)
        self.back_button.callback = self.back_callback
        self.add_item(self.back_button)

    async def on_timeout(self) -> None:
        if self.message:
            updated_view = PaginatorView(self.items, self.dates, self.is_activity, self.controller, self.message)
            await self.message.edit(view=updated_view)

    async def update(self, interaction: discord.Interaction):
        # Создаем селектор с 25 опциями на текущей странице
        start_index = self.current_page * self.page_size
        end_index = min(start_index + self.page_size, start_index + (len(self.items_list) - start_index))

        items_page = self.items_list[start_index:end_index]
        content = "\n".join(items_page)
        if self.is_activity:
            self.embed = ActivityViewerEmbed(start_index, self.page_size, content, self.chosen, self.dates)
        else:
            self.embed = SalaryViewerEmbed(start_index, self.page_size, content, self.chosen, self.dates, self.bank)

        self.prev_button.disabled = True
        self.next_button.disabled = True

        if start_index > self.page_size-1:
            self.prev_button.disabled = False

        if end_index < len(self.items):
            self.next_button.disabled = False

        await interaction.response.edit_message(view=self, embed=self.embed)

    async def select_callback(self, interaction: discord.Interaction):
        self.chosen = self.select.values
        self.current_page = 0
        if self.is_activity:
            self.filter_by_bosses()
        else:
            self.salary_filter_by_bosses()
        await self.update(interaction)

    def filter_by_bosses(self):
        chosen_bosses = self.select.values
        filtered_activity_percent = calculate_activity(self.items, chosen_bosses)
        sorted_activity_percent = dict(sorted(filtered_activity_percent.items(), key=lambda item: item[1], reverse=True))
        if len(sorted_activity_percent) > 0:
            self.max_chars_count = max(len(key) for key in sorted_activity_percent.keys())
        self.items_list = [f"{item[0].ljust(self.max_chars_count)} | {str(item[1]).rjust(4)}%" for item in sorted_activity_percent.items()]

    def salary_filter_by_bosses(self):
        chosen_bosses = self.select.values
        calculations = calculate_salary_by_nickname(self.items, chosen_bosses)
        filtered_salary = calculations[0]
        self.bank = round(calculations[1], 2)
        sorted_salary = dict(sorted(filtered_salary.items(), key=lambda item: item[1], reverse=True))
        money_char = "$"
        max_value_len = max(len(str(round(val, 2))) for val in sorted_salary.values())
        if len(sorted_salary) > 0:
            self.max_chars_count = max(len(key) for key in sorted_salary.keys())
        self.items_list = [f"{item[0].ljust(self.max_chars_count)} | {str(round(item[1], 2)).rjust(4)} {money_char:<{max_value_len}}" for item in
                           sorted_salary.items()]


    async def next_page(self, interaction: discord.Interaction):
        self.current_page += 1
        await self.update(interaction)
    async def prev_page(self, interaction: discord.Interaction):
        self.current_page -= 1
        await self.update(interaction)

    async def back_callback(self, interaction: discord.Interaction):
        view = ManagerPanelView(self.controller, self.message)
        embed =ManagerEmbed(interaction.user, ">>> *Панель - лучший инструмент для просмотра статистики активностей и зарплат мемберов*", is_formatted=True)
        await interaction.response.edit_message(view=view, embed=embed, attachments=[embed.file])
        self.stop()

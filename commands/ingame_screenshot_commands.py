import os
import uuid
from typing import List

from sqlalchemy import select

from data.configuration import CONFIGURATION
from data.models.setting import Setting
from exceptions.cancel_exception import CancelException
from exceptions.timeout_exception import TimeoutException
from ui.nickname_table_text_presentation import create_nicknames_table
from services.nickname_service import NicknameService
from ui.embeds.nicknames_table import NicknameTableEmbed
from ui.views.manual_nickname_input import ManualConfirmMessageView
from ui.views.merged_resolver_view import MergedResolverView
from utilities.progress_bar import get_progress_bar
from utilities.screenshot_handling import enchant_image, recognize_nicknames_on_image
import discord
from commands.subcommands.screenshot_io import save_attachment, screenshots_cleaning
import logging

logger = logging.getLogger("app.commands")

async def pull_nicknames_from_screenshot(interaction: discord.Interaction, attachment: discord.Attachment, session, ocr_config) -> List[List[str]]:
    current_progress_bar = await get_progress_bar(interaction, None,0)
    input_file_path = os.path.join(ocr_config['IO']['input_image_directory_path'], ocr_config['IO']['input_image_file_name'])
    if attachment.content_type.startswith("image"):
        await save_attachment(attachment, input_file_path)
    else:
        logger.info("Прикрепленный файл не является изображением")
        return interaction.followup.send("Прикрепленный файл не является изображением, прикрепите изображение в формате `.png`")

    await get_progress_bar(interaction, current_progress_bar, 1)
    output_filepath = os.path.join(ocr_config['IO']['output_image_directory_path'], ocr_config['IO']['output_image_file_name'])
    enchanter_mode = 'fast' if attachment.width > ocr_config['MODE_BOUND'][0] and attachment.height > ocr_config['MODE_BOUND'][1] else 'slow'
    enchanter = ocr_config['IMAGE_ENCHANTER'][enchanter_mode]
    await enchant_image(input_file_path, enchanter['model'], enchanter['model_path'], enchanter['scale'], output_filepath)
    await get_progress_bar(interaction, current_progress_bar, 2)

    completed_nicknames = None

    service = NicknameService(session)
    result = await service.get_nicknames(interaction.guild.id)
    existing_nicknames = [] if result is None else [nickname.name for nickname in result]
    await get_progress_bar(interaction, current_progress_bar, 3)
    visited_nicknames_with_collisions =  await recognize_nicknames_on_image(ocr_config["LANGUAGES"], output_filepath, existing_nicknames)
    await get_progress_bar(interaction, current_progress_bar, 5)
    await current_progress_bar.delete()
    choices = await resolve_merge_conflicted_nicknames(interaction, visited_nicknames_with_collisions)
    nicknames_without_conflict = eliminate_collisions(visited_nicknames_with_collisions, choices)
    table_names = await create_table_names(nicknames_without_conflict)
    manual_choices = await is_manual_needed(interaction, list(set(existing_nicknames) ^ set(nicknames_without_conflict)), table_names)
    nicknames_without_conflict.extend(manual_choices)
    completed_nicknames = nicknames_without_conflict


    await screenshots_cleaning(ocr_config['IO']['output_image_directory_path'])
    await screenshots_cleaning(ocr_config['IO']['input_image_directory_path'])
    return [completed_nicknames, choices, manual_choices]

async def resolve_merge_conflicted_nicknames(interaction: discord.Interaction, nicknames: [[[]]]):
    choices = []
    collision_nicknames = [[collisions, file] for collisions, file in nicknames if len(collisions) > 1]
    if len(collision_nicknames) == 0:
        return None
    view = MergedResolverView(collision_nicknames, len(collision_nicknames), choices)

    msg = await interaction.followup.send(ephemeral=CONFIGURATION['SLASH_COMMANDS']['IsResponsesEphemeral'], view=view, embed=view.embed, file=view.file)
    view.message = msg
    await view.wait()
    if view.cancelled:
        raise CancelException(view)
    if len(choices) < len(collision_nicknames):
        await msg.delete()
        raise TimeoutException(view)
    await msg.delete()
    return choices

def eliminate_collisions(names_with_collisions, user_choices):
    names = []
    if user_choices is None:
        return [name[0][0] for name in names_with_collisions]
    for collision in names_with_collisions:
        if len(collision[0]) > 1:
            intersection = list(set(collision[0]) and set(user_choices))
            for elem in intersection:
                names.append(elem)
            user_choices = list(set(user_choices) ^ set(intersection))
        elif len(collision[0]) == 1:
            names.append(collision[0][0])
    return names

async def create_table_names(names: []):
    # if prev_msg is None:
    #     table_list = create_nicknames_table(names)
    #     table_names_msg = await interaction.followup.send(f"{table_list}")
    #     return table_names_msg
    # else:
    #     table_list = create_nicknames_table(names)
    #     await prev_msg.edit(content=f"{table_list}")
    return create_nicknames_table(names)

async def is_manual_needed(interaction: discord.Interaction, available_names, table_names):
    choices = []
    view = ManualConfirmMessageView(available_names, choices)
    msg = await interaction.followup.send(content=f"{table_names}", ephemeral=CONFIGURATION['SLASH_COMMANDS']['IsResponsesEphemeral'], view=view, embed=view.embed)
    view.message = msg
    await view.wait()
    if view.cancelled:
        raise CancelException(view)

    await msg.delete()
    return choices

from data.configuration import CONFIGURATION


async def get_progress_bar(interaction, msg, step: int):
    progress_bar = [
        "[░░░░░░░░░░] 0%",
        "[█░░░░░░░░░] 10%",
        "[███░░░░░░░] 30%",
        "[█████░░░░░] 50%",
        "[███████░░░] 70%",
        "[██████████] 100%"
    ]

    if step == 0:
        msg = await interaction.followup.send(f"⏳ Обработка: {progress_bar[step]}", ephemeral=CONFIGURATION['SLASH_COMMANDS']['IsResponsesEphemeral'])
        return msg

    step = min(step, len(progress_bar)-1)
    # Этапы загрузки
    msg = await msg.edit(content=f"⏳ Обработка: {progress_bar[step]}")
    return msg

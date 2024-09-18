import asyncio
import discord


async def auto_delete_webhook(interaction: discord.Interaction, content: str, delete_after: int, is_ephemeral=True):
    msg_to_delete = await interaction.followup.send(content, ephemeral=is_ephemeral)
    await asyncio.sleep(delete_after)
    await msg_to_delete.delete()
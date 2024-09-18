import datetime
from typing import Dict, Tuple

import discord



class NicknameRequest:
    message: discord.Message
    created_at: datetime.datetime

    nickname: str

    def __init__(self, message, nickname):
        self.message = message
        self.nickname = nickname
        self.created_at = datetime.datetime.now()


nickname_requests: Dict[Tuple[int, int], NicknameRequest] = {}
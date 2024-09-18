from typing import List


class AGuild:
    id: int
    name: str

    def __init__(self, _name):
        self.name = _name


class AMember:
    name: str
    guild: AGuild
    def __init__(self, _name: str, _guild: AGuild):
        self.name = _name
        self.guild = _guild

class ATag:
    members: List[AMember]
    guilds: set

    def __init__(self):
        self.members = []
        self.guilds = set()

    def add_member(self, name: str, guild_name: str):
        if guild_name not in list(map(lambda x: x.name, self.guilds)):
            self.guilds.add(AGuild(guild_name))
        self.members.append(AMember(name, self.get_guild(guild_name)))

    def get_guild(self, guild_name: str):
        for guild in self.guilds:
            if guild.name == guild_name:
                return guild
        return None
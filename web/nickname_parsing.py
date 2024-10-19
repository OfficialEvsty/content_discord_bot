import requests
import json
import logging
from utilities.ingame_entities import ATag, AGuild, AMember



logger = logging.getLogger("app.web")


async def get_nicknames_from_archeage_website(archeage_config):
    tag = ATag()
    response = requests.get("https://archeage.ru/dynamic/rank/?a=heroes_data")
    if response.status_code == 200:
        response.encoding = 'utf-8'
        json_file = json.loads(response.content)
        all_union_users = json_file['data']['candidates'][archeage_config['server_id']][archeage_config['union_id']]
        print(all_union_users)
        print("\n\n\n")

        archeage_unicode_escape_encoding_guilds = [guild_name.encode().decode('unicode_escape') for guild_name in archeage_config['guilds']]
        print(archeage_unicode_escape_encoding_guilds)
        for user in all_union_users:
            if user['guild'] in archeage_unicode_escape_encoding_guilds:
                print(f"user guild: {user['guild']}, guilds: {archeage_unicode_escape_encoding_guilds}")
                tag.add_member(user['name'], user['guild'])
    else:
        logger.warning(f"Error with status code = {response.status_code}")

    return [member.name for member in tag.members]
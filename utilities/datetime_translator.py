from pytz import timezone
from datetime import datetime


def translate_utc_to_moscow_datetime(utc_time: datetime) -> datetime:
    # Часовой пояс Москва (UTC+3)
    moscow_tz = timezone('Europe/Moscow')

    # Преобразуем время в нужный часовой пояс
    return utc_time.astimezone(moscow_tz)
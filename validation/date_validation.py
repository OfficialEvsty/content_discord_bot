from datetime import datetime


def validate_date(date_text: str, date_format: str = "%d-%m-%Y") -> bool:
    try:
        # Пытаемся распарсить дату с указанным форматом
        datetime.strptime(date_text, date_format)
        return True
    except ValueError:
        # Если формат неверный или дата невалидная, возвращаем False
        return False

def check_date_range(start_date_text: str, end_date_text: str, date_format: str = "%d-%m-%Y") -> bool:
    if not (validate_date(start_date_text, date_format) and validate_date(end_date_text, date_format)):
        return False

    start_date = datetime.strptime(start_date_text, date_format)
    end_date = datetime.strptime(end_date_text, date_format)
    return start_date < end_date

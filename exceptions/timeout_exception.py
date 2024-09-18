


class TimeoutException(Exception):
    def __init__(self, view):
        message = f"Время взаимодействия с {view} вышло"
        super().__init__(message)


class CancelException(Exception):
    def __init__(self, view):
        message = f"Была нажата кнопка отмены на {view}"
        super().__init__(message)
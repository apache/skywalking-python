
class BaseCommand:
    def __init__(self,
                 command: str = None,
                 serial_number: str = None):
        self.command = command  # type: str
        self.serial_number = serial_number  # type: str

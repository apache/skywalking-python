from skywalking.command.executors.command_executor import CommandExecutor
from skywalking.command.base_command import BaseCommand


class NoopCommandExecutor(CommandExecutor):
    def __init__(self):
        pass

    def execute(self, command: BaseCommand):
        pass




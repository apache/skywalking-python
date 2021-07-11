from skywalking.command.base_command import BaseCommand


class CommandExecutor:
    def execute(self, command: BaseCommand):
        raise NotImplementedError()


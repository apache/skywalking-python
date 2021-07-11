from collections import deque
import queue
from typing import List

from skywalking.loggings import logger
from skywalking.command.base_command import BaseCommand
from skywalking.command.profile_task_command import ProfileTaskCommand
from skywalking.command.executors.command_executor import CommandExecutor
from skywalking.command.executors.profile_task_command_executor import ProfileTaskCommandExecutor
from skywalking.command.executors import noop_command_executor_instance

from skywalking.protocol.common.Common_pb2 import Commands, Command


class CommandService:

    def __init__(self):
        self.__commands = queue.Queue()  # type: queue.Queue
        # don't execute same command twice
        self.__command_serial_number_cache = CommandSerialNumberCache()

    def dispatch(self):
        while True:
            command = self.__commands.get()  # type: BaseCommand
            logger.debug("dispatch command: %s", command)

            if not self.__is_command_executed(command):
                command_executor_service.execute(command)
                self.__command_serial_number_cache.add(command.serial_number)

    def __is_command_executed(self, command: BaseCommand):
        return self.__command_serial_number_cache.contains(command.serial_number)

    def receive_command(self, commands: Commands):
        for command in commands.commands:
            try:
                base_command = CommandDeserializer.deserialize(command)
                logger.debug("Received command [{%s} {%s}]", base_command.command, base_command.serial_number)

                if self.__is_command_executed(base_command):
                    logger.warning("Command[{%s}] is executed, ignored.", base_command.command)
                    continue

                try:
                    self.__commands.put(base_command)
                except queue.Full:
                    logger.warning("Command[{%s}, {%s}] cannot add to command list. because the command list is full.",
                                   base_command.command, base_command.serial_number)
            except UnsupportedCommandException as e:
                logger.warning("Received unsupported command[{%s}].", e.command.command)


class CommandSerialNumberCache:

    def __init__(self, maxlen=64):
        self.queue = deque(maxlen=maxlen)
        self.max_capacity = maxlen

    def add(self, number: str):
        if len(self.queue) >= self.max_capacity:
            self.queue.pop()
        self.queue.append(number)

    def contains(self, number: str) -> bool:
        try:
            _ = self.queue.index(number)
            return True
        except ValueError:
            return False


class CommandExecutorService:
    """
    route commands to appropriate executor
    """

    def __init__(self):
        self.__command_executor_map = {ProfileTaskCommand.NAME: ProfileTaskCommandExecutor()}

    def execute(self, command: BaseCommand):
        self.__executor_for_command(command).execute(command)

    def __executor_for_command(self, command: BaseCommand):
        executor = self.__command_executor_map.get(command.command)
        if not executor:
            return noop_command_executor_instance
        return executor


class CommandDeserializer:

    @staticmethod
    def deserialize(command: Command) -> BaseCommand:
        command_name = command.command

        if ProfileTaskCommand.NAME == command_name:
            return ProfileTaskCommand.deserialize(command)
        else:
            raise UnsupportedCommandException(command)


class UnsupportedCommandException(Exception):

    def __init__(self, command):
        self.command = command


# init
command_executor_service = CommandExecutorService()

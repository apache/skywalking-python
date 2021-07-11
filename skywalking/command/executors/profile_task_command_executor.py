from skywalking.command.executors.command_executor import CommandExecutor
from skywalking.command.profile_task_command import ProfileTaskCommand
from skywalking.loggings import logger
from skywalking.profile import profile_task_execution_service
from skywalking.profile.profile_task import ProfileTask


class ProfileTaskCommandExecutor(CommandExecutor):

    def execute(self, command: ProfileTaskCommand):
        logger.debug("start execute ProfileTaskCommand [{%s}]", command.serial_number)

        profile_task = ProfileTask(task_id=command.task_id,
                                   first_span_op_name=command.endpoint_name,
                                   duration=command.duration,
                                   min_duration_threshold=command.min_duration_threshold,
                                   thread_dump_period=command.dump_period,
                                   max_sampling_count=command.max_sampling_count,
                                   start_time=command.start_time,
                                   create_time=command.create_time)

        profile_task_execution_service.add_profile_task(profile_task)


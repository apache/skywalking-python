class ProfileConstants:
    # Monitor duration must greater than 1 minutes
    TASK_DURATION_MIN_MINUTE = 1
    # The duration of the monitoring task cannot be greater than 15 minutes
    TASK_DURATION_MAX_MINUTE = 15
    # Dump period must be greater than or equals 10 milliseconds
    TASK_DUMP_PERIOD_MIN_MILLIS = 10
    # Max sampling count must less than 10
    TASK_MAX_SAMPLING_COUNT = 10

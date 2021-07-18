from enum import Enum


class ProfileStatus(Enum):
    NONE = 0
    PENDING = 1
    PROFILING = 2
    STOPPED = 3


class ProfileStatusReference:
    def __init__(self, status: ProfileStatus):
        self.status = status

    @staticmethod
    def create_with_none():
        return ProfileStatusReference(ProfileStatus.NONE)

    @staticmethod
    def create_with_pending():
        return ProfileStatusReference(ProfileStatus.PENDING)

    def get(self) -> ProfileStatus:
        return self.status

    def update_status(self, update: ProfileStatus):
        self.status = update

    def is_being_watched(self):
        return self.status is not ProfileStatus.NONE

    def is_profiling(self):
        return self.status is ProfileStatus.PROFILING

from abc import ABC, abstractmethod


class ReportStrategy(ABC):

    @abstractmethod
    def read_progress(self):
        pass

    @abstractmethod
    def report_time(self, key, reported_time):
        pass

    @abstractmethod
    def write_progress(self):
        pass

    @abstractmethod
    def matlab_progress(self):
        pass

    @abstractmethod
    def mean_progress(self):
        pass

    @abstractmethod
    def mean_write_progress(self):
        pass



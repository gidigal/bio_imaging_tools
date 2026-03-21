from works.report_strategy import ReportStrategy
from profiling.profiler import Profiler
import os
import time


class SingleProcessReportStrategy(ReportStrategy):

    def __init__(self, queue):
        self.queue = queue

    def read_progress(self):
        self.queue.put('Read')

    def report_time(self, key, reported_time):
        Profiler.instance().inc(key, reported_time, os.getpid())

    def write_progress(self):
        self.queue.put('Write')

    def matlab_progress(self):
        self.queue.put('Pivlab calls')



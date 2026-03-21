from works.report_strategy import ReportStrategy
import os

class MultiProcessReportStrategy(ReportStrategy):

    def __init__(self, queue):
        self.queue = queue

    def read_progress(self):
        self.queue.put({'type': 'progress', 'progress_type': 'Read'})

    def report_time(self, key, reported_time):
        self.queue.put({'type': 'profiler', 'key': key, 'reported_time': reported_time, 'process_id': os.getpid()})

    def write_progress(self):
        self.queue.put({'type': 'progress', 'progress_type': 'Write'})

    def matlab_progress(self):
        self.queue.put({'type': 'progress', 'progress_type': 'Pivlab calls'})

    def mean_progress(self):
        self.queue.put({'type': 'progress', 'progress_type': 'Mean'})

    def mean_write_progress(self):
        self.queue.put({'type': 'progress', 'progress_type': 'Mean Write'})
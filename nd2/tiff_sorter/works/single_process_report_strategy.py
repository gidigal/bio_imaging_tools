from works.report_strategy import ReportStrategy
from tqdm import tqdm
from profiling.profiler import Profiler


class SingleProcessReportStrategy(ReportStrategy):

    def __init__(self, total_planes, total_pairs):
        self.read_progress_bar = tqdm(total=total_planes, desc=f"Reading planes", position=0, leave=True)
        self.write_progress_bar = tqdm(total=total_planes, desc=f"Writing planes", position=0, leave=True)
        self.matlab_progress_bar = tqdm(total=total_pairs, desc=f"Calculating velocity", position=0, leave=True)

    def read_progress(self):
        self.read_progress_bar.update(1)

    def report_time(self, key, reported_time):
        Profiler.instance().inc(key, reported_time)

    def write_progress(self):
        self.write_progress_bar.update(1)

    def matlab_progress(self):
        self.matlab_progress_bar.update(1)



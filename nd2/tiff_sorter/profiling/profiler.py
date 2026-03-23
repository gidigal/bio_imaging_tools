import os
import time


def get_summary_message(summary_data):
    process_id = summary_data.pop('process_id')
    total_time = summary_data.pop('total_time')
    summary_message = f"Profiling data for process {process_id}\n-------------------------------\n"
    summary_message += f"Total time: {total_time}\n"
    for key in summary_data.keys():
        summary_message += f"{key} : {summary_data[key]:.2f} seconds {(summary_data[key] / total_time) * 100:.2f}%\n"
    return summary_message


class Profiler:

    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def refresh(cls):
        cls._instance = cls()

    def inc(self, key, value):
        self.counters[key] += value

    def __init__(self):
        self.total_times = {}
        self.print_summary = True
        self.counters = None
        self.start_time = None
        self.end_time = None

    def get_print_summary(self):
        return self.print_summary

    def set_print_summary(self, value):
        self.print_summary = value

    def init(self):
        counters = ['read', 'write', 'matlab_start', 'matlab_add_path', 'convert_to_matlab_format',
                    'dict_to_matlab_struct', 'process_single_pair_pivlab', 'convert_back_to_python']
        default_value = 0
        new_dict = dict.fromkeys(counters, default_value)
        self.counters = new_dict

    def start(self, start_time):
        self.start_time = start_time
        self.init()

    def end(self, end_time):
        self.end_time = end_time
        if self.print_summary:
            self.summary()

    def get_total_time(self):
        return self.end_time - self.start_time

    def get_summary_data(self):
        res = self.counters.copy()
        res['process_id'] = os.getpid()
        res['total_time'] = self.get_total_time()
        return res

    def summary(self):
        data = self.get_summary_data()
        print(get_summary_message(data))



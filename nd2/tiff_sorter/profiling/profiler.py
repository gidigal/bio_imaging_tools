import time


class Profiler:

    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def inc(self, key, value):
        self.counters[key] += value



    def __init__(self):
        self.counters = {'read': 0, 'write': 0, 'matlab_start': 0, 'matlab_add_path': 0, 'convert_to_matlab_format': 0,
                         'dict_to_matlab_struct': 0, 'process_single_pair_pivlab': 0, 'convert_back_to_python': 0}
        self.start_time = None
        self.end_time = None
        self.read_time = 0
        self.write_time = 0
        self.matlab_calls_time = 0
        self.matlab_write_results_time = 0
        self.matlab_start_time = 0
        self.matlab_add_path_time = 0

    def start(self):
        self.start_time = time.time()

    def end(self):
        self.end_time = time.time()
        self.summary()

    def summary(self):
        total_time = self.end_time - self.start_time
        print(f"\n=== Performance Summary ===")
        print(f"Total time: {total_time:.2f} seconds")
        for key in self.counters.keys():
            value = self.counters[key]
            print(f"{key} time: {value:.2f} seconds {(value / total_time) * 100:.2f} %")



import time


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

    def inc(self, key, value, process_id):
        self.processes[process_id][key] = value

    def __init__(self):
        self.processes = {}
        self.running_processes = 0
        self.done_processes = 0

    def init_process(self, process_id):
        counters = ['read', 'write', 'matlab_start', 'matlab_add_path', 'convert_to_matlab_format',
                    'dict_to_matlab_struct', 'process_single_pair_pivlab', 'convert_back_to_python']
        default_value = 0
        new_dict = dict.fromkeys(counters, default_value)
        self.processes[process_id] = new_dict

    def start(self, process_id, start_time):
        self.init_process(process_id)
        self.processes[process_id]['start'] = start_time
        self.running_processes += 1

    def end(self, process_id, end_time):
        self.processes[process_id]['end'] = end_time
        self.done_processes += 1
        if self.running_processes == self.done_processes:
            self.summary()

    def find_main_process(self):
        res = None
        for key in self.processes.keys():
            if self.processes[key]['read'] == 0:
                res = key
                break
        if res is None:
            print('!!!!!!!\nMain process was not found. We will not be able to conclude what was the total time taken'
                  ' to perform the computation\n!!!!!!!')
            # Take arbitrary process as main process
            res = [self.processes[next(iter(self.processes.keys()))]]
        return res

    def get_total_time(self):
        res = 0
        current = {}
        if len(self.processes) == 1:
            current = self.processes[next(iter(self.processes.keys()))]
        else:
            current = self.processes[self.find_main_process()]
        return current['end']-current['start']

    def get_processes_order(self):
        res = []
        if len(self.processes) == 1:
            res = [next(iter(self.processes.keys()))]
        else:
            # Find the process with read time 0. That is the main process. We want to display its data first,
            # our main interest is in its total time
            main_process_id = self.find_main_process()
            res.append(main_process_id)
            for key in self.processes.keys():
                if key != main_process_id:
                    res.append(key)
        return res

    def summary(self):
        summary_message = ''
        processes_order = self.get_processes_order()
        print('processes order: ' + str(processes_order))
        for process_id in processes_order:
            current = self.processes[process_id]
            total_time = current['end'] - current['start']
            summary_message += f"\n=== Performance Summary ===\n" + f"Total time: {total_time:.2f} seconds"
            for key in current.keys():
                value = current[key]
                summary_message += f"{key} time: {value:.2f} seconds {(value / total_time) * 100:.2f} %"
        print(summary_message)



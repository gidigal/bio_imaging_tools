import threading
from multiprocessing import Manager
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from queue import Empty
from matlab_integration.python_to_pivlab_streaming import PIVlabStreamProcessor
from works.nd2_worker import ND2Worker
from works.multi_process_report_strategy import MultiProcessReportStrategy
from profiling.profiler import Profiler


def handle_tasks(args):
    (tasks, queue, args_dict) = args
    report_strategy = MultiProcessReportStrategy(queue)
    Profiler.instance().set_print_summary(False)
    Profiler.instance().start(time.time())
    pivlab_stream_processor = None
    should_z_axis_profile = 'z_axis_profile_plot' in args_dict.keys()
    mean_results = []
    if 'matlab_output_dir' in args_dict.keys():
        pivlab_stream_processor = PIVlabStreamProcessor(report_strategy)
    for [multipoint, channel] in tasks:
        nd2_worker = ND2Worker(multipoint, channel, args_dict, report_strategy, pivlab_stream_processor)
        nd2_worker.run()
        if should_z_axis_profile:
            mean_results.append({'multipoint': multipoint, 'channel': channel, 'mean_results': nd2_worker.get_mean_results()})
    queue.put({'type': 'Done'})
    Profiler.instance().end(time.time())
    res = { 'profiler' : Profiler.instance().get_summary_data()}
    if should_z_axis_profile:
        res['z_axis_profile'] = mean_results
    return res


def poll_messages(queue, ui_queue, tasks_number):
    done_processes = 0
    while done_processes != tasks_number:
        try:
            item = queue.get(block=False)
            if item['type'] == 'Done':
                done_processes += 1
            else:
                if item['type'] == 'progress':
                    ui_queue.put(item['progress_type'])
        except Empty:
            time.sleep(0.5)
    ui_queue.put('Quit')


class RunWorkersThread(threading.Thread):
    def __init__(self, multipoint_channel_generator, ui_queue, args_dict):
        super().__init__()
        self.multipoint_channel_generator = multipoint_channel_generator
        self.ui_queue = ui_queue
        self.args_dict = args_dict
        self.profiler_results = None
        self.mean_results = None

    def get_tasks(self):
        cores = os.cpu_count()
        res = []
        core_index = 0
        for [multipoint, channel] in self.multipoint_channel_generator:
            if core_index == len(res):
                res.append([[multipoint, channel]])
            else:
                res[core_index].append([multipoint, channel])
            core_index = (core_index + 1) % cores
        return res

    def run_workers(self):
        tasks = self.get_tasks()
        tasks_number = len(tasks)
        with Manager() as manager:
            queue = manager.Queue()
            args = [(task, queue, self.args_dict) for task in tasks]
            with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
                futures = [executor.submit(handle_tasks, arg) for arg in args]
                poll_messages(queue, self.ui_queue, tasks_number)
                profiler_results = []
                mean_results = []
                for future in as_completed(futures):
                    profiler_results.append(future.result()['profiler'])
                    if 'z_axis_profile_plot' in self.args_dict.keys():
                        mean_results.extend(future.result()['z_axis_profile'])
        mean_results = sorted(mean_results, key=lambda d: (d['multipoint'], d['channel']))
        return [profiler_results, mean_results]

    def run(self):
        [self.profiler_results, self.mean_results] = self.run_workers()

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
from arguments.arguments import Arguments

def handle_tasks(args):
    (tasks, queue, arguments) = args
    Arguments.set_instance(arguments)
    report_strategy = MultiProcessReportStrategy(queue)
    Profiler.instance().set_print_summary(False)
    Profiler.instance().start(time.time())
    pivlab_stream_processor = None
    should_z_axis_profile = arguments.z_axis_profile_plot
    mean_results = []
    if arguments.is_pivlab():
        pivlab_stream_processor = PIVlabStreamProcessor(report_strategy)
    for [multipoint, channel] in tasks:
        nd2_worker = ND2Worker(multipoint, channel, report_strategy, pivlab_stream_processor)
        nd2_worker.run()
        if should_z_axis_profile:
            mean_results.append({'multipoint': multipoint, 'channel': channel, 'mean_results': nd2_worker.get_mean_results()})
    queue.put({'type': 'Done'})
    Profiler.instance().end(time.time())
    res = { 'profiler' : Profiler.instance().get_summary_data()}
    if should_z_axis_profile:
        res['z_axis_profile'] = mean_results
    return res


def poll_messages(queue, ui_queue, tasks_number, abort_event):
    done_processes = 0
    while done_processes != tasks_number:
        if abort_event.is_set():
            return
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
    def __init__(self, multipoint_channel_generator, ui_queue, abort_event):
        super().__init__()
        self.multipoint_channel_generator = multipoint_channel_generator
        self.ui_queue = ui_queue
        self.profiler_results = None
        self.mean_results = None
        self.executor = None
        self.abort_event = abort_event

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
            arguments = Arguments.instance()
            args = [(task, queue, arguments) for task in tasks]
            self.executor = ProcessPoolExecutor(max_workers=os.cpu_count())
            futures = [self.executor.submit(handle_tasks, arg) for arg in args]
            poll_messages(queue, self.ui_queue, tasks_number, self.abort_event)
            if self.abort_event.is_set():
                return [[], []]            
            profiler_results = []
            mean_results = []
            for future in as_completed(futures):
                profiler_results.append(future.result()['profiler'])
                if arguments.z_axis_profile_plot:
                    mean_results.extend(future.result()['z_axis_profile'])
        mean_results = sorted(mean_results, key=lambda d: (d['multipoint'], d['channel']))
        return [profiler_results, mean_results]

    def run(self):
        [self.profiler_results, self.mean_results] = self.run_workers()

    def terminate(self):
        for pid, proc in self.executor._processes.items():
            proc.terminate()
        self.executor.shutdown(wait=False, cancel_futures=True)

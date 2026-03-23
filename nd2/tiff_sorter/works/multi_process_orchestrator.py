from works.orchestrator import Orchestrator
from works.multi_process_report_strategy import MultiProcessReportStrategy
from queue import Queue as ThreadQueue
from queue import Empty
from nd2_tools.nd2_wrapper import ND2Wrapper
from multiprocessing import Manager
import threading
import os
from concurrent.futures import ProcessPoolExecutor
from works.nd2_worker import ND2Worker
import time
from profiling.profiler import Profiler
from gui.progress_window import ProgressWindow
from matlab_integration.python_to_pivlab_streaming import PIVlabStreamProcessor

def handle_tasks(args):
    (tasks, queue, args_dict) = args
    report_strategy = MultiProcessReportStrategy(queue)
    pivlab_stream_processor = PIVlabStreamProcessor(report_strategy)
    for [multipoint, channel] in tasks:
        nd2_worker = ND2Worker(multipoint, channel, args_dict, report_strategy, pivlab_stream_processor)
        nd2_worker.run()
        queue.put({'type': 'Done', 'process_id': os.getpid(), 'reported_time': time.time()})

def poll_messages(queue, ui_queue):
    running_processes = set()
    done_processes = set()
    cores = os.cpu_count()

    while len(done_processes) > 0 and len(done_processes) != len(running_processes):
        try:
            item = self.queue.get(block=False)
            if item['type'] == 'Done':
                done_processes.add(item['process_id'])
                Profiler.instance().end(item['process_id'], item['reported_time'])
            else:
                if item['type'] == 'progress':
                    self.ui_queue.put(item['progress_type'])
                else:
                    if item['type'] == 'profiler':
                        process_id = item['process_id']
                        if process_id not in running_processes:
                            running_processes.add(process_id)
                        Profiler.instance().inc(item['key'], item['reported_time'], item['process_id'])
        except Empty:
            time.sleep(0.5)
        ui_queue.put('Quit')
        print('Polling thread finished its work')


class MultiProcessOrchestrator(Orchestrator):
    def __init__(self, args_dict):
        super().__init__(args_dict)
        self.args_dict = args_dict
        self.ui_queue = ThreadQueue()
        self.nd2_wrapper = ND2Wrapper.instance(args_dict['input_file'])
        self.progress_window = None
        self.pivlab_stream_processor = None

    def get_tasks(self):
        cores = os.cpu_count()
        res = [[] for _ in range(cores)]
        core_index = 0
        for [multipoint, channel] in self.get_multipoint_channel_generator():
            res[core_index].append([multipoint, channel])
            core_index = (core_index + 1) % cores
        return res

    def run_workers(self):
        tasks = self.get_tasks()
        with Manager() as manager:
            queue = manager.Queue()
            args = [(task, queue, self.args_dict) for task in tasks]
            with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:            
                list(executor.map(handle_tasks, args))
            poll_messages(queue, self.ui_queue)

    def run(self):
        Profiler.instance().start(os.getpid(), time.time())
        run_workers_thread = threading.Thread(target=self.run_workers, daemon=True)
        run_workers_thread.start()
        self.progress_window = ProgressWindow(self.progress_data, self.progress_order, self.ui_queue)
        self.progress_window.start()        
        run_workers_thread.join()
        Profiler.instance().end(os.getpid(), time.time())




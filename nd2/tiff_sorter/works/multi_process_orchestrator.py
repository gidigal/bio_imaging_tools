from works.orchestrator import Orchestrator
from works.multi_process_report_strategy import MultiProcessReportStrategy
from queue import Queue as ThreadQueue
from queue import Empty
from nd2_tools.nd2_wrapper import ND2Wrapper
from multiprocessing import Queue as ProcessQueue
import threading
import os
from concurrent.futures import ProcessPoolExecutor
from works.nd2_worker import ND2Worker
import time
from profiling.profiler import Profiler
from gui.progress_window import ProgressWindow

class MultiProcessOrchestrator(Orchestrator):
    def __init__(self, args_dict):
        super().__init__(args_dict)
        self.args_dict = args_dict
        self.queue = ProcessQueue()
        self.ui_queue = ThreadQueue()
        self.nd2_wrapper = ND2Wrapper.instance(args_dict['input_file'])
        self.progress_window = None

    def get_tasks(self):
        cores = os.cpu_count()
        res = [[] for _ in range(cores)]
        core_index = 0
        for [multipoint, channel] in self.get_multipoint_channel_generator():
            res[core_index].append([multipoint, channel])
            core_index = (core_index + 1) % cores
        return res

    def handle_tasks(self, tasks):
        report_strategy = MultiProcessReportStrategy(self.queue)
        for [multipoint, channel] in tasks:
            nd2_worker = ND2Worker(multipoint, channel, self.args_dict, report_strategy, self.pivlab_stream_processor)
            nd2_worker.run()
        self.queue.put({'type': 'Done', 'process_id': os.getpid(), 'reported_time': time.time()})

    def poll_messages(self):
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
        self.ui_queue.put('Quit')
        print('Polling thread finished its work')

    def run_workers(self):
        tasks = self.get_tasks()
        with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
            list(executor.map(self.handle_tasks, tasks))

    def run(self):
        Profiler.instance().start(os.getpid(), time.time())
        run_workers_thread = threading.Thread(target=self.poll_messages, daemon=True)
        run_workers_thread.start()
        polling_thread = threading.Thread(target=self.poll_messages, daemon=True)
        polling_thread.start()
        self.progress_window = ProgressWindow(self.progress_data, self.progress_order, self.ui_queue)
        self.progress_window.start()
        polling_thread.join()
        run_workers_thread.join()
        Profiler.instance().end(os.getpid(), time.time())




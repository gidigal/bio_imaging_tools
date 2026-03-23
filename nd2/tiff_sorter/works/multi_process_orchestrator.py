from works.orchestrator import Orchestrator
from queue import Queue as ThreadQueue
from nd2_tools.nd2_wrapper import ND2Wrapper
import time
from profiling.profiler import Profiler, get_summary_message
from gui.progress_window import ProgressWindow
from works.run_workers_thread import RunWorkersThread


class MultiProcessOrchestrator(Orchestrator):
    def __init__(self, args_dict):
        super().__init__(args_dict)
        self.args_dict = args_dict
        self.ui_queue = ThreadQueue()
        self.nd2_wrapper = ND2Wrapper.instance(args_dict['input_file'])
        self.progress_window = None
        self.pivlab_stream_processor = None

    def run(self):
        Profiler.instance().start(time.time())
        run_workers_thread = RunWorkersThread(self.get_multipoint_channel_generator(), self.ui_queue, self.args_dict)
        run_workers_thread.start()
        self.progress_window = ProgressWindow(self.progress_data, self.progress_order, self.ui_queue)
        self.progress_window.start()        
        run_workers_thread.join()
        Profiler.instance().end(time.time())
        if Profiler.instance().get_print_summary() is True:
            print('Additional processes profiling data:')
            for result in run_workers_thread.results:
                print(get_summary_message(result) + '\n')





from works.orchestrator import Orchestrator
from queue import Queue as ThreadQueue
from nd2_tools.nd2_wrapper import ND2Wrapper
import time
from profiling.profiler import Profiler, get_summary_message
from gui.progress_window import ProgressWindow
from gui.z_axis_profile_window import ZAxisProfileWindow
from works.run_workers_thread import RunWorkersThread
from arguments.arguments import Arguments
import threading

class MultiProcessOrchestrator(Orchestrator):
    def __init__(self):
        super().__init__()
        self.ui_queue = ThreadQueue()
        self.nd2_wrapper = ND2Wrapper.instance(Arguments.instance().input_file)
        self.progress_window = None
        self.pivlab_stream_processor = None

    def get_z_axis_profile_data(self, mean_results):
        res = {}
        for mean_result_entry in mean_results:
            multipoint = mean_result_entry['multipoint']
            channel = mean_result_entry['channel']
            key = f"{multipoint}_{channel}"
            res[key] = mean_result_entry['mean_results']
        return res

    def run(self):
        Profiler.instance().start(time.time())
        abort_event = threading.Event()
        run_workers_thread = RunWorkersThread(self.get_multipoint_channel_generator(),
                                              self.ui_queue,
                                              abort_event)
        run_workers_thread.start()
        self.progress_window = ProgressWindow(self.progress_data, self.progress_order, self.ui_queue)
        self.progress_window.start()
        if self.progress_window.aborted:
            print('aborted')
            abort_event.set()
            run_workers_thread.terminate()
            run_workers_thread.join()
            return
        run_workers_thread.join()
        arguments = Arguments.instance()
        if arguments.z_axis_profile_single_output_file:
            z_axis_profile_data = self.get_z_axis_profile_data(run_workers_thread.mean_results)
            self.save_z_axis_profile_to_single_file(z_axis_profile_data)
        Profiler.instance().end(time.time())

        if Profiler.instance().get_print_summary() is True:
            print('Additional processes profiling data:')
            for result in run_workers_thread.profiler_results:
                print(get_summary_message(result) + '\n')
        if arguments.z_axis_profile_plot is True:
            z_axis_profile_window = ZAxisProfileWindow(run_workers_thread.mean_results, arguments.input_file)
            z_axis_profile_window.start()




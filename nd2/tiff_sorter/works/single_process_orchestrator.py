from works.orchestrator import Orchestrator
from works.single_process_report_strategy import SingleProcessReportStrategy
from nd2_tools.nd2_wrapper import ND2Wrapper
from works.nd2_worker import ND2Worker
from profiling.profiler import Profiler
from matlab_integration.python_to_pivlab_streaming import PIVlabStreamProcessor
from gui.progress_window import ProgressWindow
from gui.z_axis_profile_window import ZAxisProfileWindow
import queue
import threading
import time
import os
from arguments.arguments import Arguments
from matlab_integration.python_to_pivlab_streaming import PIVlabStreamProcessor
from arguments.arguments import Arguments


class SingleProcessOrchestrator(Orchestrator):
    def __init__(self):
        super().__init__()
        arguments = Arguments.instance()
        self.nd2_wrapper = ND2Wrapper.instance(arguments.input_file)
        self.image_series = self.nd2_wrapper.get_multipoints_number()*self.nd2_wrapper.get_channels_number()
        self.report_strategy = None
        self.pivlab_stream_processor = None
        self.velocities = {}
        self.mean_results = None
        self.progress_window = None
        self.queue = queue.Queue()

    def worker_generator(self, multipoints, channels):
        for [multipoint, channel] in self.get_multipoint_channel_generator():
            yield ND2Worker(multipoint, channel, self.report_strategy, self.pivlab_stream_processor)

    def run_workers(self):
        arguments = Arguments.instance()
        z_axis_profile_plot = arguments.z_axis_profile_plot
        self.report_strategy = SingleProcessReportStrategy(self.queue)
        if arguments.matlab_output_dir:
            self.pivlab_stream_processor = PIVlabStreamProcessor(self.report_strategy)
        if z_axis_profile_plot is True:
            self.mean_results = []
        mean_results = {}
        for worker in self.worker_generator(self.nd2_wrapper.get_multipoints_number(),
                                            self.nd2_wrapper.get_channels_number()):
            worker.run()
            if z_axis_profile_plot is True:
                self.mean_results.append({'multipoint': worker.get_multipoint(),
                                          'channel': worker.get_channel(),
                                          'mean_results': worker.get_mean_results()})
            if arguments.z_axis_profile_single_output_file:
                mean_results[f"{worker.get_multipoint()}_{worker.get_channel()}"] = worker.mean_results
        if arguments.z_axis_profile_single_output_file:
            self.save_z_axis_profile_to_single_file(mean_results)
        self.queue.put('Quit')

    def run(self):
        Profiler.instance().start(time.time())
        self.progress_window = ProgressWindow(self.progress_data, self.progress_order, self.queue)
        run_workers_thread = threading.Thread(target=self.run_workers, daemon=True)
        run_workers_thread.start()
        self.progress_window.start()
        if self.progress_window.aborted:
            print('aborted !')
            return
        Profiler.instance().end(time.time())
        arguments = Arguments.instance()
        if arguments.z_axis_profile_plot is True:
            z_axis_profile_window = ZAxisProfileWindow(self.mean_results, arguments.input_file)
            z_axis_profile_window.start()


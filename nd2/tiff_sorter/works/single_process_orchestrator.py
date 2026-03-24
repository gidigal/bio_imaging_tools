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
from matlab_integration.python_to_pivlab_streaming import PIVlabStreamProcessor

class SingleProcessOrchestrator(Orchestrator):
    def __init__(self, args_dict):
        super().__init__(args_dict)
        self.args_dict = args_dict
        self.nd2_wrapper = ND2Wrapper.instance(args_dict['input_file'])
        self.image_series = self.nd2_wrapper.get_multipoints_number()*self.nd2_wrapper.get_channels_number()
        self.report_strategy = None
        self.pivlab_stream_processor = None
        self.velocities = {}
        self.mean_results = None
        self.progress_window = None
        self.queue = queue.Queue()

    def worker_generator(self, args_dict, multipoints, channels):
        for [multipoint, channel] in self.get_multipoint_channel_generator():
            yield ND2Worker(multipoint, channel, args_dict, self.report_strategy, self.pivlab_stream_processor)

    def should_plot_z_axis_profile(self):
        return 'z_axis_profile_plot' in self.args_dict.keys()

    def run_workers(self):
        self.report_strategy = SingleProcessReportStrategy(self.queue)
        if 'matlab_output_dir' in self.args_dict.keys():
            self.pivlab_stream_processor = PIVlabStreamProcessor(self.report_strategy)
        z_axis_profile_plot = self.should_plot_z_axis_profile()
        if z_axis_profile_plot is True:
            self.mean_results = []
        for worker in self.worker_generator(self.args_dict,
                                            self.nd2_wrapper.get_multipoints_number(),
                                            self.nd2_wrapper.get_channels_number()):
            worker.run()
            if z_axis_profile_plot is True:
                self.mean_results.append({'multipoint': worker.get_multipoint(),
                                          'channel': worker.get_channel(),
                                          'mean_results': worker.get_mean_results()})
        self.queue.put('Quit')

    def run(self):
        Profiler.instance().start(time.time())
        self.progress_window = ProgressWindow(self.progress_data, self.progress_order, self.queue)
        threading.Thread(target=self.run_workers, daemon=True).start()
        self.progress_window.start()
        Profiler.instance().end(time.time())
        if 'z_axis_profile_plot' in self.args_dict.keys():
            z_axis_profile_window = ZAxisProfileWindow(self.mean_results, self.args_dict['input_file'])
            z_axis_profile_window.start()


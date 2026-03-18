from works.orchestrator import Orchestrator
from works.single_process_report_strategy import SingleProcessReportStrategy
from nd2_tools.nd2_wrapper import ND2Wrapper
from works.nd2_worker import ND2Worker
from profiling.profiler import Profiler
from matlab_integration.python_to_pivlab_streaming import PIVlabStreamProcessor
from gui.progress_window import ProgressWindow
import queue
import threading


class SingleProcessOrchestrator(Orchestrator):
    def __init__(self, args_dict):
        self.args_dict = args_dict
        self.nd2_wrapper = ND2Wrapper.instance(args_dict['input_file'])
        self.image_series = self.nd2_wrapper.get_multipoints_number()*self.nd2_wrapper.get_channels_number()
        self.report_strategy = None
        self.velocities = {}
        self.pivlab_stream_processor = PIVlabStreamProcessor()
        [self.progress_data, self.progress_order] = self.get_progress_bars_data()
        self.progress_window = None
        self.queue = queue.Queue()

    def get_progress_bars_data(self):
        frames = self.nd2_wrapper.get_total_planes()
        data = { 'Read': {'maximum': frames, 'units': 'frames'} }
        order = ['Read']
        if 'output_dir' in self.args_dict.keys():
            data['Write'] = { 'maximum': frames, 'units': 'frames' }
            order.append('Write')
        if 'matlab_output_dir' in self.args_dict.keys():
            pairs_number = self.nd2_wrapper.get_total_plane_pairs()
            data['Pivlab calls'] = { 'maximum': pairs_number, 'units': 'frame pairs' }
            order.append('Pivlab calls')
        return [data, order]

    def worker_generator(self, args_dict, multipoints, channels):
        for multipoint in range(multipoints):
            for channel in range(channels):
                yield ND2Worker(multipoint, channel, args_dict, self.report_strategy, self.pivlab_stream_processor)

    def run_workers(self):
        self.report_strategy = SingleProcessReportStrategy(self.queue)
        for worker in self.worker_generator(self.args_dict,
                                            self.nd2_wrapper.get_multipoints_number(),
                                            self.nd2_wrapper.get_channels_number()):
            worker.run()
        self.queue.put('Quit')

    def run(self):
        Profiler.instance().start()
        self.progress_window = ProgressWindow(self.progress_data, self.progress_order, self.queue)
        threading.Thread(target=self.run_workers, daemon=True).start()
        self.progress_window.start()
        Profiler.instance().end()
from works.orchestrator import Orchestrator
from works.single_process_report_strategy import SingleProcessReportStrategy
from nd2_tools.nd2_wrapper import ND2Wrapper
from works.nd2_worker import ND2Worker
from profiling.profiler import Profiler
from matlab_integration.python_to_pivlab_streaming import PIVlabStreamProcessor


class SingleProcessOrchestrator(Orchestrator):
    def __init__(self, args_dict):
        self.args_dict = args_dict
        self.nd2_wrapper = ND2Wrapper.instance(args_dict['input_file'])
        total_planes = self.nd2_wrapper.get_total_planes()
        total_pairs = self.nd2_wrapper.get_total_plane_pairs()
        self.image_series = self.nd2_wrapper.get_multipoints_number()*self.nd2_wrapper.get_channels_number()
        self.report_strategy = SingleProcessReportStrategy(total_planes, total_pairs)
        self.velocities = {}
        self.pivlab_stream_processor = PIVlabStreamProcessor()

    def worker_generator(self, args_dict, multipoints, channels):
        for multipoint in range(multipoints):
            for channel in range(channels):
                yield ND2Worker(multipoint, channel, args_dict, self.report_strategy, self.pivlab_stream_processor)

    def run(self):
        Profiler.instance().start()
        for worker in self.worker_generator(self.args_dict,
                                            self.nd2_wrapper.get_multipoints_number(),
                                            self.nd2_wrapper.get_channels_number()):
            worker.run()
        Profiler.instance().end()
from nd2_tools.nd2_wrapper import ND2Wrapper


class ND2Manager:
    def __init__(self):
        self.nd2_wrapper = None

    def get(self, input_file=None):
        if self.nd2_wrapper is not None:
            if input_file != self.nd2_wrapper.get_input_file():
                self.nd2_wrapper.close()
                self.nd2_wrapper = ND2Wrapper(input_file)
        else:
            if input_file is not None:
                self.nd2_wrapper = ND2Wrapper(input_file)
        return self.nd2_wrapper

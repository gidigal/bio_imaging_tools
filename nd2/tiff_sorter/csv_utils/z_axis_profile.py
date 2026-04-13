import io
import csv
from nd2_tools.nd2_wrapper import ND2Wrapper
from arguments.arguments import Arguments


def generate_z_profile_csv(mean_values, experiment_interval_sec):
    arguments = Arguments.instance()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["input file"])
    writer.writerow([arguments.input_file])
    if arguments.z_axis_profile_single_output_file is False:
        writer.writerow(["[sec]", "Mean"])
        for i, mean in enumerate(mean_values):
            writer.writerow([i * experiment_interval_sec, mean])
    else:
        nd2_wrapper = ND2Wrapper.instance(arguments.input_file)
        multipoints = nd2_wrapper.get_multipoints_number()
        channels = nd2_wrapper.get_channels_number()
        channel_names = nd2_wrapper.get_channel_names()
        titles = ["[sec]"]
        for multipoint in range(multipoints):
            for channel in range(channels):
                titles.append(f"{multipoint}\\{channel_names[channel]}")
        writer.writerow(titles)
        for i in range(nd2_wrapper.get_timepoints()):
            row = [i*experiment_interval_sec]
            for multipoint in range(multipoints):
                for channel in range(channels):
                    key = f"{multipoint}_{channel}"
                    row.append(mean_values[key][i])
            writer.writerow(row)
    return buffer.getvalue()
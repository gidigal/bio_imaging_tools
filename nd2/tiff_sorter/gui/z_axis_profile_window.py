from nd2_tools.nd2_wrapper import get_experiment_interval_ms
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from nd2_tools.nd2_wrapper import ND2Wrapper


class ZAxisProfileWindow:
    def __init__(self, mean_results, input_file):
        self.mean_results = mean_results
        self.input_file = input_file
        self.root = None

    def plot_series_in_tabs(self, series_data):
        """
        series_data: list of dicts, each with:
            - 'name': string, used as tab label
            - 'times': list/array of time values in seconds
            - 'means': list/array of mean intensity values
        """

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        for series in series_data:
            # Create a frame for each tab
            frame = ttk.Frame(notebook)
            notebook.add(frame, text=series['name'])

            # Create matplotlib figure
            fig, ax = plt.subplots(figsize=(7, 4))
            ax.plot(series['times'], series['means'], color='steelblue', linewidth=1.5)
            ax.set_xlabel("Time (sec)")
            ax.set_ylabel("Mean Intensity")
            ax.set_title(f"Z-axis Profile — {series['name']}")
            ax.grid(True, linestyle='--', alpha=0.5)
            fig.tight_layout()

            # Embed the figure into the tkinter frame
            canvas = FigureCanvasTkAgg(fig, master=frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def init(self):
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.title("Z-axis Intensity Profiles")
        self.root.geometry("800x500")
        experiment_interval_seconds = get_experiment_interval_ms(self.input_file) / 1000.0
        times = np.arange(len(self.mean_results[0]['mean_results']))*experiment_interval_seconds
        nd2_wrapper = ND2Wrapper.instance(self.input_file)
        channel_names = nd2_wrapper.get_channel_names()
        values_to_plot = []
        for mean_result in self.mean_results:
            data = {}
            multipoint = mean_result['multipoint']
            channel_name = channel_names[mean_result['channel']]
            data['name'] =f"{multipoint}\\{channel_name}"
            data['times'] = times
            data['means'] = mean_result['mean_results']
            values_to_plot.append(data)
        self.plot_series_in_tabs(values_to_plot)

    def on_close(self):
        self.root.quit()  # stops mainloop()
        self.root.destroy()  # destroys the window and all widgets

    def start(self):
        self.init()
        self.root.mainloop()
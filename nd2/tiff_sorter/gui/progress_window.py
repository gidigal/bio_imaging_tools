import tkinter as tk
from tkinter import ttk
import queue


class ProgressWindow:
    def __init__(self, data, order, queue):
        self.root = None
        self.data = data
        self.order = order
        self.queue = queue
        self.progress_bars = {}
        self.progress_bar_frame = None

    def init(self):
        self.progress_bar_frame = tk.Frame(self.root, bg="white", height=100)
        # Configure column weights: column 1 (entries) should expand
        self.progress_bar_frame.grid_columnconfigure(2, weight=1)
        index = 0
        for key in self.data:
            data_entry = self.data[key]
            maximum = data_entry['maximum']
            label = tk.Label(self.progress_bar_frame, bg="white", text=key)
            units = tk.Label(self.progress_bar_frame, bg="white", text=f"0/{maximum} {data_entry['units']}")
            progress_bar = ttk.Progressbar(self.progress_bar_frame, orient=tk.HORIZONTAL, length=160, maximum=maximum)
            label.grid(row=index, column=0, padx=5, pady=5, sticky="E")
            units.grid(row=index, column=1, padx=5, pady=5, sticky="E")
            progress_bar.grid(row=index, column=2, padx=5, pady=5, sticky="EW")
            self.progress_bars[key] = {'progress_bar': progress_bar, 'counter': 0, 'units': units}
            index += 1
        self.progress_bar_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def inc(self, title):
        progress_entry = self.progress_bars[title]
        progress_entry['counter'] += 1
        progress_bar = progress_entry['progress_bar']
        if progress_entry['counter'] != self.data[title]['maximum']:
            progress_bar.step()
        else:
            progress_bar['value'] = progress_bar['maximum']
        progress_entry['units'].config(text=f"{progress_entry['counter']}/{self.data[title]['maximum']} {self.data[title]['units']}")

    def poll_queue(self):
        try:
            msg = self.queue.get_nowait()  # non-blocking check
            if msg == 'Quit':
                self.close()
            else:
                self.inc(msg)
        except queue.Empty:
            pass
        self.root.after(100, self.poll_queue)

    def start(self):
        self.root = tk.Tk()
        self.init()
        self.root.after(100, self.poll_queue)
        self.root.mainloop()

    def close(self):
        self.root.destroy()

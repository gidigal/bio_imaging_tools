import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import RectangleSelector
from functools import partial


class ROIWindow:
    def __init__(self, nd2_wrapper):
        self.images = nd2_wrapper
        self.title = 'Draw Region of Interest for each series'
        self.root = None
        self.paned = None
        self.checkboxes_frame = None
        self.toggle_buttons_frame = None
        self.color_coded_boxes_frame = None
        self.color_coded_buttons = {}
        self.image_buttons = {}
        self.image_visibility = {}
        self.images_frame = None
        self.images_canvas = None
        self.buttons_frame = None
        self.h_scrollbar = None
        self.scrollable_frame = None
        self.roi_selectors = {}
        self.roi_data = {}
        self.start_button = None
        self.hide_button = None
        self.start_hit = False
        self.visibility_vars = {}
        self.image_containers = {}  # Store container references
        self.selection_frames = {}
        self.currently_selected_selection_frame = None
        self.combo_box = None
        self.selected_option_var = None

    # Update scroll region
    def update_scroll_region(self, event=None):
        self.images_canvas.configure(scrollregion=self.images_canvas.bbox("all"))

    def on_select_callback(self, eclick, erelease, multipoint, channel):
        x1, y1 = int(eclick.xdata), int(eclick.ydata)
        x2, y2 = int(erelease.xdata), int(erelease.ydata)
        # Ensure x1 < x2 and y1 < y2 (user might drag backwards)
        x_min, x_max = min(x1, x2), max(x1, x2)
        y_min, y_max = min(y1, y2), max(y1, y2)
        key = f"{multipoint}_{channel}"
        print(f"{key}")
        self.roi_data[key] = (x_min, y_min, x_max, y_max)
        print(f"ROI: ({x_min}, {y_min}) to ({x_max}, {y_max})")

    def add_first_images(self):
        first_images = self.images.get_first_images()
        channel_names = self.images.get_channel_names()  # Get the names
        m_len = self.images.get_multipoints_number()
        c_len = self.images.get_channels_number()
        # For green channel (like NIS-Elements)
        green_cmap = LinearSegmentedColormap.from_list('nis_green',
                                                       [(0, 0, 0), (0, 1, 0)])

        # For magenta channel (like NIS-Elements)
        magenta_cmap = LinearSegmentedColormap.from_list('nis_magenta',
                                                         [(0, 0, 0), (1, 0, 1)])
        channel_cmaps = [green_cmap, magenta_cmap]
        col = 0  # Track column position
        for multipoint in range(m_len):
            for channel in range(c_len):
                key = f"{multipoint}_{channel}"
                self.roi_data[key] = None  # Will store ROI coordinates or None
                current_image = first_images[key]
                container = tk.Frame(self.scrollable_frame, borderwidth=2, relief="groove")
                container.grid(row=1, column=col, padx=10, pady=10)  # Fixed position!
                self.image_containers[key] = container  # Store reference
                # Label
                channel_name = channel_names[channel] if channel < len(channel_names) else f"Ch {channel + 1}"
                lbl = tk.Label(container, text=f"M: {multipoint + 1} / {channel_name}")
                lbl.pack()
                # Matplotlib figure
                # height, width = current_image.shape
                # dpi = 100  # matplotlib default
                # fig, ax = plt.subplots(figsize=(width/dpi, height/dpi), dpi=dpi)  # Specify size!
                fig, ax = plt.subplots(figsize=(7, 7))
                # Auto-scale to use full range
                # vmin = current_image.min()
                # vmax = current_image.max()
                vmin = np.percentile(current_image, 1)
                vmax = np.percentile(current_image, 99.5)
                # channel_cmaps = ['Greens', 'Purples', 'Reds', 'Blues']
                # cmap_to_use = channel_cmaps[channel % len(channel_cmaps)]
                cmap_to_use = channel_cmaps[channel % len(channel_cmaps)]
                ax.imshow(current_image, cmap=cmap_to_use, vmin=vmin, vmax=vmax)
                # ax.imshow(current_image, cmap=cmap_to_use, vmin=vmin, vmax=vmax)
                ax.axis('off')  # Remove axes
                fig.subplots_adjust(left=0, right=1, top=1, bottom=0)  # Force to edges
                # Add RectangleSelector for ROI
                props = dict(
                    facecolor='none',  # No fill! (or use edgecolor only)
                    edgecolor='yellow',  # Border color
                    linewidth=2,  # Border thickness
                    alpha=1.0  # Fully opaque border
                )
                rect_selector = RectangleSelector(
                    ax,
                    partial(self.on_select_callback, multipoint=multipoint, channel=channel),
                    useblit=True,  # Faster drawing
                    button=[1],  # Left mouse button only
                    minspanx=5,  # Minimum rectangle size
                    minspany=5,
                    spancoords='pixels',
                    interactive=True,
                    props=props)
                self.roi_selectors[key] = rect_selector
                # Embed matplotlib in tkinter
                canvas_widget = FigureCanvasTkAgg(fig, master=container)
                canvas_widget.draw()
                canvas_widget.get_tk_widget().pack()
                col += 1  # Next column

    def add_images_frame(self):
        # Don't use PanedWindow - just use regular frames
        self.images_frame = tk.Frame(self.root, bg="lightgray")
        self.images_frame.pack(side="top", fill="both", expand=True)  # Takes all available space

        self.images_canvas = tk.Canvas(self.images_frame)
        self.h_scrollbar = ttk.Scrollbar(self.images_frame, orient="horizontal", command=self.images_canvas.xview)
        self.images_canvas.configure(xscrollcommand=self.h_scrollbar.set)
        self.h_scrollbar.pack(side="bottom", fill="x")
        self.images_canvas.pack(side="top", fill="both", expand=True)
        self.scrollable_frame = tk.Frame(self.images_canvas)
        self.images_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.scrollable_frame.bind("<Configure>",
                                   lambda e: self.images_canvas.configure(scrollregion=self.images_canvas.bbox("all")))

    def toggle_visibility(self):
        if self.checkboxes_frame.winfo_ismapped():
            self.checkboxes_frame.grid_forget()
        else:
            self.checkboxes_frame.grid(row=0, column=0, columnspan=100, sticky="ew", pady=5, padx=5)

    def on_combobox_select(self, event):
        """Event handler for when a combobox item is selected."""
        selected_item = self.combo_box.get()
        newly_selected_frame = self.selection_frames[selected_item]
        print(f"You selected: {selected_item}")
        # Hide the currently selected container and show the newly selected container.
        self.currently_selected_selection_frame.grid_remove()
        self.currently_selected_selection_frame = newly_selected_frame
        self.currently_selected_selection_frame.grid(row=0, column=0, columnspan=100, sticky="ew", pady=5, padx=5)

    def add_display_combo(self, parent):
        # Define the list of options
        OPTIONS = ['Checkboxes', 'Toggle buttons', 'Color coded boxes']
        # Create a StringVar to track the combobox's value
        # This variable can also be used to set the initial value
        self.selected_option_var = tk.StringVar(value=OPTIONS[0])  # Set default value
        # Create the Combobox widget
        self.combo_box = ttk.Combobox(
            parent,
            textvariable=self.selected_option_var,
            values=OPTIONS,
            state="readonly"  # Makes the combobox read-only (users can't type custom values)
        )
        # Bind an event to the combobox
        # The "<<ComboboxSelected>>" virtual event fires when a user selects an item
        self.combo_box.bind("<<ComboboxSelected>>", self.on_combobox_select)
        # Place the widgets in the window
        self.combo_box.pack(pady=20)
        self.combo_box.current(0)

    def add_buttons_frame(self):
        """Add bottom frame with Start button"""
        self.buttons_frame = tk.Frame(self.root, bg="white", height=100)
        self.buttons_frame.pack(side="bottom", fill="x")  # Fixed height at bottom
        self.start_button = tk.Button(self.buttons_frame, text="Start",
                                      command=self.on_start)
        self.start_button.pack(pady=20)
        self.hide_button = tk.Button(self.buttons_frame, text="Hide",
                                      command=self.toggle_visibility)
        self.hide_button.pack(pady=20)
        self.add_display_combo(self.buttons_frame)

    def toggle_image(self, key):
        container = self.image_containers[key]
        is_visible = self.visibility_vars[key].get()

        if is_visible:
            container.grid()  # Show in original position
        else:
            container.grid_remove()  # Hide but preserve grid position

    def add_checkboxes_frame(self):
        self.checkboxes_frame = tk.Frame(self.scrollable_frame, bg="white", relief="raised", borderwidth=2)
        self.currently_selected_selection_frame = self.checkboxes_frame
        self.checkboxes_frame.grid(row=0, column=0, columnspan=100, sticky="ew", pady=5, padx=5)
        tk.Label(self.checkboxes_frame, text="Show/Hide:", bg="lightgray").pack(side="left", padx=5)
        # Create checkbox for each image
        m_len = self.images.get_multipoints_number()
        c_len = self.images.get_channels_number()
        channel_names = self.images.get_channel_names()  # Get the names
        for multipoint in range(m_len):
            for channel in range(c_len):
                key = f"{multipoint}_{channel}"
                var = tk.BooleanVar(value=True)  # Initially checked/visible
                label = f"M: {multipoint + 1} / {channel_names[channel]}"
                cb = tk.Checkbutton(self.checkboxes_frame, text=label, variable=var,
                                    command=lambda k=key, v=var: self.toggle_image(k))
                cb.pack(side="left", padx=2)
                self.visibility_vars[key] = var
        self.selection_frames['Checkboxes'] = self.checkboxes_frame

    def toggle_image_button(self, key):
        # Toggle state
        self.image_visibility[key] = not self.image_visibility[key]
        # Update button appearance
        if self.image_visibility[key]:
            if key in self.image_buttons:
                self.image_buttons[key].config(relief="raised", bg="SystemButtonFace")
            if key in self.color_coded_buttons:
                # Restore original color
                colors = ['green', 'magenta', 'blue', 'red']
                channel = int(key.split('_')[1])
                color = colors[channel % len(colors)]
                self.color_coded_buttons[key].config(relief="raised", bg=color)
        else:
            if key in self.image_buttons:
                self.image_buttons[key].config(relief="sunken", bg="lightgray")
            if key in self.color_coded_buttons:
                self.color_coded_buttons[key].config(relief="sunken", bg="darkgray")
        # Show/hide image container
        container = self.image_containers[key]
        if self.image_visibility[key]:
            container.grid()
        else:
            container.grid_remove()

    def add_toggle_buttons_frame(self):
        self.toggle_buttons_frame = tk.Frame(self.scrollable_frame, bg="white", relief="raised", borderwidth=2)
        self.toggle_buttons_frame.grid(row=0, column=0, columnspan=100, sticky="ew", pady=5, padx=5)
        tk.Label(self.toggle_buttons_frame, text="Show/Hide:", bg="lightgray").pack(side="left", padx=5)
        # Create checkbox for each image
        m_len = self.images.get_multipoints_number()
        c_len = self.images.get_channels_number()
        channel_names = self.images.get_channel_names()  # Get the names
        # Calculate the longest label
        max_width = max(len(f"M: {m + 1} / {channel_names[c]}")
                        for m in range(m_len) for c in range(c_len))
        for multipoint in range(m_len):
            for channel in range(c_len):
                key = f"{multipoint}_{channel}"
                btn = tk.Button(self.toggle_buttons_frame, text=f"M: {multipoint + 1} / {channel_names[channel]}",
                                width=max_width, relief="raised",
                                command=lambda k=key: self.toggle_image_button(k))
                btn.pack(side="left", padx=2)
                self.image_buttons[key] = btn
                self.image_visibility[key] = True
        self.toggle_buttons_frame.grid_forget()
        self.selection_frames["Toggle buttons"] = self.toggle_buttons_frame

    def add_color_coded_boxes_frame(self):
        self.color_coded_boxes_frame = tk.Frame(self.scrollable_frame, bg="white", relief="raised", borderwidth=2)
        self.color_coded_boxes_frame.grid(row=0, column=0, columnspan=100, sticky="ew", pady=5, padx=5)
        tk.Label(self.color_coded_boxes_frame, text="Show/Hide:", bg="lightgray").pack(side="left", padx=5)
        # Create checkbox for each image
        m_len = self.images.get_multipoints_number()
        c_len = self.images.get_channels_number()
        channel_names = self.images.get_channel_names()  # Get the names
        # Get channel color
        colors = ['green', 'magenta', 'blue', 'red']
        for multipoint in range(m_len):
            for channel in range(c_len):
                color = colors[channel % len(colors)]
                key = f"{multipoint}_{channel}"
                # Create colored box button
                btn = tk.Button(self.color_coded_boxes_frame, text=f"M{multipoint + 1}",
                                bg=color, fg="white", width=4, height=1,
                                command=lambda k=key: self.toggle_image_button(k))
                btn.pack(side="left", padx=2)
                self.color_coded_buttons[key] = btn
                self.image_visibility[key] = True
        self.color_coded_boxes_frame.grid_forget()
        self.selection_frames["Color coded boxes"] = self.color_coded_boxes_frame

    def get_roi_data(self):
        return self.roi_data

    def on_start(self):
        self.start_hit = True
        self.on_closing()

    def on_closing(self):
        plt.close('all')  # Close all matplotlib figures
        self.root.destroy()  # Destroy tkinter window

    def start(self):
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.title(self.title)
        self.root.state('zoomed')
        self.add_buttons_frame()
        self.add_images_frame()
        self.add_checkboxes_frame()
        self.add_toggle_buttons_frame()
        self.add_color_coded_boxes_frame()
        self.add_first_images()
        self.root.mainloop()
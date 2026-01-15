import tkinter as tk
from tkinter import filedialog

from matplotlib.colors import LinearSegmentedColormap
from tkinterdnd2 import DND_FILES, TkinterDnD
import os
from gui.settings import settings_instance
from pathlib import Path
from nd2_tools.nd2_wrapper import ND2Wrapper
from tkinter import ttk
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import RectangleSelector
from functools import partial
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class MainWindow:
    def __init__(self, title, nd2_manager):
        self.image_containers = {}
        self.roi_data = {}
        self.roi_selectors = {}
        self.canvas_widgets = {}  # Store canvas widgets for resizing
        self.figure_data = {}  # Store figure data for redrawing
        self.nd2_manager = nd2_manager
        self.images = nd2_manager.get()
        self.scrollable_frame = None
        self.h_scrollbar = None
        self.images_canvas = None
        self.images_frame = None
        self.title = title
        self.root = None
        self.input_file = None
        self.output_dir = None
        self.initialized = False
        self.roi = None
        self.roi_checkbox = None
        self.control_frame = None
        self.input_file_label = None
        self.input_file_edit_box = None
        self.input_file_browse_button = None
        self.output_dir_label = None
        self.output_dir_edit_box = None
        self.output_dir_browse_button = None
        self.start_button = None
        self.start_hit = False
        self.selection_frames = {}
        self.currently_selected_selection_frame = None
        self.selected_option_var = None
        self.roi_images_selection_display_combo = None
        self.visibility_vars = {}
        self.checkboxes_frame = None
        self.image_visibility = {}
        self.image_buttons = {}
        self.color_coded_buttons = {}
        self.toggle_buttons_frame = None
        self.color_coded_boxes_frame = None

    def on_input_file_change(self, var, index, mode):
        self.images = self.nd2_manager.get(input_file=self.input_file.get())

    def init_vars(self):
        self.input_file = tk.StringVar()
        self.input_file.trace_add('write', self.on_input_file_change)
        self.input_file.set(settings_instance.get('input_file'))
        self.output_dir = tk.StringVar()
        self.output_dir.set(settings_instance.get('output_dir'))

    def on_text_change(self, var, index, mode):
        current_value = self.input_file.get()
        self.images = self.nd2_manager.get(input_file=current_value)

    def handle_drop(self, event):
        # event.data contains the path of the dropped file(s)
        print(f"Dropped: {event.data}")
        self.input_file.set(event.data[1:-1])
        settings_instance.set('input_file', self.input_file.get())

        if self.roi.get() == 1:
            images = ND2Wrapper(self.input_file.get())
            first_images = images.get_first_images()
            for key in first_images.keys():
                first_images[key].show()

        current_working_dir = None
        if self.output_dir is None or len(self.output_dir.get()) == 0:
            current_working_dir = os.getcwd()
        else:
            current_working_dir = self.output_dir

        self.output_dir = filedialog.askdirectory(initialdir=current_working_dir,  # Sets the initial directory
                                                    title="Select output directory")  # Sets the dialog title
        if self.input_file is not None and self.output_dir is not None:
            self.initialized = True

        settings_instance.set('output_dir', self.output_dir)

        self.close_window()

    """
    This function is called every time a mouse button is pressed on the window.
    The 'event' object contains details like the click type and coordinates.
    """
    def on_window_click(self, event):
        if event.widget == self.root:
            # print(f"Window clicked at x={event.x}, y={event.y} with button {event.num}")
            current_working_dir = os.getcwd()
            input_file_start_dir = current_working_dir
            if self.input_file is not None and len(self.input_file) > 0:
                file_path = Path(self.input_file)
                input_file_start_dir = file_path.parent
            self.input_file = filedialog.askopenfilename(
                initialdir=input_file_start_dir,  # Sets the initial directory
                title="Select ND2 File",  # Sets the dialog title
                filetypes=(("ND2 files", "*.nd2_tools"),)  # Filters file types
            )
            settings_instance.set('input_file', self.input_file)
            output_dir_start_dir = current_working_dir
            if self.output_dir is not None:
                output_dir_start_dir = self.output_dir
            self.output_dir = filedialog.askdirectory(initialdir=output_dir_start_dir,  # Sets the initial directory
                                                        title="Select output directory")  # Sets the dialog title
            settings_instance.set('output_dir', self.output_dir)
            if self.input_file is not None and self.output_dir is not None:
                self.initialized = True
            self.close_window()

    def get_args(self):
        return [self.input_file.get(), self.output_dir.get(), self.roi_data, self.initialized]

    def close_window(self):
        print("close window")
        # Unbind resize event to prevent it from firing during cleanup
        if self.images_frame is not None:
            self.images_frame.unbind("<Configure>")
        # Clean up matplotlib figures to prevent hanging
        for key in list(self.figure_data.keys()):
            if 'fig' in self.figure_data[key]:
                plt.close(self.figure_data[key]['fig'])
        # Clear all references
        self.canvas_widgets.clear()
        self.figure_data.clear()
        self.roi_selectors.clear()
        self.image_containers.clear()
        settings_instance.save()
        self.root.destroy()

    def on_input_file_browse_button_click(self, event):
        dialog_result = filedialog.askopenfilename(
            initialdir=os.getcwd(),  # Sets the initial directory
            title="Select ND2 File",  # Sets the dialog title
            filetypes=(("ND2 files", "*.nd2"),)  # Filters file types
        )
        self.input_file.set(dialog_result)
        settings_instance.set('input_file', self.input_file.get())

    def on_output_dir_browse_button_click(self, event):
        dialog_result = filedialog.askdirectory(initialdir=os.getcwd(),  # Sets the initial directory
                                title="Select output directory")  # Sets the dialog title
        self.output_dir.set(dialog_result)
        settings_instance.set('output_dir', self.output_dir.get())

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
        # Bind resize event to the images_frame
        self.images_frame.bind("<Configure>", self.on_images_frame_resize)

    def on_select_callback(self, eclick, erelease, multipoint, channel):
        x1, y1 = int(eclick.xdata), int(eclick.ydata)
        x2, y2 = int(erelease.xdata), int(erelease.ydata)
        # Ensure x1 < x2 and y1 < y2 (user might drag backwards)
        x_min, x_max = min(x1, x2), max(x1, x2)
        y_min, y_max = min(y1, y2), max(y1, y2)
        key = f"{multipoint}"
        if channel is not None:
            key += f"_{channel}"
        print(f"{key}")
        if x_min != x_max:
            if '_' in key:
                self.roi_data[key] = (x_min, y_min, x_max, y_max)
            else:
                c_len = self.images.get_channels_number()
                for channel in range(c_len):
                    channel_key = key + f"_{channel}"
                    self.roi_data[channel_key] = (x_min, y_min, x_max, y_max)
                    self.roi_selectors[channel_key].extents = (x_min, x_max, y_min, y_max)
        else:
            del self.roi_data[key]
        print(f"ROI: ({x_min}, {y_min}) to ({x_max}, {y_max})")

    def on_images_frame_resize(self, event):
        """Called when the images_frame is resized"""
        if not hasattr(self, 'image_containers') or not self.image_containers:
            return

        # Get available height for images
        available_height = self.images_frame.winfo_height()
        if available_height <= 1:
            return

        # Calculate size for each container (accounting for scrollbar, padding, etc.)
        # Leave some margin for scrollbar and padding
        target_height = available_height - 40  # Subtract scrollbar height

        # Resize all image containers
        for key in self.image_containers.keys():
            self.resize_image(key, target_height)

    def resize_image(self, key, target_height):
        """Resize a specific image to fit the target height"""
        if key not in self.figure_data:
            return

        fig_data = self.figure_data[key]
        container = self.image_containers[key]

        # Calculate new figure size
        dpi = 100
        label_height = 30
        fig_height = (target_height - label_height - 20) / dpi  # 20px for padding
        fig_width = fig_height  # Keep square aspect ratio

        # Minimum size
        fig_width = max(fig_width, 1)
        fig_height = max(fig_height, 1)

        # Check if size actually changed significantly
        if 'last_width' in fig_data and 'last_height' in fig_data:
            width_diff = abs(fig_data['last_width'] - fig_width)
            height_diff = abs(fig_data['last_height'] - fig_height)
            if width_diff < 0.1 and height_diff < 0.1:
                return

        # Store current size
        fig_data['last_width'] = fig_width
        fig_data['last_height'] = fig_height

        # Close old figure
        if 'fig' in fig_data:
            plt.close(fig_data['fig'])

        # Create new figure
        fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=dpi)
        images = fig_data['images']
        cmaps = fig_data['cmaps']
        vmin_list = fig_data['vmin']
        vmax_list = fig_data['vmax']
        if len(images) == 1:
            # Single channel - display normally
            ax.imshow(images[0], cmap=cmaps[0], vmin=vmin_list[0], vmax=vmax_list[0])
        else:
            composite = self.manual_blending(images, vmin_list, vmax_list)
            ax.imshow(composite)
        ax.set_facecolor('black')
        ax.axis('off')
        fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

        # Recreate RectangleSelector
        props = dict(facecolor='none', edgecolor='yellow', linewidth=2, alpha=1.0)
        rect_selector = RectangleSelector(
            ax,
            partial(self.on_select_callback, multipoint=fig_data['multipoint'],
                    channel=fig_data['channel']),
            useblit=True, button=[1], minspanx=5, minspany=5,
            spancoords='pixels', interactive=True, props=props
        )

        self.roi_selectors[key] = rect_selector
        fig_data['fig'] = fig

        # Update canvas
        if key in self.canvas_widgets:
            old_canvas = self.canvas_widgets[key]
            old_canvas.get_tk_widget().destroy()

        canvas_widget = FigureCanvasTkAgg(fig, master=container)
        canvas_widget.draw()
        canvas_widget.get_tk_widget().pack(fill="both", expand=True)
        self.canvas_widgets[key] = canvas_widget

    def get_first_images_of_all_channels(self, first_images, multipoint):
        c_len = self.images.get_channels_number()
        res = []
        for channel in range(c_len):
            key = f"{multipoint}_{channel}"
            res.append(first_images[key])
        return res

    def manual_blending(self, current_images, vmin, vmax):
        # Multiple channels - manual additive blending
        # Get image shape
        height, width = current_images[0].shape
        # Create RGB composite (height, width, 3)
        composite = np.zeros((height, width, 3), dtype=np.float32)

        # Channel colors: green, magenta, blue, red
        channel_colors = [
            np.array([0, 1, 0]),  # green
            np.array([1, 0, 1]),  # magenta
            np.array([0, 0, 1]),  # blue
            np.array([1, 0, 0])  # red
        ]

        for index in range(len(current_images)):
            # Normalize the image to 0-1 range using its own vmin/vmax
            normalized = np.clip((current_images[index].astype(np.float32) - vmin[index]) / (vmax[index] - vmin[index]),
                                 0, 1)
            # Add this channel's contribution to composite
            color = channel_colors[index % len(channel_colors)]
            composite += normalized[:, :, np.newaxis] * color

        # Clip to valid range
        return np.clip(composite, 0, 1)

    def create_first_image_container(self, multipoint, channel, first_images, channel_names, channel_cmaps, col):
        key = f"{multipoint}_{channel}" if channel is not None else f"{multipoint}"
        current_images = [first_images[key]] if channel is not None else self.get_first_images_of_all_channels(first_images, multipoint)
        container = tk.Frame(self.scrollable_frame, borderwidth=2, relief="groove")
        container.grid(row=1, column=col, padx=10, pady=10, sticky="nsew")  # Added sticky
        self.image_containers[key] = container  # Store reference

        # Configure the grid to allow expansion
        self.scrollable_frame.grid_rowconfigure(1, weight=1)
        self.scrollable_frame.grid_columnconfigure(col, weight=1)

        # Label
        channel_name = ""
        label_text = f"M: {multipoint + 1}"
        if channel is not None:
            channel_name = channel_names[channel] if channel < len(channel_names) else f"Ch {channel + 1}"
            label_text += f" / {channel_name}"
        lbl = tk.Label(container, text=label_text)
        lbl.pack()

        # Calculate initial vmin/vmax
        vmin = []
        vmax = []
        for index in range(len(current_images)):
            vmin.append(np.percentile(current_images[index], 1))
            vmax.append(np.percentile(current_images[index], 99.5))
        cmaps_to_use = [channel_cmaps[channel % len(channel_cmaps)]] if channel is not None else channel_cmaps

        # Store figure data for resizing
        self.figure_data[key] = {
            'images': current_images,
            'cmaps': cmaps_to_use,
            'vmin': vmin,
            'vmax': vmax,
            'multipoint': multipoint,
            'channel': channel
        }

        # Create initial figure
        fig, ax = plt.subplots(figsize=(7, 7))

        # print(
        #     f"Key: {key}, Number of images: {len(current_images)}, vmin: {vmin}, vmax: {vmax}, cmaps: {len(cmaps_to_use)}")

        if len(current_images) == 1:
            # Single channel - display normally
            ax.imshow(current_images[0], cmap=cmaps_to_use[0], vmin=vmin[0], vmax=vmax[0])
        else:
            composite = self.manual_blending(current_images, vmin, vmax)
            ax.imshow(composite)
        ax.set_facecolor('black')  # Ensure black background

        ax.axis('off')
        fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

        # Add RectangleSelector for ROI
        props = dict(
            facecolor='none',
            edgecolor='yellow',
            linewidth=2,
            alpha=1.0
        )
        rect_selector = RectangleSelector(
            ax,
            partial(self.on_select_callback, multipoint=multipoint, channel=channel),
            useblit=True,
            button=[1],
            minspanx=5,
            minspany=5,
            spancoords='pixels',
            interactive=True,
            props=props
        )
        self.roi_selectors[key] = rect_selector
        self.figure_data[key]['fig'] = fig

        # Embed matplotlib in tkinter
        canvas_widget = FigureCanvasTkAgg(fig, master=container)
        canvas_widget.draw()
        canvas_widget.get_tk_widget().pack(fill="both", expand=True)
        self.canvas_widgets[key] = canvas_widget

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
        blue_cmap = LinearSegmentedColormap.from_list('nis_blue',
                                                      [(0, 0, 0), (0, 0, 1)])
        red_cmap = LinearSegmentedColormap.from_list('nis_red',
                                                     [(0, 0, 0), (1, 0, 0)])
        channel_cmaps = [green_cmap, magenta_cmap, blue_cmap, red_cmap]
        col = 0  # Track column position
        for multipoint in range(m_len):
            if c_len > 1:
                self.create_first_image_container(multipoint, None, first_images, channel_names, channel_cmaps, col)
                col += 1
            for channel in range(c_len):
                self.create_first_image_container(multipoint, channel, first_images, channel_names, channel_cmaps, col)
                col += 1  # Next column

    def manage_roi(self, visible=True):
        if visible:
            self.add_images_frame()
            self.add_checkboxes_frame()
            self.add_toggle_buttons_frame()
            self.add_color_coded_boxes_frame()
            self.add_first_images()
        else:
            if self.images_frame is not None:
                # Clean up stored references
                self.canvas_widgets.clear()
                self.figure_data.clear()
                self.image_containers.clear()
                self.roi_selectors.clear()
                self.images_frame.destroy()

    def on_combobox_select(self, event):
        """Event handler for when a combobox item is selected."""
        selected_item = self.roi_images_selection_display_combo.get()
        newly_selected_frame = self.selection_frames[selected_item]
        print(f"You selected: {selected_item}")
        # Hide the currently selected container and show the newly selected container.
        self.currently_selected_selection_frame.grid_remove()
        self.currently_selected_selection_frame = newly_selected_frame
        self.currently_selected_selection_frame.grid(row=0, column=0, columnspan=100, sticky="ew", pady=5, padx=5)

    def add_display_combo(self, parent):
        # Define the list of options
        options = ['Checkboxes', 'Toggle buttons', 'Color coded boxes']
        # Create a StringVar to track the combobox's value
        # This variable can also be used to set the initial value
        self.selected_option_var = tk.StringVar(value=options[0])  # Set default value
        # Create the Combobox widget
        self.roi_images_selection_display_combo = ttk.Combobox(
            parent,
            textvariable=self.selected_option_var,
            values=options,
            state="readonly"  # Makes the combobox read-only (users can't type custom values)
        )
        # Bind an event to the combobox
        # The "<<ComboboxSelected>>" virtual event fires when a user selects an item
        self.roi_images_selection_display_combo.bind("<<ComboboxSelected>>", self.on_combobox_select)
        # Place the widgets in the window
        self.roi_images_selection_display_combo.grid(row=3, column=0, padx=5, pady=5, columnspan=3, sticky="W")
        self.roi_images_selection_display_combo.current(0)

    def on_roi_checkbox_change(self):
        current_state = self.roi.get()
        self.manage_roi(visible=current_state)

    def on_start(self):
        self.start_hit = True
        self.initialized = True
        self.close_window()

    def add_control_frame(self):
        self.control_frame = tk.Frame(self.root, bg="white", height=100)
        self.control_frame.pack(side="bottom", fill="x")

        # Configure column weights: column 1 (entries) should expand
        self.control_frame.grid_columnconfigure(1, weight=1)

        # Add input and output labels/entries/buttons
        self.input_file_label = tk.Label(self.control_frame, bg="white", text="Input file:")
        self.input_file_edit_box = tk.Entry(self.control_frame, textvariable=self.input_file)
        self.input_file_browse_button = tk.Button(self.control_frame, text="...")
        self.output_dir_label = tk.Label(self.control_frame, bg="white", text="Output directory:")
        self.output_dir_edit_box = tk.Entry(self.control_frame, textvariable=self.output_dir)
        self.output_dir_browse_button = tk.Button(self.control_frame, text="...")

        # Grid layout with proper sticky parameters
        self.input_file_label.grid(row=0, column=0, padx=5, pady=5, sticky="E")  # Right-align labels
        self.input_file_edit_box.grid(row=0, column=1, padx=5, pady=5, sticky="EW")  # Stretch horizontally
        self.input_file_browse_button.grid(row=0, column=2, padx=5, pady=5)
        self.output_dir_label.grid(row=1, column=0, padx=5, pady=5, sticky="E")  # Right-align labels
        self.output_dir_edit_box.grid(row=1, column=1, padx=5, pady=5, sticky="EW")  # Stretch horizontally
        self.output_dir_browse_button.grid(row=1, column=2, padx=5, pady=5)

        # Checkbox
        self.roi = tk.BooleanVar()
        self.roi_checkbox = tk.Checkbutton(
            self.control_frame,
            bg="white",
            text="Select Region Of Interest (ROI)",
            variable=self.roi,
            command=self.on_roi_checkbox_change,
            onvalue=1,
            offvalue=0
        )
        self.roi_checkbox.grid(row=2, column=0, padx=5, pady=5, columnspan=3, sticky="W")
        self.start_button = tk.Button(self.control_frame, text="Start",
                                      command=self.on_start)
        self.add_display_combo(self.control_frame)
        self.start_button.grid(row=4, column=0, padx=5, pady=5, columnspan=3, sticky="W")

        # Bind button events
        self.input_file_browse_button.bind('<Button-1>', self.on_input_file_browse_button_click)
        self.output_dir_browse_button.bind('<Button-1>', self.on_output_dir_browse_button_click)

    def toggle_image(self, key):
        container = self.image_containers[key]
        is_visible = self.visibility_vars[key].get()

        if is_visible:
            container.grid()  # Show in original position
        else:
            container.grid_remove()  # Hide but preserve grid position

    def add_check_box(self, multipoint, channel, channel_names):
        key = f"{multipoint}"
        label = f"M: {multipoint + 1}"
        if channel is not None:
            key += f"_{channel}"
            label += f" / {channel_names[channel]}"
        var = tk.BooleanVar(value=True)  # Initially checked/visible
        cb = tk.Checkbutton(self.checkboxes_frame, text=label, variable=var,
                        command=lambda k=key, v=var: self.toggle_image(k))
        cb.pack(side="left", padx=2)
        self.visibility_vars[key] = var


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
            if c_len > 1:
                self.add_check_box(multipoint, None, None)
            for channel in range(c_len):
                self.add_check_box(multipoint, channel, channel_names)
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
                if '_' in key:
                    channel = int(key.split('_')[1])
                    color = colors[channel % len(colors)]
                else:
                    color = "lightgray"
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

    def add_toggle_button(self, multipoint, channel, channel_names, max_width):
        key = f"{multipoint}"
        button_text = f"M: {multipoint + 1}"
        if channel is not None:
            key += f"_{channel}"
            button_text += f"/ {channel_names[channel]}"
        btn = tk.Button(self.toggle_buttons_frame, text=button_text,
                        width=max_width, relief="raised",
                        command=lambda k=key: self.toggle_image_button(k))
        btn.pack(side="left", padx=2)
        self.image_buttons[key] = btn
        self.image_visibility[key] = True

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
            if c_len > 1:
                self.add_toggle_button(multipoint, None, None, max_width)
            for channel in range(c_len):
                self.add_toggle_button(multipoint, channel, channel_names, max_width)
        self.toggle_buttons_frame.grid_forget()
        self.selection_frames["Toggle buttons"] = self.toggle_buttons_frame

    def add_color_coded_box(self, multipoint, channel, colors):
        color = colors[channel % len(colors)] if colors is not None else "lightgray"
        key = f"{multipoint}"
        if channel is not None:
            key += f"_{channel}"
        # Create colored box button
        btn = tk.Button(self.color_coded_boxes_frame, text=f"M{multipoint + 1}",
                        bg=color, fg="white", width=4, height=1,
                        command=lambda k=key: self.toggle_image_button(k))
        btn.pack(side="left", padx=2)
        self.color_coded_buttons[key] = btn
        self.image_visibility[key] = True

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
            if c_len > 1:
                self.add_color_coded_box(multipoint, None, None)
            for channel in range(c_len):
                self.add_color_coded_box(multipoint, channel, colors)
        self.color_coded_boxes_frame.grid_forget()
        self.selection_frames["Color coded boxes"] = self.color_coded_boxes_frame

    def start(self):
        # Create the main window
        self.root = TkinterDnD.Tk()
        self.init_vars()
        self.root.title(self.title)  # Set the window title
        self.root.state('zoomed')
        # self.root.geometry("500x150")  # Set the window size (width x height)

        # Bind the window close event to close_window
        self.root.protocol("WM_DELETE_WINDOW", self.close_window)

        self.root.bind('<Button-1>', self.on_window_click)
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.handle_drop)

        self.add_control_frame()

        # Enter the main event loop
        self.root.mainloop()
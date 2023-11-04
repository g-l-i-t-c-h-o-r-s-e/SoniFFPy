#FFMpeg Realtime Sonification Prototype
#Mostly Generated with GPT-4
#Pandela 2023

import tkinter as tk
from tkinter import ttk
import subprocess
import re
import zmq
import configparser
import json
import sys
import rtmidi
from rtmidi.midiconstants import CONTROL_CHANGE

# Global MIDI variables
midi_input = None
midi_channel_to_slider_map = {}  # Maps (channel, control) tuples to sliders
slider_to_option_map = {}
slider_to_filter_name_map = {}
SEND_TO_ZMQ_ALLOWED = True # Enable slider ZMQ output by default

version = "v1.18"

# If there are any arguments passed (excluding the script name), use the first one.
if len(sys.argv) > 1:
    filter_name = sys.argv[1]
else:
    filter_name = "equalizer"



config_file_path = 'presets.cfg'
config = configparser.ConfigParser()

def save_preset(filter_name, preset_name, values):
    if not config.has_section(filter_name):
        config.add_section(filter_name)
    config.set(filter_name, preset_name, json.dumps(values))
    with open("presets.cfg", "w") as configfile:
        config.write(configfile)

def load_presets(filter_name, preset_name):
    if not config.has_section(filter_name) or not config.has_option(filter_name, preset_name):
        return {}
    values_str = config.get(filter_name, preset_name)
    return json.loads(values_str)


# Load the presets at the beginning
config.read(config_file_path)


# Define the bind address (you can change it as per your needs)
bind_address = 'tcp://localhost:5555'


all_sliders = []
slider_spinbox_map = {}
slider_increment_values = {}  # Dictionary to store the increment values of each slider


# ZMQ initialization at the start
context = zmq.Context()
requester = context.socket(zmq.REQ)
requester.connect(bind_address)
requester.setsockopt(zmq.RCVTIMEO, 5000)  # Set a timeout of 5 seconds for the response

# ZMQ Send function
def send_to_zmq(cmd):
    try:
        requester.send_string(cmd)
        response = requester.recv_string()
        return response
    except zmq.Again as e:
        return "No response from ZMQ server."


def midi_callback(message, data):
    global SEND_TO_ZMQ_ALLOWED  # Declare the global variable
    SEND_TO_ZMQ_ALLOWED = False  # Disable the sliders themselves from sending to ZMQ when they are adjusted with MIDI input
    midi_data, timestamp = message
    message_type, channel_and_control, value = midi_data
    print(f"Received MIDI: Type: {message_type}, Channel and Control: {channel_and_control}, Value: {value}")

    if message_type == CONTROL_CHANGE:
        channel = channel_and_control & 0xF  # Extract MIDI channel from the second byte
        control = channel_and_control >> 4
        print(f"Channel: {channel}, Control: {control}")

        slider = midi_channel_to_slider_map.get((channel, control))
        if slider:
            # Retrieve the option dictionary for this slider
            option = slider_to_option_map.get(slider)
            
            # Retrieve the filter name for this slider
            fname = slider_to_filter_name_map.get(slider)
            
            # Retrieve the index of the filter in ffmpeg filterchain
            fidx = filters_list.index(fname)
            if option:
                option_name = option["name"] # name of option paramter in filter associated with slider
                min_val = option["min"]
                max_val = option["max"]
               
                # Calculate the slider value based on the MIDI value (0-127)
                slider_value = min_val + (value / 127.0) * (max_val - min_val)
                
                # Construct and print the message
                message = f"Parsed_{fname}_{fidx+1} {option_name} {slider_value} "
                slider.set(slider_value) #visually adjust slider in gui
                print(message)
                if send_to_zmq_var.get():
                    response = send_to_zmq(message)
                    print(f"Response from ZMQ: {response}")
                    SEND_TO_ZMQ_ALLOWED = True  # Re-enable sending to ZMQ if needed elsewhere
                else:
                    print(message)
                    SEND_TO_ZMQ_ALLOWED = True  # Re-enable sending to ZMQ if needed elsewhere


def setup_midi():
    global midi_input
    midi_input = rtmidi.MidiIn()
    ports = midi_input.get_ports()
    print(midi_input)
    print(ports)
    
    if ports:
        midi_input.open_port(0)
        midi_input.set_callback(midi_callback)
    else:
        print("No MIDI ports found.")

def midi_assignment_popup(slider):
    def submit():
        channel = int(channel_entry.get())
        control = int(control_entry.get())
        midi_channel_to_slider_map[(channel, control)] = slider
        popup.destroy()

    popup = tk.Toplevel(root)
    popup.title("MIDI Assignment")

    tk.Label(popup, text="Channel (0-15):").grid(row=0, column=0, padx=5, pady=5)
    channel_entry = tk.Entry(popup)
    channel_entry.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(popup, text="Control (0-127):").grid(row=1, column=0, padx=5, pady=5)
    control_entry = tk.Entry(popup)
    control_entry.grid(row=1, column=1, padx=5, pady=5)

    submit_button = tk.Button(popup, text="Assign", command=submit)
    submit_button.grid(row=2, column=0, columnspan=2, padx=10, pady=5)


def get_filter_parameters(filter_name):
    cmd = ["ffmpeg", "-h", f"filter={filter_name}"]
    output = subprocess.check_output(cmd).decode('utf-8')

    match = re.search(r"{} AVOptions:(.+?)(?=\n\n|\Z)".format(filter_name), output, re.DOTALL)
    if not match:
        print(f"No AVOptions found for filter {filter_name}.")
        return []

    options_str = match.group(1).strip()
    options = []

    option_pattern = r"^\s*(\w+)\s+<(\w+)>\s+(.*?)\(from ([-\w\.e+]+|INT_MAX) to ([-\w\.e+]+|INT_MAX)\)\s+\(default ([\w\.e+-]+)\)"
    boolean_pattern = r"^\s*(\w+)\s+<boolean>.*?\(default (\S+)\)"

    # Handling non-boolean options
    for option_match in re.finditer(option_pattern, options_str, re.MULTILINE):
        option_name, option_type, description, min_val, max_val, default_val = option_match.groups()

        if min_val == "INT_MAX":
            min_val = float("99999")
        elif "e" in min_val or "." in min_val:
            min_val = float(min_val)
        else:
            min_val = int(min_val)
            
        if max_val == "INT_MAX":
            max_val = float("99999")
        elif "e" in max_val or "." in max_val:
            max_val = float(max_val)
        else:
            max_val = int(max_val)

        # For default values, if they can't be converted to numbers, set them to 0
        try:
            if "e" in default_val or "." in default_val:
                default_val = float(default_val)
            else:
                default_val = int(default_val)
        except ValueError:
            default_val = 0

        # Extract a clean description from the description string
        description = re.sub(r"^\.\.[A-Z\.]+\s", "", description).strip()

        options.append({
            "name": option_name,
            "type": option_type,
            "description": description,
            "min": min_val,
            "max": max_val,
            "default": default_val
        })

    for boolean_match in re.finditer(boolean_pattern, options_str, re.MULTILINE):
        option_name, default_val = boolean_match.groups()
        options.append({
            "name": option_name,
            "type": "boolean",
            "description": "Enable or disable option",
            "min": 0,
            "max": 1,
            "default": 1 if default_val == "enabled" else 0
        })

    return options


def submit_values(filter_options, filter_name, filter_idx, sliders):
    message = ""
    for option in filter_options:
        slider = sliders[option["name"]]
        value = slider.get()

        if option["type"] == "boolean":
            value = "true" if float(value) == 1 else "false"

        message = f"Parsed_{filter_name}_{filter_idx+1} {option['name']} {value} "
        print(message)
        if send_to_zmq_var.get():
            response = send_to_zmq(message)
            print(f"Response from ZMQ: {response}")
        else:
            print(message)

        

last_clicked_slider = None

def capture_last_clicked(event):
    global last_clicked_slider
    last_clicked_slider = event.widget

def adjust_slider(event):
    global last_clicked_slider
    if last_clicked_slider:
        # Fetch the increment from the slider_increment_values dictionary
        increment = slider_increment_values.get(last_clicked_slider, 1.0)

        if event.keysym == "Right":
            last_clicked_slider.set(last_clicked_slider.get() + increment)
        elif event.keysym == "Left":
            last_clicked_slider.set(last_clicked_slider.get() - increment)



def on_slider_change(option_name, value, option_type, filter_name, filter_idx, send_to_zmq_var):
    global SEND_TO_ZMQ_ALLOWED  # Access the global variable
    message = ""
    if option_type == "boolean":
        value = "true" if float(value) == 1 else "false"
    message = f"Parsed_{filter_name}_{filter_idx+1} {option_name} {value}"

    if send_to_zmq_var.get() and SEND_TO_ZMQ_ALLOWED:
        response = send_to_zmq(message)  # Remove bind_address here
        print(message)
        print(f"Response from ZMQ: {response}")


def reset_sliders():
    for slider, default_value in all_sliders:
        slider.set(default_value)

    if send_on_reset_var.get():
        for filter_name in filters_list:
            filter_options = get_filter_parameters(filter_name)
            sliders = {option["name"]: next((slider for slider, _ in all_sliders if slider.cget("label") == option["name"]), None) for option in filter_options}
            if None in sliders.values():  # check if there's an unmatched option
                print(f"Warning: Some sliders for {filter_name} were not found.")
                continue  # skip this iteration and proceed to the next filter_name
            submit_values(filter_options, filter_name, filters_list.index(filter_name), sliders)


# Tooltip class as defined above
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.id = None
        self.widget.bind("<Enter>", self.showtip)
        self.widget.bind("<Leave>", self.hidetip)

    def showtip(self, event=None):
        "Display the tooltip"
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT, background="yellow", relief=tk.SOLID, borderwidth=1, font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self, event=None):
        "Hide the tooltip"
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()


def create_gui_for_filter(filter_name, tab):
    filter_options = get_filter_parameters(filter_name)
    sliders = {}
    row, column = 0, 0
    

    def show_edit_dialog(event):
        slider = event.widget
        if event.state & 0x1:  # Check for Shift key
            midi_assignment_popup(event.widget)
        else:

            def adjust_increment(event):
                if event.keysym == 'Right':
                    slider.set(slider.get() + float(increment_spinbox.get()))
                elif event.keysym == 'Left':
                    slider.set(slider.get() - float(increment_spinbox.get()))

            def set_slider_value(event=None):
                try:
                    val = float(entry.get())
                    min_val = float(min_entry.get())
                    max_val = float(max_entry.get())

                    if min_val <= val <= max_val:
                        slider.config(from_=min_val, to=max_val, resolution=10**-len(entry.get().split(".")[-1]) if "." in entry.get() else 0)
                        slider.set(val)
                        slider_increment_values[slider] = float(increment_spinbox.get())
                        popup.destroy()
                    else:
                        print("Value is out of the min/max range!")

                except ValueError:
                    # Invalid input, you could show a warning or simply ignore
                    print("Invalid input!")
                    popup.destroy()

            popup = tk.Toplevel(root)
            popup.title("Set Value")
            
            tk.Label(popup, text="Min:").grid(row=0, column=0, padx=5, pady=5)
            min_entry = tk.Entry(popup)
            min_entry.grid(row=0, column=1, padx=5, pady=5)
            min_entry.insert(0, slider.cget('from'))

            tk.Label(popup, text="Max:").grid(row=1, column=0, padx=5, pady=5)
            max_entry = tk.Entry(popup)
            max_entry.grid(row=1, column=1, padx=5, pady=5)
            max_entry.insert(0, slider.cget('to'))

            tk.Label(popup, text="Value:").grid(row=2, column=0, padx=5, pady=5)
            entry = tk.Entry(popup)
            entry.grid(row=2, column=1, padx=5, pady=5)
            entry.bind("<Return>", set_slider_value)

            tk.Label(popup, text="Increment:").grid(row=3, column=0, padx=5, pady=5)
            increment_spinbox = ttk.Spinbox(popup, from_=0.1, to_=10, increment=0.1, width=10)
            increment_spinbox.grid(row=3, column=1, padx=5, pady=5)
            increment_spinbox.set(1.0)  # default increment value
            slider_spinbox_map[slider] = increment_spinbox
            
            slider.bind("<Right>", adjust_increment)
            slider.bind("<Left>", adjust_increment)

            submit_button = tk.Button(popup, text="Submit", command=set_slider_value)
            submit_button.grid(row=4, column=0, columnspan=2, padx=10, pady=5)

            entry.focus_set()

    
    def save_current_preset():
        preset_name = presets_combobox.get()
        if not preset_name:  # Do nothing if name is empty
            return

        values = {name: slider.get() for name, slider in sliders.items()}
        save_preset(filter_name, preset_name, values)

        # Update the combobox values
        if config.has_section(filter_name):
            presets_combobox['values'] = list(config.options(filter_name))
        else:
            presets_combobox['values'] = []

    def load_preset(event=None):
        preset_name = presets_combobox.get()
        values = load_presets(filter_name, preset_name)
        for name, value in values.items():
            sliders[name].set(float(value))

    
    for option in filter_options:
        label = tk.Label(tab, text=option["name"])
        label.grid(row=row, column=column, padx=10, pady=10, sticky='w')

        resolution = 0.1 if option["type"] == "double" else 1
        description = option.get("description", "No description")  # Assumes each option has a description, otherwise defaults to "No description"
        ToolTip(label, description)

        if option["min"] is not None:  # For numeric parameters
            slider = tk.Scale(tab, from_=option["min"], to=option["max"], orient=tk.HORIZONTAL, resolution=resolution, command=lambda value, name=option["name"], opt_type=option["type"], fname=filter_name, fidx=filters_list.index(filter_name): on_slider_change(name, value, opt_type, fname, fidx, send_to_zmq_var))
            slider.set(option["default"])
            slider_to_option_map[slider] = option  # Map the slider to its option dictionary
            slider_to_filter_name_map[slider] = filter_name  # Map the slider to its filter name
            slider.grid(row=row, column=column + 1, padx=10, pady=10)
            slider.bind("<Button-1>", capture_last_clicked)
            slider.bind("<Button-3>", show_edit_dialog)


            # Attach the tooltip to the slider
            #ToolTip(slider, description)

        else:  # For string parameters
            default_text = option["default"]
            label.config(text=f"{option['name']}: {default_text}")
            slider = label  # Assigning the label as a slider for uniformity in processing later

            # If you want to attach the tooltip to the label (for string parameters), uncomment the line below:
            #ToolTip(label, description)

        sliders[option["name"]] = slider
        all_sliders.append((slider, option["default"]))
        column += 2
        if column >= 8:  # Reset for the next row after every 4 sliders
            column = 0
            row += 1

    submit_button = tk.Button(tab, text="Submit", command=lambda: submit_values(filter_options, filter_name, filters_list.index(filter_name), sliders))
    submit_button.grid(row=row+1, column=0, columnspan=8, pady=20)
    filter_options = get_filter_parameters(filter_name)
    save_button = tk.Button(tab, text="Save Preset", command=save_current_preset)
    save_button.grid(row=row+2, column=0, columnspan=2, pady=20, sticky='e')  # We use half the width and align it to the right (east)

    presets_combobox = ttk.Combobox(tab, values=[])
    if config.has_section(filter_name):
        presets_combobox['values'] = list(config.options(filter_name))
    presets_combobox.grid(row=row+2, column=2, columnspan=6, pady=20, sticky='w')  # It now occupies the other half and aligns to the left (west)
    presets_combobox.bind("<<ComboboxSelected>>", load_preset)


root = tk.Tk()
root.title("FFmpeg Realtime Sonification: Beta "+version)
send_on_reset_var = tk.IntVar()  # This variable will store the checkbox state (0 or 1)

notebook = ttk.Notebook(root)
notebook.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

# Use the filter_name variable to create a list of filters
filters_list = [name.strip() for name in filter_name.split(",")]

# Iterate through the filters and create a new tab for each filter
for filter_name in filters_list:
    tab = ttk.Frame(notebook)
    notebook.add(tab, text=filter_name)
    
    # Create the GUI for the filter inside this tab
    create_gui_for_filter(filter_name, tab)

# Create the checkbox only once outside the function
send_to_zmq_var = tk.IntVar()  # This variable will store the checkbox state (0 or 1)
send_to_zmq_checkbox = tk.Checkbutton(root, text="Send to ZMQ", variable=send_to_zmq_var)
send_on_reset_checkbox = tk.Checkbutton(root, text="Send on Reset", variable=send_on_reset_var)
send_on_reset_checkbox.grid(row=3, column=0, padx=10, pady=10, sticky='nsew')
send_to_zmq_checkbox.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')
reset_button = tk.Button(root, text="Reset Sliders", command=reset_sliders)
reset_button.grid(row=2, column=0, padx=10, pady=10, sticky='nsew')


root.bind("<Left>", adjust_slider)
root.bind("<Right>", adjust_slider)
if __name__ == "__main__":
    setup_midi()
    root.mainloop()  # Assuming root is your Tk main window

    # Cleanup MIDI resources
    midi_input.close_port()

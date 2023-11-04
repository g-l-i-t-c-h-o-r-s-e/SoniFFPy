##Generated with GPT4
##Pandela 2023

import tkinter as tk
from tkinter import ttk, messagebox
import re as ree
import subprocess
import configparser

CONFIG_FILE = "settings.cfg"

# Function to load presets from the configuration file
def load_presets():
    config.read(CONFIG_FILE)
    return list(config.sections())

# Function to save the current settings to the configuration file under the given preset name
def save_preset():
    preset_name = preset_combobox.get()
    if not preset_name:
        messagebox.showwarning("Warning", "Enter a preset name!")
        return

    if not config.has_section(preset_name):
        config.add_section(preset_name)

    config[preset_name]['pixel_format'] = pixel_format_combobox.get()
    config[preset_name]['sample_rate'] = sample_rate_combobox.get()
    config[preset_name]['channels'] = channels_combobox.get()
    config[preset_name]['audio_filters'] = audio_filters_combobox.get()
    config[preset_name]['video_device'] = video_device_combobox.get()
    config[preset_name]['extra_options'] = extra_options_entry.get()
    config[preset_name]['custom_command'] = custom_command_text.get("1.0", tk.END).strip() # Save custom command

    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)

    presets = load_presets()
    preset_combobox['values'] = presets
    preset_combobox.set(preset_name)

# Function to load the settings for the given preset name from the configuration file
def load_settings_for_preset(preset_name):
    if config.has_section(preset_name):
        pixel_format_combobox.set(config[preset_name].get('pixel_format', ''))
        sample_rate_combobox.set(config[preset_name].get('sample_rate', ''))
        channels_combobox.set(config[preset_name].get('channels', ''))
        audio_filters_combobox.set(config[preset_name].get('audio_filters', ''))
        video_device_combobox.set(config[preset_name].get('video_device', ''))
        extra_options_entry.delete(0, tk.END)  # Clear existing text
        extra_options_entry.insert(0, config[preset_name].get('extra_options', ''))
        custom_command_text.delete("1.0", tk.END)  # Clear existing text
        custom_command_text.insert("1.0", config[preset_name].get('custom_command', ''))
        toggle_custom_command_state()

# Initialize configparser
config = configparser.ConfigParser()


ffmpeg_process = None

def execute_ffmpeg_command():
    global ffmpeg_process

    # If an ffmpeg process is already running, kill it and its child processes
    if ffmpeg_process and ffmpeg_process.poll() is None:
        try:
            subprocess.run(['taskkill', '/F', '/T', '/PID',  str(ffmpeg_process.pid)])
        except:
            # If taskkill fails (e.g., on non-Windows platforms), use the simple terminate method
            ffmpeg_process.terminate()
        ffmpeg_process = None

    # Kill any running SoniGUI.py processes
    try:
        subprocess.run(['taskkill', '/F', '/IM', 'python.exe', '/FI', 'WINDOWTITLE eq FFmpeg Realtime Sonification*'])
    except Exception as e:
        print(f"Error when trying to kill sonigui.py: {e}")

    
    # Check if we should use the custom command
    if use_custom_command_var.get():
        cmd = custom_command_text.get("1.0", tk.END).strip()  # Fetch command from Text widget
    else:
        pixel_format = pixel_format_combobox.get()
        sample_rate = sample_rate_combobox.get()
        channels = channels_combobox.get()
        audio_filters = audio_filters_combobox.get()
        video_device = video_device_combobox.get()

        extra_options = extra_options_entry.get()
        cmd = f'ffmpeg -log_level 0 -hide_banner -f dshow {extra_options} -i video="{video_device}" -f rawvideo -pix_fmt {pixel_format} -s 640x360 -r 24 -rtbufsize 32 - | ffmpeg -probesize 32 -rtbufsize 32 -loglevel 0 -f u8 -ar {sample_rate} -ac {channels} -i - -filter_complex azmq,{audio_filters} -f u8 -ar {sample_rate} -ac {channels} -rtbufsize 32 - | ffplay -f rawvideo -pixel_format {pixel_format} -video_size 640x360 -framerate 24 -i - -framedrop -an -flags low_delay -probesize 32 -rtbufsize 32 -sync ext' 
        print(cmd)
    
    ffmpeg_process = subprocess.Popen(cmd, shell=True)
    # Extracting and printing the trimmed audio filters
    full_filter_str = audio_filters_combobox.get()
    trimmed_filters = [segment.split('=')[0] for segment in full_filter_str.split(',')]
    target_filters = str(','.join(trimmed_filters))
    
    external_script_cmd = ["python", "SoniGUI.py", target_filters]
    subprocess.Popen(external_script_cmd)


def on_closing():
    global ffmpeg_process
    if ffmpeg_process and ffmpeg_process.poll() is None:
        try:
            subprocess.run(['taskkill', '/F', '/T', '/PID',  str(ffmpeg_process.pid)])
        except:
            ffmpeg_process.terminate()
    root.destroy()

# Run the ffmpeg command to get the list of devices
cmd = "ffmpeg -f dshow -list_devices true -i meme"
result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
ffmpeg_output = result.stderr

# Extract video devices using regular expressions
video_devices = ree.findall(r'"(.*?)" \(video\)', ffmpeg_output)

def on_video_device_selected(event):
    selected_device = video_device_combobox.get()
    print(f"Selected Video Device: {selected_device}")


def preset_selected(event):
    """Load the selected preset's settings"""
    load_settings_for_preset(preset_combobox.get())

def toggle_custom_command_state():
    if use_custom_command_var.get():
        custom_command_text.tag_configure("enabled", foreground="black")  # Normal color
        custom_command_text.tag_remove("disabled", "1.0", tk.END)
        custom_command_text.tag_add("enabled", "1.0", tk.END)
    else:
        custom_command_text.tag_configure("disabled", foreground="red")  # Disabled color
        custom_command_text.tag_remove("enabled", "1.0", tk.END)
        custom_command_text.tag_add("disabled", "1.0", tk.END)


# Create the main window
root = tk.Tk()
root.title("FFmpeg Settings")
root.protocol("WM_DELETE_WINDOW", on_closing)

pixel_formats = ['yuv420p', 'rgb24', 'yuv444p', 'gray']  # Add or remove formats as required
sample_rates = ['44100', '48000', '96000']  # Add or remove rates as required
channels_list = ['1', '2', '3', '4']  # Add or remove channels as required
audio_filters_list = ["acrusher=level_in=1.0:level_out=1.0", "adeclick=window=3", "adeclip", "adecorrelate", "adelay=delays=1000|1000", "adenorm", "aderivative", "adrc", "adynamicequalizer", "adynamicsmooth", "aemphasis=type=RIAA", "aeval", "aexciter=harmonics=3:gain=1", "afade=t=in", "afreqshift=shift=100", "agate", "aintegral", "alatency", "alimiter=level=0", "ametadata", "apad=pad_len=0", "aperms", "aphaseshift", "apsyclip", "asidedata", "asubboost", "asubcut", "asupercut", "asuperpass", "asuperstop", "atilt=f=0:c0=1", "bandpass=f=1000", "bandreject=f=1000", "bass=g=10:f=100", "biquad", "dcshift=shift=0", "deesser=f=3000", "dialoguenhance", "dynaudnorm", "equalizer=f=1000:t=1:g=1", "extrastereo=m=2.5", "highpass=f=1000", "highshelf=g=10:f=1000", "lowpass=f=1000", "lowshelf=g=10:f=1000", "compensationdelay", "crossfeed", "crystalizer=e=2", "speechnorm", "stereotools", "stereowiden=delay=20", "tiltshelf=f=1000:g=10:t=h", "treble=g=10:f=1000", "tremolo=f=10:d=0.5", "vibrato=f=10:d=0.5", "virtualbass=f=40:t=h:g=10", "volume=1"]
extra_optionz = "a"
presets = []

# Video device frame
video_frame = ttk.LabelFrame(root, text="Video Device")
video_frame.pack(pady=10, padx=10, fill="x")

video_device_combobox = ttk.Combobox(video_frame, values=video_devices)
video_device_combobox.grid(row=0, column=0, padx=5, pady=5, columnspan=2)
video_device_combobox.bind("<<ComboboxSelected>>", on_video_device_selected)

# Settings frame
settings_frame = ttk.LabelFrame(root, text="Settings")
settings_frame.pack(pady=10, padx=10, fill="x")

# Pixel Format
ttk.Label(settings_frame, text="Pixel Format:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
pixel_format_combobox = ttk.Combobox(settings_frame, values=pixel_formats)
pixel_format_combobox.grid(row=0, column=1, padx=5, pady=5)

# Sample Rate
ttk.Label(settings_frame, text="Sample Rate:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
sample_rate_combobox = ttk.Combobox(settings_frame, values=sample_rates)
sample_rate_combobox.grid(row=1, column=1, padx=5, pady=5)

# Channels
ttk.Label(settings_frame, text="Channels:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
channels_combobox = ttk.Combobox(settings_frame, values=channels_list)
channels_combobox.grid(row=2, column=1, padx=5, pady=5)

# Audio Filters
ttk.Label(settings_frame, text="Audio Filters:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
audio_filters_combobox = ttk.Combobox(settings_frame, values=audio_filters_list)
audio_filters_combobox.grid(row=3, column=1, padx=5, pady=5)

# Extra Options
ttk.Label(settings_frame, text="Extra Options:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
extra_options_entry = ttk.Entry(settings_frame)
extra_options_entry.insert(0, " -framerate 24 -video_size 640x360 -vcodec mjpeg ")
extra_options_entry.grid(row=4, column=1, padx=5, pady=5)

execute_frame = ttk.Frame(root)
execute_frame.pack(pady=10, padx=10, fill="x")
execute_button = ttk.Button(execute_frame, text="Execute ffmpeg", command=execute_ffmpeg_command)
execute_button.grid(padx=80)

presets_frame = ttk.LabelFrame(root, text="Presets")
presets_frame.pack(pady=10, padx=10, fill="x")
preset_combobox = ttk.Combobox(presets_frame, values=load_presets())
preset_combobox.bind("<<ComboboxSelected>>", preset_selected)

save_button = ttk.Button(presets_frame, text="Save Preset", command=save_preset)
preset_combobox.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
save_button.grid(row=0, column=1, padx=5, pady=5)

# Custom Command section
custom_command_frame = ttk.LabelFrame(root, text="Custom Command")
custom_command_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
use_custom_command_var = tk.BooleanVar()
use_custom_command_checkbox = ttk.Checkbutton(custom_command_frame, text="Enable", variable=use_custom_command_var, command=toggle_custom_command_state)
custom_command_text = tk.Text(custom_command_frame, height=3, width=10)
custom_command_text.insert(tk.END, '''ffmpeg -loglevel 0 -hide_banner -f dshow -framerate 24 -video_size 640x360 -vcodec mjpeg -i video="Logi C615 HD WebCam" -f rawvideo -pix_fmt rgb24 -s 640x360 -r 24 - | ffmpeg  -loglevel 0 -f u8 -ar 44100 -ac 3 -i - -filter_complex "azmq,equalizer=f=1,acrusher" -f u8 -ar 44100 -ac 3 - | ffplay -f rawvideo -pixel_format rgb24 -video_size 640x360 -i - -infbuf''')
custom_command_text.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
use_custom_command_checkbox.grid(row=0, column=1, padx=5, pady=5, sticky="nw")
custom_command_frame.grid_rowconfigure(0, weight=1)
custom_command_frame.grid_columnconfigure(0, weight=1)
toggle_custom_command_state()



# Default values if no preset is loaded
if presets:
    preset_combobox.set(presets[-1])  # Set to last preset
    load_settings_for_preset(presets[-1])
else:
    if video_devices:
        video_device_combobox.set(video_devices[0])
    pixel_format_combobox.set(pixel_formats[0])
    sample_rate_combobox.set(sample_rates[0])
    channels_combobox.set(channels_list[0])
    audio_filters_combobox.set(audio_filters_list[0])

root.mainloop()
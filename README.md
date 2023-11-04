# Requirements
`pip install python-rtmidi zmq`<br>(should be all python modules you need afaik) <br>
<br>
FFmpeg & FFplay in your PATH environment variable (with libzmq support compiled in) <br>
if you're on windows grab a copy [here](https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z), otherwise you'll need to compile it.<br>
You could probably modify my colab [here](https://www.autohotkey.com/download/ahk-install.exe](https://colab.research.google.com/drive/1Wk5eqnr5Cl0qYN6I8cvhS2H0bJpAnquY?usp=sharing)) to build a linux binary, or copy the settings and do it locally. <br>

(loopmidi)[https://www.tobias-erichsen.de/software/loopmidi.html] if you want to use a DAW to control the filters


# Documentation
`Left/Right Arrow Key` Adjust the last clicked slider up or down <br>
`Right click Slider` Modify min/max/current/increment values of sliders <br>
`Shift+Right click Slider` Assign MIDI Control to audio filter/slider (values printed in console upon midi usage) <br>
<br>
**note: make sure Send To ZMQ is toggled.**<br>
MORE TO COME SOON:tm:

# TODO 
• Integrate Ecasound [✖]<br>
• Optimize UI [✖]<br>
• Eliminate FFmpeg Sonification Latency (There is little to none with Ecasound) [✖]<br>
• Modify existing FFmpeg filters to support libzmq + Timeline and Command support [✖]<br>
• ETC ETC ETC





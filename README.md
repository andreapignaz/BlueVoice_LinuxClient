# BlueVoice_LinuxClient
A Python Linux Client for the BlueVoice functionality of ST sensor boards. Tested on ST BlueTile. 

## What's BlueVoice
BlueVoice is an application developed by ST for some of their sensor boards that are equipped with a microphone. With BlueVoice, it is possible to stream audio data from their microphones to a client using only Bluetooth Low Energy technology. 

## What's working
The client will connect to the device and start getting audio data from the device. As soon as the user hits Ctrl+C, the client will disconnect from the board and save a file with the audio sample in int16 format. If you set the 'reproduce' variable accordingly, the recorded audio can be played. 

## Working on
Some problems may arise when reproducing the audio, due to the sounddevice library. Future work is to solve (or workaround) these errors. 

## How to
- Make sure Python 3 is installed on your Linux system. 
- Install the required libraries using pip: `pip install gatt sounddevice`
- Modify the mac address in the .py file with the one you intend to connect to.
- Set the variable 'reproduce' to True if you want to hear the result, False if you only want the file to be saved.
- Open a Terminal and issue the command `python3 client_bluevoice.py`



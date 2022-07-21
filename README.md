# BlueVoice_LinuxClient
A Python Linux Client for the BlueVoice functionality of ST sensor boards. Tested on ST BlueTile. 

## What's BlueVoice
BlueVoice is an application developed by ST for some of their sensor boards that are equipped with a microphone. With BlueVoice, it is possible to stream audio data from their microphones to a client using only Bluetooth Low Energy technology. 

## What's working
The client will connect to the device and start getting audio data from the device. As soon as the user hits Ctrl+C, the client will disconnect from the board and play the recorded data. 

## Working on
The client is fully working. I would like to introduce the possibility to save all the samples to a file. 

## How to
- Make sure Python 3 is installed on your Linux system. 
- Install the required libraries using pip: `pip install gatt sounddevice`
- Modify the mac address in the .py file with the one you intend to connect to.
- Open a Terminal and issue the command `python3 client_bluevoice.py`



import gatt
import signal
import struct
import array
from collections import deque
import sounddevice as sd
import os

# ----------------------------------------------------------------
#
#  CLIENT FOR ST BLUETILE - AUDIO VERSION
#  compile the following fields before running :)
#
# ----------------------------------------------------------------

# to know the name of the bluetooth controller to use, run
#          btmgmt info
# hci0 is the default one.

controller_name = 'hci0'
bluetile_mac = 'F8:71:17:CE:E6:84'
bluetile_name = 'st1'
reproduce = False

# Bluetooth Internal Variables
device1 = 0
aud_char = 0
sync_char = 0
connected = False

# UUIDs corresponding to BlueVoice characteristics
service_uuid = '00000000-0001-11e1-9ab4-0002a5d5c51b'
aud_uuid = '08000000-0001-11e1-ac36-0002a5d5c51b'
sync_uuid = '40000000-0001-11e1-ac36-0002a5d5c51b'

# Sync Variables - Definition and Initialization
sync_index = struct.pack("h", 0)[0]
sync_predSample = struct.pack("i", 0)[0]
sync_intra_flag = False

# Audio Variables - Definition and Initialization
audio_dataPkt = []
audio_audioPkt = deque()

audio_StepSizeTable = [7, 8, 9, 10, 11, 12, 13, 14, 16, 17,
                       19, 21, 23, 25, 28, 31, 34, 37, 41, 45,
                       50, 55, 60, 66, 73, 80, 88, 97, 107, 118,
                       130, 143, 157, 173, 190, 209, 230, 253, 279, 307,
                       337, 371, 408, 449, 494, 544, 598, 658, 724, 796,
                       876, 963, 1060, 1166, 1282, 1411, 1552, 1707, 1878, 2066,
                       2272, 2499, 2749, 3024, 3327, 3660, 4026, 4428, 4871, 5358,
                       5894, 6484, 7132, 7845, 8630, 9493, 10442, 11487, 12635, 13899,
                       15289, 16818, 18500, 20350, 22385, 24623, 27086, 29794, 32767]

audio_IndexTable = [-1, -1, -1, -1, 2, 4, 6, 8, -1, -1, -1, -1, 2, 4, 6, 8]
audio_index = 0
audio_predsample = 0


def update_sync_variables(data):
    global sync_index, sync_predSample, sync_intra_flag

    if len(data) != 6:
        raise NameError('error')

    sync_index = struct.unpack("h", data[0:2])[0]
    sync_predSample = struct.unpack("i", data[2:6])[0]
    sync_intra_flag = True


def audio_decode(code):
    global audio_predsample, sync_predSample, sync_intra_flag, audio_index, sync_index

    if sync_intra_flag:
        audio_predsample = sync_predSample
        audio_index = sync_index
        sync_intra_flag = False

    step = audio_StepSizeTable[audio_index]

    # 2. inverse code into diff
    diffq = step >> 3
    if (code & 4) != 0:
        diffq += step

    if (code & 2) != 0:
        diffq += step >> 1

    if (code & 1) != 0:
        diffq += step >> 2

    # 3. add diff to predicted sample
    if (code & 8) != 0:
        audio_predsample -= diffq

    else:
        audio_predsample += diffq

    # check for overflow
    if audio_predsample > 32767:
        audio_predsample = 32767

    elif audio_predsample < -32768:
        audio_predsample = -32768

    # 4. find new quantizer step size
    audio_index += audio_IndexTable[code]

    # check for overflow
    if audio_index < 0:
        audio_index = 0

    if audio_index > 88:
        audio_index = 88

    # 5. return new speech sample
    return audio_predsample


def extract_and_convert_audio(data):
    global audFile

    if len(data) != 20:
        raise NameError('error: pkt data length wrong')

    for b in data:
        audio_dataPkt.append(audio_decode(b & 0x0F))
        audio_dataPkt.append(audio_decode((b >> 4) & 0x0F))

    audio_audioPkt.append(array.array('h', audio_dataPkt).tobytes())
    for a in audio_dataPkt:
        audFile.write(str(a) + ',')
    audio_dataPkt.clear()


def disconnect_on_exit(signum, frame):
    global audio_audioPkt, device1, manager

    if connected:
        device1.disconnect()
    manager.stop()
    audFile.close()
    if reproduce:
        # TODO These lines produce errors quite easily - improvement: use a try statement.
        play = b''.join(audio_audioPkt)
        sd.default.dtype = 'int16'
        sd.default.channels = 1
        stream = sd.RawOutputStream(samplerate=8000)
        stream.start()
        stream.write(play)
    quit()


class AnyDevice(gatt.Device):
    def connect_succeeded(self):
        global connected
        super().connect_succeeded()
        print("[%s] Connected" % (self.mac_address))
        connected = True

    def connect_failed(self, error):
        super().connect_failed(error)
        print("[%s] Connection failed: %s" % (self.mac_address, str(error)))

    def disconnect_succeeded(self):
        super().disconnect_succeeded()
        print("[%s] Disconnected" % (self.mac_address))

    def characteristic_value_updated(self, characteristic, value):
        # Some checks to verify if I need to update the epoch
        if characteristic.uuid == aud_uuid:
            extract_and_convert_audio(value)
        if characteristic.uuid == sync_uuid:
            update_sync_variables(value)

    def services_resolved(self):
        global aud_char, sync_char    
    
        # Once I receive all the services from the peripheral, I subscribe to the ones I'm interested in
        super().services_resolved()

        sensors_service = next(
            s for s in self.services
            if s.uuid == service_uuid)

        aud_char = next(
            c for c in sensors_service.characteristics
            if c.uuid == aud_uuid)

        aud_char.enable_notifications()

        sync_char = next(
            c for c in sensors_service.characteristics
            if c.uuid == sync_uuid)

        sync_char.enable_notifications()

        print("[%s] Services discovered - Will now stream audio" % (self.mac_address))
        print("To stop sampling and save the file press Ctrl+C")
        print("If you set True to the \'reproduce\' variable, the recorded audio will be played.")


class AnyDeviceManager(gatt.DeviceManager):
    def device_discovered(self, device):
        global device1
        if device.mac_address == bluetile_mac:
            device1 = AnyDevice(mac_address=bluetile_mac, manager=self)
            device1.connect()


# ------------------------------------------------------
# MAIN
# ------------------------------------------------------

# Create a signal: disconnect stop and disconnect on Ctrl+C
signal.signal(signal.SIGINT, disconnect_on_exit)

filename = "output/aud_" + bluetile_name + ".csv"
os.makedirs(os.path.dirname(filename), exist_ok=True)
audFile = open(filename, "w")

# Start the Bluetooth Manager
bluetile_mac = bluetile_mac.lower()
manager = AnyDeviceManager(adapter_name=controller_name)
manager.start_discovery()
# Blocking function: the script will now wait for notifications.
# It will be stopped by disconnect_on_exit() function that can be called with the Ctrl+C signal

manager.run()
# manager.remove_all_devices()

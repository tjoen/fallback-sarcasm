# Funny fallbackskill
# Add more sarcasm to your Mycroft


from mycroft.skills.core import FallbackSkill
from mycroft.util.log import getLogger
from mycroft.api import Api
import tempfile
import subprocess
import os
import math
import random
import struct
import sys
from websocket import create_connection

__author__ = 'tjoen'

LOGGER = getLogger(__name__)

DEFAULT_TEXT = "<volume level='50'><pitch level='180'>"
DEFAULT_LANGUAGE = 'en-GB'
filename = '/tmp/r2d2.wav'
uri = 'ws://localhost:8181/core'

note_freqs = [
    #  C       C#       D      D#      E       F       F#      G       G#      A       A#      B
     16.35,  17.32,  18.35,  19.45,   20.6,  21.83,  23.12,   24.5,  25.96,   27.5,  29.14,  30.87,
      32.7,  34.65,  36.71,  38.89,   41.2,  43.65,  46.25,   49.0,  51.91,   55.0,  58.27,  61.74,
     65.41,   69.3,  73.42,  77.78,  82.41,  87.31,   92.5,   98.0,  103.8,  110.0,  116.5,  123.5,
     130.8,  138.6,  146.8,  155.6,  164.8,  174.6,  185.0,  196.0,  207.7,  220.0,  233.1,  246.9,
     261.6,  277.2,  293.7,  311.1,  329.6,  349.2,  370.0,  392.0,  415.3,  440.0,  466.2,  493.9,
     523.3,  554.4,  587.3,  622.3,  659.3,  698.5,  740.0,  784.0,  830.6,  880.0,  932.3,  987.8,
    1047.0, 1109.0, 1175.0, 1245.0, 1319.0, 1397.0, 1480.0, 1568.0, 1661.0, 1760.0, 1865.0, 1976.0,
    2093.0, 2217.0, 2349.0, 2489.0, 2637.0, 2794.0, 2960.0, 3136.0, 3322.0, 3520.0, 3729.0, 3951.0,
    4186.0, 4435.0, 4699.0, 4978.0, 5274.0, 5588.0, 5920.0, 6272.0, 6645.0, 7040.0, 7459.0, 7902.0,
]

def send_message(type, data):
    ws = create_connection(uri)
    print "Sending " + type + " to " + uri + "..."
    if data:
        data = data
    else:
        data = "{}"
    message = '{"type": "' + type + '", "data": "'+ data +'"}'
    result = ws.send(message)
    print "Receiving..."
    result =  ws.recv()
    print "Received '%s'" % result
    ws.close()

def generate_sin_wave(sample_rate, frequency, duration, amplitude):
    """
    Generate a sinusoidal wave based on `sample_rate`, `frequency`, `duration` and `amplitude`
    `frequency` in Hertz, `duration` in seconds, the values of `amplitude` must be in range [0..1]
    """
    data = []
    samples_num = int(duration * sample_rate)
    volume = amplitude * 32767
    for n in range(samples_num):
        value = math.sin(2 * math.pi * n * frequency / sample_rate)
        data.append(int(value * volume))
    return data

def generate_r2d2_message(filename):
    """
    Generate R2D2 message and save to `filename`
    """
    min_msg_len = 1
    max_msg_len = 20
    r2d2_message = []
    for _ in range(random.randint(min_msg_len, max_msg_len)):
        r2d2_message.append(note_freqs[random.randint(0, len(note_freqs) - 1)])

    sample_rate = 8000  # 8000 Hz
    dot_dur = 0.080  # 80 ms
    volume = 0.10  # 80%

    wave = WaveFile(sample_rate)
    wave_duration = 0
    wave_data = []
    for freq in r2d2_message:
        wave_duration += dot_dur
        wave_data += generate_sin_wave(sample_rate, freq, dot_dur, volume)
    wave.add_data_subchunk(wave_duration, wave_data)
    wave.save(filename)

class WaveFile(object):
    """
    Wave file worker class
    """

    def __init__(self, sample_rate):
        self.subchunk_size = 16   # subchunk data size (16 for PCM)
        self.compression_type = 1 # compression (PCM = 1 [linear quantization])
        self.channels_num = 1     # channels (mono = 1, stereo = 2)
        self.bits_per_sample = 16
        self.block_alignment = self.channels_num * self.bits_per_sample // 8
        self.sample_rate = sample_rate
        self.byte_rate = self.sample_rate * self.channels_num * self.bits_per_sample // 8
        self.duration = 0
        self.data = []

    def add_data_subchunk(self, duration, data):
        self.duration += duration
        self.data += data

    def save(self, filename):
        self.samples_num = int(self.duration * self.sample_rate)
        self.subchunk2_size = self.samples_num * self.channels_num * self.bits_per_sample // 8
        with open(filename, 'wb') as f:
            # write RIFF header
            f.write(b'RIFF')
            f.write(struct.pack('<I', 4 + (8 + self.subchunk_size) + (8 + self.subchunk2_size)))
            f.write(b'WAVE')
            # write fmt subchunk
            f.write(b'fmt ')                                   # chunk type
            f.write(struct.pack('<I', self.subchunk_size))     # data size
            f.write(struct.pack('<H', self.compression_type))  # compression type
            f.write(struct.pack('<H', self.channels_num))      # channels
            f.write(struct.pack('<I', self.sample_rate))       # sample rate
            f.write(struct.pack('<I', self.byte_rate))         # byte rate
            f.write(struct.pack('<H', self.block_alignment))   # block alignment
            f.write(struct.pack('<H', self.bits_per_sample))   # sample depth
            # write data subchunk
            f.write(b'data')
            f.write(struct.pack ('<I', self.subchunk2_size))
            for d in self.data:
                sound_data = struct.pack('<h', d)
                f.write(sound_data)

class SarcasmSkill(FallbackSkill):
    def __init__(self):
        super(SarcasmSkill, self).__init__()

    def initialize(self):
        self.register_fallback(self.handle_fallback, 80)

    def say(self,text,lang):
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            fname = f.name
        cmd = ['pico2wave', '--wave', fname]
        cmd.extend(['-l', lang])
        cmd.append(text)
        with tempfile.TemporaryFile() as f:
            subprocess.call(cmd, stdout=f, stderr=f)
            f.seek(0)
            output = f.read()
        send_message('recognizer_loop:audio_output_start', '{}')
        self.play(fname)
        os.remove(fname)
        send_message('recognizer_loop:audio_output_end', '{}')


    def r2d2talk(self, filename):
        filename = '/tmp/r2d2.wav'
        generate_r2d2_message(filename)
        send_message('recognizer_loop:audio_output_start', '{}')
        self.play(filename)
        os.remove(filename)
        send_message('recognizer_loop:audio_output_end', '{}')

    def play(self,filename):
        cmd = ['aplay', str(filename)]
        with tempfile.TemporaryFile() as f:
            subprocess.call(cmd, stdout=f, stderr=f)
            f.seek(0)
            output = f.read()

    def handle_fallback(self, message):
        txt = message.data.get("utterance")
        SFoptions = self.settings.get('SFoptions', 'default')
        rnd = random.randint(1, 3)
        LOGGER.debug("The message data is: {}".format(message.data))
        if SFoptions == 'default':
            if rnd == 1 or :
                self.say(DEFAULT_TEXT + txt,DEFAULT_LANGUAGE)
            elif rnd == 2:
                self.r2d2talk('/tmp/r2d2.wav')
            else:
                self.speak_dialog('sarcasm', {'talk': txt})
            return True
        elif SFoptions == 'beep':
            self.r2d2talk('/tmp/r2d2.wav')
            return True
        elif SFoptions == 'dialog':
            self.speak_dialog('sarcasm', {'talk': txt})
            return True
        else:
            self.say(DEFAULT_TEXT + txt,DEFAULT_LANGUAGE)
            return True


def create_skill():
    return SarcasmSkill()

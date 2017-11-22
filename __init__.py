# High pitched voiced fallbackskill
# Add more sarcasm to your Mycroft
# Install prereq picotts with 'sudo apt-get libttspico-utils' first

from mycroft.skills.core import FallbackSkill
from mycroft.util.log import getLogger
import tempfile
import subprocess
import os

__author__ = 'tjoen'

LOGGER = getLogger(__name__)

DEFAULT_TEXT = "<volume level='50'><pitch level='200'>"
DEFAULT_LANGUAGE = 'en-GB'

class UnknownSkill(FallbackSkill):
    def __init__(self):
        super(UnknownSkill, self).__init__()

    def initialize(self):
        self.register_fallback(self.handle_fallback, 100)

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
        self.play(fname)
        os.remove(fname)

    def play(self,filename):
        cmd = ['aplay', str(filename)]
        with tempfile.TemporaryFile() as f:
            subprocess.call(cmd, stdout=f, stderr=f)
            f.seek(0)
            output = f.read()

    def handle_fallback(self, message):
        txt = message.data.get("utterance")
        LOGGER.debug("The message data is: {}".format(message.data))
        self.say(DEFAULT_TEXT + txt,DEFAULT_LANGUAGE)
        return True


def create_skill():
    return UnknownSkill()

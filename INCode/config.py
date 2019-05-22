import os
from enum import IntEnum
import json
from json import JSONDecodeError
from configparser import ConfigParser

FILE_NAME = "config.ini"


class Config(ConfigParser):
    LOCAL_ONLY = "localonly"

    def __init__(self):
        super().__init__()
        self.read(FILE_NAME)

    def save(self):
        with open(FILE_NAME, 'w') as config_file:
            self.write(config_file)

    def store(self, option, value):
        self.set(self.default_section, option, str(value))
        self.save()

    def load(self, option):
        if not self.has_option(self.default_section, option):
            return None
        data = None
        try:
            data = self.getboolean(self.default_section, option)
        except Exception:
            data = self.get(self.default_section, option)
        return data

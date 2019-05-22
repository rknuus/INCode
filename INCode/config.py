from configparser import ConfigParser


class Config(ConfigParser):
    LOCAL_ONLY = "localonly"

    def __init__(self, file_name="config.ini"):
        super().__init__()
        self.file_name_ = file_name
        self.read(self.file_name_)

    def save(self):
        with open(self.file_name_, 'w') as config_file:
            self.write(config_file)

    def store(self, option, value):
        self.set(self.default_section, option, str(value))
        self.save()

    def load(self, option):
        if not self.has_option(self.default_section, option):
            return None
        try:
            data = self.getboolean(self.default_section, option)
        except Exception:
            data = self.get(self.default_section, option)
        return data

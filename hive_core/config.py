import yaml
import os

class Config:
    _instance = None

    @classmethod
    def load(cls, mode='hivemind'):
        cls._instance = Config(mode)
        return cls._instance

    def __init__(self, mode='hivemind'):
        config_path = os.path.join(os.path.dirname(__file__), '..', 'configs', f'{mode}.yaml')
        with open(config_path, 'r') as f:
            self.settings = yaml.safe_load(f)

    def get(self, key: str, default=True):
        val = self.settings.get(key, default)
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            return val.lower() in ['on', 'true', 'yes', '1']
        return bool(val)

def is_enabled(key: str) -> bool:
    if Config._instance is None:
        Config.load('hivemind')
    return Config._instance.get(key)

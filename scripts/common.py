#!/usr/bin/env python3

import json
import os
from typing import Any


class Config:  # pylint: disable=too-few-public-methods
    _HOME = os.path.expanduser('~')
    _XDG_CONFIG_HOME = os.environ.get('XDG_CONFIG_HOME') or \
        os.path.join(_HOME, '.config')
    _CONFIG_PATH = os.path.join(_XDG_CONFIG_HOME, 'scripts')

    def __init__(self, config_file: str):
        self._config_file = config_file
        self._config = None

    def get_value(self, key: str) -> Any | None:
        if self._config is None:
            self._config = self._read_config()
        if key in self._config:
            return self._config[key]
        return None

    def _read_config(self) -> dict[str, Any]:
        if os.path.isfile(self._config_file):
            config_path = self._config_file
        elif os.path.isfile(os.path.join(self._CONFIG_PATH, self._config_file)):
            config_path = os.path.join(self._CONFIG_PATH, self._config_file)
        else:
            return {}
        with open(config_path, 'r', encoding='utf-8') as config:
            return json.load(config)

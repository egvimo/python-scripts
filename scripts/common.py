#!/usr/bin/env python3

import json
import logging
import os
from typing import Any


class Config:  # pylint: disable=too-few-public-methods
    _HOME = os.path.expanduser('~')
    _XDG_CONFIG_HOME = os.environ.get('XDG_CONFIG_HOME') or \
        os.path.join(_HOME, '.config')
    _CONFIG_PATH = os.path.join(_XDG_CONFIG_HOME, 'scripts')

    def __init__(self, config_file: str):
        self._config: dict[str, Any] | None = None
        if os.path.isfile(config_file):
            self._config_file = config_file
        elif os.path.isfile(os.path.join(self._CONFIG_PATH, config_file)):
            self._config_file = os.path.join(self._CONFIG_PATH, config_file)
        else:
            self._config_file = None

    def get_config(self) -> dict[str, Any]:
        if self._config is None:
            self._config = self._read_config()
        return self._config

    def set_config(self, config: dict[str, Any]) -> None:
        self._config = config
        with open(self._config_file, 'w', encoding='utf-8') as file:
            return json.dump(config, file)

    def get_value(self, key: str) -> Any | None:
        return self.get_config().get(key, None)

    def _read_config(self) -> dict[str, Any]:
        if self._config_file:
            with open(self._config_file, 'r', encoding='utf-8') as file:
                return json.load(file)
        else:
            return {}


class Logger:

    def __init__(self) -> None:
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self._logger = logging.getLogger('scripts')

    def verbose(self):
        self._logger.setLevel(logging.DEBUG)

    def debug(self, msg, *args, **kwargs) -> None:
        self._logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs) -> None:
        self._logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs) -> None:
        self._logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs) -> None:
        self._logger.error(msg, *args, **kwargs)

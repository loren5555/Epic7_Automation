import time
import logging
import argparse
from dataclasses import dataclass, astuple
from typing import Optional
from pprint import pformat, pprint

import yaml

from E7A.common.utils.dict2str import dict2str


@dataclass
class LoggerConfig:
    # 自定义Logger类的参数
    logger_name: str = "DefaultLogger"
    log_dir: str = "./log"
    log_name: str = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime(time.time()))
    logger_level: int = logging.DEBUG
    console_log: bool = True
    console_log_level: int = logging.NOTSET
    file_log: bool = True
    file_log_level: bool = logging.NOTSET
    fmt: str = "{asctime} | {levelname:<8} | {name:<14} |{message}"
    datefmt: str = "%Y-%m-%d %H:%M:%S"
    propagate: bool = True


@dataclass
class EmulatorConfig:
    vm_index: int = 0
    vm_name: Optional[str] = None


class MetaConfig(type):
    def __str__(self):
        result = {}
        for field_name, fields in self.__dataclass_fields__.items():
            result[field_name] = fields.default.__dict__
        return "Config:" + dict2str(result)


@dataclass
class Config(metaclass=MetaConfig):
    """
    Read configuration from YAML file.
    access to param using Config.section.parameter
    section is the first hierarchy in YAML file.
    parameter is objects in the second hierarchy.
    """
    # Config包含的参数类，自定义参数应在此注册。
    logger: LoggerConfig = LoggerConfig()
    emulator: EmulatorConfig = EmulatorConfig()

    @classmethod
    def load_config(cls, config_file_path: str = "config.yaml") -> None:
        with open(config_file_path, "r") as f:
            config_data: dict = yaml.safe_load(f)

        if config_data is None:
            config_data = {}

        # 解析命令行参数
        parser = argparse.ArgumentParser()
        for section, parameters in config_data.items():
            if isinstance(parameters, dict) is True:
                for parameter, value in parameters.items():
                    parser.add_argument(f"--{section}_{parameter}", default=value, type=type(value))
            # else:
                # parser.add_argument(f"--{section}", default=parameters, type=type(parameters))
            # raise TypeError(f"Section {section} is not a dictionary: params={parameters}. Check the config.py.")
        args = parser.parse_args()

        # 将命令行参数更新至类
        for section, parameters in config_data.items():
            arg_sub_class = getattr(cls, section, )
            for parameter, value in parameters.items():
                arg_value = getattr(args, f"{section}_{parameter}")
                setattr(arg_sub_class, parameter, arg_value)

import yaml
import argparse
import urllib.request
from pprint import pformat
from dataclasses import dataclass, make_dataclass, is_dataclass


class MetaConfig(type):
    """
    Metaclass for Config to handle dynamic attribute creation and pretty printing.
    """
    def __new__(cls, name, bases, dct):
        dct.setdefault('dataclasses_list', [])
        return super().__new__(cls, name, bases, dct)

    def __repr__(self):
        result = {}
        for section in self.dataclasses_list:
            parameters = getattr(self, section)
            if is_dataclass(parameters):
                result.update({section: parameters.__dict__})
            else:
                result.update({section: parameters})
        return pformat(result)


@dataclass
class Config(metaclass=MetaConfig):
    """
    Config class to read and manage configuration from YAML file.
    Access parameters using Config.section.parameter.
    """
    dataclasses_list = []

    @classmethod
    def load_config(cls, config_file_path: str = "config.yaml") -> None:
        """
        Load configuration from a YAML file or URL and update the class attributes.

        :param config_file_path: Path to the YAML file or URL.
        """
        config_data = cls._load_yaml(config_file_path)

        parser = cls._create_arg_parser(config_data)
        args, _ = parser.parse_known_args()

        # 将命令行参数更新至类
        cls._update_class_attributes(config_data, args)

    @staticmethod
    def _load_yaml(config_file_path: str) -> dict:
        """
        Load YAML content from a file or URL.

        :param config_file_path: Path to the YAML file or URL.
        :return: Parsed YAML data as a dictionary.
        """
        if config_file_path.startswith("http"):
            response = urllib.request.urlopen(config_file_path)
            data = response.read().decode("utf-8")
        else:
            with open(config_file_path, "rb") as f:
                data = f.read().decode("utf-8")

        config_data = yaml.safe_load(data)
        return config_data if config_data else {}

    @staticmethod
    def _create_arg_parser(config_data: dict) -> argparse.ArgumentParser:
        """
        Create an argument parser and add arguments based on the config data.

        :param config_data: Configuration data dictionary.
        :return: Argument parser.
        """
        parser = argparse.ArgumentParser(description="Modified config class.")
        for section, parameters in config_data.items():
            if isinstance(parameters, dict):
                for parameter, value in parameters.items():
                    if not parameter.endswith("_help"):
                        parser.add_argument(
                            f"--{section}_{parameter}",
                            default=value,
                            type=type(value),
                            help=config_data[section].get(f"{parameter}_help", "No help provided.")
                        )
            else:
                if not section.endswith("_help"):
                    parser.add_argument(
                        f"--{section}",
                        default=parameters,
                        type=type(parameters),
                        help=config_data.get("_help", {}).get(f"{section}", "No help provided.")
                    )
        return parser

    @classmethod
    def _update_class_attributes(cls, config_data: dict, args: argparse.Namespace) -> None:
        """
        Update the class attributes with the parsed arguments.

        :param config_data: Configuration data dictionary.
        :param args: Parsed arguments.
        """
        for section, parameters in config_data.items():
            if isinstance(parameters, dict) is True:
                # 键, 类型, 默认值
                section_fields = [
                    (parameter, type(value), value)
                    for parameter, value in parameters.items()
                    if not parameter.endswith("_help")
                ]
                # 以section名命名的dataclass类
                SectionClass = make_dataclass(
                    section.capitalize() + "Config", section_fields
                )
                # 用args中的参数初始化数据类.
                section_instance = SectionClass(
                    **{
                        parameter: getattr(args, f"{section}_{parameter}")
                        for parameter in parameters
                        if not parameter.endswith("_help")
                    }
                )
                # 将子数据类设为Config的属性.
                setattr(cls, section, section_instance)
                cls.dataclasses_list.append(section)
            else:
                # 非字典类型参数.
                setattr(cls, section, parameters)
                cls.dataclasses_list.append(section)


if __name__ == "__main__":
    url = (r"https://raw.githubusercontent.com/loren5555/Epic7_Automation/master/config/config.yaml")

    # Config.load_config(url)
    Config.load_config(r"C:\Users\loren\Projects\Epic7_Automation_Python\config\config.yaml")

    print(Config)

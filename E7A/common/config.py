import argparse
from dataclasses import dataclass, make_dataclass, is_dataclass, asdict
from pprint import pprint, pformat

import yaml


class MetaConfig(type):
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
    Read configuration from YAML file.
    access to param using Config.section.parameter
    section is the first hierarchy in YAML file.
    parameter is objects in the second hierarchy.
    """
    dataclasses_list = []

    @classmethod
    def load_config(cls, config_file_path: str = "config.yaml") -> None:
        if config_file_path.startswith("http"):
            # load config from url
            import urllib.request
            url = config_file_path
            response = urllib.request.urlopen(url)
            data = response.read().decode("utf-8")

            config_data = yaml.safe_load(data)
        else:
            # load config from a YAML file.
            with open(config_file_path, "rb") as f:
                config_data: dict = yaml.safe_load(f)

        if config_data is None:
            config_data = {}

        # 解析命令行参数
        parser = argparse.ArgumentParser(description="Modified config class.")
        for section, parameters in config_data.items():
            # section, section parameters dict
            if isinstance(parameters, dict) is True:
                for parameter, value in parameters.items():
                    if parameter.endswith("_help"):
                        continue
                    """
                    Add each key in the parameters' dict.
                    If the key is not a single value, it shouldn't be altered in
                    command line.
                    """
                    parser.add_argument(
                        f"--{section}_{parameter}",
                        default=value,
                        type=type(value),
                        help=config_data[section].get(
                            f"{parameter}_help", "No help provided."
                        )
                    )
            else:
                if section.endswith("_help"):
                    continue
                parser.add_argument(
                    f"--{section}",
                    default=parameters,
                    type=type(parameters),
                    help=config_data.get("_help", {}).get(
                        f"{section}", "No help provided."
                    )
                )
        args = parser.parse_args()

        # 将命令行参数更新至类
        for section, parameters in config_data.items():
            if isinstance(parameters, dict) is True:
                # 键, 类型, 默认值
                section_fields = [
                    (parameter, type(value), value)
                    for parameter, value in parameters.items()
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
    url = (r"https://github.com/loren5555/Epic7_Automation/blob/606902ff18e617145c1eb38f7a8ca3b0cdebff58/config/config.yaml")

    # Config.load_config(url)
    Config.load_config(r"./config.yaml")

    print(Config)

from setuptools import setup, find_packages


setup(
    name='E7A',
    version='0.1',
    packages=find_packages(),
    package_dir={'E7A': 'E7A'},
    install_requires=[
        # 列出项目的依赖，例如：
        'numpy>=2.0.1',
        'opencv-python>=4.10.0.84',
        'PyQt6>=6.4.2',
        'pyyaml>=5.4.1',
        'scrcpy_client>=0.4.7'
    ],
    entry_points={
        'console_scripts': [
            # 如果有命令行脚本的话，可以在这里定义
            # 'your_command=module:function',
        ],
    },
)

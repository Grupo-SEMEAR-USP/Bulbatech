# setup.py
from glob import glob
from setuptools import find_packages, setup

package_name = "voice"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/config", glob("config/*.yaml")),
        ("share/" + package_name + "/launch", glob("launch/*.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    entry_points={
        "console_scripts": [
            "stt_node = voice.stt_node:main",
            "tts_node = voice.tts_node:main",
            "command_node = voice.command_node:main",
            "vitality_node = voice.vitality_node:main",
        ],
    },
)
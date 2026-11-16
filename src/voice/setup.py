# setup.py
import os
from glob import glob
from setuptools import find_packages, setup

package_name = "voice"

# Função auxiliar para mapear pastas inteiras no setup.py
def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append((os.path.join('share/' + package_name, path), [os.path.join(path, filename)]))
    return paths

extra_files = package_files('models')

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/config", glob("config/*.yaml")),
        ("share/" + package_name + "/launch", glob("launch/*.py")),
    ] + package_files('models'),
    install_requires=["setuptools"],
    zip_safe=True,
    entry_points={
        "console_scripts": [
            "stt_node = voice.stt_node:main",
            "tts_node = voice.tts_node:main",
            "engine_node = voice.engine_node:main",        ],
    },
)
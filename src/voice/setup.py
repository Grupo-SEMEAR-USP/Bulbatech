import os
from setuptools import find_packages, setup

package_name = 'voice'

def package_data_files(directory):
    data_files = []

    if not os.path.isdir(directory):
        return data_files

    for root, _, files in os.walk(directory):
        for file_name in files:
            source = os.path.join(root, file_name)
            destination = os.path.join(
                'share',
                package_name,
                root
            )
            data_files.append((destination, [source]))

    return data_files

data_files = [
    (
        'share/ament_index/resource_index/packages',
        ['resource/' + package_name]
    ),
    (
        'share/' + package_name,
        ['package.xml']
    ),
]

# Instala os arquivos preservando a estrutura de config/, models/ e voiceFiles/.
for directory in ['config', 'models', 'voiceFiles']:
    data_files.extend(package_data_files(directory))

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='yobenjas',
    maintainer_email='kauabenjamint@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
        ],
    },
)

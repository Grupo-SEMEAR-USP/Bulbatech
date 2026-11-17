from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'percepcao'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
            ('share/ament_index/resource_index/packages',
                ['resource/' + package_name]),
            ('share/' + package_name, ['package.xml']),
            (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
            (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
            (os.path.join('share', package_name, 'weights'), glob('weights/*.pt')),
        ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='lucas',
    maintainer_email='souza.lucas2@usp.br',
    description='TODO: Package description',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'no_camera = percepcao.no_camera:main',
            'no_detector = percepcao.no_detector:main',
            'no_controlador = percepcao.no_controlador:main',
            'no_localizador = percepcao.no_localizador:main'
        ],
    },
)

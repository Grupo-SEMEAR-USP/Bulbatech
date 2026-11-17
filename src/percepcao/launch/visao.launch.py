from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    no_camera = Node(
        package="percepcao",
        executable="no_camera",
        name="no_camera",
        output="screen",
    )
    no_detector = Node(
        package="percepcao",
        executable="no_detector",
        name="no_detector",
        output="screen",
        parameters=[{"confianca_minima": 0.6}],
    )
    no_controlador = Node(
        package="percepcao",
        executable="no_controlador",
        name="no_controlador",
        output="screen",
    )
    no_localizador = Node(
        package="percepcao",
        executable="no_localizador",
        name="no_localizador",
        output="screen",
        parameters=[{"lado_real_m": 0.03, "foco_px": 0.0}]
    )
    return LaunchDescription([no_camera, no_detector, no_controlador, no_localizador])
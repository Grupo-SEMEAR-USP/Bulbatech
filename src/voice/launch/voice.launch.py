import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import EmitEvent, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch_ros.actions import Node


def generate_launch_description():
    config = os.path.join(
        get_package_share_directory("voice"), "config", "voice.yaml"
    )

    def no(executable):
        return Node(
            package="voice",
            executable=executable,
            name=executable,
            parameters=[config],
            output="screen",
        )

    stt, tts, eng = no("stt_node"), no("tts_node"), no("engine_node")

    # Quando o command_node encerra ("desligar"), derruba todos os outros
    encerrar = RegisterEventHandler(
        OnProcessExit(target_action=eng, on_exit=[EmitEvent(event=Shutdown())])
    )

    return LaunchDescription([stt, tts, eng, encerrar])
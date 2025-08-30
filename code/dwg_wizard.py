#!/usr/bin/env python3
import sys
from typing import Callable
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, pyqtSignal
from classes.dynamic_world_wizard import DynamicWorldWizard


### EXAMPLE OF RUN dwg_wizard.py from outer app and connect exit from outer app to close dwg_wizzard window.
#
# # add module path to sys.path for working local path imports in source module
# DYNAMIC_WORLD_GENERATOR_MODULE_PATH_str = str(DYNAMIC_WORLD_GENERATOR_MODULE_PATH)
# if DYNAMIC_WORLD_GENERATOR_MODULE_PATH_str not in sys.path:
#     sys.path.insert(0, DYNAMIC_WORLD_GENERATOR_MODULE_PATH_str)

# from modules.Dynamic_World_Generator.code.dwg_wizard import run as world_generator_run
# from modules.Dynamic_World_Generator.code.dwg_wizard import dwg_wizard_close_emitter

# def close_callback(close_emitter_instance):
#     # QApplication from outer app
#     QApplication.instance().aboutToQuit.connect(close_emitter_instance.on_app_quit)

# close_emitter = dwg_wizard_close_emitter(close_callback)

# world_generator_run(close_emitter)


class dwg_wizard_close_emitter(QObject):
    app_closed = pyqtSignal()

    def __init__(self, close_callback:Callable = None):
        super().__init__()
        if callable(close_callback):
            close_emitter_instance = self
            close_callback(close_emitter_instance)

    def on_app_quit(self):
        print("Outer app closing, wizard is closing also...\n")
        self.app_closed.emit()


def run(dwg_wizard_close_emitter: dwg_wizard_close_emitter):
    # Initialize and run the application
    if not QApplication.instance():
        app = QApplication(sys.argv)
        wizard = DynamicWorldWizard()
        wizard.show()

        if dwg_wizard_close_emitter:
            dwg_wizard_close_emitter.app_closed.connect(wizard.close)
        app.exec_()
    else:
        print('Dynamic World Wizzard window already open.')


if __name__ == "__main__":
    run()

#!/usr/bin/env python3
import sys
from PyQt5.QtWidgets import QApplication
from classes.dynamic_world_wizard import DynamicWorldWizard


def run():
    # Initialize and run the application
    app = QApplication(sys.argv)
    wizard = DynamicWorldWizard()
    wizard.show()
    app.exec_()


if __name__ == "__main__":
    run()

#!/usr/bin/env python3
import sys
from PyQt5.QtWidgets import QApplication
from classes.dynamic_world_wizard import DynamicWorldWizard

if __name__ == "__main__":
    # Initialize and run the application
    app = QApplication(sys.argv)
    wizard = DynamicWorldWizard()
    wizard.show()
    sys.exit(app.exec_())
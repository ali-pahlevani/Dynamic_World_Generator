#!/usr/bin/env python3
import sys
from PyQt5.QtWidgets import QApplication
from classes.dynamic_world_wizard import DynamicWorldWizard

if __name__ == "__main__":
    print("Entering main block")
    app = QApplication(sys.argv)
    print("QApplication created")
    wizard = DynamicWorldWizard()
    print("DynamicWorldWizard instance created")
    wizard.show()
    print("Wizard shown")
    sys.exit(app.exec_())
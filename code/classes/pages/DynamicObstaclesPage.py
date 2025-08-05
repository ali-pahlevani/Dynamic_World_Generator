from PyQt5.QtWidgets import QWizardPage, QVBoxLayout, QLabel, QMessageBox

class DynamicObstaclesPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Add Dynamic Obstacles")
        self.world_manager = None

        layout = QVBoxLayout()
        layout.addWidget(QLabel("This page is under development."))
        self.setLayout(layout)

    def initializePage(self):
        self.world_manager = self.wizard().world_manager
        if not self.world_manager:
            QMessageBox.warning(self, "Error", "Please select a simulation platform and create/load a world first.")

    def isComplete(self):
        return self.world_manager is not None and self.world_manager.world_name is not None
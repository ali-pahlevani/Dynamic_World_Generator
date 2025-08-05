from PyQt5.QtWidgets import QWizardPage, QVBoxLayout, QPushButton, QLabel, QMessageBox

class SaveResultsPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Save Results")
        self.world_manager = None

        layout = QVBoxLayout()
        self.save_button = QPushButton("Save World")
        self.save_button.clicked.connect(self.save_world)
        layout.addWidget(self.save_button)
        layout.addWidget(QLabel("Preview of future features..."))
        self.setLayout(layout)

    def initializePage(self):
        self.world_manager = self.wizard().world_manager
        if not self.world_manager:
            QMessageBox.warning(self, "Error", "Please select a simulation platform and create/load a world first.")

    def save_world(self):
        if not self.world_manager:
            QMessageBox.warning(self, "Error", "Please select a simulation platform and create/load a world first.")
            return
        try:
            self.world_manager.save_sdf(self.world_manager.world_path)
            QMessageBox.information(self, "Success", f"World saved to {self.world_manager.world_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save world: {str(e)}")

    def isComplete(self):
        return self.world_manager is not None and self.world_manager.world_name is not None
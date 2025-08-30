from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication


def gazebo_not_installed_notice():
    QMessageBox.information(
        QApplication.instance().main_window,
        'Gazebo no found',
        'If you want to see map in runtime install Gazebo but you can go further without it.'
    )  

from PyQt5.QtWidgets import QMainWindow, QApplication, QDockWidget, QListWidget, QTextEdit
import sys
from PyQt5.QtGui import QIcon
from PyQt5 import QtGui
from PyQt5.QtCore import Qt

class DockDialog(QMainWindow):
    def __init__(self):
        super().__init__()
        self.title = "PyQt5 StackedWidget"
        self.top = 200
        self.left = 500
        self.width = 400
        self.height = 300
        self.setWindowIcon(QtGui.QIcon("icon.png"))
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.createDockWidget()
        self.show()
    def createDockWidget(self):
        menubar = self.menuBar()
        file = menubar.addMenu("File")
        file.addAction("New")
        file.addAction("Save")
        file.addAction("Close")
        self.dock = QDockWidget("Dockable", self)
        self.listWiget = QListWidget()
        list = ["Python", "C++", "Java", "C#"]
        self.listWiget.addItems(list)
        self.dock.setWidget(self.listWiget)
        #self.dock.setFloating(False)
        self.setCentralWidget(QTextEdit())
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock)

App = QApplication(sys.argv)
window = DockDialog()
sys.exit(App.exec())

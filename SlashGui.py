import sys
import importlib.util

from PySide import QtGui, QtCore

from .TodoResultTreeModel import ResultTreeModel
from .SlashWrapper import SlashWrapper
from .TodoResultsViewer import TestResultManager
from .MainWindow import Ui_MainWindow
from .LogViewer import LogViewer
# ----------------------------------------------------------------------------------------------------------------------


class ControlMainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(ControlMainWindow, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Connect actions
        self.ui.actionQuit.triggered.connect(ControlMainWindow.Quit)

        # Init log
        LogViewer.setup(self.ui.tabWidgetLog,
                        self.ui.actionActionCloseLogs)

        #Log.mainLog.info("Ready!")

        # Init TestManager
        self.TestManager = SlashWrapper(self.ui.tabWidgetTest,
                                        self.ui.actionStartSet,
                                        self.ui.actionStartTest,
                                        self.ui.actionAbort)

        # Init TestResultManager
        self.result_tree_model = ResultTreeModel(self.ui.TreeViewResults, self.ui.actionTestResultsClicked)
        self.ui.TreeViewResults.setModel(self.result_tree_model)
        self.ui.TreeViewResults.setAlternatingRowColors(True)

        TestResultManager.setup(self.result_tree_model)

        self.restoreGuiState()

    @staticmethod
    def Quit():
        QtGui.qApp.closeAllWindows()

    def closeEvent(self, event):
        self.saveGuiState()

    def saveGuiState(self):
        qsettings = QtCore.QSettings("VF", "SlashGui")

        qsettings.beginGroup("mainWindow")
        qsettings.setValue("geometry", self.saveGeometry())
        qsettings.setValue("maximized", self.isMaximized())
        isMax = self.isMaximized()
        if not self.isMaximized():
            qsettings.setValue("pos", self.pos())
            qsettings.setValue("size", self.size())
        qsettings.endGroup()

    def restoreGuiState(self):
        qsettings = QtCore.QSettings("VF", "SlashGui")

        qsettings.beginGroup("mainWindow")
        # No need for toPoint, etc. : PySide converts types
        self.restoreGeometry(qsettings.value("geometry", self.saveGeometry()))
        self.move(qsettings.value("pos", self.pos()))
        self.resize(qsettings.value("size", self.size()))

        if qsettings.value("maximized", self.isMaximized()) == "true":
            self.showMaximized()

        qsettings.endGroup()

    @staticmethod
    def start():
        app = QtGui.QApplication(sys.argv)
        mySW = ControlMainWindow()
        mySW.show()
        sys.exit(app.exec_())

if __name__ == "__main__":
    ControlMainWindow.start()

import logbook
import slash

from PySide import QtGui

class LogModel:
    tabWidget = None
    systemHandler = None

    @staticmethod
    def setup(tabWidget, actionCloseLogs):
        LogModel.tabWidget = tabWidget
        LogModel.tabWidget.setTabsClosable(True)
        LogModel.tabWidget.tabCloseRequested.connect(LogModel.closeTab)
        actionCloseLogs.triggered.connect(LogModel.closeAllTabs)

        LogModel.systemHandler = LogModel.getLogHandler("System", logbook.INFO, False)

    @staticmethod
    def closeTab(currentIndex):
        if (currentIndex == 0):
            slash.logger.warning("Cannot close the system log")
            return

        LogModel.tabWidget.removeTab(currentIndex)

    @staticmethod
    def closeAllTabs():
        for i in range(LogModel.tabWidget.count() - 1):
            LogModel.tabWidget.removeTab(1)

    @staticmethod
    def getLogHandler(name, level=logbook.INFO, bubble=True):
        listView = QtGui.QListView(LogModel.tabWidget)
        LogModel.tabWidget.addTab(listView, name)
        LogModel.tabWidget.setCurrentWidget(listView)

        listViewHandler = ListViewHandler(listView, level, bubble)
        return listViewHandler

class ListViewHandler(logbook.Handler):
    def __init__(self, listView, level=logbook.INFO, bubble=True):
        super().__init__(level=level, bubble=bubble)

        self.listView = listView
        self.modelLog = QtGui.QStandardItemModel(self.listView)
        self.listView.setModel(self.modelLog)

        self.font = QtGui.QFont("Courier New", 9, QtGui.QFont.Light)

    def emit(self, record):
        line = self.format(record)

        item = QtGui.QStandardItem(line)

        if record.level == logbook.DEBUG or record.level == logbook.INFO:
            item.setForeground(QtGui.QColor("black"))
#        elif record.level == loglevel_SUCCESS:
#            item.setForeground(QtGui.QColor("green"))
        elif record.level == logbook.WARNING:
            item.setForeground(QtGui.QColor("orange"))
        elif record.level == logbook.ERROR or record.level == logbook.CRITICAL:
            item.setForeground(QtGui.QColor("red"))

        self.font.setBold(record.level == logbook.CRITICAL)

        item.setFont(self.font)
        self.modelLog.appendRow(item)

    def write(self, m):
        pass

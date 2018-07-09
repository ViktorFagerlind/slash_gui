from queue import Queue, Empty
from PySide import QtGui, QtCore

import logbook
import slash

# ----------------------------------------------------------------------------------------------------------------------


class LogViewer:
    tabWidget = None
    systemHandler = None

    @staticmethod
    def setup(tabWidget, actionCloseLogs):
        LogViewer.tabWidget = tabWidget
        LogViewer.tabWidget.setTabsClosable(True)
        LogViewer.tabWidget.tabCloseRequested.connect(LogViewer.closeTab)
        actionCloseLogs.triggered.connect(LogViewer.closeAllTabs)

        LogViewer.systemHandler = LogViewer.getLogHandler("System", logbook.INFO, False)

    @staticmethod
    def closeTab(currentIndex):
        if (currentIndex == 0):
            slash.logger.warning("Cannot close the system log")
            return

        LogViewer.tabWidget.removeTab(currentIndex)

    @staticmethod
    def closeAllTabs():
        for i in range(LogViewer.tabWidget.count() - 1):
            LogViewer.tabWidget.removeTab(1)

    @staticmethod
    def getLogHandler(name, level=logbook.INFO, bubble=True):
        listView = QtGui.QListView(LogViewer.tabWidget)
        LogViewer.tabWidget.addTab(listView, name)
        LogViewer.tabWidget.setCurrentWidget(listView)

        listViewHandler = ListViewLogHandler(listView, level, bubble)
        return listViewHandler
# ----------------------------------------------------------------------------------------------------------------------


class ListViewLogHandler(logbook.Handler):
    def __init__(self, listView, level=logbook.INFO, bubble=True):
        super().__init__(level=level, bubble=bubble)
        self.formatter = logbook.StringFormatter('[{record.time:%H:%M:%S}] {record.message}')

        self.listView = listView
        self.modelLog = QtGui.QStandardItemModel(self.listView)
        self.listView.setModel(self.modelLog)

        self.font = QtGui.QFont("Courier New", 9, QtGui.QFont.Light)

        self.timer = QtCore.QTimer(listView)
        self.message_queue = Queue()
        self.threaded = False

    def emit(self, record):
        self.message_queue.put({'line': str(self.format(record)), 'level': record.level})
        if not self.threaded:
            self._updateLogWindow()

    def enterThreadedMode(self, refresh_rate_ms=20):
        #print('enterThreadedMode')
        self.timer.timeout.connect(self._updateLogWindow)
        self.timer.start(refresh_rate_ms)
        self.threaded = True

    def exitThreadedMode(self):
        #print('exitThreadedMode')
        self.timer.timeout.disconnect(self._updateLogWindow)
        self.timer.stop()
        self._updateLogWindow()
        self.threaded = False

    def _updateLogWindow(self):
        try:
            while True:
                message = self.message_queue.get(False)
                line = message['line']
                level = message['level']

                item = QtGui.QStandardItem(line)
                if level == logbook.DEBUG or level == logbook.INFO:
                    item.setForeground(QtGui.QColor("black"))
                elif level == logbook.WARNING:
                    item.setForeground(QtGui.QColor("orange"))
                elif level == logbook.ERROR or level == logbook.CRITICAL:
                    item.setForeground(QtGui.QColor("red"))

                self.font.setBold(level == logbook.CRITICAL)

                item.setFont(self.font)
                self.modelLog.appendRow(item)

        except Empty:
            pass

        self.listView.scrollToBottom()

    def write(self, m):
        pass
# ----------------------------------------------------------------------------------------------------------------------


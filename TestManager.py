from slash.frontend.slash_run import slash_run
from slash.loader import Loader
from slash.utils.suite_files import iter_suite_file_paths
from PySide import QtGui
from LogModel import LogModel

import sys
import slash
import glob
import logbook
import re
import colorama
import os

# ---- TestManager -----------------------------------------------------------------------------------------------------

def get_filenames_from_dir(wildcard, dir):
    result = []
    sys.path.append(dir)

    file_names = glob.glob(dir + wildcard)
    for fn in file_names:
        split_name = fn.split('\\')
        result.append(fn.split('\\')[-1])

    return result

class Test:
    def __init__(self, filepath, tests):
        self.filepath = filepath
        self.display_name = filepath.split('\\')[-1]
        for t,o in tests.items():
            self.display_name += '\n   ' + t + '  ' + o


class TestSuite:
    def __init__(self, name, test_paths, cmd, listView):
        self.name = name
        self.cmd = cmd
        self.tests = []
        for fp,tests in test_paths.items():
            self.tests.append(Test(fp,tests))

        # Init test list view
        self.list_view = listView
        self.model_tests = QtGui.QStandardItemModel(self.list_view)
        self.list_view.setModel(self.model_tests)

        self.refresh_gui()

    def start(self):
        slash.logger.info('Start suit: slash run ' + self.cmd)
        slash_run(self.cmd.split())

    def startTest(self):
        selected_items = self.list_view.selectedIndexes()
        if (len(selected_items) != 1):
            slash.logger.error("No test selected!")
            return

        cmd = self.tests[selected_items[0].row()].filepath

        slash.logger.info('Start single test file: slash run ' + cmd)
        slash_run([cmd])


    def refresh_gui(self):
        self.model_tests.clear()
        for t in self.tests:
            item = QtGui.QStandardItem(t.display_name)
            self.model_tests.appendRow(item)

class TestManager:
    def __init__(self, tabWidget, actionStartSuit, actionStartTest, actionAbort):

        self.tabWidget = tabWidget

        colorama.init()

        test_dir = 'tests/'
        suit_dir = 'suits/'

        actionStartTest.triggered.connect(self.startTest)
        actionStartSuit.triggered.connect(self.startSuit)
        actionAbort.triggered.connect(TestManager.Abort)

        suit_filenames = get_filenames_from_dir('*.suit', suit_dir)

        self.suites = []
        self.add_test_suite('All', TestManager.get_tests_from_dirs([test_dir]), test_dir)

        for sfn in suit_filenames:
            path_tuples = []
            path_tuples.extend(iter_suite_file_paths([suit_dir + sfn]))
            paths = [pt[0] for pt in path_tuples]
            self.add_test_suite(sfn.split('.')[0], TestManager.get_tests_from_dirs(paths), '-f ' + suit_dir + sfn)

    def __del__(self):
        pass#Log.mainLog.pop_application()


    @staticmethod
    def get_tests_from_dirs(dirs):
        tests = {}
        with slash.Session():
            runnables = Loader().get_runnables(dirs)

            for r in runnables:
                rel_path = os.path.relpath(r.__slash__.address, '.')
                full_name = rel_path.split('\\')[-1]
                if not ('(' in full_name):
                    full_name += '()'

                p = re.compile(r'(.*):(.*)(\(.*\))')
                items = p.findall(full_name)

                filename = items[0][0]
                filepath = os.path.dirname(rel_path) + '\\' + filename
                testname = items[0][1]
                opt = items[0][2]

                if filepath in tests:
                    if testname in tests[filepath]:
                        tests[filepath][testname] += ' ' + opt
                    else:
                        tests[filepath][testname] = opt
                else:
                    tests[filepath] = {testname:opt}
        return tests

    def add_test_suite(self, suite_name, test_runnables, cmd):
        list_view = QtGui.QListView(self.tabWidget)
        test_suite = TestSuite(suite_name, test_runnables, cmd, list_view)
        self.tabWidget.addTab(list_view, suite_name)
        self.suites.append(test_suite)

    @staticmethod
    @slash.hooks.session_start.register
    def session_start_handlder():
        LogModel.systemHandler.push_application()
        slash.logger.handlers.insert(0, LogModel.systemHandler)
        slash.logger.info("Session started: " + str(slash.context.session))

    @staticmethod
    @slash.hooks.session_end.register
    def session_end_handlder():
        slash.logger.info("Session ended: " + str(slash.context.session))
        slash.logger.handlers.remove(LogModel.systemHandler)
        LogModel.systemHandler.pop_application()

    handlers = {}

    @staticmethod
    @slash.hooks.test_start.register
    def test_start_handlder():
        #slash.logger.info("Test started: " + str(slash.context.test_id))

        handler = LogModel.getLogHandler(slash.test.__slash__.function_name + ' #' + str(slash.context.test.__slash__.test_index1),
                                         logbook.INFO,
                                         False)
        slash.logger.handlers.insert(0,handler)
        TestManager.handlers[slash.context.test_id] = handler

    @staticmethod
    @slash.hooks.test_end.register
    def test_end_handlder():
        handler = TestManager.handlers[slash.context.test_id]
        slash.logger.handlers.remove(handler)
        del TestManager.handlers[slash.context.test_id]

        #slash.logger.info("Test ended: " + str(slash.context.test_id))

    def startTest(self):
        self.suites[self.tabWidget.currentIndex()].startTest()

    def startSuit(self):
        self.suites[self.tabWidget.currentIndex()].start()

    @staticmethod
    def Abort():
        slash.logger.warning("Abort")

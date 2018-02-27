from slash.loader import Loader
from slash.utils.suite_files import iter_suite_file_paths
from PySide import QtGui, QtCore
from enum import IntEnum
from threading import Event

import sys
import slash
import glob
import logbook
import re
import colorama
import os
import threading
import time

from .LogModel import LogModel


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
    def __init__(self, name, test_paths, listView):
        self.name = name
        self.tests = []
        for fp,tests in test_paths.items():
            self.tests.append(Test(fp,tests))

        # Init test list view
        self.list_view = listView
        self.model_tests = QtGui.QStandardItemModel(self.list_view)
        self.list_view.setModel(self.model_tests)

        self.refresh_gui()

    @staticmethod
    def slash_runner_thread(test_files):
        #slash_run(args)
        with slash.Session() as session:
                print('XXX Start session')
                tests = Loader().get_runnables(test_files)
                with session.get_started_context():
                    slash.run_tests(tests)
                print('XXX End session')

    @staticmethod
    def run_slash_in_thread(args):
        t = threading.Thread(target=TestSuite.slash_runner_thread, args=(args,))
        t.start()
        #TestSuite.slash_runner_thread(args)

    def start(self):
        slash.logger.info('Start suit: ' + self.name)
        test_paths = [t.filepath for t in self.tests]
        TestSuite.run_slash_in_thread(test_paths)

    def start_test(self):
        selected_items = self.list_view.selectedIndexes()
        if (len(selected_items) != 1):
            slash.logger.error("No test selected!")
            return

        testfile = self.tests[selected_items[0].row()].filepath

        slash.logger.info('Start single test file: slash run ' + testfile)
        TestSuite.run_slash_in_thread([testfile])


    def refresh_gui(self):
        self.model_tests.clear()
        for t in self.tests:
            item = QtGui.QStandardItem(t.display_name)
            self.model_tests.appendRow(item)



class TestManager:
    def __init__(self, tab_widget, action_start_suit, action_start_test, action_abort):
        self.tabWidget = tab_widget

        slash.logger.handlers.insert(0, LogModel.systemHandler)

        colorama.init()

        test_dir = 'src/tests/'
        suit_dir = 'suits/'

        action_start_test.triggered.connect(self.start_test)
        action_start_suit.triggered.connect(self.start_suit)
        action_abort.triggered.connect(TestManager.abort)

        suit_filenames = get_filenames_from_dir('*.suit', suit_dir)

        self.suites = []
        self.add_test_suite('All', TestManager.get_tests_from_dirs([test_dir]))

        for sfn in suit_filenames:
            path_tuples = []
            path_tuples.extend(iter_suite_file_paths([suit_dir + sfn]))
            paths = [pt[0] for pt in path_tuples]
            self.add_test_suite(sfn.split('.')[0], TestManager.get_tests_from_dirs(paths))

    def __del__(self):
        pass

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

    def add_test_suite(self, suite_name, test_runnables):
        list_view = QtGui.QListView(self.tabWidget)
        test_suite = TestSuite(suite_name, test_runnables, list_view)
        self.tabWidget.addTab(list_view, suite_name)
        self.suites.append(test_suite)

    def start_test(self):
        self.suites[self.tabWidget.currentIndex()].start_test()

    def start_suit(self):
        self.suites[self.tabWidget.currentIndex()].start()

    @staticmethod
    def abort():
        print("Abort")
        # TODO not implemented

# -- These handlers are invoked by the slash hooks but run in the GUI thread -------------------------------------------

event = Event()
handlers = {}

@QtCore.Slot(str)
def session_start(id):
    print('session_start ' + id)
#    LogModel.systemHandler.push_application()
    #slash.logger.handlers.insert(0, LogModel.systemHandler)
    LogModel.systemHandler.enterThreadedMode()
    slash.logger.info("Session started: " + str(slash.context.session))
    print('session_start done')
    event.set()

@QtCore.Slot(str)
def session_end(id):
    print('session_end ' + id)
    slash.logger.info("Session ended: " + id)
    #slash.logger.handlers.remove(LogModel.systemHandler)
    LogModel.systemHandler.exitThreadedMode()
#    LogModel.systemHandler.pop_application()
    print('session_end done')
    event.set()

@QtCore.Slot(str)
def test_start(id):
    print('test_start ' + id)
    slash.logger.info("Test started: " + id)
    handler = LogModel.getLogHandler(
        slash.test.__slash__.function_name + ' #' + str(slash.context.test.__slash__.test_index1),
        logbook.INFO,
        False)
    slash.logger.handlers.insert(0, handler)
    handler.enterThreadedMode()
    handlers[id] = handler
    print('test_start done')
    event.set()

@QtCore.Slot(str)
def test_end(id):
    print('test_stop ' + id)
    handler = handlers[id]
    handler.exitThreadedMode()
    slash.logger.handlers.remove(handler)
    del handlers[id]
    slash.logger.info("Test ended: " + id)
    print('test_end done')
    event.set()

class MessageSender(QtCore.QObject):
    session_start = QtCore.Signal(str)
    session_end = QtCore.Signal(str)
    test_start = QtCore.Signal(str)
    test_end = QtCore.Signal(str)

# ---- These handlers are invoked from slash in a separate thread ------------------------------------------------------

message_sender = MessageSender()
message_sender.session_start.connect(session_start)
message_sender.session_end.connect(session_end)
message_sender.test_start.connect(test_start)
message_sender.test_end.connect(test_end)

@staticmethod
@slash.hooks.session_start.register
def session_start_handler():
    print('session_start_handler - start')
    message_sender.session_start.emit(str(slash.context.session_id))
    event.wait()
    event.clear()
    print('session_start_handler- stop')

@staticmethod
@slash.hooks.session_end.register
def session_end_handler():
    print('session_end_handler - start')
    message_sender.session_end.emit(str(slash.context.session_id))
    event.wait()
    event.clear()
    print('session_end_handler - stop')

@staticmethod
@slash.hooks.test_start.register
def test_start_handler():
    print('test_start_handler - start: ' + slash.context.test.__slash__.function_name)
    message_sender.test_start.emit(str(slash.context.test_id))
    event.wait()
    event.clear()
    print('test_start_handler - stop')

@staticmethod
@slash.hooks.test_end.register
def test_end_handler():
    print('test_end_handler - start')
    message_sender.test_end.emit(str(slash.context.test_id))
    event.wait()
    event.clear()
    print('test_end_handler - stop')


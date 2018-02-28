import subprocess
import os
import sys
import operator

from PySide import QtCore
from .TodoResultTreeItems import LogTreeItem, SetTreeItem, TestTreeItem, CriteriaTreeItem, EvaluationTreeItem, RootTreeItem
from .TodoResultsViewer import TestResultManager


class ResultTreeModel(QtCore.QAbstractItemModel):
    def __init__(self, treeView, clickedAction, inParent=None):
        super(ResultTreeModel, self).__init__(inParent)
        self.rootItem = RootTreeItem()
        self.treeView = treeView
        clickedAction.triggered.connect(self.doubleClicked)

    def doubleClicked(self):
        i = self.treeView.selectedIndexes()[0].internalPointer()

        if (isinstance(i, LogTreeItem)):
            absLogPath = os.path.abspath(i.filePath)
            Log.mainLog.info("opening " + absLogPath + "...")
            if sys.platform.startswith('darwin'):
                subprocess.call(('open', absLogPath))
            elif os.name == 'nt':
                os.startfile(absLogPath)
            elif os.name == 'posix':
                subprocess.call(('xdg-open', absLogPath))

    def refreshGui(self):
        self.beginResetModel()
        self.rootItem = RootTreeItem()
        for sr in sorted(TestResultManager.setResults, key=operator.attrgetter("name")):
            sri = SetTreeItem(self.rootItem, sr.name, sr.isSuccess())
            self.rootItem.AddChild(sri)
            for tr in sorted(sr.testResults, key=operator.attrgetter("name")):
                tri = TestTreeItem(sri, tr.name, tr.isSuccess())
                sri.AddChild(tri)
                li = LogTreeItem(tri, sr.getResultDir() + tr.name + ".log")
                tri.AddChild(li)
                for c in sorted(tr.criteria, key=operator.attrgetter("name")):
                    ci = CriteriaTreeItem(tri, c.name, c.isSuccess())
                    tri.AddChild(ci)
                    for e in sorted(c.evaluations, key=operator.attrgetter("time")):
                        ei = EvaluationTreeItem(ci, ("%.3f" % e.time) + ": " + e.text, e.success)
                        ci.AddChild(ei)

        TestResultManager.setResults = sorted(TestResultManager.setResults, key=operator.attrgetter("name"))

        self.endResetModel()

    def index(self, row, column, parentindex):
        """
        The index is used to access data by the view
        This method overrides the base implementation (needs to be overridden)
        @param row: The row to create the index for
        @param column: Not really relevant, the tree item handles this
        @param parent: The parent this index should be created under
        """

        # if the index does not exist, return a default index
        if not self.hasIndex(row, column, parentindex):
            return QtCore.QModelIndex()

        # make sure the parent exists, if not assume it's the root
        parent_item = None
        if not parentindex.isValid():
            parent_item = self.rootItem
        else:
            parent_item = parentindex.internalPointer()

        # get the child from that parent and create an index for it
        child_item = parent_item.GetChild(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        else:
            return QtCore.QModelIndex()

    def parent(self, childindex):
        """
        creates an index for a parent based on a child index, and binds the data
        used by the view to get a parent (from a child)
        @param childindex: the index of the child to get the parent from
        """

        if not childindex.isValid():
            return QtCore.QModelIndex()

        child_item = childindex.internalPointer()
        if not child_item:
            return QtCore.QModelIndex()

        parent_item = child_item.GetParent()

        if parent_item == self.rootItem:
            return QtCore.QModelIndex()

        return self.createIndex(parent_item.Row(), 0, parent_item)

    def rowCount(self, parentindex):
        """
        Returns the amount of rows a parent has
        This comes down to the amount of children associated with the parent
        @param parentindex: the index of the parent
        """

        if parentindex.column() > 0:
            return 0

        item = None
        if not parentindex.isValid():
            item = self.rootItem
        else:
            item = parentindex.internalPointer()

        return item.GetChildCount()

    def columnCount(self, parentindex):
        """
        Amount of columns associated with the parent index
        @param parentindex: the parent index object
        """

        if not parentindex.isValid():
            return self.rootItem.ColumnCount()

        return parentindex.internalPointer().ColumnCount()

    def data(self, index, role):
        """
        The view calls this to extract data for the row and column associated with the parent object
        @param index: the parentindex to extract the data from
        @param role: the data accessing role the view requests from the model
        """

        if not index.isValid():
            return QtCore.QVariant()

        # get the item out of the index
        parent_item = index.internalPointer()

        if (index.column() != 0):
            Log.mainLog.error("Only support for one column at the moment");
            return None

        # Return the data associated with the column
        if role == QtCore.Qt.DisplayRole:
            return parent_item.Data()
        if role == QtCore.Qt.SizeHintRole:
            return QtCore.QSize(22, 22)
        if role == QtCore.Qt.DecorationRole:
            return parent_item.Icon()

        # Otherwise return default
        return None

    def headerData(self, column, orientation, role):
        if (orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole):
            try:
                return self.rootItem.Data()
            except IndexError:
                pass

        return None

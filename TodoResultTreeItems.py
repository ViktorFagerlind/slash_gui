from PySide import QtCore, QtGui


class BaseTreeItem(object):
    def __init__(self, inParentItem):
        self.parent = inParentItem
        self.children = []

    def AddChild(self, inChild):
        self.children.append(inChild)

    def GetChildCount(self):
        return len(self.children)

    def GetChild(self, row):
        return self.children[row]

    def GetParent(self):
        return self.parent

    def ColumnCount(self):
        return 1

    def Data(self):
        raise Exception("Data gather method not implemented!")

    def Icon(self):
        raise Exception("Data gather method not implemented!")

    def Parent(self):
        return self.parent

    def Row(self):
        if self.parent:
            return self.parent.children.index(self)
        return 0


class RootTreeItem(BaseTreeItem):
    def __init__(self):
        super(RootTreeItem, self).__init__(None)

    def Data(self):
        return "Test Results"

    def Icon(self):
        return None


class NormalTreeItem(BaseTreeItem):
    def __init__(self, parent, name, isSuccess):
        super(NormalTreeItem, self).__init__(parent)
        self.name = name
        self.isSuccess = isSuccess

    def Data(self):
        return self.name

    def Icon(self):
        raise Exception("Icon method not implemented!")


class SetTreeItem(NormalTreeItem):
    def __init__(self, parent, name, isSuccess):
        super(SetTreeItem, self).__init__(parent, name, isSuccess)

    def Icon(self):
        if (self.isSuccess):
            return QtGui.QIcon("gui/icons/PassedSet.png")
        else:
            return QtGui.QIcon("gui/icons/FailedSet.png")


class TestTreeItem(NormalTreeItem):
    def __init__(self, parent, name, isSuccess):
        super(TestTreeItem, self).__init__(parent, name, isSuccess)

    def Icon(self):
        if (self.isSuccess):
            return QtGui.QIcon("gui/icons/PassedTest.png")
        else:
            return QtGui.QIcon("gui/icons/FailedTest.png")


class CriteriaTreeItem(NormalTreeItem):
    def __init__(self, parent, name, isSuccess):
        super(CriteriaTreeItem, self).__init__(parent, name, isSuccess)

    def Icon(self):
        if (self.isSuccess):
            return QtGui.QIcon("gui/icons/PassedCriteria.png")
        else:
            return QtGui.QIcon("gui/icons/FailedCriteria.png")


class EvaluationTreeItem(NormalTreeItem):
    def __init__(self, parent, name, isSuccess):
        super(EvaluationTreeItem, self).__init__(parent, name, isSuccess)

    def Icon(self):
        if (self.isSuccess):
            return QtGui.QIcon("gui/icons/Passed.png")
        else:
            return QtGui.QIcon("gui/icons/Failed.png")


class LogTreeItem(BaseTreeItem):
    def __init__(self, parent, filePath):
        super(LogTreeItem, self).__init__(parent)
        self.filePath = filePath

    def Data(self):
        return "Log"

    def Icon(self):
        return QtGui.QIcon("gui/icons/Script.png")

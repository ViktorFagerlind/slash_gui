import sys

from TestManager import TestConfiguration
from Logging import Log, LogManager, Settings, StreamToLog
from Results import TestResult


class Test:
    def __init__(self, name, instanceName):
        self.name = name
        self.instanceName = instanceName

    def fullName(self):
        return self.name + " (" + self.instanceName + ")"

    def getFloatParameter(self, name, default=0):
        valueString = TestConfiguration.getValueString(self.name, self.instanceName, name)
        if valueString is None:
            return float(default)
        return float(valueString)

    def getIntParameter(self, name, default=0):
        valueString = TestConfiguration.getValueString(self.name, self.instanceName, name)
        if valueString is None:
            return int(default)
        return int(valueString)

    def getLongParameter(self, name, default=0):
        valueString = TestConfiguration.getValueString(self.name, self.instanceName, name)
        if valueString is None:
            return long(default)
        return long(valueString)

    def checkEqual(self, criteriaName, variableName, actualValue, expectedValue):
        self.check(criteriaName, variableName + "=" + str(expectedValue), actualValue == expectedValue)

    def initCriteria(self, criteriaNames):
        self.ongoingResult.initCriteria(criteriaNames)

    def check(self, criteriaName, text, success):
        self.ongoingResult.addEvaluation(criteriaName, text, success, self.log)

    def printStart(self):
        self.log.largeHeading(self.fullName())
        self.log.newline()

    def printSubstep(self, name):
        self.log.newline()
        self.log.mediumHeading(name)

    def runInGui(self, logDir):
        timeName = self.fullName() + " - " + Settings.getNowString()
        log = LogManager.addLog(self.fullName(), logDir, timeName)
        return self.__run(log, timeName)

    def runStandalone(self):
        timeName = self.fullName() + " - " + Settings.getNowString()
        log = LogManager.getStandaloneLog(self.fullName())
        return self.__run(log, timeName)

    def __run(self, log, timeName):
        self.log = log

        self.ongoingResult = TestResult(timeName)

        self.printStart()

        saved_stdout = sys.stdout
        sys.stdout = StreamToLog(self.log, False)

        self.runSequence()

        sys.stdout = saved_stdout

        self.printSubstep(self.name + " done!")

        self.ongoingResult.log(self.log)

        return self.ongoingResult

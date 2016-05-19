#!/usr/bin/python3

import sys
import re
import datetime

from PySide import QtGui, QtCore

from Timeslots import Timeslots
from Schedule import Schedule

class BoolSignal(QtCore.QObject):
    ''' Custom Boolean signal '''
    sig = QtCore.Signal(bool)

class Worker(QtCore.QThread):
    ''' Creating a QThread class to run the time intensive webscrape of
    timeslots. '''
    def __init__(self, timeslotObjects, parent = None):
        super(Worker, self).__init__(parent)
        self.signal = BoolSignal()
        self.firstRun = True
        self.timeslotObjects = timeslotObjects

    def run(self):
        for room in self.timeslotObjects:
            if self.timeslotObjects[room].initHtml():
                self.timeslotObjects[room].update()
            else:
                pass

        self.signal.sig.emit(self.firstRun)
        self.firstRun = False

class Window(QtGui.QDialog):
    ''' '''
    def __init__(self):
        super(Window, self).__init__()
        self.INTERVAL = 300000  # update interval in milliseconds

        # Container lists for shift widgets and timeslots.
        self.shiftsWidgets = []
        self.timeslotObjects = {}

        # Create viewport
        self.viewport = QtGui.QWidget(self)
        self.viewportLayout = QtGui.QVBoxLayout(self)
        self.viewport.setLayout(self.viewportLayout)

        # Scroll Area
        self.scrollArea = QtGui.QScrollArea()
        self.scrollArea.setVisible(True)
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setMinimumWidth(self.viewport.sizeHint().width())
        self.scrollArea.setWidget(self.viewport)

        # Regex for grabbing room names from shift summaries.
        self.pattern = re.compile("(\D*) \d*")

        # Initialize a schedule object and related timeslot objects.
        self.getSchedule()
        self.getTimeslots()

        # Create a QThread object for the webscrape.
        self.worker = Worker(self.timeslotObjects)

        # Connect QThread objects signals.
        self.worker.started.connect(self.starting)
        self.worker.finished.connect(self.finished)
        self.worker.signal.sig.connect(self.updateDisplay)

        self.worker.start()

        self.timeslotTimer()

        self.mainLayout()

        self.createActions()
        self.createTrayIcon()

        self.setIcon()
        self.trayIcon.show()

        self.setWindowTitle("RoomWhen")
        self.setFixedHeight(500)

    def starting(self):
        print("Starting thread!")

    def finished(self):
        print("Finished thread!")

    def updateDisplay(self, data):
        ''' If first run create widgets and layout, else update widgets
        information. '''
        if data:
            self.createShiftWidgets()
            self.createShiftLayout()
        else:
            self.updateTimeslotStatus()

    def getSchedule(self):
        ''' Pull the current schedule, requires .icalURL file in same directory '''
        url = ''
        with open('.icalURL', 'r') as icalURL:
            url = icalURL.readline().replace('\n', '')

        self.schedule = Schedule(url)
        self.schedule.events = self.schedule.sortEventsByDatetime()

    def getTimeslots(self):
        ''' Initiate timeslot objects, requires an already initialized schedule object. '''

        # Schedule.listRooms() returns a dict of room:week for us to
        # create a timeslot for each room and only fetch important weeks.
        roomList = self.schedule.listRooms()

        for room in roomList:
            self.timeslotObjects[room] = Timeslots(room, roomList[room])

    def timeslotTimer(self):
        ''' Method to start the worker thread at given interval. '''

        self.timer = QtCore.QTimer()
        self.timer.setSingleShot(False)
        self.timer.timeout.connect(self.worker.start)
        self.timer.start(self.INTERVAL)

    def updateTimeslotStatus(self):
        ''' '''

        # Loop each widget in our shifts container.
        for widget in range(len(self.shiftsWidgets)):

            # For current widget, fetch info to be used.
            room = self.schedule.getRoom(self.schedule.events[widget])
            start = self.schedule.events[widget]['timeStart']
            end = self.schedule.events[widget]['timeEnd'] + datetime.timedelta(minutes=5)

            timeslots = self.timeslotObjects[room].findGames(start, end)

            # For each QLabel holding booking status of game.
            # Update the status.
            for i in range(1, self.shiftsWidgets[widget].layout().count()):
                self.shiftsWidgets[widget].layout().itemAt(i).layout().itemAt(1).widget().setText(timeslots[i-1]['Status'])

    def setIcon(self):
        ''' '''
        icon =  QtGui.QIcon('images/drink.png')
        self.trayIcon.setIcon(icon)
        self.setWindowIcon(icon)

        self.trayIcon.setToolTip("Placeholder")

    def mainLayout(self):
        ''' Create the main layout '''
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.addWidget(self.scrollArea)
        self.setLayout(self.layout)

    def createShiftLayout(self):
        ''' Create a layout for a single shift. '''

        for widget in self.shiftsWidgets:
            self.viewportLayout.addWidget(widget)

    def createActions(self):
        self.minimizeAction = QtGui.QAction("Mi&nimize", self,
                triggered=self.hide)

        self.restoreAction = QtGui.QAction("&Restore", self,
                triggered=self.showNormal)

        self.quitAction = QtGui.QAction("&Quit", self,
                triggered=QtGui.qApp.quit)

    def createTrayIcon(self):
        ''' '''
        self.trayIconMenu = QtGui.QMenu(self)
        self.trayIconMenu.addAction(self.minimizeAction)
        self.trayIconMenu.addAction(self.restoreAction)
        self.trayIconMenu.addAction(self.quitAction)

        self.trayIcon = QtGui.QSystemTrayIcon(self)
        self.trayIcon.setContextMenu(self.trayIconMenu)
        
    def createShiftWidgets(self):
        ''' Create a widget with shift information for each shift. Requires
        already initialized schedule and timeslot objects.'''

        # For each shift create QWidget and set it's layout.
        for shift in self.schedule.events:
            shiftWidget = QtGui.QWidget()
            layout = QtGui.QVBoxLayout()

            date = shift['timeStart'].strftime("%Y-%m-%d")
            room = shift['summary'].upper()

            # Use regex to get nice room name for our widget.
            patternMatch = re.match(self.pattern, room)
            room = patternMatch.group(1)

            # Create a layout to display header information, date and which room
            headerLayout = QtGui.QHBoxLayout()
            headerLayout.addWidget(QtGui.QLabel(date))
            headerLayout.addWidget(QtGui.QLabel(room))
            layout.addLayout(headerLayout)

            for timeslot in self.timeslotObjects[self.schedule.getRoom(shift)].findGames(shift['timeStart'], shift['timeEnd'] + datetime.timedelta(minutes=5)):

                timeslotLayout = QtGui.QHBoxLayout()

                # Get a combined timestamp for start and end of game
                timestamp = timeslot['Start'].strftime("%H:%M")+'-'+timeslot['End'].strftime("%H:%M")

                # Populate the timeslot layout with current timeslot infomation
                timeslotLayout.addWidget(QtGui.QLabel(timestamp))
                timeslotLayout.addWidget(QtGui.QLabel(timeslot['Status']))

                # Add the timeslot layout to the layout of our shift.
                layout.addLayout(timeslotLayout)

            shiftWidget.setLayout(layout)

            # Add finished widget to our list of shift widgets.
            self.shiftsWidgets.append(shiftWidget)

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    window = Window()
    window.show()
    sys.exit(app.exec_())

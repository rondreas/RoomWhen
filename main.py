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
        for timeslotObject in self.timeslotObjects:
            if timeslotObject.initHtml():
                timeslotObject.update()
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
        self.timeslotObjects = []

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

        self.errorLayout()
        self.mainLayout()

        self.createActions()
        self.createTrayIcon()

        self.setIcon()
        self.trayIcon.show()

        self.setWindowTitle("RoomWhen")

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
            self.layout().addWidget(self.shiftDisplay)

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
            self.timeslotObjects.append(Timeslots(room, roomList[room]))

    def timeslotTimer(self):
        ''' Method to start the worker thread at given interval. '''

        self.timer = QtCore.QTimer()
        self.timer.setSingleShot(False)
        self.timer.timeout.connect(self.worker.start)
        self.timer.start(self.INTERVAL)

    def updateTimeslotStatus(self):
        ''' Method to loop through all shift widgets and update their displayed
        status. 
        
        Current widget structure:
            
            MainWindow
                ShiftDisplay - QVBoxLayout
                    ShiftWidget - QVBoxLayout
                        Timeslot 0
                        Timeslot 1
                        ...
        '''
        #TODO Could easy implement a check for status change and maybe connect
        # a signal.

        # Loop each widget in our shifts container.
        for widget in range(len(self.shiftsWidgets)):

            # Fetch room name from the child QLabel
            room = self.shiftsWidgets[widget].layout().itemAt(0).layout().itemAt(1).widget().text()

            # Loop timeslots to match room name to a timeslot object.
            for timeslotObject in self.timeslotObjects:
                if timeslotObject.room[:4] in room.lower():
                    # Fetch information about the timeslots for current shift widget.
                    timeslots = timeslotObject.findGames(self.schedule.events[widget]['timeStart'],
                                                         self.schedule.events[widget]['timeEnd'] + datetime.timedelta(minutes=5))

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
        layout = QtGui.QVBoxLayout()

        layout.addWidget(self.errorWidget)

        self.setLayout(layout)

    def createShiftLayout(self):
        ''' Create a layout for a single shift. '''
        self.shiftDisplay = QtGui.QWidget()

        self.shiftDisplay.setMinimumSize(170, 510)

        self.scrollArea = QtGui.QScrollArea()
        self.scrollArea.setWidget(self.shiftDisplay)

        self.shiftLayout = QtGui.QVBoxLayout()
        for widget in self.shiftsWidgets:
            self.shiftLayout.addWidget(widget)

        self.shiftDisplay.setLayout(self.shiftLayout)

    def errorLayout(self):
        ''' '''
        self.errorWidget = QtGui.QWidget()
        layout = QtGui.QHBoxLayout()

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        self.errorMsg = QtGui.QLabel("{}".format(now))

        self.errorBtn = QtGui.QPushButton("Ok")
        self.errorBtn.clicked.connect(self.updateTimeslotStatus)
        
        layout.addWidget(self.errorMsg)
        layout.addWidget(self.errorBtn)

        self.errorWidget.setLayout(layout)

    def errorBtnClicked(self):
        ''' '''
        self.errorWidget.hide()

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

            patternMatch = re.match(self.pattern, room)
            room = patternMatch.group(1)

            # Create a layout to display header information, date and which room
            headerLayout = QtGui.QHBoxLayout()
            headerLayout.addWidget(QtGui.QLabel(date))
            headerLayout.addWidget(QtGui.QLabel(room))
            layout.addLayout(headerLayout)

            # Populate shift widget with all timeslots for given shift.
            for timeslotObject in self.timeslotObjects:
                # Match current timeslot to the shift
                if timeslotObject.room[:4] in shift['summary'].lower():
                    # shift datetime is off by 25ms on linux - just to be sure
                    # I'm then adding 5 min to it.
                    for timeslot in timeslotObject.findGames(shift['timeStart'], shift['timeEnd'] + datetime.timedelta(minutes=5)):

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

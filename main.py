#!/usr/bin/python3

import sys
import re
import datetime

from PySide import QtGui, QtCore

from Timeslots import Timeslots
from Schedule import Schedule

class Worker(QtCore.QThread):
    ''' Creating a QThread class to run the time intensive webscrape of
    timeslots. '''

    signal = QtCore.Signal(bool)

    def __init__(self, timeslotObjects, parent = None):
        super(Worker, self).__init__(parent)
        self.firstRun = True
        self.timeslotObjects = timeslotObjects

    def run(self):
        for room in self.timeslotObjects:
            try:
                self.timeslotObjects[room].update()
            except:
                pass

        self.signal.emit(self.firstRun)
        self.firstRun = False

class Window(QtGui.QDialog):
    ''' '''
    def __init__(self):
        super(Window, self).__init__()
        self.INTERVAL = 300000  # update interval in milliseconds

        # Container lists for shift widgets and timeslots.
        self.shiftWidgets = []
        self.timeslotObjects = {}

        # Create viewport
        self.viewport = QtGui.QWidget(self)
        self.viewportLayout = QtGui.QVBoxLayout(self)
        self.viewportLayout.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        self.viewport.setLayout(self.viewportLayout)

        # Scroll Area
        self.scrollArea = QtGui.QScrollArea()
        self.scrollArea.setVisible(True)
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setMinimumWidth(self.viewport.sizeHint().width())
        self.scrollArea.setWidget(self.viewport)

        # Create a progress bar
        self.progressbar = QtGui.QProgressBar(self)
        self.progressbar.setObjectName("status")
        self.progressbar.setMinimum(0)
        self.progressbar.setMaximum(0)

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
        self.worker.signal.connect(self.updateDisplay)

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
        self.progressbar.show()
        print("Starting thread!")

    def finished(self):
        self.progressbar.hide()
        print("Finished thread!")

    def updateDisplay(self, data):
        ''' If first run create widgets and layout, else update widgets
        information. '''
        if data:
            self.createShiftWidgets()
        else:
            self.updateTimeslotStatus()

    def getSchedule(self):
        ''' Pull the current schedule, requires .icalURL file in same directory '''
        url = ''
        try:
            with open('.icalURL', 'r') as icalURL:
                url = icalURL.readline().replace('\n', '')
        except IOError:
            pass    # No pre made url file, so create dialogue for creating one.

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
        self.layout.addWidget(self.progressbar)
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

    def showMessage(self, titel, body):
        ''' '''
        icon = QtGui.QSystemTrayIcon.MessageIcon(1)
        self.trayIcon.showMessage(
                titel,
                body,
                icon,
                5000
        )


    def createShiftWidgets(self):
        ''' Create a widget with shift information for each shift. Requires
        already initialized schedule and timeslot objects.'''

        # For each shift create QWidget and set it's layout.
        for shift in self.schedule.events:

            # Use regex to get nice room name for our widget.
            patternMatch = re.match(self.pattern, shift['summary'])
            roomNiceName = patternMatch.group(1)

            start = shift['timeStart']
            end = shift['timeEnd'] + datetime.timedelta(minutes=5)
            room = self.schedule.getRoom(shift)

            shiftWidget = ShiftWidget(
                roomNiceName,
                start.strftime("%Y-%m-%d"),
                self.timeslotObjects[room].findGames(start, end),
                room,
                start,
                end,
                parent = self.viewport
            )

            self.shiftWidgets.append(shiftWidget)
            self.viewportLayout.addWidget(shiftWidget)

    def updateTimeslotStatus(self):
        ''' Iterate through all widgets and update any changes. '''

        for widget in self.shiftWidgets:

            # Query timeslot for given widget room, about all games during it.
            timeslots = self.timeslotObjects[widget.room].findGames(widget.start, 
                                                                    widget.end)
            for timeslot in timeslots:

                # Check if there has been any change
                if timeslot['Status'] != widget.statuses[timeslot['Timestamp']].text():

                    # Compose notification message.
                    titel = widget.titel + ' ' + widget.date + " status changed"
                    body = "The " +  widget.titel + " at the " +  widget.date + \
                           " had it's status change from " + \
                           widget.statuses[timeslot['Timestamp']].text() + \
                           " to " + timeslot['Status']

                    self.showMessage(titel, body)

                    # Update widget with the change.
                    widget.statuses[timeslot['Timestamp']].setText(timeslot['Status'])

                else:
                    pass

class ShiftWidget(QtGui.QWidget):
    ''' '''
    def __init__(self, titel, date, timeslots, room, start, end, parent = None):
        super(ShiftWidget, self).__init__(parent)

        self.titel = titel
        self.date = date
        self.timeslots = timeslots
        self.room = room
        self.start = start
        self.end = end

        # Container dict for out changeable widgets.
        self.statuses = {}

        # Create labels for out 'header' and set the layout.
        self.dateLabel = QtGui.QLabel(date, parent = self)
        self.titelLabel = QtGui.QLabel(titel, parent = self)

        self.headerLayout = QtGui.QHBoxLayout()

        self.headerLayout.addWidget(self.dateLabel)
        self.headerLayout.addWidget(self.titelLabel)
   
        # Create the widget layout
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.addLayout(self.headerLayout)
        self.addTimeslots()
        self.setLayout(self.layout)

        self.layout.setSizeConstraint(QtGui.QLayout.SetFixedSize)

    def addTimeslots(self):
        for timeslot in self.timeslots:

            timeslotLayout = QtGui.QHBoxLayout()

            timeslotTimestampLabel = QtGui.QLabel(timeslot['Timestamp'], parent = self)
            timeslotStatusLabel = QtGui.QLabel(timeslot['Status'], parent = self)

            # Add status widget to our dict for ease of access.
            self.statuses.update({timeslot['Timestamp']:timeslotStatusLabel})

            timeslotLayout.addWidget(timeslotTimestampLabel)
            timeslotLayout.addWidget(timeslotStatusLabel)

            self.layout.addLayout(timeslotLayout)

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    window = Window()
    window.show()
    sys.exit(app.exec_())

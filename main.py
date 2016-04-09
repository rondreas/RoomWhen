#!/usr/bin/python3

import sys
from Timeslots import Timeslots
import datetime
from PySide import QtGui, QtCore

class Window(QtGui.QDialog):
    ''' '''
    def __init__(self):
        super(Window, self).__init__()
        self.INTERVAL = 300000  # update interval in milliseconds

        self.shiftsWidgets = []

        self.getSchedule()
        self.getTimeslots()
        self.timeslotTimer()
        self.createShiftWidgets()

        self.icalLayout()
        self.createShiftLayout()
        self.errorLayout()
        self.mainLayout()

        self.createActions()
        self.createTrayIcon()

        self.setIcon()
        self.trayIcon.show()

        self.setWindowTitle("RoomWhen")

    def updateTimeslotStatus(self):
        ''' Method to loop through all shift widgets and update their displayed
        status. '''

        for widget in range(len(self.shiftsWidgets)):

            # Fetch all timeslots for current shift. Poorly named 'widget' will
            # have to fix sometime later.
            timeslots = self.timeslots.findGames(self.shifts[widget]['startTime'], 
                                                 self.shifts[widget]['endTime'])

            # Get the layout for given shift widget.
            shiftWidgetLayout = self.shiftsWidgets[widget].layout()

            # Loop through layouts with information for timeslots in given widget
            for i in range(1, shiftWidgetLayout.count()):
                # Get the layout for timeslot
                timeslotLayout = shiftWidgetLayout.itemAt(i)
                # Get the widget containing the status for timeslot
                timeslotStatus = timeslotLayout.layout()
                timeslotStatus.itemAt(1).widget().setText(timeslots[i-1]['Status'])

    def setIcon(self):
        ''' '''
        icon =  QtGui.QIcon('images/drink.png')
        self.trayIcon.setIcon(icon)
        self.setWindowIcon(icon)

        self.trayIcon.setToolTip("Placeholder")

    def mainLayout(self):
        ''' Create the main layout '''
        layout = QtGui.QVBoxLayout()

        layout.addLayout(self.ical)
        layout.addWidget(self.shiftDisplay)
        layout.addWidget(self.errorWidget)

        self.setLayout(layout)

    def icalLayout(self):
        self.ical = QtGui.QHBoxLayout()
        icalEdit = QtGui.QLineEdit()
        self.ical.addWidget(icalEdit)

    def createShiftLayout(self):
        ''' Create a layout for a single shift. '''
        self.shiftDisplay = QtGui.QWidget()
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

    def timeslotTimer(self):
        ''' Call method to update all focused timeslots at
        given interval. '''
        self.timer = QtCore.QTimer()
        self.timer.setSingleShot(False)
        self.timer.timeout.connect(self.getTimeslots)
        self.timer.start(self.INTERVAL)

    def getTimeslots(self):
        ''' '''
        self.timeslots = Timeslots(self.shifts[0]['Summary'])
        if self.timeslots.initHtml():
            self.timeslots.update()
        else:
            self.errorMsg.setText("Could not fetch timeslots...")
        
    def createShiftWidgets(self):
        ''' Create a widget with shift information for each shift. '''

        # For each shift create QWidget and set it's layout.
        for shift in self.shifts:
            shiftWidget = QtGui.QWidget()
            layout = QtGui.QVBoxLayout()

            date = shift['startTime'].strftime("%Y-%m-%d")
            room = shift['Summary'].upper()

            # Add a widget with date and which room as a header
            layout.addWidget(QtGui.QLabel(date + " " + room))

            # Populate shift widget with all timeslots for given shift.
            for timeslot in self.timeslots.findGames(shift['startTime'], shift['endTime']):

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

    def getSchedule(self):
        ''' Pull the current schedule '''
        # Temporary spoof shift data.
        self.shifts = []
        today = datetime.date.today()
        for i in range(1, 4):
            sTime = datetime.time(12, 30)
            eTime = datetime.time(18, 00)
            day = today + datetime.timedelta(days=i)
            self.shifts.append({"Summary":'bunker',
                                "startTime":datetime.datetime.combine(day, sTime),
                                "endTime":datetime.datetime.combine(day, eTime)})

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    window = Window()
    window.show()
    sys.exit(app.exec_())

import icalendar
import requests
from datetime import datetime

class Schedule():
    ''' Create a schedule object, holding the events from doodle ical schedule 
    taken from given url.'''
    def __init__(self, url):
        self.request = requests.get(url)
        self.events = []

        if self.request.status_code == requests.codes.ok:
            self.calendar = icalendar.Calendar.from_ical(self.request.content)
            self.parseCalendar()

    def parseCalendar(self):
        ''' Goes through the Doodle ical url, ignoring already past events
        and stores the information for each event as a dictionary. Each
        dictionary will then be appended to class list of events. '''

        tzDeltaTime = datetime.now() - datetime.utcnow()

        for event in self.calendar.walk('vevent'):
            summary = event.get('summary')
            dtStart = event.get('dtstart')
            dtEnd = event.get('dtend')
            
            # Doodle datetimes are represented in gmt so I'm adjusting
            # the datetime objects to represent local time.
            dtStart.dt += tzDeltaTime
            dtEnd.dt += tzDeltaTime

            # Get the week
            week = dtEnd.dt.isocalendar()[1]

            # One can't compare naive to aware datetime objects, so we
            # strip the tzinfo from the calendar datetime.
            if dtEnd.dt.replace(tzinfo=None) > datetime.now():
                self.events.append({'summary':summary,
                                    'timeStart':dtStart.dt.replace(tzinfo=None),
                                    'timeEnd':dtEnd.dt.replace(tzinfo=None),
                                    'week':week})

    def sortEventsByDatetime(self):
        ''' Takes the stored events list and returns a list sorted in
        chronological ascending order. '''
        newList = sorted(self.events, key=lambda k: k['timeEnd'])
        return newList

    def getRoom(self, event):
        ''' Checks which room given event is to take place in '''
        #TODO add new rooms, not sure how they look in doodle.
        if 'zombie' in event['summary'].lower():
            return 'zombie_lab'
        elif 'bank' in event['summary'].lower():
            return 'bank'
        elif 'bunker' in event['summary'].lower():
            return 'bunker'
        else:
            print("Unexpected event, nothing to return")

    def listRooms(self):
        ''' Check schedule and return a dict with each unique room
        in schedule and which weeks are related to those rooms. '''
        scheduledRooms = {}
        for event in self.events:
            room = self.getRoom(event)
            if room in scheduledRooms:
                if event['week'] not in scheduledRooms[room]:
                    scheduledRooms[room].append(event['week'])
            else:
                scheduledRooms[room] = [event['week']]
        return scheduledRooms

    def prunePastEvents(self):
        ''' Goes through our list of events and deletes any event
        that has already passed. '''
        self.events[:] = [event for event in self.events if event['timeEnd']>datetime.now()]

if __name__ == '__main__':
    url = ''
    with open('.icalURL', 'r') as icalURL:
        url = icalURL.readline().replace('\n', '')

    mySchedule = Schedule(url)
    mySchedule.events = mySchedule.sortEventsByDatetime()
    mySchedule.prunePastEvents()
    print(mySchedule.listRooms())
    for shift in mySchedule.events:
        print(shift)

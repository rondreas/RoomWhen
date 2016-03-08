import icalendar
import requests
from datetime import datetime

#TODO evaluate removal of getNextEventID() and getEvent(), also the removal of
# adding a id to stored events.

#TODO Why convert event values to string? When they are mostly converted back
# to datetime objects for operations.

class Schedule():
    ''' Create a schedule object, holding the events from doodle ical schedule taken from given url.'''
    def __init__(self, url):
        try:
            self.request = requests.get(url)
        except:
            print("Error: Could not get requested URL")

        self.events = []
        self.tzDeltaTime = datetime.now() - datetime.utcnow()
        self.calendar = icalendar.Calendar.from_ical(self.request.content)

        if self.request:
            self.parseCalendar()

    def parseCalendar(self):

        sid = 0

        for event in self.calendar.walk('vevent'):
            summary = event.get('summary')
            dtStart = event.get('dtstart')
            dtEnd = event.get('dtend')

            # Doodle datetimes are represented in gmt so I'm adjusting
            # the datetime objects to represent local time.
            dtStart.dt += self.tzDeltaTime
            dtEnd.dt += self.tzDeltaTime

            # One can't compare naive to aware datetime objects, so we
            # strip the tzinfo from the calendar datetime.
            if dtEnd.dt.replace(tzinfo=None) > datetime.now():
                self.events.append({'summary':str(summary),
                                    'date':dtStart.dt.replace(tzinfo=None).date().strftime('%Y-%m-%d'),
                                    'timeStart':dtStart.dt.replace(tzinfo=None).time().strftime('%H:%M'),
                                    'timeEnd':dtEnd.dt.replace(tzinfo=None).time().strftime('%H:%M'),
                                    'id':sid,
                                    'datetime':dtEnd.dt.replace(tzinfo=None)})

            # increment shift id number
            sid += 1

    def getNextEventID(self):
        ''' Get the next scheduled shift ID. '''

        earliest = ''
        earliest_id = None
        dtPattern = "%Y-%m-%d %H:%M"

        for event in self.events:
            check = event['date'] + ' ' + event['timeStart']
            # if earliest is empty...
            if not earliest:
                earliest = check
                earliest_id = event['id']
            # Compare datetimes for which one is earliest.
            elif datetime.strptime(earliest, dtPattern) > datetime.strptime(check, dtPattern):
                earliest = check
                earliest_id = event['id']

        return earliest_id

    def sortEventsByDatetime(self):
        ''' '''
        newList = sorted(self.events, key=lambda k: k['datetime'])
        return newList

    def getRoom(self, event):
        if 'zombie' in event['summary'].lower():
            return 'zombie_lab'
        elif 'bank' in event['summary'].lower():
            return 'bank'
        elif 'bunker' in event['summary'].lower():
            return 'bunker'
        else:
            print("Unexpected event, nothing to return")

    def getEvent(self, sid):
        for event in self.events:
            if event['id'] == sid:
                return event

    def prunePastEvents(self):
        ''' Goes through our list of events and deletes any event
        that has already passed. '''
        self.events[:] = [event for event in self.events if event['datetime']>datetime.now()]

if __name__ == '__main__':
    url = ''
    with open('.icalURL', 'r') as icalURL:
        url = icalURL.readline().replace('\n', '')

    mySchedule = Schedule(url)
    mySchedule.events = mySchedule.sortEventsByDatetime()
    mySchedule.prunePastEvents()
    print(mySchedule.events)

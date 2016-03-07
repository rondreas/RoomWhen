import icalendar
import requests
from datetime import datetime

#TODO utilize datetime.strf() to get formatted strings.

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
            if dtStart.dt.replace(tzinfo=None) > datetime.now():
                self.events.append({'summary':str(summary),
                                    'date':str(dtStart.dt.replace(tzinfo=None).date()),
                                    'timeStart':str(dtStart.dt.replace(tzinfo=None).time()),
                                    'timeEnd':str(dtEnd.dt.replace(tzinfo=None).time()),
                                    'id':sid})

            # increment shift id number
            sid += 1

    def getNextEventID(self):
        ''' Get the next scheduled shift ID. '''

        earliest = ''
        earliest_id = None
        dtPattern = "%Y-%m-%d %H:%M:%S"

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

    def getEvent(self, sid):
        for event in self.events:
            if event['id'] == sid:
                return event


if __name__ == '__main__':
    url = ''
    with open('.icalURL', 'r') as icalURL:
        url = icalURL.readline().replace('\n', '')

    mySchedule = Schedule(url)
    print(mySchedule.getEvent(mySchedule.getNextEventID()))

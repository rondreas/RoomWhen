import time
from Schedule import Schedule
from Timeslots import Timeslots
from datetime import datetime

# TODO Clean-up, and make code more DRY

INTERVAL = 300

def main(schedule_url):
    ''' Main loop '''
    
    # Create Schedule object.
    schedule = Schedule(schedule_url)

    # Sort the list of events in chronological order
    schedule.events = schedule.sortEventsByDatetime()

    while True:
        # Remove any passed events from our list of events
        schedule.prunePastEvents()

        # Get the current/upcomming event and the one
        # after it. Create a Timeslots object for each.
        rooms = []
        currentRoom = Timeslots(schedule.getRoom(schedule.events[0]))
        nextRoom = Timeslots(schedule.getRoom(schedule.events[1]))
        rooms.append(currentRoom)
        rooms.append(nextRoom)

        # Get datetimes for start and finish of shifts.
        e1Start = schedule.events[0]['date'] + ' ' + schedule.events[0]['timeStart']
        e1Start = datetime.strptime(e1Start, "%Y-%m-%d %H:%M")
        e2Start = schedule.events[1]['date'] + ' ' + schedule.events[1]['timeStart']
        e2Start = datetime.strptime(e2Start, "%Y-%m-%d %H:%M")

        e1End = schedule.events[0]['date'] + ' ' + schedule.events[0]['timeEnd']
        e1End = datetime.strptime(e1End, "%Y-%m-%d %H:%M")
        e2End = schedule.events[1]['date'] + ' ' + schedule.events[1]['timeEnd']
        e2End = datetime.strptime(e2End, "%Y-%m-%d %H:%M")

        # Find all games during focused shifts
        games1 = rooms[0].findGames(e1Start, e1End)
        games2 = rooms[1].findGames(e2Start, e2End)

        games1 = rooms[0].filter(games1, Status='Reserved')
        games2 = rooms[1].filter(games2, Status='Reserved')

        print(games1)
        print(games2)

        time.sleep(INTERVAL)

if __name__ == '__main__':

    url = ''

    with open('.icalURL', 'r') as icalURL:
        url = icalURL.readline().replace('\n', '')
    
    main(url)

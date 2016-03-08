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

        # Find all games during focused shifts
        games1 = rooms[0].findGames(schedule.events[0]['timeStart'], schedule.events[0]['timeEnd'])
        games2 = rooms[1].findGames(schedule.events[1]['timeStart'], schedule.events[1]['timeEnd'])

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

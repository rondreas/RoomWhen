import time
from Schedule import Schedule
from Timeslots import Timeslots
from datetime import datetime

INTERVAL = 300

def main(schedule_url):
    ''' Main loop '''

    timeLastUpdate = ''

    # Create Schedule object.
    try:
        schedule = Schedule(schedule_url)
    except:
        pass

    # Sort the list of events in chronological order
    schedule.events = schedule.sortEventsByDatetime()

    while True:
        # Remove any passed events from our list of events
        schedule.prunePastEvents()

        rooms = []
        games = []

        for i in range(2):
            rooms.append(Timeslots(schedule.getRoom(schedule.events[i])))
        
        i = 0
        for room in rooms:
            if room.initHtml():
                room.update()
                timeLastUpdate = datetime.now().strftime('%H:%M')

                # Find all games during focused shifts
                r = rooms[i].findGames(schedule.events[i]['timeStart'], schedule.events[i]['timeEnd'])

                games.append(rooms[i].filter(r, Status='Reserved'))

            else:
                print("Bad Request - make sure there is an established connection")

            i += 1

        print('Last Report fetched: ' + timeLastUpdate + '\n')
        if len(games) > 0:
            showGames(games[0])
            showGames(games[1])

        time.sleep(INTERVAL)

def showGames(g):
    ''' Function to print out the dict of info in a nice fashion
    to the commandline. '''
    for i in g:
        print(i['Start'].strftime('%Y-%m-%d'))
        print(i['Start'].strftime('%H:%M') + '-' + i['End'].strftime('%H:%M') + '\n')

if __name__ == '__main__':

    url = ''

    with open('.icalURL', 'r') as icalURL:
        url = icalURL.readline().replace('\n', '')
    
    main(url)

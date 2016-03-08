import time
from Schedule import Schedule
from Timeslots import Timeslots

INTERVAL = 300

def main(schedule_url):
    ''' Main loop '''
    
    # Create Timeslot objects for each room.
    bank = Timeslots('bank')
    bunker = Timeslots('bunker')
    zombie_lab = Timeslots('zombie_lab')

    # Create Schedule object.
    schedule = Schedule(schedule_url)

    while True:

        # Update each room

        # Report any changes for current and next shift

        # Log

        time.sleep(INTERVAL)

if __name__ == '__main__':

    url = ''

    with open('.icalURL', 'r') as icalURL:
        url = icalURL.readline().replace('\n', '')
    
    main(url)

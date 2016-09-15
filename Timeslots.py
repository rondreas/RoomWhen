#!/usr/bin/env python3
import requests
import datetime
from bs4 import BeautifulSoup

class Timeslots:
    '''Creates an object with timeslots for given room.'''
    def __init__(self, room, weeks):
        self.room = room    # Valid options are; bank, bunker, zombie_lab
        self.weeks = weeks  # list of iso week numbers

        self.url = "http://stockholm.roomescapelive.se/reservation/index/game/{}"

        self.games = []     # container for games

    def getSoup(self, week):
        '''Get the HTML with availability for given week. Returning Beautiful
        Soup Object of the HTML response.'''

        # Get the webpage
        r = requests.get(self.url.format(self.room)\
                         + '/week/{}'.format(week))

        if r.status_code == requests.codes.ok:
            # Soupify the page
            soup = BeautifulSoup(r.text.encode('utf-8').decode('ascii', 'ignore'),
                                 'html.parser')
            return soup
        else:
            return None
        

    def update(self):
        '''Get and store two weeks of timeslots into a list. Return list of
        dicts containing all important information like; start and end time,
        date. And the status of the game.'''

        games = []
        date = None
        sTime = None
        eTime = None
        status = ''

        soups = []
        # Create a soup object for each week. And append to our containter list.
        for week in self.weeks:
            soups.append(self.getSoup('{}'.format(week)))

        # Iterate our soup objects, should be one per week requested.
        for soup in soups:

            # Get the tag holding the calendar widget
            calendarWidget = soup.find('table',
                                       class_='table booking_table hidden-xs')

            # Fetch all timeslots and their status from the calendar widget
            htmlTimeslots = list()
            buttonContainers = calendarWidget.find_all("div", "buttonContainer")
            for btn in buttonContainers:
                htmlTimeslots.append(btn.parent.get('class')[1])
                
            # Each calendar widget on page has the starting day of that week as yy-mm-dd
            weekStart = datetime.datetime.strptime(soup.find('span', id='calendar').get('data-date'), '%Y-%m-%d')
            
            sTime = datetime.time(9, 30)
            eTime = datetime.time(10, 30)
            
            # Make a list of all dates that week.
            weekDates = []
            for day in range(7):
                weekDates.append((weekStart + datetime.timedelta(day)).date())
            
            for i in range(len(htmlTimeslots )):
                
                # Increment time, really hacky solution but it works.
                if(i > 0 and i % 7 == 0):
                    delta = datetime.timedelta(hours = 1, minutes = 30)
                    sTime = (datetime.datetime.combine(datetime.date(1,1,1), sTime)\
                            + delta).time()
                    eTime = (datetime.datetime.combine(datetime.date(1,1,1), eTime)\
                            + delta).time()

                # Set date to be correct for current html div.
                date = weekDates[i%7]

                # Get status of game.
                if("unavailableButton" in htmlTimeslots[i]):
                    status = "Unavailable"
                elif("reservedButton" in htmlTimeslots[i]):
                    status = "Reserved"
                elif("availableButton" in htmlTimeslots[i]):
                    status = "Available"
                elif("lastMinuteButton" in htmlTimeslots[i]):
                    status = "Last Minute"
                else:
                    status = ''

                data = {"Start": datetime.datetime.combine(date, sTime),
                        "End": datetime.datetime.combine(date, eTime),
                        "Status": status,
                        "Timestamp":sTime.strftime("%H:%M") + '-' + eTime.strftime("%H:%M")}

                games.append(data)

            # We've now parsed all games for first souped week.
            weekStart = weekStart + datetime.timedelta(7)

        self.games = games

    def findGames(self, DTstart, DTend):
        ''' Find all games inside the timespan of DTstart and DTend. '''

        foundGames = []
        
        for game in self.games:
            if game['Start'] >= DTstart and game['End'] <= DTend:
                foundGames.append(game)

        return foundGames

    def filter(self, dictList, **kwargs):
        ''' Searches list of dictionaries for matches to
        all key value pairs expressed as key='value' '''
        
        sortedList = []

        for dictionary in dictList:
            matches = 0
            for key, value in kwargs.items():
                if dictionary[key] == value:
                    matches += 1
                if matches == len(kwargs):
                    sortedList.append(dictionary)

        return sortedList

if __name__ == '__main__':
    timeslots = Timeslots('zombie_lab', [datetime.datetime.now().isocalendar()[1]])
    timeslots.update()
    for game in timeslots.games:
        print(game)

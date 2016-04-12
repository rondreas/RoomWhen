#!/usr/bin/env python3
import requests
import datetime
from bs4 import BeautifulSoup

class Timeslots:
    '''Creates an object with timeslots for given room.'''
    def __init__(self, room, weeks):
        self.room = room    # Valid options are; bank, bunker, zombie_lab
        self.weeks = weeks

        self.session = requests.Session()
        self.url = "http://stockholm.roomescapelive.se/reservation/index/game/{}/step/{}"
        self.payload = {'game': self.room, 'group': '4'}
        self.header = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:39.0) Gecko/20100101 Firefox/39.0'}

        self.games = []

    def initHtml(self):
        '''Request first step of the booking process, seeing we're blocked from
        going straight for the second step which has all timeslots.'''
        try:
            r = self.session.get(self.url.format(self.room, '1'))
            return r.status_code == requests.codes.ok
        except:
            return False

    def getHtml(self, week):
        '''Get the HTML with availability for given week. Returning Beautiful
        Soup Object of the HTML response.'''

        r = self.session.post(self.url.format(self.room, '2')\
                              + '/group/4/week/{}'.format(week),
                              data = self.payload,
                              headers = self.header)

        soup = BeautifulSoup(r.content, 'html.parser')

        return soup

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
            soups.append(self.getHtml('{}'.format(week)))

        # Iterate our soup objects, should be one per week requested.
        for soup in soups:

            # Fetch all timeslots
            htmlTimeslots = soup.find_all("div", "col-lg-12-5 text-center")

            # Get the starting date of the week fetched.
            weekStart = datetime.datetime.strptime(soup.find_all("small", limit = 1)[0].contents[0], "%Y-%m-%d")

            # Set starting time depending on room.
            if(self.room == 'bank' or self.room == 'bunker'):
                sTime = datetime.time(9, 30)
                eTime = datetime.time(10, 30)
            elif(self.room == 'zombie_lab'):
                sTime = datetime.time(10, 00)
                eTime = datetime.time(11, 00)
            
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
                if("well reservationUnavailableButton" in str(htmlTimeslots[i])):
                    status = "Unavailable"
                elif("well reservationReservedButton" in str(htmlTimeslots[i])):
                    status = "Reserved"
                elif("well cp reservationAvailableButton" in str(htmlTimeslots[i])):
                    status = "Available"
                elif("well cp reservationLastMinuteButton" in str(htmlTimeslots[i])):
                    status = "Last Minute"
                else:
                    status = ''

                data = {"Start": datetime.datetime.combine(date, sTime),
                        "End": datetime.datetime.combine(date, eTime),
                        "Status":status}

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
    timeslots = Timeslots('zombie_lab', [1])
    if timeslots.initHtml():
        timeslots.update()
        for game in timeslots.games:
            print(game)
    else:
        print("Bad request")

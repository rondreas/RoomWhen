#!/usr/bin/env python3

import requests
import datetime
from bs4 import BeautifulSoup

class Timeslots:
    '''Creates an object with timeslots for given room.'''
    def __init__(self, room):
        self.room = room    # Valid options are; bank, bunker, zombie_lab

        self.session = requests.Session()
        self.url = "http://stockholm.roomescapelive.se/reservation/index/game/{}/step/{}"
        self.payload = {'game': self.room, 'group': '4'}
        self.header = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:39.0) Gecko/20100101 Firefox/39.0'}

        self.games = []

    def initHtml(self):
        '''Request first step of the booking process, seeing we're blocked from
        going straight for the second step which has all timeslots.'''
        r = self.session.get(self.url.format(self.room, '1'))
        return r.status_code == requests.codes.ok

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

        soups = [self.getHtml('0'),
                 self.getHtml('1')]

        # Get date for timeslot.
        today = datetime.datetime.now()
        weekStart = today - datetime.timedelta(today.weekday())

        for soup in soups:
            htmlTimeslots = soup.find_all("div", "col-lg-12-5 text-center")

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

                data = {"Start": sTime.strftime("%H:%M"),
                        "End": eTime.strftime("%H:%M"),
                        "Status":status,
                        "Date": str(date),
                        "Datetime":datetime.datetime.combine(date, eTime)}

                games.append(data)

            # We've now parsed all games for first souped week.
            weekStart = weekStart + datetime.timedelta(7)

        self.games = games

    def findGames(self, DTstart, DTend):
        ''' Find all games inside the timespan of DTstart and DTend. '''

        foundGames = []
        
        for game in self.games:
            gameDT = datetime.datetime.strptime((game['Date'] + ' ' + game['Start']), 
                                                "%Y-%m-%d %H:%M")

            if gameDT >= DTstart and gameDT < DTend:
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
    zombie = Timeslots('zombie_lab')
    
    if zombie.initHtml():
        zombie.update()
        for game in zombie.games:
            print(game)
    else:
        print("Bad request")

#!/usr/bin/python

from flask.app import Flask
import requests
import json
import os
import time, datetime
from pprint import pprint
from operator import itemgetter
import flask
from flask import request, jsonify

app = flask.Flask(__name__)
app.config["DEBUG"] = True


class Team:
    def __init__(self, franchise_dict, slack_id=''):
        self.name = franchise_dict['name']
        self.id = franchise_dict['id']
        self.icon = franchise_dict['icon']
        self.slack_id = slack_id
        self.record = '0-0-0'
        self.playoff_record = '0-0-0'
        self.total_pts = 0
        self.wins = 0
        self.playoff_wins = 0
        self.losses = 0
        self.playoff_losses = 0
    
    def calc_record(self, teams, ytd_scores, record_type, debug=False):
        """
        {
            "1" : [
                {
                    "id" : "0011",
                    "nonstarters" : "15284,12652,15282,12676,14834,",
                    "opt_pts" : "107.6",
                    "optimal" : "13593,0531,9694,15282,15284,14102,13299,14841,13629,",
                    "player" : [
                        {
                        "id" : "13593",
                        "score" : "22.00",
                        "shouldStart" : "1",
                        "status" : "starter"
                        },
                    ...
                    "score" : "83.5",
                    "starters" : "13593,13604,14841,10271,14102,13629,13299,9694,0531,"
                },


        """
        if record_type == 'reg':
            weeks = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14']
        elif record_type == 'playoff':
            weeks = ['15', '16']

        for week, scores in ytd_scores.items():
            w, l = 0, 0

            if not scores or not scores[0].get('score') or week not in weeks:
                continue
            
            pts_for = float([x for x in scores if x['id'] == self.id][0]['score'])

            self.total_pts += pts_for
            for x in scores:
                pts_against = float(x['score'])

                if x ['id'] == self.id or x['id'] not in [y.id for y in teams] or self.id not in [y.id for y in teams]:
                    continue

                if debug:
                    print('{} ({}) - {} ({}) : '.format(self.id, pts_for, x['id'], pts_against), end='')
                if pts_for > pts_against:
                    if debug:
                        print('W')
                    w += 1
                elif pts_for < pts_against:
                    if debug:
                        print('L')
                    l += 1                
            
            if record_type == 'reg':
                self.wins += w 
                self.losses += l 
                self.record = '{}-{}'.format(self.wins, self.losses)

            elif record_type == 'playoff':
                self.playoff_wins += w 
                self.playoff_losses += l 
                self.playoff_record = '{}-{}'.format(self.playoff_wins, self.playoff_losses)

            # if self.id == '0006':
            #     print('{} | {}-{}-{}'.format(pts_for, w, l, d))

        self.total_pts = round(self.total_pts, 2)

    def update(self, teams, ytd_scores):
        self.wins, self.playoff_wins, self.losses, self.playoff_losses, self.total_pts = 0, 0, 0, 0, 0
        self.calc_record(teams, ytd_scores, 'reg')


class League:
    def __init__(self, year=''):
        if not year:
            year = datetime.date.today().year
        # with open('config.json') as f:
        #     self.config = json.load(f)

        self.api_base_url = 'https://www73.myfantasyleague.com/{}/export'.format(year)
        self.session = requests.Session()
        self.session.headers.update()
        self.session.params.update({'L': '60050', 'JSON': 1})

        self.teams = []
        self.playoff_teams = []
        self.name = ''
        self.scores = {}
        self.build_league_info()
        self.update()

    def update(self):
        self.refresh_scores()
        self.calc_standings()
        
        # Check if playoff slots have been determined
        if self.scores.get('14'):
            print('PLAYOFFS')
            self.teams = sorted(self.teams, key=lambda x: x.wins, reverse=True)
            self.playoff_teams = self.teams[0:6]
            for team in self.playoff_teams:
                team.calc_record(self.playoff_teams, self.scores, 'playoff')

        return self.print_playoff_scoreboard('')

    # def print_scoreboard(self, title):
    #     format_str = '{:45} {:>15} {:>11} {:>9}'
    #     scoreboard = ['```', str(datetime.datetime.today())]
    #     scoreboard.append(format_str.format(title, 'Reg Season', 'Playoffs', 'Total',))
    #     scoreboard.append('-' * 90)
    #     for p in sorted(self.teams, key=lambda x: int(x.record.split('-')[0]), reverse=True):
    #         scoreboard.append(format_str.format(
    #             p.name, 
    #             p.record, 
    #             p.playoff_record,
    #             p.total_pts
    #             ))
        
    #     scoreboard.append('```')
    #     return '\n'.join(scoreboard)
    
    def print_playoff_scoreboard(self, title):
        format_str = '{:40} {:>10} {:>9} {:>9} {:>9}'
        scoreboard = ['```', str(datetime.datetime.today())]
        scoreboard.append(format_str.format(title, 'Record', 'Week 1', 'Week 2', 'Total'))
        scoreboard.append('-' * 81)
        for p in sorted(self.playoff_teams, key=lambda x: x.playoff_wins, reverse=True):
            w1_score = [x for x in self.scores['15'] if p.id == x['id']][0]['score']
            w2_score = [x for x in self.scores['16'] if p.id == x['id']][0]['score']
            scoreboard.append(format_str.format(
                p.name, 
                p.playoff_record, 
                w1_score,
                w2_score,
                round(float(w1_score) + float(w2_score), 2)
                ))
        
        scoreboard.append('```')
        return '\n'.join(scoreboard)

    def simulate_games():
        """
        Simulate remaining games to determin odds of making playoffs/championship
        """
        pass

    def is_stale(self, file_name):
        try:
            mtime = os.path.getmtime(file_name)
        except OSError:
            mtime = 0

        now = int(time.time())

        if now - mtime > 900:
            return True
        else:
            return False

    def refresh_scores(self, force=False):
        if self.is_stale('scores.json'):
            self.session.params.update({'TYPE': 'weeklyResults', 'W': 'YTD'})

            r = self.session.get(self.api_base_url)
            r = r.json()

            for i, v in enumerate(r['allWeeklyResults']['weeklyResults']):
                if v['franchise'][0].get('score'):
                    self.scores[i+1] = sorted(v['franchise'], key=lambda x: float(x['score']), reverse=True)
                else:
                    self.scores[i+1] = v['franchise']

            self.session.params.update({'TYPE': 'liveScoring', 'W': ''})
            r = self.session.get(self.api_base_url)
            r = r.json()
            self.scores[r['liveScoring']['week']] = sorted(r['liveScoring']['franchise'], key=lambda x: float(x['score']), reverse=True)

            with open('scores.json', 'w') as f:
                json.dump(self.scores, f, separators=(',', ':'), indent=2)
        
        with open('scores.json') as f:
            self.scores = json.load(f)

        for t in self.teams:
            t.ytd_scores = self.scores

    def build_league_info(self):
        """
        Get basic league info and list of teams. Should only be first run

        {
        "encoding" : "utf-8",
        "league" : {
            "baseURL" : "https://www73.myfantasyleague.com",
            "bbidConditional" : "Yes",
            "bbidFCFSCharge" : "",
            "bbidIncrement" : "1",
            "bbidMinimum" : "1",
            "bbidSeasonLimit" : "100",
            "bbidTiebreaker" : "TIMESTAMP",
            "bestLineup" : "No",
            "currentWaiverType" : "BBID_FCFS",
            "defaultTradeExpirationDays" : "4",
            "endWeek" : "17",
            "franchises" : {
                "count" : "12",
                "franchise" : [
                    {
                    "abbrev" : "DDFCNC",
                    "bbidAvailableBalance" : "52.00",
                    "country" : "US",
                    "future_draft_picks" : "FP_0001_2021_1,FP_0001_2021_2,FP_0001_2021_4,FP_0001_2021_6,FP_0001_2021_7,FP_0001_2021_8,FP_0001_2021_9,FP_0001_2021_10,FP_0001_2021_11,FP_0001_2021_12,FP_0001_2021_13,FP_0001_2021_14,FP_0001_2021_15,FP_0001_2022_1,FP_0001_2022_2,FP_0001_2022_3,FP_0001_2022_4,FP_0001_2022_5,FP_0001_2022_6,FP_0001_2022_7,FP_0001_2022_8,FP_0001_2022_9,FP_0001_2022_10,FP_0001_2022_11,FP_0001_2022_12,FP_0001_2022_13,FP_0001_2022_14,FP_0001_2022_15,",
                    "icon" : "https://www73.myfantasyleague.com/fflnetdynamic2021/60050_franchise_icon0001.jpg",
                    "id" : "0001",
                    "lastVisit" : "1640052975",
                    "logo" : "https://www73.myfantasyleague.com/fflnetdynamic2021/60050_franchise_logo0001.jpg",
                    "name" : "Din Din with Firecrotch and Normcore",
                    "waiverSortOrder" : "10"
                    },

        """
        if not os.path.isfile('league.json'):
            self.session.params.update({'TYPE': 'league'})
            r = self.session.get(self.api_base_url)
            r = r.json()
            with open('league.json', 'w') as f:
                json.dump(r, f)
        
        with open('league.json') as f:
            league = json.load(f)

        for team in league['league']['franchises']['franchise']:
            self.teams.append(Team(team))
        
        for team in self.teams:
            team.teams = self.teams

        self.name = league['league']['name']

    def calc_standings(self):
        for team in self.teams:
            team.update(self.teams, self.scores)

    def reply(self, message, url):
        """
        reply to slack with the payload.
        """


def help(err=False):
    commands = ['```']
    if err:
        commands.append('Unknown command: {}'.format(err))
        commands.append('')
        
    commands.extend([
        'Available Commands:',
        '  scores  - show the playoff scoreboard',
        '  help    - show available commands and usage',
        '```'
    ])

    return '\n'.join(commands)


if __name__ == '__main__':
    
    @app.route('/', methods=['POST'])
    def main():
        gesl = League()
        gesl.update()
        if request.content_length > 2000:
            return 'NO'
        
        payload = str(request.get_data())
        print(payload)
        payload = payload.split('&')
        params = {}
        for keypair in payload:
            k = keypair.split('=')
            params[k[0].lower()] = k[1].lower()
        
        pprint(params)
        if params['text'] == 'scores':
            return gesl.print_playoff_scoreboard('')

        # elif params['text'] == 'group':
        #     return euro.print_group_tables(params['user_name'])

        # elif 'team' in params['text']:
        #     team_name = params['text'].split('+')[1]
        #     team = [x for x in euro.teams if team_name in x.name.lower()]
        #     if not team:
        #         return 'Unknown team name: {}'.format(team_name)
        #     else:
        #         return team[0].print_team_info()

        # elif params['text'] == 'teams':
        #     return euro.print_remaining_teams()

        # elif params['text'] == 'bracket':
        #     return euro.bracket.print_bracket()

        elif params['text'] == 'help':
            return help()

        else:
            return help(params['text'])
            

    app.run()
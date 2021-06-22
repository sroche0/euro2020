#!/usr/bin/python

from flask.app import Flask
import requests
import json
import os
import time, datetime
from pprint import pprint
import flask
from flask import request, jsonify

app = flask.Flask(__name__)
app.config["DEBUG"] = True


class Person:
    def __init__(self, name):
        self.name = name
        self.teams = []
        self.pts = {
            'Group': 0, 
            '8th Finals': 0, 
            'Quarter-finals': 0, 
            'Semi-finals': 0, 
            'Finals': 0,
            'Total': 0
        }
        self.record = '0-0-0'
        self.total_pts = 0

    def calc_pts(self):
        for team in self.teams:
            for rnd, pts in team.pts.items():
                if 'Qualifying' in rnd:
                    continue
                
                self.pts[rnd] += pts

        self.total_pts = self.pts['Total']
    
    def calc_record(self):
        wins, losses, draws = 0, 0, 0
        for team in self.teams:
            for rnd, results in team.fixtures.items():
                if 'Qualifying' in rnd:
                    continue
                wins += results['w']
                losses += results['l']
                draws += results['d']

        self.record = '{}-{}-{}'.format(wins, losses, draws)

    def update(self):
        self.calc_pts()
        self.calc_record()
    

class Tournament:
    def __init__(self):
        with open('config.json') as f:
            self.config = json.load(f)
        self.headers = {    
            "x-rapidapi-key": self.config['x-rapidapi-key'],
            "x-rapidapi-host": self.config['x-rapidapi-host'],
            }
        self.api_base_url = 'https://api-football-v1.p.rapidapi.com/v3'
        self.team_data = {}
        self.fixtures = {}

        self.teams = []
        
        self.people = []
        for name, teams in self.config['players'].items():
            player = Person(name)
            for country in teams:
                team = (Team(country, name))
                self.teams.append(team)
                player.teams.append(team)

            self.people.append(player)
            player.update()



    def print_group_table(self, group):
        pass

    def print_pool_scoreboard(self):
        format_str = '{:5} {:>9} {:>9} {:>9} {:>9} {:>9} {:>9} {:>9}'
        scoreboard = ['```', str(datetime.datetime.today())]
        scoreboard.append(format_str.format('', 'Record', 'Group', 'Rd 16', 'Quarters', 'Semis', 'Finals', 'Total'))
        scoreboard.append('-' * 76)
        people = sorted(self.people, key=lambda x: (x.total_pts), reverse=True)
        for p in people:
            scoreboard.append(format_str.format(
                p.name, 
                p.record, 
                p.pts['Group'], 
                p.pts['8th Finals'], 
                p.pts['Quarter-finals'], 
                p.pts['Semi-finals'], 
                p.pts['Finals'], 
                p.pts['Total']
                ))
        
        scoreboard.append('```')
        return '\n'.join(scoreboard)
        pass

    def refresh_cache(self):
        self.fixtures = self.fetch_fixture_data()
        self.team_data = self.fetch_teams_data()

    def is_stale(self, file_name):
        try:
            mtime = os.path.getmtime(file_name)
        except OSError:
            mtime = 0

        now = int(time.time())

        if now - mtime > 3600:
            return True
        else:
            return False

    def fetch_fixture_data(self, force=False):
        if self.is_stale('fixtures.json'):
            url = "{}/fixtures".format(self.api_base_url)

            params = {"league": "4", "season": '2020'}
            r = requests.get(url, headers=self.headers, params=params)

            resp = r.text
            resp = resp.replace('winner":null', 'winner":"null"')
            resp = json.loads(resp)

            with open('fixtures.json', 'w') as f:
                f.write(json.dumps(resp, separators=(',', ':'), indent=2))
        
        with open('fixtures.json') as f:
            return json.load(f)

    def fetch_teams_data(self):
        # TODO only fetch this if teams.json doesnt exist. build a custom cache on first run and save that as teams.json
        if self.is_stale('teams.json'):
            url = "{}/teams".format(self.api_base_url)

            params = {"league": "4", "season": '2020'}
            r = requests.get(url, headers=self.headers, params=params)

            resp = r.json()

            with open('teams.json', 'w') as f:
                f.write(json.dumps(resp, separators=(',', ':'), indent=2))
        
        with open('teams.json') as f:
            return json.load(f)

    def print_group_tables(self):
        resp = ['```']
        format_str = '{:15} {:>4} {:>4} {:>4} {:>4}'
        headers = format_str.format('', 'W', 'L', 'D', 'PTS')
        for group in ['Group A', 'Group B', 'Group C', 'Group D', 'Group E', 'Group F']:
            group_table = [group, headers, '-' * 36]

            teams = [x for x in self.teams if group in x.group]

            teams = sorted(teams, key=lambda x: (x.pts['Group']), reverse=True)
            for t in teams:
                group_table.append(format_str.format(t.name, t.fixtures['Group']['w'], t.fixtures['Group']['l'], t.fixtures['Group']['d'], t.pts['Group']))
            
            group_table.append('')
            group_table.append('')

            resp.append('\n'.join(group_table))

        
        resp.append('```')
        return '\n'.join(resp)


class Team:
    def __init__(self, country, owner):
        with open('config.json') as f:
            self.config = json.load(f)
        self.name = country
        self.id = ''        
        self.group = ''
        self.owner = owner
        self.fixtures = self.get_fixture_results()
        self.pts = self.calc_pts()

    def get_fixture_results(self):
        results = {}
        with open('fixtures.json') as f:
            fixtures = json.load(f)

        for game in fixtures['response']:
            if game['fixture']['status']['short'] != 'FT':
                continue

            rnd = game['league']['round']
            group = ''

            if 'Qualifying' in rnd:
                rnd = 'Qualifying'
            elif 'Group' in rnd:
                group = game['league']['round']
                rnd = 'Group'

            if not results.get(rnd):
                results[rnd] = {'w': 0, 'l': 0, 'd': 0}

            for side, team in game['teams'].items():
                if team['name'] == self.name:
                    if not self.group and group:
                        self.group = group
                    if team['winner'] is True:
                        results[rnd]['w'] += 1
                    elif team['winner'] == 'null':
                        results[rnd]['d'] += 1
                    else:
                        results[rnd]['l'] += 1


        return results

    def calc_pts(self):
        pts = {'Total': 0}
        for rnd, results in self.fixtures.items():
            if 'Qualifying' in rnd:
                    continue

            if not pts.get(rnd):
                pts[rnd] = 0
            
            pts[rnd] += results['w'] * self.config['pts'][rnd]
            pts['Total'] += results['w'] * self.config['pts'][rnd]
            pts[rnd] += results['d']
            pts['Total'] += results['d']

        return pts

    def calc_record(self):
        wins, losses, draws = 0, 0, 0

        for rnd, results in self.fixtures.items():
            if 'Qualifying' in rnd:
                continue
            wins += results['w']
            losses += results['l']
            draws += results['d']

        self.record = '{}-{}-{}'.format(wins, losses, draws)

    def parse_team_data(self):
        with open('teams.json') as f:
            teams = json.load(f)
        
        for t in teams['response']:
            if t['team']['name'] != self.name:
                continue
            self.id = t['team']['id']


def help():
    commands = [
        '```',
        'Available Commands:',
        '',
        'scores - print the pool scores',
        'group  - print the group tables',
        'help   - print this help text',
        '```'
    ]

    return '\n'.join(commands)


if __name__ == '__main__':
    
    @app.route('/', methods=['POST'])
    def main():
        euro = Tournament()
        euro.refresh_cache()
        if request.content_length > 2000:
            return 'NO'
            
        payload = request.get_data()
        payload = payload.split('&')
        params = {}
        for keypair in payload:
            k = keypair.split('=')
            params[k[0]] = k[1]
        
        if params['text'] == 'scores':
            return euro.print_pool_scoreboard()

        elif params['text'] == 'group':
            return euro.print_group_tables()
        elif params['text'] == 'help':
            return help()

        else:
            return 'Unknown command: {}'.format(params['text'])
            

    app.run()


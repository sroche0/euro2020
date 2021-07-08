#!/usr/bin/python

from flask.app import Flask
import requests
import json
import os
import time, datetime
from pprint import pprint
import flask
from flask import request, jsonify
from bracket import Bracket

app = flask.Flask(__name__)
app.config["DEBUG"] = True


class Person:
    def __init__(self, name, slack_id):
        self.name = name
        self.slack_id = slack_id
        self.teams = []
        self.pts = {
            'Group': 0, 
            '8th Finals': 0, 
            'Quarter-finals': 0, 
            'Semi-finals': 0, 
            'Final': 0,
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
            for rnd, results in team.record.items():
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
        self.fixtures = self.refresh_fixture_data()

        self.teams = []
        self.people = []

        for name, data in self.config['players'].items():
            player = Person(name, data['slack_id'])
            for country in data['teams']:
                team = (Team(country, name, data['slack_id']))
                self.teams.append(team)
                player.teams.append(team)

            self.people.append(player)
            player.update()
        
        self.bracket = Bracket()
        self.bracket.g_1['teams'] = ['Belgium', 'Portugal', 'Italy', 'Austria']
        self.bracket.g_2['teams'] = ['France', 'Switzerland', 'Spain', 'Croatia']
        self.bracket.g_3['teams'] = ['Sweden', 'Ukraine', 'England', 'Germany']
        self.bracket.g_4['teams'] = ['Netherlands', 'Czech Republic', 'Wales', 'Denmark']
        self.cache_team_data()

    def print_pool_scoreboard(self):
        format_str = '{:5} {:>9} {:>9} {:>9} {:>9} {:>9} {:>9} {:>9}'
        scoreboard = ['```', str(datetime.datetime.today())]
        scoreboard.append(format_str.format('', 'Record', 'Group', 'Rd 16', 'Quarters', 'Semis', 'Final', 'Total'))
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
                p.pts['Final'], 
                p.pts['Total']
                ))
        
        scoreboard.append('```')
        return '\n'.join(scoreboard)

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

    def refresh_fixture_data(self, force=False):
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

    def cache_team_data(self):
        team_data = {}
        for team in self.teams:
            team_data[team.name] = {
                'id': team.id,
                'owner': team.owner,
                'name': team.name
            }

        with open('teams.json', 'w') as f:
            json.dump(team_data, f, separators=(',', ':'), indent=2 )

    def print_group_tables(self, user):
        resp = ['```']
        format_str = '{:15} {:>4} {:>4} {:>4} {:>4}'
        headers = format_str.format('', 'W', 'L', 'D', 'PTS')
        for group in ['Group A', 'Group B', 'Group C', 'Group D', 'Group E', 'Group F']:
            group_table = [group, headers, '-' * 36]

            teams = [x for x in self.teams if group in x.group]

            teams = sorted(teams, key=lambda x: (x.pts['Group']), reverse=True)
            for t in teams:
                if user == t.owner_id:
                    name = '{} *'.format(t.name)
                else:
                    name = t.name
                group_table.append(format_str.format(name, t.fixtures['Group']['w'], t.fixtures['Group']['l'], t.fixtures['Group']['d'], t.pts['Group']))
            
            group_table.append('')
            group_table.append('')

            resp.append('\n'.join(group_table))

        resp.append('* Teams owned by you')
        resp.append('```')
        return '\n'.join(resp)

    def print_remaining_teams(self):
        resp = ['```']
        team_format_str = '  {:18} {:7} {:4}'
        for person in self.people:
            resp.append('{}:'.format( person.name))
            for team in person.teams:
                if team.eliminated:
                    name = '*{}*'.format(team.name)
                else:
                    name = team.name
                resp.append(team_format_str.format(name, team.recordstr, team.pts['Total']))
            
            resp.append('')

        resp.append('* Eliminated teams')
        resp.append('```')
        
        return '\n'.join(resp)


class Team:
    def __init__(self, country, owner, owner_id):
        with open('config.json') as f:
            self.config = json.load(f)
        self.name = country
        self.id = ''
        self.owner_id = owner_id        
        self.group = ''
        self.owner = owner
        self.fixtures = []
        self.record = self.get_fixture_results()
        self.recordstr =  self.calc_record()
        self.pts = self.calc_pts()
        self.eliminated = self.is_eliminated()

    def get_fixture_results(self):
        results = {}
        with open('fixtures.json') as f:
            fixtures = json.load(f)

        for game in fixtures['response']:
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
                    self.fixtures.append(game)
                    if not self.group and group:
                        self.group = group

                    if not self.id:
                        self.id = team['id']

                    if game['fixture']['status']['long'] != 'Match Finished':
                        continue

                    if team['winner'] is True:
                        results[rnd]['w'] += 1
                    elif team['winner'] == 'null':
                        results[rnd]['d'] += 1
                    else:
                        results[rnd]['l'] += 1


        return results

    def calc_pts(self):
        pts = {'Total': 0}
        for rnd, results in self.record.items():
            rnd = str(rnd)
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

        for rnd, results in self.record.items():
            if 'Qualifying' in rnd:
                continue
            wins += results['w']
            losses += results['l']
            draws += results['d']

        return'{}-{}-{}'.format(wins, losses, draws)

    def print_team_info(self):
        resp = ['```', self.name, '  Owner: {}'.format(self.owner)]
        if self.eliminated:
            resp.append('  {} *Eliminated'.format(self.recordstr))
        else:
            resp.append('  {}'.format(self.recordstr))

        resp.append('```')
        return '\n'.join(resp)

    def is_eliminated(self):
        last_game = self.fixtures[-1]
        if last_game['fixture']['status']['long'] != 'Match Finished':
            return False
        
        for side, team in last_game['teams'].items():
            if team['name'] == self.name:
                 if team['winner'] is True:
                    return False
        
        return True


def help(err=False):
    commands = ['```']
    if err:
        commands.append('Unknown command: {}'.format(err))
        commands.append('')
        
    commands.extend([
        'Available Commands:',
        '  scores  - show the pool scoreboard',
        '  group   - print the group tables',
        '  teams   - show table of teams sorted by player',
        '  bracket - print the knockout bracket',
        '  help    - show available commands and usage',
        '```'
    ])

    return '\n'.join(commands)


if __name__ == '__main__':
    
    @app.route('/', methods=['POST'])
    def main():
        euro = Tournament()
        if request.content_length > 2000:
            return 'NO'
            
        payload = request.get_data()
        payload = payload.split('&')
        params = {}
        for keypair in payload:
            k = keypair.split('=')
            params[k[0].lower()] = k[1].lower()
        
        pprint(params)
        if params['text'] == 'scores':
            return euro.print_pool_scoreboard()

        elif params['text'] == 'group':
            return euro.print_group_tables(params['user_name'])

        # elif 'team' in params['text']:
        #     team_name = params['text'].split('+')[1]
        #     team = [x for x in euro.teams if team_name in x.name.lower()]
        #     if not team:
        #         return 'Unknown team name: {}'.format(team_name)
        #     else:
        #         return team[0].print_team_info()

        elif params['text'] == 'teams':
            return euro.print_remaining_teams()

        elif params['text'] == 'bracket':
            return euro.bracket.print_bracket()

        elif params['text'] == 'help':
            return help()

        else:
            return help(params['text'])
            

    app.run()


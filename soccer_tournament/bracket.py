import json
from pprint import pprint

class Bracket:
    def __init__(self):
        self.g_1 = {'teams': [], 'Quarter-finals': [], 'Semi-finals':[], 'Finals': []}
        self.g_2 = {'teams': [], 'Quarter-finals': [], 'Semi-finals':[], 'Finals': []}
        self.g_3 = {'teams': [], 'Quarter-finals': [], 'Semi-finals':[], 'Finals': []}
        self.g_4 = {'teams': [], 'Quarter-finals': [], 'Semi-finals':[], 'Finals': []}
        self.rounds = ['Quarter-finals', 'Semi-finals', 'Finals']
        
    def build_bracket(self):
        bracket = {'Quarter-finals': [], 'Semi-finals':[], 'Finals': []}
        for r in self.rounds:
            teams = self.build_round(r)
            
            for g in [self.g_1, self.g_2, self.g_3, self.g_4]:
                scheduled = False
                for t in g['teams']:
                    if t in teams:
                        g[r].append(t)
                        scheduled = True
          
                if not scheduled:
                    g[r].append('TBD')
        
        team_format_str = '{:_<16s}'
        bot_team_format_str = '{:_<16s}|'
        vert_bar_format = '{:16}|'

        top_final = [x for x in bracket['Finals'] if x in self.g_1['teams'] or x in self.g_2['teams']]
        if top_final:
            top_final = team_format_str.format(top_final[0])
        else:
            top_final = team_format_str.format('TBD')


        bottom_final = [x for x in bracket['Finals'] if x in self.g_3['teams'] or x in self.g_4['teams']]
        if bottom_final:
            bottom_final = team_format_str.format(bottom_final[0])
        else:
            bottom_final = team_format_str.format('TBD')

        bracket_list = []
        
        bracket_list.append([team_format_str.format(self.g_1['teams'][0]), '', '', '', '', '', ''])
        bracket_list.append([vert_bar_format.format(''), '___', team_format_str.format(self.g_1['Quarter-finals'][0]), '', '', '', ''])
        bracket_list.append([bot_team_format_str.format(self.g_1['teams'][1]), '', vert_bar_format.format(''), '', '', '', ''])
        bracket_list.append(['', '', vert_bar_format.format(''), '___', team_format_str.format(self.g_1['Semi-finals'][0]), '', ''])
        bracket_list.append([team_format_str.format(self.g_1['teams'][2]), '', vert_bar_format.format(''), '', vert_bar_format.format(''), '', ''])
        bracket_list.append([vert_bar_format.format(''), '___', bot_team_format_str.format(self.g_1['Quarter-finals'][1]), '', vert_bar_format.format(''), '', ''])
        bracket_list.append([bot_team_format_str.format(self.g_1['teams'][3]), '', '', '', vert_bar_format.format(''), '', ''])
        bracket_list.append(['', '', '', '', vert_bar_format.format(''), '___', top_final])
        bracket_list.append([team_format_str.format(self.g_2['teams'][0]), '', '', '', vert_bar_format.format(''), '', ''])
        bracket_list.append([vert_bar_format.format(''), '___', team_format_str.format(self.g_2['Quarter-finals'][0]), '', vert_bar_format.format(''), '', ''])
        bracket_list.append([bot_team_format_str.format(self.g_2['teams'][1]), '', vert_bar_format.format(''), '', vert_bar_format.format(''), '', ''])
        bracket_list.append(['', '', vert_bar_format.format(''), '___', bot_team_format_str.format(self.g_2['Semi-finals'][0]), '', ''])
        bracket_list.append([team_format_str.format(self.g_2['teams'][2]), '', vert_bar_format.format(''), '', '', '', ''])
        bracket_list.append([vert_bar_format.format(''), '___', bot_team_format_str.format(self.g_2['Quarter-finals'][1]), '', '', '', ''])
        bracket_list.append([bot_team_format_str.format(self.g_2['teams'][3]), '', '', '', '', '', ''])

        bracket_list.append(['', '', '', '', '', '', ''])
        bracket_list.append(['-' * 75, '', '', '', '', '', ''])
        bracket_list.append(['', '', '', '', '', '', ''])

        bracket_list.append([team_format_str.format(self.g_3['teams'][0]), '', '', '', '', '', ''])
        bracket_list.append([vert_bar_format.format(''), '___', team_format_str.format(self.g_3['Quarter-finals'][0]), '', '', '', ''])
        bracket_list.append([bot_team_format_str.format(self.g_3['teams'][1]), '', vert_bar_format.format(''), '', '', '', ''])
        bracket_list.append(['', '', vert_bar_format.format(''), '___', team_format_str.format(self.g_3['Semi-finals'][0]), '', ''])
        bracket_list.append([team_format_str.format(self.g_3['teams'][2]), '', vert_bar_format.format(''), '', vert_bar_format.format(''), '', ''])
        bracket_list.append([vert_bar_format.format(''), '___', bot_team_format_str.format(self.g_3['Quarter-finals'][1]), '', vert_bar_format.format(''), '', ''])
        bracket_list.append([bot_team_format_str.format(self.g_3['teams'][3]), '', '', '', vert_bar_format.format(''), '', ''])
        bracket_list.append(['', '', '', '', vert_bar_format.format(''), '___', top_final])
        bracket_list.append([team_format_str.format(self.g_4['teams'][0]), '', '', '', vert_bar_format.format(''), '', ''])
        bracket_list.append([vert_bar_format.format(''), '___', team_format_str.format(self.g_4['Quarter-finals'][0]), '', vert_bar_format.format(''), '', ''])
        bracket_list.append([bot_team_format_str.format(self.g_4['teams'][1]), '', vert_bar_format.format(''), '', vert_bar_format.format(''), '', ''])
        bracket_list.append(['', '', vert_bar_format.format(''), '___', bot_team_format_str.format(self.g_4['Semi-finals'][0]), '', ''])
        bracket_list.append([team_format_str.format(self.g_4['teams'][2]), '', vert_bar_format.format(''), '', '', '', ''])
        bracket_list.append([vert_bar_format.format(''), '___', bot_team_format_str.format(self.g_4['Quarter-finals'][1]), '', '', '', ''])
        bracket_list.append([bot_team_format_str.format(self.g_4['teams'][3]), '', '', '', '', '', ''])

        return bracket_list
        

    def build_round(self, round_name):
        teams = []
        with open('fixtures.json') as f:
            fixtures = json.load(f)

        for game in fixtures['response']:
            if round_name != game['league']['round']:
                continue            
            teams.append(game['teams']['home']['name'])
            teams.append(game['teams']['away']['name'])

        return teams


    def print_bracket(self):
        lines = self.build_bracket()
        format_str = '{:17}{:3}{:17}{:3}{:17}{:3}{:17}'
        resp = ['```']

        for line in lines:
            resp.append(format_str.format(line[0], line[1], line[2], line[3], line[4], line[5], line[6]))

        resp.append('```')

        return '\n'.join(resp)
        # 15 lines tall
        # 4 teams, 3 separators wide, each separator is 3 characters per half
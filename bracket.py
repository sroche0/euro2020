import json

class Bracket:
    def __init__(self):
        self.g_1 = {'teams': [], 'Quarter-finals': [], 'Semi-finals':[]}
        self.g_2 = {'teams': [], 'Quarter-finals': [], 'Semi-finals':[]}
        self.g_3 = {'teams': [], 'Quarter-finals': [], 'Semi-finals':[]}
        self.g_4 = {'teams': [], 'Quarter-finals': [], 'Semi-finals':[]}
        self.rounds = ['Quarter-finals', 'Semi-finals', 'Finals']
        
    def build_bracket(self):
        bracket = {'Quarter-finals': [], 'Semi-finals':[], 'Finals': []}
        for r in self.rounds:
            bracket[r] = self.build_round(r)
            if r == 'Finals':
                continue
            
            for g in [self.g_1, self.g_2, self.g_3, self.g_4]:
                if g['teams'][0] in bracket[r]:
                    g[r].append(g['teams'][0])
                elif g['teams'][1] in bracket[r]:
                    g[r].append(g['teams'][1])
                else:
                    g[r].append('TBD')

                if g['teams'][2] in bracket[r]:
                    g[r].append(g['teams'][2])
                elif g['teams'][3] in bracket[r]:
                    g[r].append(g['teams'][3])
                else:
                    g[r].append('TBD')
                
        top_final = [x for x in bracket['Finals'] if x in self.g_1['teams'] or x in self.g_2['teams']]
        if top_final:
            top_final = top_final[0]
        else:
            top_final = 'TBD'


        bottom_final = [x for x in bracket['Finals'] if x in self.g_3['teams'] or x in self.g_4['teams']]
        if bottom_final:
            bottom_final = bottom_final[0]
        else:
            bottom_final = 'TBD'

        bracket_list = []
        
        bracket_list.append([self.g_1['teams'][0], '--   ', '', '', '', '', ''])
        bracket_list.append(['', '  |--', self.g_1['Quarter-finals'][0], '--   ', '', '', ''])
        bracket_list.append([self.g_1['teams'][1], '--   ', '', '  |  ', '', '', ''])
        bracket_list.append(['', '', '', '  |--', self.g_1['Semi-finals'][0], '--   ', ''])
        bracket_list.append([self.g_1['teams'][2], '--   ', '', '  |  ', '', '  |  ', ''])
        bracket_list.append(['', '  |--', self.g_1['Quarter-finals'][1], '--   ', '', '  |  ', ''])
        bracket_list.append([self.g_1['teams'][3], '--   ', '', '', '', '  |  ', ''])
        bracket_list.append(['', '', '', '', '', '  |--', top_final])
        bracket_list.append([self.g_2['teams'][0], '--   ', '', '', '', '  |  ', ''])
        bracket_list.append(['', '  |--', self.g_2['Quarter-finals'][0], '--   ', '', '  |  ', ''])
        bracket_list.append([self.g_2['teams'][1], '--   ', '', '  |  ', '', '  |  ', ''])
        bracket_list.append(['', '', '', '  |--', self.g_2['Semi-finals'][0], '--   ', ''])
        bracket_list.append([self.g_2['teams'][2], '--   ', '', '  |  ', '', '', ''])
        bracket_list.append(['', '  |--', self.g_2['Quarter-finals'][1], '--   ', '', '', ''])
        bracket_list.append([self.g_2['teams'][3], '--   ', '', '', '', '', ''])

        bracket_list.append(['', '', '', '', '', '', ''])
        bracket_list.append(['-' * 75, '', '', '', '', '', ''])
        bracket_list.append(['', '', '', '', '', '', ''])

        bracket_list.append([self.g_3['teams'][0], '--   ', '', '', '', '', ''])
        bracket_list.append(['', '  |--', self.g_3['Quarter-finals'][0], '--   ', '', '', ''])
        bracket_list.append([self.g_3['teams'][1], '--   ', '', '  |  ', '', '', ''])
        bracket_list.append(['', '', '', '  |--', self.g_3['Semi-finals'][0], '--   ', ''])
        bracket_list.append([self.g_3['teams'][2], '--   ', '', '  |  ', '', '  |  ', ''])
        bracket_list.append(['', '  |--', self.g_3['Quarter-finals'][1], '--   ', '', '  |  ', ''])
        bracket_list.append([self.g_3['teams'][3], '--   ', '', '', '', '  |  ', ''])
        bracket_list.append(['', '', '', '', '', '  |--', top_final])
        bracket_list.append([self.g_4['teams'][0], '--   ', '', '', '', '  |  ', ''])
        bracket_list.append(['', '  |--', self.g_4['Quarter-finals'][0], '--   ', '', '  |  ', ''])
        bracket_list.append([self.g_4['teams'][1], '--   ', '', '  |  ', '', '  |  ', ''])
        bracket_list.append(['', '', '', '  |--', self.g_4['Semi-finals'][0], '--   ', ''])
        bracket_list.append([self.g_4['teams'][2], '--   ', '', '  |  ', '', '', ''])
        bracket_list.append(['', '  |--', self.g_4['Quarter-finals'][1], '--   ', '', '', ''])
        bracket_list.append([self.g_4['teams'][3], '--   ', '', '', '', '', ''])

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
        format_str = '{:14} {:5} {:14} {:5} {:14} {:5} {:14}'
        resp = ['```']

        for line in lines:
            resp.append(format_str.format(line[0], line[1], line[2], line[3], line[4], line[5], line[6]))

        resp.append('```')

        return '\n'.join(resp)
        # 15 lines tall
        # 4 teams, 3 separators wide, each separator is 3 characters per half
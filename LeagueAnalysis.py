#!/usr/bin/env python
# coding: utf-8

# # Imports

import requests
import pandas as pd
from bs4 import BeautifulSoup
import numpy as np
from datetime import datetime
from funcy import join
from os.path import exists
from argparse import ArgumentParser
import sys

# # Variables (Optional Values)
def input_handler():
    
    parser = ArgumentParser(description='Calculate LOL Regions Ranking')

    # Which year to start scraping for each event
    parser.add_argument('-m','--msi',type=int,required=True ,help='MSI Start Year')
    parser.add_argument('-w','--worlds',type=int,required=True,help='Worlds Start Year')

    # Delete last generated Data to retrieve new set of Data
    parser.add_argument('-t','--template',type=int,required=False,default=False,help="Generate new 'data_ranking.xlsx'? (DEV recommended)")

    # Reference points for first place in every event 
    parser.add_argument('-s','--score',type=int,required=False,default=10,help="Reference points for first place in every event")
    
    # Whether consider or not unique campaigns for each region
    parser.add_argument('-u','--unique',type=int,required=True, help="Consider only best campaign for each region?")
    
    # Activate DEBUG mode to retrieve code exceptions
    parser.add_argument('-d','--debug',type=int,required=False,default=False,help="Get detailed log for exceptions (DEV recommended)")
    args = parser.parse_args()

    if not args.debug:
        sys.tracebacklimit = 0
    
    valid_msi_years = list(np.arange(2015,datetime.now().year))
    valid_worlds_years = list(np.arange(2014,datetime.now().year))

    if args.msi not in valid_msi_years or args.worlds not in valid_worlds_years:
        raise ValueError('Year must be valid')

    return args

# # Web Scraping

class ScrapeLeague:
    
    def __init__(self,msi_start_year,worlds_start_year):
        self.current_year = datetime.now().year
        self.events = ['Worlds','MSI']
        self.worlds_start_year = worlds_start_year
        self.msi_start_year = msi_start_year
        
    def catch_event_data(self,year:int,worlds:bool):
        
        if worlds:        
            final_endpoint = 'Season_World_Championship'
        else:
            final_endpoint = 'Mid-Season_Invitational'

        data_url = f"https://lol.fandom.com/wiki/{year}_{final_endpoint}"
        page = requests.get(data_url)
        soup = BeautifulSoup(page.content,'html.parser')
        indicators = soup.select('.tournament-results-team')
        team_list = [[count, ind.select('.teamname')[0].a['title']] for count,ind in enumerate(indicators,start=1)]
        return team_list
    
    def map_teams(self,tp_list,region,event):
        map_list = []

        for tp_value,reg in zip(tp_list,region): 
            t_dict = {  
                    'Team': tp_value[1],
                    'Position': tp_value[0],
                    'Region': reg,
                    'Championship': event
                     }
            map_list.append(t_dict)
        return map_list
    
    def get_region(self,team_list):
        region_list = []
        for x,y in team_list:
            y = y.replace(' ','_')
            team_url=f'https://lol.fandom.com/wiki/{y}'
            page = requests.get(team_url)
            soup = BeautifulSoup(page.content,'html.parser')
            try:
                indicators = soup.select('.region-object span')[0]
                region_list.append(indicators.text)
            except:
                indicators = soup.select('.region-object span')
                region_list.append(indicators)

        return region_list
    
    def set_event_data(self,event):
        if event == 'Worlds':
            years = list(np.arange(self.worlds_start_year,self.current_year))
            type_event = True
        elif event == 'MSI':
            years = list(np.arange(self.msi_start_year,self.current_year))
            type_event = False
        return years,type_event
    
    def generate_df(self,all_data):
        fixed_data = join(join(all_data))
        df = pd.DataFrame(fixed_data)
        return df
    
    def run(self):
        all_list = []
        for event in self.events:
            all_event_list = []
            years_list,event_bool = self.set_event_data(event)
            for year in years_list: 
                event_str = f'{event} {year}'
                print(f'Getting {event_str} ranking data...\n')
                tp_list = self.catch_event_data(year,event_bool)
                print(f'Getting {event_str} teams regions...\n')
                r_list = self.get_region(tp_list)
                print(f'Mapping {event_str}...\n')
                mapped_teams = self.map_teams(tp_list,r_list,event_str)
                all_event_list.append(mapped_teams)
            all_list.append(all_event_list)
        df = self.generate_df(all_list)

        return df


# # Template Management

class Template:
    def __init__(self):
        self.m_temp = []
        self.w_temp = []
    def read_template(self,df):
        dt = df.to_dict(orient="index")
        for y in dt.values():
            print(f"Fixing {y['Event']} Data Template...\n")
            if y['Event'] == 'MSI':
                self.m_temp = self.fix_data(y)
            elif y['Event'] == 'Worlds':
                self.w_temp = self.fix_data(y)

    def fix_data(self,template):
        for col,row in template.items():
            if row.startswith('1'): # First place designates that there's a ranking after it
                row = row.replace(' ','').replace('-',' ').split('/')
            for count,x in enumerate(row):
                if len(x) > 1:
                    ref = x.split(' ')

                    if len(ref) > 1:
                        ref = list(map(int, ref)) 
                        sub = ref[1] - ref[0]
                        if sub > 1:
                            for x in range(1,sub):
                                ref.append(ref[0] + x)
                        ref.sort()
                        row[count] = ref
            template[col] = row
        template.pop('Event')
        return template
    def run(self,file_name):
        try:
            print('Reading Template...\n')
            df = pd.read_excel(file_name) 
            self.read_template(df)
            print(f"Done with Template!\n")
        except FileNotFoundError as exc:
            raise exc
        except Exception:
            raise DataError(f'Data in ranking_template.xlsx mismatch with template')
        return self.m_temp,self.w_temp


# # Scoring Results (for Unique or Multiple teams per Region)

class ScoreResults:
    def __init__(self,initscore,df,msi_start,worlds_start):
        self.initscore = int(initscore) + 1
        self.df = df
        self.duplicates = []
        event_list = self.df['Championship'].unique()
        self.dict_df = {event: {} for event in event_list}
        self.valid_msi = list(np.arange(msi_start,datetime.now().year))
        self.valid_worlds = list(np.arange(worlds_start,datetime.now().year))

        
    def __score_per_row(self,row):
        event,year = row['Championship'].split(' ')
        
        if event == 'MSI':
            
            if int(year) in self.valid_msi:
                pos_list = msi_temp[int(year)]
                try:
                    ind_val = self.initscore - pos_list.index(str(row['Position']))
                except:
                    for pos in pos_list:
                        if type(pos) is list and row['Position'] in pos:
                            ind_val = self.initscore - pos_list.index(pos)
                return ind_val
        
        elif event == 'Worlds':
            if int(year) in self.valid_worlds:
                pos_list = worlds_temp[int(year)]
                try:
                    ind_val = self.initscore - pos_list.index(str(row['Position']))
                except:
                    for pos in pos_list:
                        if type(pos) is list and row['Position'] in pos:
                            ind_val = self.initscore - pos_list.index(pos)
                return ind_val

    def __check_duplicates_regions(self):# Transform score DataFrame to unique team per Region
        
        
        for count,(region,pos_ind,event) in enumerate(zip(self.df['Region'],self.df['PositionIndex'],self.df['Championship'])):
            self.dict_df[event][count] = {}
            self.dict_df[event][count]['Region'] = region 
            self.dict_df[event][count]['Championship'] = event 
            self.dict_df[event][count]['PositionIndex'] = pos_ind
        for key,group in self.dict_df.items():
            seen_region = []
            for keygroup,value in group.items():
                if value['Region'] in seen_region:
                    self.duplicates.append(keygroup)
                else:
                    seen_region.append(value['Region'])
        
                    
    def __remove_duplicates_regions(self):
        for key in self.dict_df.keys():
            for duplicate in self.duplicates:
                if duplicate in self.dict_df[key]:
                    del self.dict_df[key][duplicate]
    def __fix_df_dict(self):
        ref_dict = {}
        for value in self.dict_df.values():
            ref_dict.update(value)
        self.dict_df = ref_dict
                
    def generate_unique_df(self):
        self.__check_duplicates_regions()
        self.__remove_duplicates_regions()
        self.__fix_df_dict()
        self.df = pd.DataFrame.from_dict(self.dict_df,orient='index')        
    
    def generate_default_df(self): # Generates default score DataFrame with multiple teams per Region
        self.df['PositionIndex'] = self.df.apply(self.__score_per_row, axis=1)
        
    def sum_per_region(self):
        self.df = self.df.groupby('Region')[['PositionIndex']].agg('sum').sort_values('PositionIndex',ascending=False).reset_index()
        self.df.rename(columns={'PositionIndex': 'Overall Score'}, inplace=True)
        
    def run(self,unique_teams:bool):
        self.generate_default_df()
        if unique_teams:        
            self.generate_unique_df()
        self.sum_per_region()
        
        return self.df

class DataError(Exception):
    pass

# # Run

args = input_handler()
if args.template:
    file_exists = exists('./data_ranking.xlsx')
    if file_exists:
        print('Data Ranking already exists and is ready to use!\n')
        df = pd.read_excel('data_ranking.xlsx')
    else:
        raise FileNotFoundError("Cannot use data_ranking.xlsx because file does not exist")
    
else:        
    print("Data Ranking doesn't exist. Gathering new data...\n")
    df = ScrapeLeague(args.msi,args.worlds).run()
    df.to_excel('data_ranking.xlsx',index=False)
    print("Data Gathering succeeded!\n")
    
print('Getting Championship Templates...')
msi_temp,worlds_temp = Template().run('ranking_template.xlsx')

print('Scoring Regions...')
sc_df = ScoreResults(args.score,df,args.msi,args.worlds).run(unique_teams=args.unique)

print('Saving sheet...')
sc_df.to_excel('region_ranking.xlsx',index=False)

print('Process Finished')

    
print(sc_df)

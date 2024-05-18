import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
import urllib.request as ur
import requests as req
import os
from tqdm import tqdm
import time

dat_path = os.getcwd()[:-4] + 'data/'
figures_path = os.getcwd()[:-4] + 'figures/'



def get_match_id(soup):
    id_table = soup.find('table')
    temp_id = id_table.findAll('td', attrs={'class':'ScoreCardBanner'})
    try:
        temp_id_text = temp_id[0].text.replace(' ','').replace('\r\n','').replace('\t','').replace(' ','').split('#')
        return (int(temp_id_text[-1]))
    except:
        return None



def get_match_date(soup):
    match_summary_table = soup.find('table', attrs={'class':'ScorecardHeaderTable'})
    try:
        match_summary_table_body = match_summary_table.findAll('td', attrs={'class':'ScorecardHeader'})     
        return match_summary_table_body[2].text.replace('  ','').replace('\r\n','')
    except:
        return None
    

def match_venue_PoM(soup):
    match_summary_table = soup.find_all('table', attrs={'border':'0', 'cellpadding':'5', 'cellspacing':'0', 'width':'890'})
    try:
        a = match_summary_table[0].text.split('Venue')
    except:
        return None, None
    
    prob_items = ['\r', '\n', '\t', 'View', 'Partnerships', 'Toss', 'NOTES', '\xa0']

    venue = a[1].split('Toss')[0]
    for item in prob_items:
        venue = venue.replace(item, '').strip()
    
    
    try:
        try:
            PoM = a[1].split('Toss')[1].split('Player of Match')[1]
        except:
            PoM = a[1].split('Toss')[1].split('Players of Match')[1]
    except:
        return venue, None


    for item in prob_items:
        PoM = PoM.replace(item, '').strip()

    if 'No Award' in PoM:
        PoM = None

    return venue, PoM



def get_team_stat(soup):
    team_name_table = soup.find('table')
    team_name_table_body = team_name_table.findAll('tr')
    team_name_text = team_name_table_body[8].findAll('td')
    
    raw_text = team_name_text[0].text.replace(' ','').replace('\xa0','').replace('\t','').split('\n')
    raw_text = [x.replace('\r','') for x in raw_text]
    raw_text = [x for x in raw_text if x != '']

    t1 = raw_text[0]
    t2 = raw_text[2]

    raw_text_T1 = (raw_text[1].split(')'))
    o1 = float(raw_text_T1[0].replace('(','').replace('overs',''))
    r1 = int(raw_text_T1[1].split('/')[0])
    try:
        w1 = int(raw_text_T1[1].split('/')[1])
    except:
        w1 = 10

    if len(raw_text) < 4:
        return None

    raw_text_T2 = (raw_text[3].split(')'))
    o2 = float(raw_text_T2[0].replace('(','').replace('overs',''))
    r2 = int(raw_text_T2[1].split('/')[0])
    try:
        w2 = int(raw_text_T2[1].split('/')[1])
    except:
        w2 = 10

    #first_team_check 
    first_team_check_table = soup.find('table')
    first_team_check_body = first_team_check_table.findAll('tr')
    first_team_check_text = first_team_check_body[12].findAll('td')
    first_team = first_team_check_text[0].text.replace(' ','').replace('\xa0','').replace('\t','').replace('\r','').replace('\n','')

    if t1 == first_team:
        return t1, o1, r1, w1, t2, o2, r2, w2
    else:
        return t2, o2, r2, w2, t1, o1, r1, w1



def get_bat_stat(temp, pla, pl_name, bat_pos, bat_run, bat_ball, bat_four, bat_six, bat_wicket, captain, wicketkeeper):

    
    # wicketkeeper
    if '†' in temp[0]:
        wicketkeeper[pla] = 1
    # captain
    if '*' in temp[0]:
        captain[pla] = 1
    # player name 
    pl_name[pla] = temp[0].replace('\r','').replace('\xa0','').replace('\n','').replace('†','').replace('*','')  


    # batting position
    if pla <= 10:
        bat_pos[pla] = pla + 1
    else:
        bat_pos[pla] = pla - 10

    # captain or normal player
    check, run, ball, four, six = 2, 4, 6, 9, 12
    if (wicketkeeper[pla] == 1) or (captain[pla] == 1):
        check, run, ball, four, six = 3, 5, 7, 10, 13


    # batting stat
    if (temp[check].replace('\r','').replace('\xa0','').replace(' ','') != '') and (temp[run].replace('\r','').replace('\xa0','').replace(' ','') != ''):
        # batting run
        bat_run[pla] = int(temp[run].replace('\r','').replace('\xa0','').replace(' ',''))
        # batting ball
        if temp[ball].replace('\r','').replace('\xa0','').replace(' ','') == '':
            bat_ball[pla] = bat_run[pla]
        else:
            bat_ball[pla] = int(temp[ball].replace('\r','').replace('\xa0','').replace(' ',''))
        # batting four
        bat_four[pla] = int(temp[four].replace('\r','').replace('\xa0','').replace(' ',''))
        # batting six
        bat_six[pla] = int(temp[six].replace('\r','').replace('\xa0','').replace(' ',''))
        # batting wicket
        bat_wicket[pla] = temp[check].replace('\r','').replace('\xa0','').replace(' ','')

    else:
        # batting run
        bat_run[pla] = 'NA'
        # batting ball
        bat_ball[pla] = 'NA'
        # batting four
        bat_four[pla] = 'NA'
        # batting six
        bat_six[pla] = 'NA'
        # batting wicket
        bat_wicket[pla] = 'NA'

    return pl_name, bat_pos, bat_run, bat_ball, bat_four, bat_six, bat_wicket, captain, wicketkeeper


def get_no_bat_stat(temp, pl_name, bat_pos, bat_run, bat_ball, bat_four, bat_six, bat_wicket, captain, wicketkeeper, shift_index):

    no_bat_plrs_list = temp[-1].split(',')
            
    for n, no_bat_plr in enumerate(no_bat_plrs_list):
        temp_plr_name = no_bat_plr.strip().replace('\r','').replace('\xa0','').replace('\n','')
        
        pl_name[n+shift_index-len(no_bat_plrs_list)] = temp_plr_name.replace('†','').replace('*','')
        bat_pos[n+shift_index-len(no_bat_plrs_list)] = n+shift_index-len(no_bat_plrs_list)+1
        bat_run[n+shift_index-len(no_bat_plrs_list)] = 'NA'
        bat_ball[n+shift_index-len(no_bat_plrs_list)] = 'NA'
        bat_four[n+shift_index-len(no_bat_plrs_list)] = 'NA'
        bat_six[n+shift_index-len(no_bat_plrs_list)] = 'NA'
        bat_wicket[n+shift_index-len(no_bat_plrs_list)] = 'NA'
        if '†' in temp_plr_name:
            wicketkeeper[n+shift_index-len(no_bat_plrs_list)] = 1
        if '*' in temp_plr_name:
            captain[n+shift_index-len(no_bat_plrs_list)] = 1

    return pl_name, bat_pos, bat_run, bat_ball, bat_four, bat_six, bat_wicket, captain, wicketkeeper
    


def get_bowl_stat(temp, pl_name, bowl_over, bowl_maiden, bowl_runs, bowl_wicket):
    try:
        pl_ind = pl_name.index(temp[2].replace('\r','').replace('\xa0',''))
        # bowling over
        bowl_over[pl_ind] = float(temp[5].replace('\r','').replace('\xa0','').replace(' ',''))
        # bowling maiden
        bowl_maiden[pl_ind] = int(temp[8].replace('\r','').replace('\xa0','').replace(' ',''))
        # bowling runs
        bowl_runs[pl_ind] = int(temp[11].replace('\r','').replace('\xa0','').replace(' ',''))
        # bowling wicket
        bowl_wicket[pl_ind] = int(temp[14].replace('\r','').replace('\xa0','').replace(' ',''))
    except:
        pass

    return bowl_over, bowl_maiden, bowl_runs, bowl_wicket



def get_player_stat(soup):
    
    pl_name, bat_pos, bat_run, bat_ball, bat_four, bat_six, bat_wicket, bowl_over, bowl_maiden, bowl_runs, bowl_wicket, captain, wicketkeeper = ([0]*22 for x in range(13))

    player_score_table = soup.find('table', attrs={'class':'ScorecardMain'})
    player_score_table_body = player_score_table.findAll('tr')



    # Team 1 batting stat
    cccc = 0
    for pla in range(11):
        temp = player_score_table_body[pla+2].text.split('\n')
        temp = [x for x in temp if x != '']

        if 'did not bat' in player_score_table_body[pla+2].text.lower():

            pl_name, bat_pos, bat_run, bat_ball, bat_four, bat_six, bat_wicket, captain, wicketkeeper = get_no_bat_stat(temp, pl_name, bat_pos, bat_run, bat_ball, bat_four, bat_six, bat_wicket, captain, wicketkeeper, shift_index=11)

            cccc = 1
            continue
        
        if cccc == 0:
            pl_name, bat_pos, bat_run, bat_ball, bat_four, bat_six, bat_wicket, captain, wicketkeeper = get_bat_stat(temp, pla, pl_name, bat_pos, bat_run, bat_ball, bat_four, bat_six, bat_wicket, captain, wicketkeeper)



    # Team 2 batting stat
    team2_bat_pos_start = pla + 2 + 1       # look a little bit above for why + 2
    while('batting' not in player_score_table_body[team2_bat_pos_start].text.lower()):
        team2_bat_pos_start += 1
    team2_bat_pos_start += 1


    cccc = 0
    for pla in range(11, 22):   
        temp = player_score_table_body[pla+team2_bat_pos_start - 11].text.split('\n')
        temp = [x for x in temp if x != '']

        if 'did not bat' in player_score_table_body[pla+team2_bat_pos_start - 11].text.lower():
            pl_name, bat_pos, bat_run, bat_ball, bat_four, bat_six, bat_wicket, captain, wicketkeeper = get_no_bat_stat(temp, pl_name, bat_pos, bat_run, bat_ball, bat_four, bat_six, bat_wicket, captain, wicketkeeper, shift_index=22)

            cccc = 1
            continue
        
        if cccc == 0:
            pl_name, bat_pos, bat_run, bat_ball, bat_four, bat_six, bat_wicket, captain, wicketkeeper = get_bat_stat(temp, pla, pl_name, bat_pos, bat_run, bat_ball, bat_four, bat_six, bat_wicket, captain, wicketkeeper)
    



    '''
    Bowling data collection begins below
    '''

    # Team 1 bowling stat
    pla = team2_bat_pos_start
    while('bowling' not in player_score_table_body[pla].text.lower()):
        pla += 1
    while(player_score_table_body[pla].text.replace('\xa0\r','').replace('\r','').replace(' ','').replace('\n','') != ''):
        temp = player_score_table_body[pla].text
        temp = temp.split('\n')

        bowl_over, bowl_maiden, bowl_runs, bowl_wicket = get_bowl_stat(temp, pl_name, bowl_over, bowl_maiden, bowl_runs, bowl_wicket)
        
        pla += 1


    # Team 2 bowling stat
    pla = team2_bat_pos_start
    while('bowling' not in player_score_table_body[pla].text.lower()):
        pla -= 1

    pla = pla + 1
    while(player_score_table_body[pla].text.replace('\xa0\r','').replace('\r','').replace(' ','').replace('\n','') != ''):
        temp = player_score_table_body[pla].text
        temp = temp.split('\n')

        bowl_over, bowl_maiden, bowl_runs, bowl_wicket = get_bowl_stat(temp, pl_name, bowl_over, bowl_maiden, bowl_runs, bowl_wicket)
        
        pla += 1

    for bowl in range(len(bowl_over)):
        if bowl_over[bowl] == 0:
            bowl_over[bowl] = 'NA'
            bowl_maiden[bowl] = 'NA'
            bowl_runs[bowl] = 'NA'
            bowl_wicket[bowl] = 'NA'

    return pl_name, bat_pos, bat_run, bat_ball, bat_four, bat_six, bat_wicket, bowl_over, bowl_maiden, bowl_runs, bowl_wicket, captain, wicketkeeper



def odi_data():
    df = pd.DataFrame(columns=['search_ID','Match_ID','Match_Date','Venue','Team1','Overs_T1','Runs_T1','Wickets_T1','player_name_T1','bat_pos_T1','bat_run_T1','bat_balls_T1','bat_fours_T1','bat_sixes_T1','bat_wicket_T1','bowl_overs_T1','bowl_maiden_T1','bowl_runs_T1','bowl_wickets_T1','captain_T1','wicketkeeper_T1','Team2','Overs_T2','Runs_T2','Wickets_T2','player_name_T2','bat_pos_T2','bat_run_T2','bat_balls_T2','bat_fours_T2','bat_sixes_T2','bat_wicket_T2','bowl_overs_T2','bowl_maiden_T2','bowl_runs_T2','bowl_wickets_T2','captain_T2','wicketkeeper_T2','PoM','Winner'])

    #iterate over all matches
    for i in range(5000):

        ind = str(i).zfill(4)

        temp_data = [0 for i in range(len(df.columns))]
        try:
            # url = ur.urlopen('http://howstat.com/cricket/Statistics/Matches/MatchScorecard_ODI.asp?MatchCode='+ind,timeout=5)
            url = req.get('http://howstat.com/cricket/Statistics/Matches/MatchScorecard_ODI.asp?MatchCode='+ind,timeout=5)
        except:
            url = req.get('http://howstat.com/cricket/Statistics/Matches/MatchScorecard_ODI.asp?MatchCode='+ind,timeout=2000)
        
        # soup = BeautifulSoup(url.read(),features="lxml")
        soup = BeautifulSoup(url.content,features="lxml")

        sanity_check = 1    #default value

        ###### Match ID ######
        match_id = get_match_id(soup)
        if match_id != None:
            temp_data[df.columns.get_loc('Match_ID')] = get_match_id(soup)
        else:
            sanity_check = 0


        ###### Match Date ######
        match_date = get_match_date(soup)
        if match_date != None:
            temp_data[df.columns.get_loc('Match_Date')] = match_date
        else:
            sanity_check = 0

        ####### Team Statistics ######
        if sanity_check ==1:
            try:
                t1, o1, r1, w1, t2, o2, r2, w2 = get_team_stat(soup)
            except:
                sanity_check = 0

        ####### Match Venue and Player of the Match ######
        venue, PoM = match_venue_PoM(soup)
        if venue == None or PoM == None:
            sanity_check = 0



        '''
        ##############################
        If all good till now, then only proceed to player statistics
        ##############################
        '''



        if sanity_check == 1:
            ###### team statistics ######
            ## team name, overs, runs, wickets

            temp_data[df.columns.get_loc('Team1')] = t1
            temp_data[df.columns.get_loc('Team2')] = t2
            
            temp_data[df.columns.get_loc('Overs_T1')] = o1
            temp_data[df.columns.get_loc('Overs_T2')] = o2

            temp_data[df.columns.get_loc('Runs_T1')] = r1
            temp_data[df.columns.get_loc('Runs_T2')] = r2

            temp_data[df.columns.get_loc('Wickets_T1')] = w1
            temp_data[df.columns.get_loc('Wickets_T2')] = w2

            temp_data[df.columns.get_loc('Venue')] = venue
            temp_data[df.columns.get_loc('search_ID')] = ind
            temp_data[df.columns.get_loc('PoM')] = PoM


            ######## result ########
            if r1 > r2:
                temp_data[df.columns.get_loc('Winner')] = t1
            elif r1 < r2:
                temp_data[df.columns.get_loc('Winner')] = t2
            elif r1 == r2:
                temp_data[df.columns.get_loc('Winner')] = 'Tie'
            else: 
                temp_data[df.columns.get_loc('Winner')] = 'error'


            ###### player statistics ######
            ## player name, bat_pos, batting runs, batting balls, batting fours, batting sixes, batting_wicket, bowling overs, bowling maiden, bowling runs, bowling wickets, captain, wicketkeeper

            pl_name, bat_pos, bat_run, bat_ball, bat_four, bat_six, bat_wicket, bowl_over, bowl_maiden, bowl_runs, bowl_wicket, captain, wicketkeeper = get_player_stat(soup)

            

            for j in range(11):
                template_data = temp_data.copy()
                template_data[df.columns.get_loc('player_name_T1')] = pl_name[j]
                template_data[df.columns.get_loc('bat_pos_T1')] = bat_pos[j]
                template_data[df.columns.get_loc('bat_run_T1')] = bat_run[j]
                template_data[df.columns.get_loc('bat_balls_T1')] = bat_ball[j]
                template_data[df.columns.get_loc('bat_fours_T1')] = bat_four[j]
                template_data[df.columns.get_loc('bat_sixes_T1')] = bat_six[j]
                template_data[df.columns.get_loc('bat_wicket_T1')] = bat_wicket[j]
                template_data[df.columns.get_loc('bowl_overs_T1')] = bowl_over[j]
                template_data[df.columns.get_loc('bowl_maiden_T1')] = bowl_maiden[j]
                template_data[df.columns.get_loc('bowl_runs_T1')] = bowl_runs[j]
                template_data[df.columns.get_loc('bowl_wickets_T1')] = bowl_wicket[j]
                template_data[df.columns.get_loc('captain_T1')] = captain[j]
                template_data[df.columns.get_loc('wicketkeeper_T1')] = wicketkeeper[j]

                template_data[df.columns.get_loc('player_name_T2')] = pl_name[j+11]
                template_data[df.columns.get_loc('bat_pos_T2')] = bat_pos[j+11]
                template_data[df.columns.get_loc('bat_run_T2')] = bat_run[j+11]
                template_data[df.columns.get_loc('bat_balls_T2')] = bat_ball[j+11]
                template_data[df.columns.get_loc('bat_fours_T2')] = bat_four[j+11]
                template_data[df.columns.get_loc('bat_sixes_T2')] = bat_six[j+11]
                template_data[df.columns.get_loc('bat_wicket_T2')] = bat_wicket[j+11]
                template_data[df.columns.get_loc('bowl_overs_T2')] = bowl_over[j+11]
                template_data[df.columns.get_loc('bowl_maiden_T2')] = bowl_maiden[j+11]
                template_data[df.columns.get_loc('bowl_runs_T2')] = bowl_runs[j+11]
                template_data[df.columns.get_loc('bowl_wickets_T2')] = bowl_wicket[j+11]
                template_data[df.columns.get_loc('captain_T2')] = captain[j+11]
                template_data[df.columns.get_loc('wicketkeeper_T2')] = wicketkeeper[j+11]

                df.loc[len(df)] = template_data

        
        if (i%100 == 0) and (i != 0):
            df.to_csv(dat_path+f'ODI_data_{i}.csv')

        print(i, ' is done.')


    time_now = int(time.time())  

    df.to_csv(dat_path+f'ODI_data_new_unmerged_{time_now}.csv')
    ##remove all previous files
    for i in range(0, 5000, 100):
        try:
            os.remove(dat_path+f'ODI_data_{i}.csv')
        except:
            pass


odi_data()
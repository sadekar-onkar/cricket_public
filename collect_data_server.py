import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
import urllib.request as ur
import os
from tqdm import tqdm

ROOTHPATH = os.getcwd()

# ind = '4083'
# url = ur.urlopen('http://howstat.com/cricket/Statistics/Matches/MatchScorecard_ODI.asp?MatchCode='+ind)
# soup = BeautifulSoup(url.read(),features="lxml")

def get_match_id(soup):
    id_table = soup.find('table')
    temp_id = id_table.findAll('td', attrs={'class':'ScoreCardBanner2'})
    try:
        temp_id_text = temp_id[0].text.replace(' ','').replace('\r\n','').replace('\t','').replace(' ','').split('#')
        return (int(temp_id_text[-1]))
    except:
        return None

def get_match_date(soup):
    match_summary_table = soup.find('table', attrs={'class':'Table_D'})
    try:
        match_summary_table_body = match_summary_table.findAll('td', attrs={'class':'TextBlackBold8'})     
        return match_summary_table_body[2].text.replace('  ','').replace('\r\n','')
    except:
        return None

def match_venue_PoM(soup):
    match_summary_table = soup.find_all('table', attrs={'class':'Table_D'})
    try:
        a = match_summary_table[1].text.split('Venue')
        venue = a[1].split('Toss')[0].replace('\r\n                \n\n', '').replace('\n\n\n\n\r\n                  ','')
        PoM = a[1].split('Toss')[1].split('Player of Match')[1].replace('\n\n\n\n\r\n\t\t\t\t\t\t\t\t\tPartnerships\r\n\t\t\t\t\t\t\t\t\n\nView\n\n\n','').replace('\r\n                \n\n','')
    except:
        venue = None
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
        wicketkeeper[pla-1] = 1
    # captain
    if '*' in temp[0]:
        captain[pla-1] = 1
    # player name 
    pl_name[pla-1] = temp[0].replace('\r','').replace('\xa0','').replace('\n','').replace('†','').replace('*','')  


    # batting position
    if pla <= 11:
        bat_pos[pla-1] = pla
    else:
        bat_pos[pla-1] = pla-11

    # captain or normal player
    check, run, ball, four, six = 2, 4, 6, 9, 12
    if (wicketkeeper[pla-1] == 1) or (captain[pla-1] == 1):
        check, run, ball, four, six = 3, 5, 7, 10, 13


    # batting stat
    if (temp[check].replace('\r','').replace('\xa0','').replace(' ','') != '') and (temp[run].replace('\r','').replace('\xa0','').replace(' ','') != ''):
        # batting run
        bat_run[pla-1] = int(temp[run].replace('\r','').replace('\xa0','').replace(' ',''))
        # batting ball
        if temp[ball].replace('\r','').replace('\xa0','').replace(' ','') == '':
            bat_ball[pla-1] = bat_run[pla-1]
        else:
            bat_ball[pla-1] = int(temp[ball].replace('\r','').replace('\xa0','').replace(' ',''))
        # batting four
        bat_four[pla-1] = int(temp[four].replace('\r','').replace('\xa0','').replace(' ',''))
        # batting six
        bat_six[pla-1] = int(temp[six].replace('\r','').replace('\xa0','').replace(' ',''))
        # batting wicket
        bat_wicket[pla-1] = temp[check].replace('\r','').replace('\xa0','').replace(' ','')

    else:
        # batting run
        bat_run[pla-1] = 'NA'
        # batting ball
        bat_ball[pla-1] = 'NA'
        # batting four
        bat_four[pla-1] = 'NA'
        # batting six
        bat_six[pla-1] = 'NA'
        # batting wicket
        bat_wicket[pla-1] = 'NA'

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

    player_score_table = soup.find('table', attrs={'class':'Scorecard'})
    player_score_table_body = player_score_table.findAll('tr')

    venue, PoMdata = match_venue_PoM(soup)

    # Team 1 batting stat
    for pla in range(1,12):
        temp = player_score_table_body[pla].text.split('\n')
        temp = [x for x in temp if x != '']

        pl_name, bat_pos, bat_run, bat_ball, bat_four, bat_six, bat_wicket, captain, wicketkeeper = get_bat_stat(temp, pla, pl_name, bat_pos, bat_run, bat_ball, bat_four, bat_six, bat_wicket, captain, wicketkeeper)

    # find team 2 batting stat position
    while('target' not in player_score_table_body[pla].text):
        pla += 1

    t2_bat_pos = pla+1

    # Team 2 batting stat
    for ind, ind2 in zip(range(12,23),range(pla+1,pla+12)):     
        temp = player_score_table_body[ind2].text.split('\n')
        temp = [x for x in temp if x != '']
        pla = ind

        pl_name, bat_pos, bat_run, bat_ball, bat_four, bat_six, bat_wicket, captain, wicketkeeper = get_bat_stat(temp, pla, pl_name, bat_pos, bat_run, bat_ball, bat_four, bat_six, bat_wicket, captain, wicketkeeper)


    # Team 1 bowling stat
    while('Bowling' not in player_score_table_body[ind2].text):
        ind2 += 1

    ind2 += 2
    while(player_score_table_body[ind2].text.replace('\xa0\r','').replace('\r','').replace(' ','').replace('\n','') != ''):
        temp = player_score_table_body[ind2].text
        temp = temp.split('\n')

        bowl_over, bowl_maiden, bowl_runs, bowl_wicket = get_bowl_stat(temp, pl_name, bowl_over, bowl_maiden, bowl_runs, bowl_wicket)
        
        ind2 += 1


    # Team 2 bowling stat
    while('Bowling' not in player_score_table_body[t2_bat_pos].text):
        t2_bat_pos -= 1

    t2_bowl = t2_bat_pos + 1
    while(player_score_table_body[t2_bowl].text.replace('\xa0\r','').replace('\r','').replace(' ','').replace('\n','') != ''):
        temp = player_score_table_body[t2_bowl].text
        temp = temp.split('\n')

        bowl_over, bowl_maiden, bowl_runs, bowl_wicket = get_bowl_stat(temp, pl_name, bowl_over, bowl_maiden, bowl_runs, bowl_wicket)
        
        t2_bowl += 1

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
    for i in tqdm(range(6500)):

        ind = str(i).zfill(4)

        temp_data = [0 for i in range(len(df.columns))]
        try:
            url = ur.urlopen('http://howstat.com/cricket/Statistics/Matches/MatchScorecard_ODI.asp?MatchCode='+ind,timeout=5)
        except:
            url = ur.urlopen('http://howstat.com/cricket/Statistics/Matches/MatchScorecard_ODI.asp?MatchCode='+ind,timeout=2000)
        soup = BeautifulSoup(url.read(),features="lxml")

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

        
        if sanity_check ==1:
            try:
                t1, o1, r1, w1, t2, o2, r2, w2 = get_team_stat(soup)
            except:
                sanity_check = 0

        if sanity_check == 1:

            venue, PoM = match_venue_PoM(soup)
            
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
            # print(i, ' is done.')
            df.to_csv(ROOTHPATH[:-4]+f'/Data/ODI_data_{i}.csv')

    df.to_csv(ROOTHPATH[:-4]+f'/Data/ODI_data_new_unmerged.csv')
    ##remove all previous files
    for i in range(0, 6500, 100):
        try:
            os.remove(ROOTHPATH[:-4]+f'/Data/ODI_data_{i}.csv')
        except:
            pass

odi_data()
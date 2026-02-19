from io import StringIO
from collections import defaultdict

import pandas as pd

from basketball_reference_scraper.drafts import get_draft_class
from basketball_reference_scraper.request_utils import get_wrapper
from bs4 import BeautifulSoup, Comment


DRAFT_CLASSES = {i for i in range(1995, 2026)}

REMOVE_COLS = [
    'COLLEGE', 'TOTALS_PTS', 'TOTALS_TRB', 'TOTALS_AST', 'SHOOTING_FG%', 'SHOOTING_3P%', 'SHOOTING_FT%', 'PER_GAME_MP',
    'PER_GAME_PTS', 'PER_GAME_TRB', 'PER_GAME_AST'
]

AWARDS_URL = 'https://www.basketball-reference.com/awards/awards_{}.html'

def voting_dict_maker():
    return {
        'all_nba': 0,
        'all_defense': 0,
        'all_rookie': 0,
    }

def years_dict_maker():
    return {
        'all_first': list(),
        'all_second': list(),
        'all_third': list(),
        'all_races': list(),
        'def_first': list(),
        'def_second': list(),
        'mvp': list(),
    }

def get_drafts():
    res = list()
    for cls in DRAFT_CLASSES:
        newdf = get_draft_class(cls)
        newdf['year'] = cls
        res.append(newdf)
    return pd.concat(res).drop(REMOVE_COLS, axis=1)

def get_awards():
    def extract_table_from_comments(table_id: str):
        """
        Extract a table that's hidden in HTML comments.
        """
        # Find all comments in the page
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))

        for comment in comments:
            # Check if this comment contains our table
            if f'id="{table_id}"' in comment:
                # Parse the commented HTML
                comment_soup = BeautifulSoup(comment, 'html.parser')
                table = comment_soup.find('table', {'id': table_id})
                if table:
                    return table
        return None

    def single_award(award: str, vote_dict: defaultdict, first_dict: dict) -> None:
        award_soup = soup.find('table', attrs={'id': award})
        if not award_soup:
            award_soup = extract_table_from_comments(award)
        if award_soup:
            df = pd.read_html(StringIO(str(award_soup)))[0]
            for row in df.itertuples():
                name = row[2]
                if row[0] == 0:
                    if first_dict.get(name) is None:
                        first_dict[name] = year
                vote_dict[name] += row[6]
                if award == 'mvp':
                    all_years_dict[name]['mvp'].append(year)

    mvp_vote_dict = defaultdict(int)
    mvp_first_dict = dict()
    roy_vote_dict = defaultdict(int)
    roy_first_dict = dict()
    dpoy_vote_dict = defaultdict(int)
    dpoy_first_dict = dict()
    smoy_vote_dict = defaultdict(int)
    smoy_first_dict = dict()
    mip_vote_dict = defaultdict(int)
    mip_first_dict = dict()
    all_vote_dict = defaultdict(voting_dict_maker)
    all_years_dict = defaultdict(years_dict_maker)

    for cls in DRAFT_CLASSES:
        print(cls)
        year = str(cls)
        url = AWARDS_URL.format(year)
        r = get_wrapper(url)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'html.parser')
            leading_all_nba_soup = soup.find('table', attrs={'id': 'leading_all_nba'})
            leading_all_defense_soup = soup.find('table', attrs={'id': 'leading_all_defense'})
            leading_all_rookie_soup = soup.find('table', attrs={'id': 'leading_all_rookie'})

            all_nba_df = pd.read_html(StringIO(str(leading_all_nba_soup)))[0]
            all_defense_df = pd.read_html(StringIO(str(leading_all_defense_soup)))[0]
            all_rookie_df = pd.read_html(StringIO(str(leading_all_rookie_soup)))[0]

            single_award('mvp', mvp_vote_dict, mvp_first_dict)
            single_award('roy', roy_vote_dict, roy_first_dict)
            single_award('dpoy', dpoy_vote_dict, dpoy_first_dict)
            single_award('smoy', smoy_vote_dict, smoy_first_dict)
            single_award('mip', mip_vote_dict, mip_first_dict)

            for row in all_nba_df.itertuples():
                i = row[0]
                if i not in {0, 6, 12, 18}:
                    name = row[3]
                    all_vote_dict[name]['all_nba'] += row[6]
                    all_years_dict[name]['all_races'].append(year)
                    if i < 6:
                        all_years_dict[name]['all_first'].append(year)
                    elif i < 12:
                        all_years_dict[name]['all_second'].append(year)
                    elif i < 18:
                        all_years_dict[name]['all_third'].append(year)

            for row in all_rookie_df.itertuples():
                i = row[0]
                if i not in {5, 11}:
                    name = row[2]
                    all_vote_dict[name]['all_rookie'] += row[5]
                    if i < 5:
                        all_years_dict[name].update({'rookie': 'first'})
                    elif i < 11:
                        all_years_dict[name].update({'rookie': 'second'})

            for row in all_defense_df.itertuples():
                i = row[0]
                if i not in {5, 11}:
                    name = row[3]
                    all_vote_dict[name]['all_defense'] += row[6]
                    if i < 6:
                        all_years_dict[name]['def_first'].append(year)
                    elif i < 12:
                        all_years_dict[name]['def_second'].append(year)


        else:
            raise ConnectionError('Request to basketball reference failed')
    res = [
        pd.DataFrame.from_dict(mvp_vote_dict, orient='index').rename(columns={0: 'MVP_Votes'}),
        pd.DataFrame.from_dict(mvp_first_dict, orient='index').rename(columns={0: 'First_MVP'}),
        pd.DataFrame.from_dict(roy_vote_dict, orient='index').rename(columns={0: 'RotY_Votes'}),
        pd.DataFrame.from_dict(roy_first_dict, orient='index').rename(columns={0: 'RotY'}),
        pd.DataFrame.from_dict(dpoy_vote_dict, orient='index').rename(columns={0: 'DPOY_Votes'}),
        pd.DataFrame.from_dict(dpoy_first_dict, orient='index').rename(columns={0: 'First_DPOY'}),
        pd.DataFrame.from_dict(smoy_vote_dict, orient='index').rename(columns={0: 'SMotY_Votes'}),
        pd.DataFrame.from_dict(smoy_first_dict, orient='index').rename(columns={0: 'First_SMotY'}),
        pd.DataFrame.from_dict(mip_vote_dict, orient='index').rename(columns={0: 'MIP_Votes'}),
        pd.DataFrame.from_dict(mip_first_dict, orient='index').rename(columns={0: 'First_MIP'}),
        pd.DataFrame.from_dict(all_vote_dict, orient='index'),
        pd.DataFrame.from_dict(all_years_dict, orient='index'),
    ]
    return pd.concat(res, axis=1)

def run():

    def clean_nans():
        df.fillna({col: 0 for col in {
            'MVP_Votes', 'First_MVP', 'RotY_Votes', 'DPOY_Votes', 'SMotY_Votes', 'First_DPOY', 'First_SMotY',
            'First_MIP', 'RotY', 'all_nba', 'all_defense', 'all_rookie'
        }}, inplace=True)
        for col in {
            'all_first', 'all_second', 'all_third', 'all_races', 'def_first', 'def_second', 'mvp'
        }:
            df[col] = df[col].apply(lambda x: ','.join(x) if isinstance(x, list) else '')
        df.fillna({'rookie': 'none'}, inplace=True)

    draft_df = get_drafts()
    awards_df = get_awards().reset_index(names='PLAYER')
    draft_df['YEARS'] = draft_df.YEARS.fillna('0').astype(int)
    draft_df['final_season'] = draft_df['year'] + draft_df['YEARS']
    df = draft_df.merge(awards_df, on='PLAYER', how='left')

    clean_nans()

    df.to_csv('./draft_data.csv', index=False)
if __name__ == '__main__':
    run()
import pandas as pd

NORM_COLS = [
    'YEARS', 'TOTALS_G', 'TOTALS_MP', 'ADVANCED_WS', 'ADVANCED_WS/48', 'MVP_Votes', 'RotY_Votes', 'DPOY_Votes',
    'SMotY_Votes', 'MIP_Votes', 'all_nba_votes', 'all_defense_votes', 'all_rookie_votes'
]

TEAM_REMAP = {
    'CHH': 'CHA',
    'CHO': 'CHA',
    'NJN': 'BRK',
    'NOH': 'NOP',
    'NOK': 'NOP',
    'SEA': 'OKC',
    'VAN': 'MEM',
    'WSB': 'WAS'
}

def read_data() -> pd.DataFrame:
    return pd.read_csv('./draft_data.csv')

def run():
    pick_dfs = dict()
    dc_dfs = list()

    def clean_data():
        df.fillna({
            c: '' for c in [
                'all_first', 'mvp', 'def_second', 'def_first', 'all_races', 'all_second', 'all_third'
            ]
        }, inplace=True)
        df.fillna({
            c: 0.0 for c in [
                'MIP_Votes'
            ]
        }, inplace=True)
        df['retired'] = df.final_season != 2026
        df['rookie_first'] = df.rookie == 'first'
        df['rookie_second'] = df.rookie == 'second'

    def dc_norm():
        dcs = df.year.unique()
        for dc in dcs:
            dc_df = df.loc[df['year'] == dc].copy().reset_index()
            dc_df['dcn_past_retirement'] = (dc_df.YEARS > dc_df[dc_df.retired].YEARS.mean()).astype(int)
            for col in NORM_COLS:
                new_col = 'dcn_{}'.format(col)
                mask = dc_df[col] != 0
                dc_df[new_col] = 0.0
                group = dc_df[col][mask]
                if group.sum() != 0.0:
                    dc_df.loc[mask, new_col] = group/group.mean()
                dc_df.fillna({new_col: 0.0}, inplace=True)
            dc_dfs.append(dc_df)

    def pick_norm():
        picks = df.PICK.unique()
        for pick in picks:
            pick_df = df.loc[df['PICK'] == pick].copy().reset_index()
            pick_df['pn_past_retirement'] = (pick_df.YEARS > pick_df[pick_df.retired].YEARS.mean()).astype(int)
            for col in NORM_COLS:
                new_col = 'pn_{}'.format(col)
                mask = pick_df[col] != 0
                pick_df[new_col] = 0.0
                group = pick_df[col][mask]
                if group.sum() != 0:
                    pick_df.loc[mask, new_col] = group/group.mean()
            pick_dfs.update({pick: pick_df})

    def add_trends():
        for pick, pickdf in pick_dfs.items():
            for col in NORM_COLS:
                pcol = 'pn_{}'.format(col)
                dccol = 'dcn_{}'.format(col)
                pickdf['{}_ma'.format(pcol)] = pickdf[pcol].rolling(5).mean()
                pickdf['{}_ma'.format(dccol)] = pickdf[dccol].rolling(5).mean()
            for col in [
                'rookie_first', 'rookie_second', 'dcn_past_retirement', 'pn_past_retirement',
            ]:
                pickdf['{}_ma'.format(col)] = pickdf[col].rolling(5).mean()

    df = read_data()
    clean_data()
    dc_norm()
    df = pd.concat(dc_dfs).set_index('index')
    pick_norm()
    add_trends()
    df = pd.concat(pick_dfs.values()).set_index('index')
    df['exists'] = 1
    df.replace({'TEAM': TEAM_REMAP}, inplace=True)
    df[[
        'year', 'PICK', 'TEAM', 'PLAYER', 'YEARS', 'TOTALS_G', 'TOTALS_MP', 'final_season', 'ADVANCED_WS',
        'ADVANCED_WS/48', 'ADVANCED_BPM', 'ADVANCED_VORP', 'MVP_Votes', 'First_MVP', 'RotY_Votes', 'RotY', 'DPOY_Votes',
        'First_DPOY', 'SMotY_Votes', 'First_SMotY', 'MIP_Votes', 'First_MIP', 'all_nba_votes', 'all_defense_votes',
        'all_rookie_votes', 'all_first', 'all_second', 'all_third', 'all_races', 'def_first', 'def_second', 'mvp',
        'rookie', 'retired', 'rookie_first', 'rookie_second', 'dcn_past_retirement', 'dcn_YEARS', 'dcn_TOTALS_G',
        'dcn_TOTALS_MP', 'dcn_ADVANCED_WS', 'dcn_ADVANCED_WS/48', 'dcn_MVP_Votes', 'dcn_RotY_Votes', 'dcn_DPOY_Votes',
        'dcn_SMotY_Votes', 'dcn_MIP_Votes', 'dcn_all_nba_votes', 'dcn_all_defense_votes', 'dcn_all_rookie_votes',
        'pn_past_retirement', 'pn_YEARS', 'pn_TOTALS_G', 'pn_TOTALS_MP', 'pn_ADVANCED_WS', 'pn_ADVANCED_WS/48',
        'pn_MVP_Votes', 'pn_RotY_Votes', 'pn_DPOY_Votes', 'pn_SMotY_Votes', 'pn_MIP_Votes', 'pn_all_nba_votes',
        'pn_all_defense_votes', 'pn_all_rookie_votes', 'pn_YEARS_ma', 'dcn_YEARS_ma', 'pn_TOTALS_G_ma',
        'dcn_TOTALS_G_ma', 'pn_TOTALS_MP_ma', 'dcn_TOTALS_MP_ma', 'pn_ADVANCED_WS_ma', 'dcn_ADVANCED_WS_ma',
        'pn_ADVANCED_WS/48_ma', 'dcn_ADVANCED_WS/48_ma', 'pn_MVP_Votes_ma', 'dcn_MVP_Votes_ma', 'pn_RotY_Votes_ma',
        'dcn_RotY_Votes_ma', 'pn_DPOY_Votes_ma', 'dcn_DPOY_Votes_ma', 'pn_SMotY_Votes_ma', 'dcn_SMotY_Votes_ma',
        'pn_MIP_Votes_ma', 'dcn_MIP_Votes_ma', 'pn_all_nba_votes_ma', 'dcn_all_nba_votes_ma', 'pn_all_defense_votes_ma',
        'dcn_all_defense_votes_ma', 'pn_all_rookie_votes_ma', 'dcn_all_rookie_votes_ma', 'rookie_first_ma',
        'rookie_second_ma', 'dcn_past_retirement_ma', 'pn_past_retirement_ma', 'exists'
    ]].to_csv('./full_data.csv', index=True)


if __name__ == '__main__':
    run()
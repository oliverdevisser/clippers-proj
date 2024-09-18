-- Create table 'team'
CREATE TABLE IF NOT EXISTS team (
    teamid BIGINT PRIMARY KEY,
    teamname TEXT,
    teamnameshort TEXT,
    teamnickname TEXT,
    leaguelk TEXT
);
-- Create table 'team_affiliate'
CREATE TABLE IF NOT EXISTS team_affiliate (
    nba_teamid BIGINT PRIMARY KEY,
    nba_abrv TEXT,
    glg_teamid BIGINT,
    glg_abrv TEXT
);
-- Create table 'game_schedule'
CREATE TABLE IF NOT EXISTS game_schedule (
    game_id BIGINT PRIMARY KEY,
    home_id BIGINT,
    away_id BIGINT,
    home_score INTEGER,
    away_score INTEGER,
    game_date TIMESTAMP
);
-- Create table 'player'
CREATE TABLE IF NOT EXISTS player (
    player_id BIGINT PRIMARY KEY,
    first_name TEXT,
    last_name TEXT
);
-- Create table 'lineup'
CREATE TABLE IF NOT EXISTS lineup (
    team_id BIGINT,
    player_id BIGINT,
    lineup_num INTEGER,
    period INTEGER,
    time_in INTEGER,
    time_out INTEGER,
    game_id BIGINT,
    PRIMARY KEY (team_id, player_id, lineup_num, game_id)
);
-- Create table 'roster'
CREATE TABLE IF NOT EXISTS roster (
    team_id BIGINT,
    player_id BIGINT,
    first_name TEXT,
    last_name TEXT,
    position TEXT,
    contract_type TEXT,
    PRIMARY KEY (team_id, player_id)
);
DROP TABLE IF EXISTS basic_queries;
CREATE TABLE basic_queries AS
WITH team_stats AS (
    SELECT
        t.teamid,
        t.teamname,
        COUNT(CASE WHEN g.home_id = t.teamid THEN 1 END) +
        COUNT(CASE WHEN g.away_id = t.teamid THEN 1 END) AS games_played,
        SUM(
            CASE
                WHEN g.home_id = t.teamid AND g.home_score > g.away_score THEN 1
                WHEN g.away_id = t.teamid AND g.away_score > g.home_score THEN 1
                ELSE 0
            END
        ) AS wins,
        SUM(
            CASE
                WHEN g.home_id = t.teamid AND g.home_score < g.away_score THEN 1
                WHEN g.away_id = t.teamid AND g.away_score < g.home_score THEN 1
                ELSE 0
            END
        ) AS losses,
        COUNT(CASE WHEN g.home_id = t.teamid THEN 1 END) AS home_games,
        COUNT(CASE WHEN g.away_id = t.teamid THEN 1 END) AS away_games
    FROM team t
    LEFT JOIN game_schedule g ON t.teamid = g.home_id OR t.teamid = g.away_id
    GROUP BY t.teamid, t.teamname
)
SELECT
    teamid,
    teamname,
    games_played,
    RANK() OVER (ORDER BY games_played DESC) AS rank_games_played,
    wins,
    losses,
    CASE
        WHEN games_played > 0 THEN ROUND(wins * 1.0 / games_played, 2)
        ELSE NULL
    END AS win_percentage,
    home_games,
    RANK() OVER (ORDER BY home_games DESC) AS rank_home_games,
    away_games,
    RANK() OVER (ORDER BY away_games DESC) AS rank_away_games
FROM team_stats
ORDER BY win_percentage DESC NULLS LAST;

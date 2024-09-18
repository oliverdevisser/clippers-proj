
WITH home_games AS (
    SELECT 
        g.home_id AS home_team,
        t.teamname,
        g.game_date::date AS game_date,
        LEAD(g.game_date::date) OVER (
            PARTITION BY g.home_id
            ORDER BY g.game_date::date
        ) AS next_game_date
    FROM 
        game_schedule g
    JOIN 
        team t ON g.home_id = t.teamid
)
SELECT 
    home_team,
    teamname,
    COUNT(*) AS home_b2b_count
FROM 
    home_games
WHERE 
    next_game_date - game_date = 1
GROUP BY 
    home_team,
    teamname
ORDER BY 
    home_b2b_count DESC
LIMIT 20;



-- Away Back-to-Back Games
WITH away_games AS (
    SELECT 
        g.away_id AS away_team,
        t.teamname,
        g.game_date::date AS game_date,
        LEAD(g.game_date::date) OVER (
            PARTITION BY g.away_id
            ORDER BY g.game_date::date
        ) AS next_game_date
    FROM 
        game_schedule g
    JOIN 
        team t ON g.away_id = t.teamid
)
SELECT 
    away_team,
    teamname,
    COUNT(*) AS away_b2b_count
FROM 
    away_games
WHERE 
    next_game_date - game_date = 1
GROUP BY 
    away_team,
    teamname
ORDER BY 
    away_b2b_count DESC
LIMIT 20;



-- Longest Rest Days Between Games
WITH team_games AS (
    SELECT 
        t.teamid AS team_id,
        t.teamname,
        g.game_date::date AS game_date,
        LEAD(g.game_date::date) OVER (
            PARTITION BY t.teamid
            ORDER BY g.game_date::date
        ) AS next_game_date
    FROM 
        game_schedule g
    JOIN 
        team t ON g.home_id = t.teamid OR g.away_id = t.teamid
),
rest_periods AS (
    SELECT 
        team_id,
        teamname,
        next_game_date - game_date AS rest_days,
        game_date AS last_game_date,
        next_game_date AS next_game_date,
        RANK() OVER (ORDER BY next_game_date - game_date DESC) AS rest_rank
    FROM 
        team_games
    WHERE 
        next_game_date IS NOT NULL
)
SELECT 
    team_id,
    teamname,
    rest_days,
    last_game_date,
    next_game_date
FROM 
    rest_periods
WHERE 
    rest_rank = 1;



-- Teams Playing 3 Games in 4 Days
WITH team_games AS (
    SELECT 
        t.teamid AS team_id,
        t.teamname,
        g.game_date::date AS game_date,
        ROW_NUMBER() OVER (
            PARTITION BY t.teamid
            ORDER BY g.game_date::date
        ) AS game_num
    FROM 
        game_schedule g
    JOIN 
        team t ON g.home_id = t.teamid OR g.away_id = t.teamid
),
game_stretches AS (
    SELECT 
        g1.team_id,
        g1.teamname,
        g1.game_date AS game_date1,
        g2.game_date AS game_date2,
        g3.game_date AS game_date3,
        (g3.game_date - g1.game_date) AS days_span
    FROM 
        team_games g1
    JOIN 
        team_games g2 ON g1.team_id = g2.team_id AND g2.game_num = g1.game_num + 1
    JOIN 
        team_games g3 ON g1.team_id = g3.team_id AND g3.game_num = g1.game_num + 2
)
SELECT 
    team_id,
    teamname,
    COUNT(*) AS num_3_in_4s
FROM 
    game_stretches
WHERE 
    days_span < 4
GROUP BY 
    team_id,
    teamname
ORDER BY 
    num_3_in_4s DESC;

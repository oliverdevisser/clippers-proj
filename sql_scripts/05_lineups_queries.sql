--- a -----
DROP TABLE IF EXISTS wide_table;
CREATE TABLE wide_table AS
WITH lineup_wide AS (
    SELECT l.game_id,
        l.team_id,
        l.lineup_num,
        l.period,
        l.time_in,
        l.time_out,
        MAX(
            CASE
                WHEN rn = 1 THEN p.first_name || ' ' || p.last_name
            END
        ) AS player1,
        MAX(
            CASE
                WHEN rn = 2 THEN p.first_name || ' ' || p.last_name
            END
        ) AS player2,
        MAX(
            CASE
                WHEN rn = 3 THEN p.first_name || ' ' || p.last_name
            END
        ) AS player3,
        MAX(
            CASE
                WHEN rn = 4 THEN p.first_name || ' ' || p.last_name
            END
        ) AS player4,
        MAX(
            CASE
                WHEN rn = 5 THEN p.first_name || ' ' || p.last_name
            END
        ) AS player5
    FROM (
            SELECT l.game_id,
                l.team_id,
                l.lineup_num,
                l.period,
                l.time_in,
                l.time_out,
                l.player_id,
                ROW_NUMBER() OVER (
                    PARTITION BY l.game_id,
                    l.team_id,
                    l.lineup_num,
                    l.period,
                    l.time_in,
                    l.time_out
                    ORDER BY l.player_id
                ) AS rn
            FROM lineup l
            GROUP BY l.game_id,
                l.team_id,
                l.lineup_num,
                l.period,
                l.time_in,
                l.time_out,
                l.player_id
        ) l
        JOIN player p ON l.player_id = p.player_id
    GROUP BY l.game_id,
        l.team_id,
        l.lineup_num,
        l.period,
        l.time_in,
        l.time_out
    HAVING COUNT(*) = 5
)
SELECT *
FROM lineup_wide
ORDER BY game_id,
    team_id,
    lineup_num,
    period;
-------



--- b -----
-- gets individual stints
DROP TABLE IF EXISTS temp_stint_accumulation;
CREATE TEMP TABLE temp_stint_accumulation AS
WITH player_stints AS (
    SELECT
        gs.game_date,
        gs.game_id,
        l.team_id,
        t.teamname AS team,
        CASE
            WHEN l.team_id = gs.home_id THEN opp.teamname
            ELSE home.teamname
        END AS opponent,
        p.first_name || ' ' || p.last_name AS player_name,
        l.period,
        l.time_in,
        l.time_out,
        LEAD(l.time_in) OVER (
            PARTITION BY l.player_id, l.game_id, l.period
            ORDER BY l.time_in DESC, l.time_out DESC
        ) AS next_time_in
    FROM lineup l
    JOIN game_schedule gs ON l.game_id = gs.game_id
    JOIN team t ON l.team_id = t.teamid
    JOIN team opp ON (
        CASE WHEN l.team_id = gs.home_id THEN gs.away_id ELSE gs.home_id END
    ) = opp.teamid
    JOIN team home ON gs.home_id = home.teamid
    JOIN player p ON l.player_id = p.player_id
    GROUP BY
        gs.game_date, gs.game_id, l.team_id, t.teamname, opp.teamname, home.teamname, 
        p.first_name, p.last_name, l.period, l.time_in, l.time_out, l.player_id, l.game_id
),
stint_grouping AS (
    SELECT *,
        LAG(CASE 
                WHEN next_time_in IS NOT NULL AND next_time_in < time_out THEN 1
                ELSE 0
            END, 1, 0) OVER (
            PARTITION BY player_name, game_id, period
            ORDER BY time_in DESC, time_out DESC
        ) AS stint_break
    FROM player_stints
),
stint_numbers AS (
    SELECT *,
        SUM(stint_break) OVER (
            PARTITION BY player_name, game_id, period
            ORDER BY time_in DESC, time_out DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) + 1 AS stint_number
    FROM stint_grouping
)
SELECT
    game_date,
    game_id,
    team_id,
    team,
    opponent,
    player_name,
    period,
    time_in,
    time_out,
    stint_number
FROM stint_numbers
ORDER BY game_date, team, player_name, game_id, period, time_in DESC, time_out DESC;

-- combines stints to get final results
DROP TABLE IF EXISTS stints_results;
CREATE TABLE stints_results AS
SELECT
    game_date,
    team,
    opponent,
    player_name,
    period,
    stint_number,
    TO_CHAR(MAX(time_in) * INTERVAL '1 second', 'MI:SS') AS stint_start_time,
    TO_CHAR(MIN(time_out) * INTERVAL '1 second', 'MI:SS') AS stint_end_time
FROM temp_stint_accumulation
GROUP BY
    game_date,
    game_id,
    team,
    opponent,
    player_name,
    period,
    stint_number
ORDER BY
    game_date, team, player_name, period, stint_number;

-- get seconds of each stint for later use
DROP TABLE IF EXISTS temp_stint_durations;
CREATE TEMP TABLE temp_stint_durations AS
SELECT
    sr.*,
    (MAX(tsa.time_in) - MIN(tsa.time_out)) AS stint_seconds
FROM stints_results sr
JOIN temp_stint_accumulation tsa ON
    sr.game_date = tsa.game_date AND
    sr.team = tsa.team AND
    sr.player_name = tsa.player_name AND
    sr.period = tsa.period AND
    sr.stint_number = tsa.stint_number
GROUP BY
    sr.game_date,
    sr.team,
    sr.opponent,
    sr.player_name,
    sr.period,
    sr.stint_number,
    sr.stint_start_time,
    sr.stint_end_time;



----- c -------
DROP TABLE IF EXISTS stints_results_averages;
CREATE TABLE stints_results_averages AS 
    SELECT player_name,
        team,
        ROUND(COUNT(*)::NUMERIC / COUNT(DISTINCT game_date), 2) AS average_stints_per_game,
        ROUND(CAST(AVG(stint_seconds) AS NUMERIC), 2) AS avg_stint_length_seconds
    FROM temp_stint_durations
    GROUP BY player_name,
        team
    ORDER BY team,
        avg_stint_length_seconds DESC,
        average_stints_per_game DESC;

----- d --------
DROP TABLE IF EXISTS final_summary;
CREATE TABLE final_summary AS WITH game_results AS (
    SELECT gs.game_id,
        gs.game_date,
        gs.home_id AS team_id,
        t.teamname AS team,
        CASE
            WHEN gs.home_score > gs.away_score THEN 'win'
            ELSE 'loss'
        END AS result
    FROM game_schedule gs
        JOIN team t ON gs.home_id = t.teamid
    UNION ALL
    SELECT gs.game_id,
        gs.game_date,
        gs.away_id AS team_id,
        t.teamname AS team,
        CASE
            WHEN gs.away_score > gs.home_score THEN 'win'
            ELSE 'loss'
        END AS result
    FROM game_schedule gs
        JOIN team t ON gs.away_id = t.teamid
),
stint_durations_with_results AS (
    SELECT tsd.*,
        gr.result
    FROM temp_stint_durations tsd
        JOIN game_results gr ON tsd.game_date = gr.game_date
        AND tsd.team = gr.team
)
SELECT player_name,
    team,
    COUNT(DISTINCT game_date) AS games,
    ROUND(
        COUNT(*)::NUMERIC / NULLIF(COUNT(DISTINCT game_date), 0),
        2
    ) AS avg_stints_per_game,
    ROUND(CAST(AVG(stint_seconds) AS NUMERIC), 2) AS avg_stint_length_seconds,
    -- Wins
    COUNT(
        DISTINCT CASE
            WHEN result = 'win' THEN game_date
        END
    ) AS games_won,
    ROUND(
        SUM(
            CASE
                WHEN result = 'win' THEN 1
                ELSE 0
            END
        )::NUMERIC / NULLIF(
            COUNT(
                DISTINCT CASE
                    WHEN result = 'win' THEN game_date
                END
            ),
            0
        ),
        2
    ) AS avg_stints_wins,
    ROUND(
        AVG(
            CASE
                WHEN result = 'win' THEN stint_seconds
            END
        ),
        2
    ) AS avg_stint_length_wins,
    -- Losses
    COUNT(
        DISTINCT CASE
            WHEN result = 'loss' THEN game_date
        END
    ) AS games_lost,
    ROUND(
        SUM(
            CASE
                WHEN result = 'loss' THEN 1
                ELSE 0
            END
        )::NUMERIC / NULLIF(
            COUNT(
                DISTINCT CASE
                    WHEN result = 'loss' THEN game_date
                END
            ),
            0
        ),
        2
    ) AS avg_stints_losses,
    ROUND(
        AVG(
            CASE
                WHEN result = 'loss' THEN stint_seconds
            END
        ),
        2
    ) AS avg_stint_length_losses,
    -- Differences
    ROUND(
        COALESCE(
            AVG(
                CASE
                    WHEN result = 'win' THEN stint_seconds
                END
            ) - AVG(
                CASE
                    WHEN result = 'loss' THEN stint_seconds
                END
            ),
            0
        ),
        2
    ) AS diff_avg_stint_length,
    ROUND(
        COALESCE(
            (
                SUM(
                    CASE
                        WHEN result = 'win' THEN 1
                        ELSE 0
                    END
                )::NUMERIC / NULLIF(
                    COUNT(
                        DISTINCT CASE
                            WHEN result = 'win' THEN game_date
                        END
                    ),
                    0
                )
            ) - (
                SUM(
                    CASE
                        WHEN result = 'loss' THEN 1
                        ELSE 0
                    END
                )::NUMERIC / NULLIF(
                    COUNT(
                        DISTINCT CASE
                            WHEN result = 'loss' THEN game_date
                        END
                    ),
                    0
                )
            ),
            0
        ),
        2
    ) AS diff_avg_stints_per_game
FROM stint_durations_with_results
GROUP BY player_name,
    team
ORDER BY player_name;









import os
import time
from flask import Flask, render_template, request, jsonify, redirect, session, url_for
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

#dummy user data with hashed passwords
users = {
    'user_one': generate_password_hash('password123'),
    'user_two': generate_password_hash('123password')
}

#get database url
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    DATABASE_HOST = os.environ.get('DATABASE_HOST', 'db')
    DATABASE_PORT = os.environ.get('DATABASE_PORT', '5432')
    DATABASE_NAME = os.environ.get('DATABASE_NAME', 'lac_fullstack_dev')
    DATABASE_USER = os.environ.get('DATABASE_USER', 'postgres')
    DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD', 'postgres')
    DATABASE_URL = f'postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}'


#get db connection
def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

#run SQL files written in questions 1-4
def run_sql_file(filename):
    conn = get_db_connection()
    cur = conn.cursor()

    with open(filename, 'r') as sql_file:
        sql_commands = sql_file.read()
        try:
            cur.execute(sql_commands)
            conn.commit()
        except Exception as e:
            print(f"Error executing {filename}: {e}")
            conn.rollback()

    cur.close()
    conn.close()

#check if the db is initialized, so doesn't write into empty db
def is_db_initialized():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.close()
        conn.close()
        return False#count > 0
    except Exception as e:
        print(f"Error checking if DB is initialized: {e}")
        return False


#wait for db
while True:
    try:
        if is_db_initialized():
            print("Database is initialized.")
            break
        else:
            print("Database is not initialized. Initializing...")
            # Run SQL scripts to create tables
            print("Running SQL Files 01")
            run_sql_file('sql_scripts/01_create_tables.sql')
            # Load data
            from scripts.transfer_json_to_db import load_data_to_db
            load_data_to_db()
            break
    except Exception as e:
        print(f"Error during initialization: {e}")
        time.sleep(5)


#run sql sqcripts in the correct order
def run_all_sql_files():
    run_sql_file('sql_scripts/03_basic_queries.sql')
    run_sql_file('sql_scripts/04_schedule_queries.sql')
    run_sql_file('sql_scripts/05_lineups_queries.sql')

#added check for log
print("Running SQL Files 03, 04, 05.")
run_all_sql_files()



# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Authenticate user
        if username in users and check_password_hash(users[username], password):
            session['user'] = username
            if username == 'user_two':
                session['team'] = 'LA Clippers'  # Default team
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Invalid credentials')
    else:
        return render_template('login.html')



# Logout route
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))



# Home route
@app.route('/')
def home():
    if 'user' in session:
        user = session['user']
        if user == 'user_two':
            # Fetch list of teams from the database
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT team FROM final_summary ORDER BY team;")
            teams = [row[0] for row in cur.fetchall()]
            cur.close()
            conn.close()
            return render_template('index.html', user=user, teams=teams, default_team='LA Clippers', selected_team='LA Clippers')
        else:
            return render_template('index.html', user=user)
    else:
        return redirect(url_for('login'))


# Stint visualization rout
@app.route('/api/stint-data')
def get_stint_data():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    team = request.args.get('team', None)  #get selected team

    #connect to psql and fetch data from the database
    conn = get_db_connection()
    cur = conn.cursor()
    
    if team: #for coach view
        
        cur.execute("""
            SELECT player_name, team, games, avg_stints_per_game, avg_stint_length_seconds, 
                   games_won, avg_stints_wins, avg_stint_length_wins, 
                   games_lost, avg_stints_losses, avg_stint_length_losses, 
                   diff_avg_stint_length, diff_avg_stints_per_game
            FROM final_summary
            WHERE team = %s
            ORDER BY player_name;
        """, (team,))
    else:
        #fetch all players for scout view
        cur.execute("""
            SELECT player_name, team, games, avg_stints_per_game, avg_stint_length_seconds, 
                   games_won, avg_stints_wins, avg_stint_length_wins, 
                   games_lost, avg_stints_losses, avg_stint_length_losses, 
                   diff_avg_stint_length, diff_avg_stints_per_game
            FROM final_summary
            ORDER BY player_name;
        """)
    
    data = cur.fetchall()
    column_names = [desc[0] for desc in cur.description]

    cur.close()
    conn.close()
    return jsonify({'data': data, 'columns': column_names})

# schedule visualization for scout route
@app.route('/api/scout-schedule')
def get_scout_schedule():
    try:
        #connect to psql and fetch data from the database
        conn = get_db_connection()
        cur = conn.cursor()

        # calculate team records from game_schedule
        cur.execute("""
            WITH team_records AS (
                SELECT team_id, team_nickname, SUM(wins) AS total_wins, SUM(losses) AS total_losses
                FROM (
                    SELECT gs.home_id AS team_id, ht.teamnickname AS team_nickname,
                        CASE WHEN gs.home_score > gs.away_score THEN 1 ELSE 0 END AS wins,
                        CASE WHEN gs.home_score < gs.away_score THEN 1 ELSE 0 END AS losses
                    FROM game_schedule gs
                    JOIN team ht ON gs.home_id = ht.teamid
                    UNION ALL
                    SELECT gs.away_id AS team_id, at.teamnickname AS team_nickname,
                        CASE WHEN gs.away_score > gs.home_score THEN 1 ELSE 0 END AS wins,
                        CASE WHEN gs.away_score < gs.home_score THEN 1 ELSE 0 END AS losses
                    FROM game_schedule gs
                    JOIN team at ON gs.away_id = at.teamid
                ) sub
                GROUP BY team_id, team_nickname
            )
            SELECT
                gs.game_id,
                gs.game_date,
                ht.teamnickname AS home_team,
                at.teamnickname AS away_team,
                (home_record.total_wins + away_record.total_wins) - (home_record.total_losses + away_record.total_losses) AS total_game_difficulty
            FROM game_schedule gs
            JOIN team ht ON gs.home_id = ht.teamid
            JOIN team at ON gs.away_id = at.teamid
            JOIN team_records home_record ON ht.teamid = home_record.team_id
            JOIN team_records away_record ON at.teamid = away_record.team_id
            ORDER BY gs.game_date;
        """)

        difficulty_levels = [
            (10, 'purple'),
            (5, 'red'),
            (0, '#d4af37'),
            (-5, '#228b22'),
            (-10, '#006400')
        ]

        data = cur.fetchall()
        events = []

        for row in data: #get background event color
            game_id, game_date, home_team, away_team, difficulty = row
            for threshold, color in difficulty_levels:
                if difficulty >= threshold:
                    event_color = color
                    break
            else:
                event_color = '#006400'  # Default color

            event = { #create event and return 
                'title': f"{home_team} vs {away_team} (Diff: {difficulty})",
                'start': game_date.isoformat(),
                'allDay': True,
                'difficulty': difficulty,
                'home_team': home_team,
                'away_team': away_team,
                'game_id': game_id,
                'color': event_color
            }
            events.append(event)

        cur.close()
        conn.close()
        return jsonify({'events': events})
    except Exception as e:
        print(f"Error fetching scout schedule data: {e}")
        return jsonify({'error': str(e)}), 500


# schedule visualization for coach route
@app.route('/api/coach-schedule')
def get_coach_schedule():
    if 'user' not in session or session['user'] != 'user_two':
        return jsonify({'error': 'Unauthorized'}), 401

    team_name = request.args.get('team', 'LA Clippers')  #defaults to clippers

    try:
        #connect to psql and fetch data from the database
        conn = get_db_connection()
        cur = conn.cursor()

        # calculate team records from game_schedule
        cur.execute("""
            WITH team_records AS (
                SELECT 
                    team_id, 
                    team_name, 
                    SUM(wins) AS total_wins, 
                    SUM(losses) AS total_losses
                FROM (
                    SELECT 
                        gs.home_id AS team_id, 
                        ht.teamname AS team_name,
                        CASE WHEN gs.home_score > gs.away_score THEN 1 ELSE 0 END AS wins,
                        CASE WHEN gs.home_score < gs.away_score THEN 1 ELSE 0 END AS losses
                    FROM game_schedule gs
                    JOIN team ht ON gs.home_id = ht.teamid
                    
                    UNION ALL
                    
                    SELECT 
                        gs.away_id AS team_id, 
                        at.teamname AS team_name,
                        CASE WHEN gs.away_score > gs.home_score THEN 1 ELSE 0 END AS wins,
                        CASE WHEN gs.away_score < gs.home_score THEN 1 ELSE 0 END AS losses
                    FROM game_schedule gs
                    JOIN team at ON gs.away_id = at.teamid
                ) sub
                GROUP BY team_id, team_name
            )
            SELECT
                gs.game_id,
                gs.game_date,
                ht.teamnickname AS home_team,
                at.teamnickname AS away_team,
                CASE
                    WHEN ht.teamname = %s THEN (away_record.total_wins - away_record.total_losses)
                    ELSE (home_record.total_wins - home_record.total_losses)
                END AS opponent_difficulty
            FROM game_schedule gs
            JOIN team ht ON gs.home_id = ht.teamid
            JOIN team at ON gs.away_id = at.teamid
            JOIN team_records home_record ON ht.teamid = home_record.team_id
            JOIN team_records away_record ON at.teamid = away_record.team_id
            WHERE %s IN (ht.teamname, at.teamname)
            ORDER BY gs.game_date;
        """, (team_name, team_name))

        data = cur.fetchall()
        if not data:  # Check if data is empty
            print(f"No data found for the given team name: {team_name}")

        difficulty_levels = [
            (5, 'purple'),
            (2.5, 'red'),
            (0, '#d4af37'),  # Darker Yellow
            (-2.5, '#228b22'),  # Darker Green
            (-5, '#006400')  # Dark Green
        ]

        events = []
        for row in data: #get background event color
            game_id, game_date, home_team, away_team, difficulty = row

            for threshold, color in difficulty_levels:
                if difficulty >= threshold:
                    event_color = color
                    break
            else:
                event_color = '#006400'  # Default color

            event = { #create event and return
                'title': f"{home_team} vs {away_team} (Diff: {difficulty})",
                'start': game_date.isoformat(),
                'allDay': True,
                'difficulty': difficulty,
                'home_team': home_team,
                'away_team': away_team,
                'game_id': game_id,
                'color': event_color
            }
            events.append(event)

        cur.close()
        conn.close()
        return jsonify({'events': events})
    except Exception as e:
        print(f"Error fetching coach schedule data: {e}")
        return jsonify({'error': str(e)}), 500


#app.py
if __name__ == '__main__':
    app.run(debug=True)
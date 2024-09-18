import os
import pandas as pd
from sqlalchemy import create_engine, text  # Import text here
from sqlalchemy.types import BigInteger, Integer, String, TIMESTAMP

def load_data_to_db():
    DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/lac_fullstack_dev')
    engine = create_engine(DATABASE_URI)

    DATA_DIR = '/dev_test_data'  # Path inside Docker container

    # Map JSON files to table names
    file_to_table = {
        'team.json': 'team',
        'team_affiliate.json': 'team_affiliate',
        'game_schedule.json': 'game_schedule',
        'player.json': 'player',
        'lineup.json': 'lineup',
        'roster.json': 'roster'
    }

    # Define data types for each table
    dtype_mapping = {
        'team': {
            'teamid': BigInteger(),
            'teamname': String(),
            'teamnameshort': String(),
            'teamnickname': String(),
            'leaguelk': String(),
        },
        'team_affiliate': {
            'nba_teamid': BigInteger(),
            'nba_abrv': String(),
            'glg_teamid': BigInteger(),
            'glg_abrv': String(),
        },
        'game_schedule': {
            'game_id': BigInteger(),
            'home_id': BigInteger(),
            'away_id': BigInteger(),
            'home_score': Integer(),
            'away_score': Integer(),
            'game_date': TIMESTAMP(),
        },
        'player': {
            'player_id': BigInteger(),
            'first_name': String(),
            'last_name': String(),
        },
        'lineup': {
            'team_id': BigInteger(),
            'player_id': BigInteger(),
            'lineup_num': Integer(),
            'period': Integer(),
            'time_in': Integer(),
            'time_out': Integer(),
            'game_id': BigInteger(),
        },
        'roster': {
            'team_id': BigInteger(),
            'player_id': BigInteger(),
            'first_name': String(),
            'last_name': String(),
            'position': String(),
            'contract_type': String(),
        }
    }

    # Load JSON files and transfer to PostgreSQL
    for file_name, table_name in file_to_table.items():
        file_path = os.path.join(DATA_DIR, file_name)
        try:
            print(f"Processing {file_name}...")
            # Read JSON into DataFrame
            df = pd.read_json(file_path)
            # Convert column names to lowercase
            df.columns = [col.lower() for col in df.columns]

            # Ensure data types match
            if table_name == 'game_schedule':
                df['game_date'] = pd.to_datetime(df['game_date'])

            # Delete existing data
            with engine.connect() as connection:
                connection.execute(text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE;"))
                # Note: Wrap the SQL string with text()

            # Write DataFrame to table
            df.to_sql(table_name, con=engine, if_exists='append', index=False, dtype=dtype_mapping.get(table_name))
            print(f"Table '{table_name}' has been updated successfully.")
        except Exception as e:
            print(f"Failed to process {file_path}. Error: {e}")

if __name__ == '__main__':
    load_data_to_db()

import os
import pandas as pd
from sqlalchemy import create_engine, text, MetaData, Table
from sqlalchemy.types import BigInteger, Integer, String, TIMESTAMP
from sqlalchemy.dialects.postgresql import insert as pg_insert

def load_data_to_db():
    DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/lac_fullstack_dev')
    engine = create_engine(DATABASE_URI)

    # Correct the DATA_DIR path
    DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'dev_test_data')

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

    metadata = MetaData()
    metadata.reflect(bind=engine)

    # Load JSON files and transfer to PostgreSQL
    for file_name, table_name in file_to_table.items():
        file_path = os.path.join(DATA_DIR, file_name)
        try:
            print(f"Processing {file_name} at {file_path}...")
            # Read JSON into DataFrame
            df = pd.read_json(file_path)
            # Convert column names to lowercase
            df.columns = [col.lower() for col in df.columns]

            # Ensure data types match
            if table_name == 'game_schedule':
                df['game_date'] = pd.to_datetime(df['game_date'])

            # Get the table metadata
            table = Table(table_name, metadata, autoload_with=engine)

            # Convert DataFrame to list of dictionaries
            records = df.to_dict(orient='records')

            # Prepare the insert statement with ON CONFLICT DO NOTHING
            stmt = pg_insert(table).values(records)
            do_nothing_stmt = stmt.on_conflict_do_nothing()

            # Execute the statement
            with engine.connect() as connection:
                connection.execute(do_nothing_stmt)
                connection.commit()

            print(f"Table '{table_name}' has been updated successfully.")
        except Exception as e:
            print(f"Failed to process {file_path}. Error: {e}")

if __name__ == '__main__':
    load_data_to_db()

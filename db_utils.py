import os
import pandas as pd
import psycopg2

from constants import SYMBOL_SPREAD_TABLE_NAME


def populate_db_table_with_csv_data(db, table_name,
                                    file_name="socket_data/symbols_initial_data.csv"):
    try:
        file_name = os.path.join(os.environ.get('WORKING_DIR'), file_name)
        with open(file_name, 'r') as file:
            data_df = pd.read_csv(file)

        data_df.to_sql(table_name, con=db.engine, index=False, index_label='id', if_exists='replace')
    except Exception as e:
        print(f"Cannot populate table from csv: Error {e}")
        pass


# psycopg2.connect(
#     database=database, user=user, password=password, host=host, port=port
# )

def reset_database(db, populate_csv_initial_data=False):
    # db.drop_all()
    db.create_all()
    db.session.commit()

    if populate_csv_initial_data:
        # Populate DB with csv data
        populate_db_table_with_csv_data(db, SYMBOL_SPREAD_TABLE_NAME)

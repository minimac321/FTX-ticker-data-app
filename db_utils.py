import os
import pandas as pd


def reset_database(db):
    db.drop_all()
    db.create_all()
    db.session.commit()


def populate_db_table_with_csv_data(db, table_name,
                                    file_name="socket_data/symbols_initial_data.csv"):
    file_name = os.path.join(os.environ.get('WORKING_DIR'), file_name)
    with open(file_name, 'r') as file:
        data_df = pd.read_csv(file)
        # for i, row in data_df.iterrows():
        #     del row["id"]
        #     print("row", row)
        #     add_and_commit_new_entry(db, row)

    data_df.to_sql(table_name, con=db.engine, index=False, index_label='id', if_exists='replace')



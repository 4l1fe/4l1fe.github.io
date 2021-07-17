import duckdb
import typer
import subprocess

from random import randint


app = typer.Typer()


class RandomDB:

    CREATE_TABLE_DUCKDB = '''
        CREATE TABLE IF NOT EXISTS {table_name}(
        grp UINTEGER,
        value1 UINTEGER,  
        value2 UINTEGER,  
        value3 UINTEGER);  
        '''
    CREATE_TABLE_SQLITE = '''
        CREATE TABLE IF NOT EXISTS {table_name}(
        grp INTEGER,
        value1 INTEGER,  
        value2 INTEGER,  
        value3 INTEGER);  
        '''
    LIMIT_GRADE = 1_000_000

    def __init__(self):
        self.duckdb_name = 'random.duckdb'
        self.sqlite_name = 'random.sqlite'
        self.base_table_name = 'random_data'
        self.connection = duckdb.connect(database=self.duckdb_name)

    def fill_duckdb(self, sample_size: int = 2000, samples_count: int = 2000):
        """Create the base table and fill it up with random data."""
        self.connection.execute(self.CREATE_TABLE_DUCKDB.format(table_name=self.base_table_name))

        group_min = 0
        group_max = 256
        value_min = 0
        value_max = 4294967295

        for i in range(samples_count):
            values_exp = 'VALUES '
            for j in range(sample_size):
                values_exp += '({},{},{},{}), '.format(randint(group_min, group_max),
                                                       randint(value_min, value_max),
                                                       randint(value_min, value_max),
                                                       randint(value_min, value_max))
            values_exp = values_exp.rstrip().rstrip(',')
            self.connection.execute(f"INSERT INTO {self.base_table_name} {values_exp}")
            print(f'Sample {i} is filled up')
        print(f'Database {self.duckdb_name} is filled up')

    def fill_sqlite(self, csv_path: str):
        """Create the base table and fill it up with random data."""
        create_query = self.CREATE_TABLE_SQLITE.format(table_name=self.base_table_name)
        import_cmd = f'.import {csv_path} {self.base_table_name}'
        subprocess.run(['sqlite3', self.sqlite_name, '-cmd', create_query, '.mode csv', import_cmd])
        print(f'Database {self.sqlite_name} is filled up')

    def split_duckdb(self, tables_count: int = 10):
        """Split the base table onto smaller tables."""
        for i in range(1, tables_count + 1):
            table_name = self.base_table_name + f'{i}'
            self.connection.execute(self.CREATE_TABLE_DUCKDB.format(table_name=table_name))
            print('Table created: ', table_name)

        limit = self.LIMIT_GRADE
        for i in range(1, tables_count + 1):
            table_name = self.base_table_name + f'{i}'
            print('Table filling:  ', table_name)
            self.connection.execute(f'INSERT INTO {table_name} SELECT * FROM {self.base_table_name} LIMIT {limit}')
            limit += self.LIMIT_GRADE

    def split_sqlite(self, tables_count: int = 10):
        """Split the base table onto smaller tables."""
        for i in range(1, tables_count + 1):
            table_name = self.base_table_name + f'{i}'
            self.connection.execute(self.CREATE_TABLE_SQLITE.format(table_name=table_name))
            print('Table created: ', table_name)

        limit = self.LIMIT_GRADE
        for i in range(1, tables_count + 1):
            table_name = self.base_table_name + f'{i}'
            print('Table filling:  ', table_name)
            self.connection.execute(f'INSERT INTO {table_name} SELECT * FROM {self.base_table_name} LIMIT {limit}')
            limit += self.LIMIT_GRADE

    def dump_csv(self, path='.'):
        """Dump data from the base table to csv file in a specified directory directory."""
        self.connection.execute(f"EXPORT DATABASE '{path}' (FORMAT CSV, HEADER TRUE);")


if __name__ == '__main__':
    db = RandomDB()
    app.command()(db.fill_duckdb)
    app.command()(db.fill_sqlite)
    app.command()(db.split_duckdb)
    app.command()(db.split_sqlite)
    app.command()(db.dump_csv)
    app()
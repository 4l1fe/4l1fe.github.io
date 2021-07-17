from typing import List


sqlite_output: str = '''sqlite3 random.sqlite < edited-query.sql > /dev/null  1,42s user 0,04s system 99% cpu 1,464 total
sqlite3 random.sqlite < edited-query.sql > /dev/null  2,84s user 0,12s system 99% cpu 2,966 total
sqlite3 random.sqlite < edited-query.sql > /dev/null  4,21s user 0,18s system 99% cpu 4,412 total
sqlite3 random.sqlite < edited-query.sql > /dev/null  5,75s user 0,22s system 99% cpu 5,971 total
sqlite3 random.sqlite < edited-query.sql > /dev/null  7,19s user 0,22s system 99% cpu 7,406 total
sqlite3 random.sqlite < edited-query.sql > /dev/null  8,66s user 0,26s system 99% cpu 8,951 total
sqlite3 random.sqlite < edited-query.sql > /dev/null  10,07s user 0,37s system 99% cpu 10,459 total
sqlite3 random.sqlite < edited-query.sql > /dev/null  11,59s user 0,42s system 99% cpu 12,015 total
sqlite3 random.sqlite < edited-query.sql > /dev/null  13,23s user 0,49s system 99% cpu 13,747 total
sqlite3 random.sqlite < edited-query.sql > /dev/null  14,52s user 0,58s system 99% cpu 15,126 total
'''

duck_output = '''duckdb random.duckdb < edited-query.sql > /dev/null  0,12s user 0,07s system 99% cpu 0,186 total
duckdb random.duckdb < edited-query.sql > /dev/null  0,21s user 0,02s system 99% cpu 0,226 total
duckdb random.duckdb < edited-query.sql > /dev/null  0,23s user 0,07s system 99% cpu 0,296 total
duckdb random.duckdb < edited-query.sql > /dev/null  0,31s user 0,07s system 99% cpu 0,382 total
duckdb random.duckdb < edited-query.sql > /dev/null  0,36s user 0,07s system 99% cpu 0,431 total
duckdb random.duckdb < edited-query.sql > /dev/null  0,38s user 0,11s system 99% cpu 0,492 total
duckdb random.duckdb < edited-query.sql > /dev/null  0,49s user 0,09s system 99% cpu 0,586 total
duckdb random.duckdb < edited-query.sql > /dev/null  0,53s user 0,10s system 99% cpu 0,630 total
duckdb random.duckdb < edited-query.sql > /dev/null  0,56s user 0,17s system 99% cpu 0,728 total
duckdb random.duckdb < edited-query.sql > /dev/null  0,62s user 0,16s system 99% cpu 0,781 total
'''


def convert(time_output: str) -> List[float]:
    """Extract seconds float value from a str line"""
    converted_output = []
    for line in time_output.splitlines():
        seconds = line.rsplit(' ', 2)[-2]
        seconds = float(seconds.replace(',', '.'))
        converted_output.append(seconds)

    return converted_output

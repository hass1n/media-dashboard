from sqlalchemy import create_engine, inspect

engine = create_engine('postgresql://postgres:1234@localhost:5432/media_db_4')
ins = inspect(engine)

for table in ins.get_table_names():
    cols = [c['name'] for c in ins.get_columns(table) if 'views' in c['name'].lower()]
    if cols:
        print(f"{table}: {cols}")

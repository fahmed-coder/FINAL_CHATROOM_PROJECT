from sqlalchemy import create_engine, text

engine = create_engine("sqlite:///project.db",echo=False)

with engine.begin() as conn:
    conn.execute(text("drop table if exists message"))
    conn.execute(text("drop table if exists user"))

    conn.execute(text("""create table message(
                            unique_id integer primary key AUTOINCREMENT,
                            username varchar(40),
                            message varchar(1000) not null,
                            message_date date,
                            message_time time)
                      """))
    conn.execute(text("""create table user(
                            user_id integer primary key AUTOINCREMENT,
                            username varchar(40) unique,
                            email varchar(40) unique,
                            password varchar(40))
                      """))
    

    result = conn.execute(text("select * from user"))
    for row in result.mappings().all():
        print(row)

import sqlite3

import utils

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('proverbs.db')
        self.c = self.conn.cursor()

    def init(self):
        script = utils.read("resources/dbscript.sql").replace('\n', ' ').split(';')
        for stmt in script:
            stmt = stmt.strip()
            if stmt:
                self.execute(stmt)

    def execute(self, sql):
        self.c.execute(sql)
        self.conn.commit()

    def insert(self, sql, *args):
        self.c.execute(sql, args)
        self.conn.commit()
        return self.c.lastrowid

    def select_one(self, sql, *args):
        self.c.execute(sql, args)
        return self.c.fetchone()

    def select_all(self, sql, *args):
        self.c.execute(sql, args)
        return self.c.fetchall()

    def close(self):
        self.conn.close()

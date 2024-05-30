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
        self.c.execute(sql, self.update_args(args))
        self.conn.commit()
        return self.c.lastrowid

    def select_one(self, sql, *args):
        self.c.execute(sql, args)
        return self.c.fetchone()

    def select_all(self, sql, *args):
        self.c.execute(sql, self.update_args(args))
        return self.c.fetchall()

    def update_args(self, args):
        new_args = []
        for arg in args:
            if arg is not None:
                new_arg = arg
            else:
                new_arg = 'None'
            new_args.append(new_arg)
        return new_args

    def close(self):
        self.conn.close()

    def get_categories(self):
        return self.select_all("SELECT id, name FROM category")

    def get_proverbs_by_category(self, category_id):
        return self.select_all("SELECT id, value, description FROM proverb WHERE category_id = ?", (category_id,))

    def get_random_descriptions(self, category_id, exclude_description):
        return self.select_all(
            "SELECT description FROM proverb WHERE category_id != ? AND description != ? ORDER BY RANDOM() LIMIT 3",
            (category_id, exclude_description))

DROP TABLE IF EXISTS lemmas_usage;
DROP TABLE IF EXISTS proverb;
DROP TABLE IF EXISTS lemma;
DROP TABLE IF EXISTS category;
DROP TABLE IF EXISTS category_lemma_statistics;

CREATE TABLE IF NOT EXISTS category (
    id integer primary key autoincrement,
    name varchar(100) unique not null
);

CREATE TABLE IF NOT EXISTS proverb (
    id integer primary key autoincrement,
    value varchar(255) unique not null,
    description varchar(500) not null,
    category_id integer not null,
    foreign key (category_id) references category(id)
);

CREATE TABLE IF NOT EXISTS lemma (
    id integer primary key autoincrement,
    value varchar(100) unique not null,
    pos varchar(25) not null
);

CREATE TABLE IF NOT EXISTS category_lemma_statistics (
    category_id integer not null,
    category_name varchar(50) not null,
    lemma_id integer not null,
    lemma varchar(50) not null,
    frequency integer not null,
    foreign key (lemma_id) references lemma(id),
    foreign key (category_id) references category(id)
);

CREATE TABLE IF NOT EXISTS lemmas_usage (
    lemma_id integer not null,
    proverb_id integer not null,
    usage_type varchar(50) not null,
     frequency integer not null,
    foreign key (lemma_id) references lemma(id),
    foreign key (proverb_id) references proverb(id)
);

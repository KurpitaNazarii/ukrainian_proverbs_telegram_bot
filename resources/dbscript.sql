DROP TABLE IF EXISTS lemmas_usage;
DROP TABLE IF EXISTS proverb;
DROP TABLE IF EXISTS lemma;
DROP TABLE IF EXISTS category;
DROP TABLE IF EXISTS word;

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

CREATE TABLE IF NOT EXISTS lemmas_usage (
    lemma_id integer not null,
    proverb_id integer not null,
    usage_type varchar(50) not null,
    foreign key (lemma_id) references lemma(id),
    foreign key (proverb_id) references proverb(id)
);

CREATE TABLE IF NOT EXISTS word (
    id integer primary key autoincrement,
    proverb_id integer not null,
    usage_type varchar(50) not null,
    value varchar(100) not null,
    pos varchar(25) not null,
    aspect varchar(25) DEFAULT 'None',
    number varchar(25) DEFAULT 'None',
    person varchar(25) DEFAULT 'None',
    gender varchar(25) DEFAULT 'None',
    tense varchar(25) DEFAULT 'None',
    foreign key (proverb_id) references proverb(id)
);
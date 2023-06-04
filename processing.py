import json
import pymorphy2 as pymorphy2
import tokenize_uk as tokenize_uk

import utils
from db import Database

db = Database()
db.init()

analyzer = pymorphy2.MorphAnalyzer(lang='uk')

json_data = utils.read('resources/proverbs-with-description-edited.json')
data = dict(json.loads(json_data))


def get_lemmas(text):
    lemmas = list()
    for word in tokenize_uk.tokenize_words(text):
        parsed = analyzer.parse(word)[0]
        pos = parsed.tag.POS
        if pos:
            lemma = parsed.normal_form
            lemmas.append((lemma, pos))
    return lemmas


def process_lemmas(text, type, proverb_id):
    all_lemmas = get_lemmas(text)
    unique_lemmas = set(all_lemmas)
    for lemma_info in unique_lemmas:
        lemma = lemma_info[0]
        pos = lemma_info[1]

        lemma_id_row = db.select_one(f'SELECT id FROM lemma WHERE value = ?', lemma)
        if lemma_id_row:
            lemma_id = lemma_id_row[0]
        else:
            lemma_id = db.insert(f'INSERT INTO lemma (value, pos) VALUES (?, ?)', lemma, pos)

        frequency = all_lemmas.count(lemma_info)
        db.insert(f'INSERT INTO lemmas_usage VALUES (?, ?, ?, ?)', lemma_id, proverb_id, type, frequency)


def process_proverb(proverb, description):
    print(f'Processing proverb: {proverb}')
    substring_description = "Синонім. "
    substring_synonyms = "; "
    if substring_description in description:
        parts = description.split(substring_description)
        synonyms = parts[1].split(substring_synonyms)
        description = parts[0]
        synonyms = list(synonyms)
        for synonym in synonyms:
            print(f'Processing synonym: {synonym}')
            process_proverb(synonym, description)

    proverb_id = db.insert(f'INSERT INTO proverb (value, description, category_id) VALUES (?, ?, ?)',
                           proverb, description, category_id)

    process_lemmas(proverb, 'VALUE', proverb_id)
    process_lemmas(description, 'DESCRIPTION', proverb_id)


if __name__ == '__main__':
    for category, proverbs in data.items():
        category_id = db.insert(f'INSERT INTO category (name) VALUES (?)', category)
        print(f'Processing category: {category}')
        for proverb, description in proverbs.items():
            process_proverb(proverb, description)
    all_lemmas_statistics_in_categories = db.select_all(f'SELECT p.category_id, (SELECT name FROM category '
                                                        f'where id = p.category_id), u.lemma_id, (SELECT value FROM '
                                                        f'lemma where id = u.lemma_id), sum(u.frequency) as frequency '
                                                        f'FROM lemmas_usage u JOIN proverb p ON p.id = u.proverb_id '
                                                        f'where u.usage_type = ? GROUP by p.category_id, u.lemma_id order by category_id, frequency desc', 'VALUE')
    for row in all_lemmas_statistics_in_categories:
        db.insert(f'INSERT into category_lemma_statistics VALUES (?, ?, ?, ?, ?)', row[0], row[1], row[2], row[3], row[4])

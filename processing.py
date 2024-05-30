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


def get_words(text):
    words = list()
    for word in tokenize_uk.tokenize_words(text):
        parsed = analyzer.parse(word)[0]
        pos = parsed.tag.POS
        word = word.lower()
        if pos:
            if pos == "VERB":
                aspect = parsed.tag.aspect
                number = parsed.tag.number
                person = parsed.tag.person
                gender = parsed.tag.gender
                tense = parsed.tag.tense
                words.append((word, pos, aspect, number, person, gender, tense))
                continue
            words.append((word, pos))
    return words


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


def process_words(text, type, proverb_id):
    all_words = get_words(text)
    unique_words = set(all_words)
    for word_info in unique_words:
        word = word_info[0]
        pos = word_info[1]
        if pos == "VERB":
            aspect = word_info[2]
            number = word_info[3]
            person = word_info[4]
            gender = word_info[5]
            tense = word_info[6]
            db.insert(
                f'INSERT INTO word (proverb_id, usage_type, value, pos, aspect, number, person, gender, tense) VALUES '
                f'(?, ?, ?, ?, ?, ?, ?, ?, ?)',
                proverb_id, type, word, pos, aspect, number, person, gender, tense)
        else:
            db.insert(
                f'INSERT INTO word (proverb_id, usage_type, value, pos) VALUES (?, ?, ?, ?)', proverb_id, type, word,
                pos)


def process_proverb(proverb, description):
    substring_description = " Синонім. "
    substring_synonyms = "; "
    if substring_description in description:
        parts = description.split(substring_description)
        synonyms = parts[1].split(substring_synonyms)
        description = parts[0]
        synonyms = list(synonyms)
        for synonym in synonyms:
            process_proverb(synonym, description)

    proverb_id = db.insert(f'INSERT INTO proverb (value, description, category_id) VALUES (?, ?, ?)',
                           proverb, description, category_id)

    process_lemmas(proverb, 'VALUE', proverb_id)
    process_lemmas(description, 'DESCRIPTION', proverb_id)
    process_words(proverb, 'VALUE', proverb_id)
    process_words(description, 'DESCRIPTION', proverb_id)


if __name__ == '__main__':
    for category, proverbs in data.items():
        category_id = db.insert(f'INSERT INTO category (name) VALUES (?)', category)
        print(f'Processing category: {category}')
        for proverb, description in proverbs.items():
            process_proverb(proverb, description)

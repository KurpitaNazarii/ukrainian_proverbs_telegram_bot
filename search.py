class ProverbSearchResult:
    def __init__(self, category, proverb, description):
        self.category = category
        self.proverb = proverb
        self.description = description


class ProverbsFilter:

    def __init__(self,
                 lemma=None, usage_types=None,
                 first_proverb_letter=None,
                 substring=None):
        self.lemma = lemma
        self.usage_types = usage_types
        self.first_proverb_letter = first_proverb_letter
        self.substring = substring

    def get_query(self, offset: int = 0):
        if self.lemma:
            usage_types_query_part = ''
            for usage_type in self.usage_types:
                usage_types_query_part += f" lu.usage_type = '{usage_type}' OR"
            usage_types_query_part = usage_types_query_part[:-2]
            query = 'SELECT DISTINCT c.name, p.value, p.description FROM lemma l ' \
                    'JOIN lemmas_usage lu ON l.id = lu.lemma_id ' \
                    'JOIN proverb p on lu.proverb_id = p.id ' \
                    f'JOIN category c on p.category_id = c.id WHERE ({usage_types_query_part}) AND l.value = ? LIMIT ' \
                    f'5 OFFSET ?'
            return query, [self.lemma, offset]
        elif self.first_proverb_letter:
            query = f' SELECT DISTINCT c.name, p.value, p.description FROM proverb p ' \
                    f'JOIN category c ON p.category_id = c.id ' \
                    f'WHERE substr(p.value,1,1) IN(?, ?) LIMIT 5 OFFSET ?'
            return query, [self.first_proverb_letter.lower(), self.first_proverb_letter.upper(), offset]
        elif self.substring:
            query = f'SELECT DISTINCT c.name, p.value, p.description FROM proverb p ' \
                    f'JOIN category c ON p.category_id = c.id ' \
                    f'WHERE p.value LIKE (\'%\' || ? || \'%\') OR ' \
                    f'p.description LIKE (\'%\' || ? || \'%\') LIMIT 5 OFFSET ?'
            return query, [self.substring, self.substring, offset]


def search_proverbs(filter, db, offset: int = 0):
    query, params = filter.get_query(offset=offset)
    rows = db.select_all(query, *params)

    results = []
    for row in rows:
        result = ProverbSearchResult(row[0], row[1], row[2])
        results.append(result)

    return results


def search_lemmas_by_first_letter(letter, usage_type, db):
    rows = db.select_all('SELECT DISTINCT (l.value) FROM lemmas_usage u JOIN lemma l ON u.lemma_id = l.id '
                         'WHERE u.usage_type = ? AND substr(l.value,1,1) = ? ORDER BY l.value', usage_type,
                         letter.lower())
    return [row[0] for row in rows]

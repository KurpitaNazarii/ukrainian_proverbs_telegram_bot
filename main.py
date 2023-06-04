import streamlit as st

import search
from search import ProverbsFilter

st.set_page_config(page_title='Словник паремій', page_icon='📖', layout='wide', initial_sidebar_state="auto",
                   menu_items=None)
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

from db import Database

db = Database()


def searching_page():
    by_lemma_in_proverb = 'За лемою у паремії'
    by_lemma_in_proverb_and_meaning = 'За лемою у паремії і значенні'
    by_first_letter_in_proverb = 'За першою літерою паремії'
    by_substring_in_proverb = 'За частинкою у паремії і значенні'
    search_type = st.selectbox("Виберіть, як шукати:", [
        by_lemma_in_proverb,
        by_lemma_in_proverb_and_meaning,
        by_first_letter_in_proverb,
        by_substring_in_proverb
    ])

    user_input = st.text_input('Введіть ваш запит').strip()
    submit_button = st.button('Шукати')

    if submit_button and user_input:
        if search_type == by_lemma_in_proverb:
            # lemma = input('Enter the lemma: ').strip()
            filter = ProverbsFilter(lemma=user_input, usage_types=['VALUE'])
        elif search_type == by_lemma_in_proverb_and_meaning:
            # lemma = input('Enter the lemma: ').strip()
            filter = ProverbsFilter(lemma=user_input, usage_types=['VALUE', 'DESCRIPTION'])
        elif search_type == by_first_letter_in_proverb:
            # letter = input('Enter the letter: ').strip()
            filter = ProverbsFilter(first_proverb_letter=user_input)
        elif search_type == by_substring_in_proverb:
            # substring = input('Enter the substring: ')
            filter = ProverbsFilter(substring=user_input)

        results = search.search_proverbs(filter, db)
        st.markdown('***')
        display_proverbs(results)


def display_proverbs(results):
    if not results:
        st.write('Нічого не знайдено :(')
    by_category = dict()
    for result in results:
        if result.category not in by_category:
            by_category[result.category] = list()
        proverbs_in_category = by_category[result.category]

        proverbs_in_category.append(result)
    for category, proverbs_infos in by_category.items():
        st.subheader(f'{category}')
        for proverb_info in proverbs_infos:
            proverb = proverb_info.proverb.replace("*", "\\*")
            st.write(f'**{proverb}**  \n'
                     f'{proverb_info.description}  ')
        st.markdown('***')


def lemmas_by_alphabet_page():
    letters = "А, Б, В, Г, Ґ, Д, Е, Є, Ж, З, И, І, Ї, Й, К, Л, М, Н, О, П, Р, С, Т, У, Ф, Х, Ц, Ч, Ш, Щ, Ь, Ю, Я" \
        .split(', ')
    lemmas, proverbs = st.columns(spec=2, gap='large')
    with lemmas:
        tabs = st.tabs(letters)
    tabs = dict(zip(letters, tabs))

    for letter, tab in tabs.items():
        with tab:
            lemmas = search.search_lemmas_by_first_letter(letter, 'VALUE', db)
            for lemma in lemmas:
                lemma_button = st.button(lemma)
                if lemma_button:
                    proverbs.text('')
                    with proverbs:
                        results = search.search_proverbs(ProverbsFilter(lemma=lemma, usage_types=['VALUE']), db)
                        display_proverbs(results)


pages = {
    'Пошук паремій': searching_page,
    'Алфавітний покажчик лем': lemmas_by_alphabet_page
}

selected_page = st.sidebar.selectbox("  ", pages.keys())
pages[selected_page]()

import asyncio
import logging
import random
import re
from itertools import combinations

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, KeyboardButton, \
    InlineKeyboardBuilder

import resources.keyboard as kb
from db import Database
from resources.config import TOKEN
from search import ProverbsFilter, search_proverbs


class Test(StatesGroup):
    test1 = State()
    category_id = State()
    correct_proverb = State()
    correct_answers = State()
    category_proverbs = State()
    used_proverbs = State()
    next_proverb = State()


class Search(StatesGroup):
    search_type = State()
    lemma = State()
    offset = State()
    lemma_meaning = State()
    letter = State()
    substring = State()
    send_results = State()
    results = State()
    next_search = State()


class Quiz(StatesGroup):
    choosing_category = State()
    category_id = State()
    answering_question = State()
    category_proverbs = State()
    used_proverbs = State()
    used_proverb_name = State()
    correct_answers = State()


class QuizVerb(StatesGroup):
    choosing_category = State()
    category_proverbs = State()
    category_id = State()
    answering_question = State()
    correct_verbs = State()
    used_proverb_value = State()
    correct_answers = State()


db = Database()
router = Router()
bot = Bot(token=TOKEN)
dp = Dispatcher()
PAGE_SIZE = 7  # Number of categories per page


async def choose_category(message: Message, page: int = 1,
                          call: CallbackQuery = None):
    # Calculate the offset for the query
    offset = (page - 1) * PAGE_SIZE
    # Query to fetch categories with pagination
    categories = db.select_all('SELECT id, name FROM category LIMIT ? OFFSET ?',
                               PAGE_SIZE, offset)
    builder = InlineKeyboardBuilder()
    # Add category buttons
    for category_id, category_name in categories:
        builder.add(InlineKeyboardButton(text=category_name,
                                         callback_data=f'category:{category_id}'))
    # Check if there are more pages
    if db.select_one('SELECT COUNT(*) FROM category')[0] > page * PAGE_SIZE:
        builder.add(InlineKeyboardButton(text='Далі...',
                                         callback_data=f'page:{page + 1}'))
    # Add a 'Previous' button if it's not the first page
    if page > 1:
        builder.add(InlineKeyboardButton(text='Назад',
                                         callback_data=f'page:{page - 1}'))
    builder.adjust(1)  # Adjust the keyboard layout to have 2 buttons per row
    # Edit the message if it's from a callback, otherwise send a new message
    if call:
        await call.message.edit_text('Оберіть категорію:',
                                     reply_markup=builder.as_markup())
        await call.answer()  # Stop the loading spinner on the button
    else:
        await message.answer('Оберіть категорію:',
                             reply_markup=builder.as_markup())


def generate_groups(verbs, group_size):
    if group_size < 1:
        raise ValueError("Group size must be at least 1")

    # Generate all possible unique combinations of the specified group size
    all_combinations = list(combinations(verbs, group_size))
    random.shuffle(
        all_combinations)  # Shuffle the combinations to add randomness to the order

    # Convert tuples to comma-separated strings
    groups = [", ".join(comb) for comb in all_combinations]

    return groups


# Handler for navigation
@router.callback_query(F.data.startswith('page:'))
async def handle_page_switch(callback: CallbackQuery):
    page = int(callback.data.split(':')[1])
    await choose_category(callback.message, page, callback)
    await callback.answer()  # This is necessary to stop the loading animation


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await message.answer('Оберіть опцію на своїй клавіатурі.',
                         reply_markup=kb.main)
    await state.clear()


@router.message(Command('help'))
async def command_get_help(message: Message):
    await get_help(message)


@router.message(F.text == 'Навчатися')
async def study(message: Message):
    await message.answer(
        'У Вашому доступі є низка вправ для вивчення/запам\'ятовувавння прислів\'їв та приказок. '
        'Після вибору вправи, необхідно обрати категорію в якій Ви хочете удосконалити свої знання. '
        'Оберіть вправу на своїй клавіатурі.', reply_markup=kb.study)


@router.message(F.text == 'Допомога')
async def get_help(message: Message):
    text = (
        '/start \\- розпочати бота\n/help \\- команда яка викликає це повідомлення\n\n'
        '`Навчатися` \\- кнопка для навчання\n'
        '*Вправа зібрати прислів\'я/приказку* \\- розставити слова у правильному порядку\n'
        '*Вправа відгадати значення прислів\'я/приказки* \\- обрати на клавіатурі правильне пояснення\n'
        '*Вправа доповнити прислів\'я/приказку дієсловом* \\- обрати на клавіатурі дієслово, якого не вистачає\n\n'
        '`Пошук 🔎`\\- кнопка для пошуку\n'
        '*за лемою у паремії* \\- пошук за лемою, яка є частиною самого прислів\'я/приказки\n'
        '_лема це канонічна форма лексеми\\. Наприклад: "хотіти" лема слів "хочу", "хотіла" і т\\.д\\._\n'
        '*за лемою у паремії і значенні* \\- пошук за лемою, яка є частиною самого прислів\'я/приказки або пояснення\n'
        '*за першою літерою паремії* \\- пошук за літерою на яку починається прислів\'я/приказка\n'
        '*за частинкою у паремії і значенні* \\- пошук за будь\\-яким набором символів у прислів\'ї/приказці або '
        'поясненні\n'
        '_наприклад: за пошуком "берись дру", "сутуж" або "не буде" бот знайде таку паремію "Берись дружно — не буде '
        'сутужно\\."_')
    await message.answer(text, reply_markup=kb.main, parse_mode='MarkdownV2')


@router.message(F.text == 'Вправа зібрати прислів\'я/приказку')
async def construct_proverb(message: Message, state: FSMContext):
    await choose_category(message)
    await state.set_state(Test.test1)


@router.callback_query(Test.test1)
async def for_category(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.removeprefix('category:'))
    category_name = \
        db.select_one('SELECT name FROM category WHERE id = ?', category_id)[0]
    await callback.message.edit_text('Обрано категорію: ' + category_name)
    await state.update_data(correct_answers=0)
    proverbs = db.select_all('SELECT value FROM proverb WHERE category_id = ?',
                             category_id)
    proverbs = [proverb[0] for proverb in proverbs]
    await state.update_data(category_proverbs=proverbs)
    proverb = random.choice(proverbs)
    words = proverb.split()
    random.shuffle(words)
    await bot.send_message(callback.message.chat.id,
                           text='Складіть прислів\'я/приказку зі слів: \n' + '\n'.join(
                               words),
                           reply_markup=kb.ongoing_test)
    await state.set_state(Test.correct_proverb)
    await state.update_data(category_id=category_id)
    await state.update_data(correct_proverb=proverb)


def compare_strings(str1, str2):
    # Define a function to clean the strings
    def clean_string(s):
        # Remove punctuation, dashes, and convert to lowercase
        return re.sub(r'[\W_]', '', s).lower()

    # Clean both strings
    cleaned_str1 = clean_string(str1)
    cleaned_str2 = clean_string(str2)

    # Compare the cleaned strings
    return cleaned_str1 == cleaned_str2


@router.message(Test.correct_proverb)
async def check_proverb(message: Message, state: FSMContext):
    data = await state.get_data()
    correct_proverb = data['correct_proverb']
    if message.text not in ["Завершити", "Обрати іншу категорію"]:
        if compare_strings(message.text, correct_proverb):
            await message.answer("Правильно! 🎉")
            correct_answers = (await state.get_data())['correct_answers']
            correct_answers += 1
            await state.update_data(correct_answers=correct_answers)
        else:
            await message.answer(
                "Неправильно :(\nПравильний порядок: " + correct_proverb)

        if 'used_proverbs' not in data:
            used_proverbs = []
        else:
            used_proverbs = data['used_proverbs']
        used_proverbs.append(correct_proverb)
        await state.update_data(used_proverbs=used_proverbs)
        category_proverbs = data['category_proverbs']
        category_id = data['category_id']
        chat_id = message.chat.id
        proverbs = []
        for proverb in category_proverbs:
            if proverb not in used_proverbs:
                proverbs.append(proverb)
        if not proverbs:
            correct_answers = (await state.get_data())['correct_answers']
            category_name = (
                db.select_one('SELECT name FROM category WHERE id = ?',
                              category_id))[0]
            await bot.send_message(chat_id,
                                   text=f'Вітаю! Ви зібрали усі прислів\'я/приказки у категорії: '
                                        f'{category_name}'
                                        f'\nВаш результат: {correct_answers} правильних із {len(used_proverbs)}.'
                                        f'\nОберіть іншу категорію або завершіть навчання.',
                                   reply_markup=kb.end_test)
            return
        proverb = random.choice(proverbs)
        words = proverb.split()
        random.shuffle(words)
        await bot.send_message(message.chat.id,
                               text='Складіть прислів\'я/приказку зі слів: \n' + '\n'.join(
                                   words))
        await state.update_data(correct_proverb=proverb)
        await state.set_state(Test.correct_proverb)
    elif message.text == 'Завершити':
        await state.clear()
        await message.answer('Вправу завершено.', reply_markup=kb.main)
        return
    elif message.text == 'Обрати іншу категорію':
        await state.clear()
        await choose_category(message)
        await state.set_state(Test.test1)
        return


@router.message(F.text == 'Вправа відгадати значення прислів\'я/приказки')
async def start_quiz(message: Message, state: FSMContext):
    await choose_category(message)
    await state.set_state(Quiz.choosing_category)


@router.callback_query(Quiz.choosing_category)
async def process_category(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.removeprefix('category:'))
    category_name = \
        db.select_one('SELECT name FROM category WHERE id = ?', category_id)[0]
    await callback.message.edit_text(f'Обрано категорію: *{category_name}*',
                                     parse_mode='MarkdownV2')
    await state.update_data(correct_answers=0)
    proverbs = db.select_all(
        'SELECT id, value, description FROM proverb WHERE category_id = ?',
        category_id)
    await state.update_data(category_proverbs=proverbs)
    quiz_proverb = random.choice(proverbs)
    correct_description = quiz_proverb[2]
    random_descriptions = db.select_all(
        "SELECT DISTINCT description FROM proverb WHERE category_id = ? AND description != ? ORDER BY RANDOM() LIMIT 3",
        category_id, correct_description)
    wrong_descriptions = [desc[0] for desc in random_descriptions]
    options = [correct_description] + wrong_descriptions
    random.shuffle(options)
    reply_markup = generate_quiz_markup(len(options))
    replace_dict = {".": "\\.", "(": "\\(", ")": "\\)", "!": "\\!", "?": "\\?",
                    "-": "\\-"}
    proverb = quiz_proverb[1]
    for old, new in replace_dict.items():
        proverb = proverb.replace(old, new)
    await callback.message.answer(f"Прислів'я/Приказка:\n *{proverb}*",
                                  parse_mode='MarkdownV2')
    letters = ['А', 'Б', 'В', 'Г']
    number = 0
    for option in options:
        if option == correct_description:
            correct_description = letters[number]
        option = letters[number] + ': ' + option
        options[number] = option
        number += 1
    new_options = '\n'.join(options)
    for old, new in replace_dict.items():
        new_options = new_options.replace(old, new)
    await callback.message.answer(f"Варіанти відповідей:\n _{new_options}_",
                                  reply_markup=reply_markup,
                                  parse_mode='MarkdownV2')
    # Store data in state
    await state.update_data(correct_description=correct_description,
                            category_id=category_id,
                            used_proverb_name=quiz_proverb[1])
    await state.set_state(Quiz.answering_question)


@router.message(Quiz.answering_question)
async def check_answer(message: Message, state: FSMContext):
    user_data = await state.get_data()
    correct_description = user_data['correct_description']
    if message.text not in ["Завершити", "Обрати іншу категорію"]:
        if message.text == correct_description:
            await message.answer("Правильно! 🎉")
            correct_answers = (await state.get_data())['correct_answers']
            correct_answers += 1
            await state.update_data(correct_answers=correct_answers)
        else:
            await message.answer(
                "Неправильно :( Правильне значення: " + correct_description)

        correct_proverb = user_data['used_proverb_name']
        if 'used_proverbs' not in user_data:
            used_proverbs = []
        else:
            used_proverbs = user_data['used_proverbs']
        used_proverbs.append(correct_proverb)
        await state.update_data(used_proverbs=used_proverbs)
        category_proverbs = (await state.get_data())['category_proverbs']
        proverbs_number = len(category_proverbs)
        category_id = (await state.get_data())['category_id']
        chat_id = message.chat.id
        proverbs = []
        for proverb in category_proverbs:
            if not proverb[1] in used_proverbs:
                proverbs.append(proverb)
        if not proverbs:
            correct_answers = (await state.get_data())['correct_answers']
            category_name = (
                db.select_one('SELECT name FROM category WHERE id = ?',
                              category_id))[0]
            await bot.send_message(chat_id,
                                   text=f'Вітаю! Ви співставили усі прислів\'я/приказки з їх значеннями у категорії: '
                                        f'{category_name}'
                                        f'\nТвій результат: {correct_answers} правильних із {proverbs_number}.'
                                        f'\nОберіть іншу категорію або завершіть навчання.',
                                   reply_markup=kb.end_test)
            return
        quiz_proverb = random.choice(proverbs)
        correct_description = quiz_proverb[2]
        random_descriptions = db.select_all(
            "SELECT DISTINCT description FROM proverb WHERE category_id = ? AND description != ? ORDER BY RANDOM() "
            "LIMIT 3",
            category_id, correct_description)
        wrong_descriptions = [desc[0] for desc in random_descriptions]
        options = [correct_description] + wrong_descriptions
        random.shuffle(options)
        reply_markup = generate_quiz_markup(len(options))
        proverb_name = quiz_proverb[1]
        replace_dict = {".": "\\.", "(": "\\(", ")": "\\)", "!": "\\!",
                        "?": "\\?", "-": "\\-"}
        for old, new in replace_dict.items():
            proverb_name = proverb_name.replace(old, new)
        await bot.send_message(message.chat.id,
                               text=f"Прислів'я/Приказка:\n *{proverb_name}*",
                               parse_mode='MarkdownV2')
        letters = ['А', 'Б', 'В', 'Г']
        number = 0
        for option in options:
            if option == correct_description:
                correct_description = letters[number]
            option = letters[number] + ': ' + option
            options[number] = option
            number += 1
        new_options = '\n'.join(options)
        for old, new in replace_dict.items():
            new_options = new_options.replace(old, new)
        await bot.send_message(message.chat.id,
                               text=f"Варіанти відповідей:\n _{new_options}_",
                               reply_markup=reply_markup,
                               parse_mode='MarkdownV2')
        # Store data in state
        await state.update_data(correct_description=correct_description,
                                category_id=category_id,
                                used_proverb_name=quiz_proverb[1])
        await state.set_state(Quiz.answering_question)
    elif message.text == 'Завершити':
        await state.clear()
        await message.answer('Вправу завершено.', reply_markup=kb.main)
        return
    elif message.text == 'Обрати іншу категорію':
        await state.clear()
        await choose_category(message)
        await state.set_state(Quiz.choosing_category)
        return


def generate_quiz_markup(options_len):
    options = ['А', 'Б', 'В', 'Г']
    builder = ReplyKeyboardBuilder()
    for option in range(0, options_len):
        builder.add(KeyboardButton(text=options[option]))
    # Add control buttons with specific row setting
    builder.add(KeyboardButton(text="Завершити"),
                KeyboardButton(text="Обрати іншу категорію"))
    builder.adjust(2, 2, 2)  # Set one button per row for options if needed
    return builder.as_markup(one_time_keyboard=True,
                             input_field_placeholder='Оберіть варіант відповіді',
                             resize_keyboard=True)


@router.message(F.text == 'Вправа доповнити прислів\'я/приказку дієсловом')
async def start_quiz(message: Message, state: FSMContext):
    await choose_category(message)
    await state.set_state(QuizVerb.choosing_category)


@router.callback_query(QuizVerb.choosing_category)
async def process_category(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.removeprefix('category:'))
    category_name = \
        db.select_one('SELECT name FROM category WHERE id = ?', category_id)[0]
    await callback.message.edit_text('Обрано категорію: ' + category_name)
    await state.update_data(correct_answers=0)
    proverbs = db.select_all(
        "SELECT DISTINCT proverb.id, proverb.value FROM proverb JOIN word ON proverb.id = proverb_id WHERE "
        "proverb.category_id = ? AND word.pos = 'VERB' AND word.usage_type = 'VALUE'",
        category_id)
    await state.update_data(category_proverbs=proverbs)
    quiz_proverb = random.choice(proverbs)
    quiz_proverb_id = quiz_proverb[0]
    quiz_proverb_value = quiz_proverb[1]
    correct_verb_list = db.select_one(
        "SELECT value, aspect, number, gender, tense FROM word WHERE word.pos = 'VERB' AND word.proverb_id = ? AND "
        "word.usage_type = 'VALUE'",
        quiz_proverb_id)
    correct_verb = correct_verb_list[0]
    aspect = correct_verb_list[1]
    number = correct_verb_list[2]
    gender = correct_verb_list[3]
    tense = correct_verb_list[4]
    number_of_correct_verbs = 1  # len(correct_verb)
    random_verbs = db.select_all(
        'SELECT DISTINCT word.value FROM word JOIN proverb ON proverb_id = proverb.id '
        "WHERE word.pos = 'VERB' AND word.proverb_id != ? AND word.aspect = ? AND word.number = ? AND word.gender = ? "
        "AND word.tense = ?",
        quiz_proverb_id, aspect, number, gender, tense)
    wrong_verbs = [verb[0] for verb in random_verbs]
    wrong_verbs = generate_groups(wrong_verbs, number_of_correct_verbs)
    options = [correct_verb] + random.sample(wrong_verbs, 3)
    random.shuffle(options)
    reply_markup = generate_quiz_verb_markup(options)
    replace_dict = {".": "\\.", "(": "\\(", ")": "\\)", "!": "\\!", "?": "\\?",
                    "—": "\\—", "-": "\\-"}
    proverb = quiz_proverb[1]
    for old, new in replace_dict.items():
        proverb = proverb.replace(old, new)
    for verb in correct_verb_list:
        # Use a regular expression to replace the verb in a case-insensitive manner
        proverb = re.sub(r'\b' + re.escape(verb) + r'\b', '──────', proverb,
                         flags=re.IGNORECASE)
    await callback.message.answer(f"Прислів'я/Приказка:\n *{proverb}*",
                                  reply_markup=reply_markup,
                                  parse_mode='MarkdownV2')
    # Store data in state
    await state.update_data(correct_verbs=correct_verb, category_id=category_id,
                            used_proverb_value=quiz_proverb_value)
    await state.set_state(QuizVerb.answering_question)


@router.message(QuizVerb.answering_question)
async def check_answer(message: Message, state: FSMContext):
    user_data = await state.get_data()
    correct_verbs = user_data['correct_verbs']
    if message.text not in ["Завершити", "Обрати іншу категорію"]:
        if message.text == correct_verbs:
            await message.answer("Правильно! 🎉")
            correct_answers = (await state.get_data())['correct_answers']
            correct_answers += 1
            await state.update_data(correct_answers=correct_answers)
        else:
            await message.answer(
                "Неправильно :( Правильне дієслово: " + correct_verbs)

        correct_proverb = user_data['used_proverb_value']
        if not 'used_proverbs' in user_data:
            used_proverbs = []
        else:
            used_proverbs = user_data['used_proverbs']
        used_proverbs.append(correct_proverb)
        await state.update_data(used_proverbs=used_proverbs)
        category_proverbs = (await state.get_data())['category_proverbs']
        proverbs_number = len(category_proverbs)
        category_id = (await state.get_data())['category_id']
        chat_id = message.chat.id
        proverbs = []
        for proverb in category_proverbs:
            if not proverb[1] in used_proverbs:
                proverbs.append(proverb)
        if not proverbs:
            correct_answers = (await state.get_data())['correct_answers']
            category_name = (
                db.select_one('SELECT name FROM category WHERE id = ?',
                              category_id))[0]
            await bot.send_message(chat_id,
                                   text=f'Вітаю! Ви дібрали до усіх прислів\'їв/приказок дієлсова у категорії: '
                                        f'{category_name}'
                                        f'\nТвій результат: {correct_answers} правильних із {proverbs_number}.'
                                        f'\nОберіть іншу категорію або завершіть навчання.',
                                   reply_markup=kb.end_test)
            return
        quiz_proverb = random.choice(proverbs)
        quiz_proverb_id = quiz_proverb[0]
        quiz_proverb_value = quiz_proverb[1]
        correct_verb_list = db.select_one(
            "SELECT value, aspect, number, gender, tense FROM word WHERE word.pos = 'VERB' AND word.proverb_id = ? "
            "AND word.usage_type = 'VALUE'",
            quiz_proverb_id)
        correct_verb = correct_verb_list[0]
        aspect = correct_verb_list[1]
        number = correct_verb_list[2]
        gender = correct_verb_list[3]
        tense = correct_verb_list[4]
        number_of_correct_verbs = 1  # len(correct_verb)
        random_verbs = db.select_all(
            'SELECT DISTINCT word.value FROM word JOIN proverb ON proverb_id = proverb.id '
            "WHERE word.pos = 'VERB' AND word.proverb_id != ? AND word.aspect = ? AND word.number = ? AND word.gender "
            "= ? AND word.tense = ?",
            quiz_proverb_id, aspect, number, gender, tense)
        wrong_verbs = [verb[0] for verb in random_verbs]
        wrong_verbs = generate_groups(wrong_verbs, number_of_correct_verbs)
        options = [correct_verb] + random.sample(wrong_verbs, 3)
        random.shuffle(options)
        reply_markup = generate_quiz_verb_markup(options)
        replace_dict = {".": "\\.", "(": "\\(", ")": "\\)", "!": "\\!",
                        "?": "\\?", "—": "\\—", "-": "\\-"}
        proverb = quiz_proverb[1]
        for old, new in replace_dict.items():
            proverb = proverb.replace(old, new)
        for verb in correct_verb_list:
            # Use a regular expression to replace the verb in a case-insensitive manner
            proverb = re.sub(r'\b' + re.escape(verb) + r'\b', '──────', proverb,
                             flags=re.IGNORECASE)
        await bot.send_message(message.chat.id,
                               text=f"Прислів'я/Приказка:\n *{proverb}*",
                               reply_markup=reply_markup,
                               parse_mode='MarkdownV2')
        # Store data in state
        await state.update_data(correct_verbs=correct_verb,
                                category_id=category_id,
                                used_proverb_value=quiz_proverb_value)
        await state.set_state(QuizVerb.answering_question)
    elif message.text == 'Завершити':
        await state.clear()
        await message.answer('Вправу завершено.', reply_markup=kb.main)
        return
    elif message.text == 'Обрати іншу категорію':
        await state.clear()
        await choose_category(message)
        await state.set_state(QuizVerb.choosing_category)
        return


def generate_quiz_verb_markup(options):
    builder = ReplyKeyboardBuilder()
    for option in options:
        builder.add(KeyboardButton(text=option))
    # Add control buttons with specific row setting
    builder.add(KeyboardButton(text="Завершити"),
                KeyboardButton(text="Обрати іншу категорію"))
    builder.adjust(1, 1, 1, 1,
                   2)  # Set one button per row for options if needed
    return builder.as_markup(one_time_keyboard=True,
                             input_field_placeholder='Оберіть варіант відповіді',
                             resize_keyboard=False)


@router.callback_query(F.data == 'end_test')
async def go_next(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text('Вправу завершено.')
    await bot.send_message(callback.message.chat.id,
                           text='Оберіть опцію на клавіатурі.',
                           reply_markup=kb.main)
    await state.clear()


@router.message(F.text == 'Завершити')
async def go_next(message: Message, state: FSMContext):
    await bot.send_message(message.chat.id, text='Оберіть опцію на клавіатурі.',
                           reply_markup=kb.main)
    await state.clear()


@router.callback_query(F.data == 'change_category')
async def change_category_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text('Чудово! Повчимося ще!')
    await choose_category(callback.message)
    current_state = await state.get_state()
    if current_state == 'Quiz:answering_question':
        await state.clear()
        await state.set_state(Quiz.choosing_category)
    elif current_state == 'Test:correct_proverb':
        await state.clear()
        await state.set_state(Test.test1)
    elif current_state == 'QuizVerb:answering_question':
        await state.clear()
        await state.set_state(QuizVerb.choosing_category)


@router.message(F.text == 'Обрати іншу категорію')
async def change_category_handler(message: Message, state: FSMContext):
    await choose_category(message)
    current_state = await state.get_state()
    if current_state == 'Quiz:answering_question':
        await state.clear()
        await state.set_state(Quiz.choosing_category)
    elif current_state == 'Test:correct_proverb':
        await state.clear()
        await state.set_state(Test.test1)
    elif current_state == 'QuizVerb:answering_question':
        await state.clear()
        await state.set_state(QuizVerb.choosing_category)


@router.message(F.text == 'Пошук 🔎')
async def search(message: Message):
    await message.answer('Оберіть вид пошуку:', reply_markup=kb.search)


@router.callback_query(F.data == 'by_lemma_in_proverb')
async def by_lemma_in_proverb(callback: CallbackQuery, state: FSMContext):
    await callback.answer('Пошук здійснюватиметься за лемою у паремії')
    await callback.message.edit_text(
        'Пошук здійснюватиметься за лемою у паремії.'
        '\nУведіть лему для пошуку:')
    await state.set_state(Search.lemma)
    await state.update_data(offset=0)
    await state.update_data(next_search=False)


@router.callback_query(F.data == 'by_lemma_in_proverb_and_meaning')
async def by_lemma_in_proverb(callback: CallbackQuery, state: FSMContext):
    await callback.answer(
        'Пошук здійснюватиметься за лемою у паремії і значенні')
    await callback.message.edit_text(
        'Пошук здійснюватиметься за лемою у паремії і значенні.\nУведіть лему для пошуку:')
    await state.set_state(Search.lemma_meaning)
    await state.update_data(offset=0)
    await state.update_data(next_search=False)


@router.callback_query(F.data == 'by_first_letter_in_proverb')
async def by_lemma_in_proverb(callback: CallbackQuery, state: FSMContext):
    await callback.answer('Пошук здійснюватиметься за першою літерою паремії')
    await callback.message.edit_text(
        'Пошук здійснюватиметься за першою літерою паремії.\nУведіть літеру для пошуку:')
    await state.set_state(Search.letter)
    await state.update_data(offset=0)
    await state.update_data(next_search=False)


@router.callback_query(F.data == 'by_substring_in_proverb')
async def by_lemma_in_proverb(callback: CallbackQuery, state: FSMContext):
    await callback.answer(
        'Пошук здійснюватиметься за частинкою у паремії і значенні')
    await callback.message.edit_text(
        'Пошук здійснюватиметься за частинкою у паремії і значенні.\nУведіть слово чи його частину для пошуку:')
    await state.set_state(Search.substring)
    await state.update_data(offset=0)
    await state.update_data(next_search=False)


@router.message(Search.lemma)
async def search_by_lemma_in_proverb(message: Message, state: FSMContext):
    await state.update_data(search_type=Search.lemma)
    if not (await state.get_data())['next_search']:
        await state.update_data(lemma=message.text)
    dic = await state.get_data()
    filter = ProverbsFilter(lemma=dic['lemma'], usage_types=['VALUE'])
    offset = (await state.get_data())['offset']
    results = search_proverbs(filter, db, offset=offset)
    await state.update_data(results=results)
    await process_results(message, state)


@router.message(Search.lemma_meaning)
async def search_by_lemma_in_proverb_meaning(message: Message,
                                             state: FSMContext):
    await state.update_data(search_type=Search.lemma_meaning)
    if not (await state.get_data())['next_search']:
        await state.update_data(lemma_meaning=message.text)
    dic = await state.get_data()
    filter = ProverbsFilter(lemma=dic['lemma_meaning'],
                            usage_types=['VALUE', 'DESCRIPTION'])
    offset = (await state.get_data())['offset']
    results = search_proverbs(filter, db, offset=offset)
    await state.update_data(results=results)
    await process_results(message, state)


@router.message(Search.letter)
async def search_by_letter_in_proverb(message: Message, state: FSMContext):
    await state.update_data(search_type=Search.letter)
    if not (await state.get_data())['next_search']:
        await state.update_data(letter=message.text)
    dic = await state.get_data()
    filter = ProverbsFilter(first_proverb_letter=dic['letter'])
    offset = (await state.get_data())['offset']
    results = search_proverbs(filter, db, offset=offset)
    await state.update_data(results=results)
    await process_results(message, state)


@router.message(Search.substring)
async def search_by_substring_in_proverb(message: Message, state: FSMContext):
    await state.update_data(search_type=Search.substring)
    if not (await state.get_data())['next_search']:
        await state.update_data(substring=message.text)
    dic = await state.get_data()
    filter = ProverbsFilter(substring=dic['substring'])
    offset = (await state.get_data())['offset']
    results = search_proverbs(filter, db, offset=offset)
    await state.update_data(results=results)
    await process_results(message, state)


@router.message(Search.send_results)
async def process_results(message: Message, state: FSMContext):
    results = (await state.get_data())['results']
    offset = (await state.get_data())['offset']
    if not results:
        if offset == 0:
            noanswer = 'Нічого не знайдено 😔 \nПеревірте чи не допустили Ви помилки і спробуйте знову.\nОберіть вид ' \
                       'пошуку:'
            await bot.send_message(chat_id=message.chat.id, text=noanswer,
                                   disable_notification=True,
                                   reply_markup=kb.search)
        else:
            await bot.send_message(chat_id=message.chat.id,
                                   text='Це усі знайдені прислів\'я/приказки',
                                   disable_notification=True)
        await state.clear()
        return
    by_category = dict()
    count = 0
    for result in results:
        if result.category not in by_category:
            by_category[result.category] = list()
        proverbs_in_category = by_category[result.category]
        proverbs_in_category.append(result)
    for category, proverbs_infos in by_category.items():
        await bot.send_message(chat_id=message.chat.id,
                               text=f'Категорія: *{category}*',
                               disable_notification=True,
                               parse_mode='MarkdownV2')
        for proverb_info in proverbs_infos:
            replace_dict = {".": "\\.", "(": "\\(", ")": "\\)", "!": "\\!",
                            "?": "\\?", "-": "\\-"}
            for old, new in replace_dict.items():
                proverb_info.proverb = proverb_info.proverb.replace(old, new)
                proverb_info.description = proverb_info.description.replace(old,
                                                                            new)
            if count == len(results) - 1:
                if len(results) < 5:
                    await bot.send_message(chat_id=message.chat.id,
                                           text=f'\n `{proverb_info.proverb}`  \n'
                                                f'Значення: _{proverb_info.description}_  ',
                                           disable_notification=True,
                                           parse_mode='MarkdownV2')
                    await bot.send_message(chat_id=message.chat.id,
                                           text='Це усі знайдені прислів\'я/приказки',
                                           disable_notification=True)
                    await state.clear()
                    return
                builder = InlineKeyboardBuilder()
                builder.add(InlineKeyboardButton(text='Далі...',
                                                 callback_data='continue_search'))
                await bot.send_message(chat_id=message.chat.id,
                                       text=f'\n `{proverb_info.proverb}`  \n'
                                            f'Значення: _{proverb_info.description}_  ',
                                       disable_notification=True,
                                       parse_mode='MarkdownV2',
                                       reply_markup=builder.as_markup())
                await state.update_data(offset=offset + 5)
                return
            else:
                await bot.send_message(chat_id=message.chat.id,
                                       text=f'\n `{proverb_info.proverb}`  \n'
                                            f'Значення: _{proverb_info.description}_  ',
                                       disable_notification=True,
                                       parse_mode='MarkdownV2')
                count += 1


@router.callback_query(F.data == 'continue_search')
async def handle_next_search(callback: CallbackQuery, state: FSMContext):
    search_type = (await state.get_data())['search_type']
    await state.update_data(next_search=True)
    if search_type == 'Search:lemma':
        await search_by_lemma_in_proverb(callback.message, state)
    elif search_type == 'Search:lemma_meaning':
        await search_by_lemma_in_proverb_meaning(callback.message, state)
    elif search_type == 'Search:letter':
        await search_by_letter_in_proverb(callback.message, state)
    elif search_type == 'Search:substring':
        await search_by_substring_in_proverb(callback.message, state)
    await callback.answer()  # This is necessary to stop the loading animation


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    dp.include_router(router)
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')

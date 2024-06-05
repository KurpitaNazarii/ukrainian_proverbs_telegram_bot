from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Навчатися')],
    [KeyboardButton(text='Пошук 🔎'), KeyboardButton(text='Допомога')]
], resize_keyboard=True, input_field_placeholder='Оберіть опцію у меню.')

search = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='За лемою у паремії', callback_data='by_lemma_in_proverb'),
     InlineKeyboardButton(text='За лемою у паремії і тлумаченні', callback_data='by_lemma_in_proverb_and_meaning')],
    [InlineKeyboardButton(text='За першою літерою паремії', callback_data='by_first_letter_in_proverb'),
     InlineKeyboardButton(text='За частинкою у паремії і тлумаченні', callback_data='by_substring_in_proverb')]])

study = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Вправа: скласти прислів\'я/приказку')],
    [KeyboardButton(text='Вправа: відгадати значення прислів\'я/приказки')],
    [KeyboardButton(text='Вправа: доповнити прислів\'я/приказку дієсловом')]
], resize_keyboard=True, input_field_placeholder='Оберіть опцію у меню.')

end_test = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Завершити', callback_data='end_test'),
     InlineKeyboardButton(text='Обрати іншу тему', callback_data='change_category')],
], resize_keyboard=True)

ongoing_test = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Завершити'), KeyboardButton(text='Обрати іншу тему')],
], resize_keyboard=True, input_field_placeholder='Оберіть опцію у меню.')

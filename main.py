from peewee import IntegrityError
from telebot import TeleBot, StateMemoryStorage
from telebot.custom_filters import StateFilter
from telebot.types import Message, BotCommand
from typing import Dict
import requests

from models import User, create_model
from config import BOT_TOKEN, DEFAULT_COMMAND, API_KEY

"""
    Папка main.py - является проектом по созданию телеграмм бота, который помогает пользователю выбрать фильм по отдельно созданным коммандам.
    Телеграмм бот называется - MovieFinderBot, пользователи его могут найти, как - TG_movie_finder_bot.

    Импорты из проектов:
        Импорт из папки models: User; create_model - User позволяет создать или другими словами зарегестрировать пользователя; create_model -
        функция, которая создаёт модель пользователя.

        Импорт из папки config: BOT_TOKEN; DEFAULT_COMMAND; API_KEY
"""

bot = TeleBot(BOT_TOKEN, state_storage=StateMemoryStorage())


@bot.message_handler(commands=["start"])
def handle_start(message: Message) -> None:
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    try:
        User.create(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        bot.reply_to(message, "Добро пожаловать в менеджер задач!")


    except IntegrityError:
        bot.reply_to(message,
                     f"Рад вас снова видеть, {first_name}! \nНапишите комманду /help, чтобы увидеть функции этого бота.")


@bot.message_handler(commands=['help'])
def help_bot(message) -> None:
    bot.send_message(message.from_user.id, 'Доступные комманды бота: '
                                           '\nmovie_search - поиск фильма/сериала по названию'
                                           ' \nmovie_by_rating - поиск фильма/сериала по рейтингу '
                                           '\nlow_budget_movie - поиск фильмов/сериалов с низким бюджетом'
                                           '\nhigh_budget_movie - поиск фильмов/сериалов с высоким бюджетом'
                                           '\nhistory - история просмотра запросов и поиска фильмов/сериалов'
                                           'Чтобы воспользоапться одной из комманд, можете воспользоваться кнопкой меню!')


@bot.message_handler(commands=['movie_search'])
def movie_search(message: Message) -> None:
    bot.send_message(message.chat.id, 'Введите название фильма/сериала для поиска по названию')
    bot.register_next_step_handler(message, name_film)



@bot.message_handler(commands=['movie_by_rating'])
def movie_by_rating(message: Message) -> None:
    url: str = 'https://api.kinopoisk.dev/v1.4/movie/search?page=1&limit=10'
    headers: Dict = {
        "accept": "application/json",
        "X-API-KEY": API_KEY
    }
    resp = requests.get(url, headers=headers)
    data = resp.json()
    films = data.get("docs", [])
    for count in range(10):
        film = films[count]
        name: str = film.get('name', 'Без названия')
        rating: int = film.get('rating', {}).get('kp', 'Нет рейтинга')
        year = film.get('year', 'Нет года выпуска')
        description = film.get('description', 'Описание отсутствует')
        bot.send_message(message.from_user.id, f'{count + 1})Название фильма: {name} \nРейтинг: {rating}')

        with open('user_history_request.txt', 'a', encoding='utf-8') as file:
            file.write(f'Название :{name} \n Год выпуска: {year} \nОписание: {description} \nРейтинг: {rating}' + '\n')

    bot.send_message(message.chat.id, 'Если хотите посмотреть ещё подборки, можете указать комманду в меню.')


    with open('user_history_request.txt', 'r', encoding='utf-8') as file:
        lines: int = sum(1 for _ in file)
        if lines < 10:
            with open('user_history_request.txt', 'w') as f:
                pass


@bot.message_handler(commands=['low_budget_movie'])
def low_budget_movie(message: Message) -> None:
    bot.send_message(message.from_user.id, 'Укажите диапозон суммы, которой вы бы хотели найти фильм/сериал '
                                           '\nможете указать диапазон через -. Например: 1000-5000. '
                                           '\nИли же конкретное число, например: 15000')
    bot.register_next_step_handler(message, small_budget)





@bot.message_handler(commands=['high_budget_movie'])
def high_budget_movie(message: Message) -> None:
    bot.send_message(message.from_user.id, 'Укажите диапозон суммы, которой вы бы хотели найти фильм/сериал '
                                           '\nможете указать диапазон через -. Например: 1000-5000. '
                                           '\nИли же конкретное число, например: 15000')
    bot.register_next_step_handler(message, big_budget)




@bot.message_handler(commands=['history'])
def user_history(message: Message) -> None:
    with open('user_history_request.txt', 'r', encoding='utf-8') as file:
        bot.send_message(message.from_user.id, file.read())


# -----------------------------------------------------------------------------------------------------------------------


def small_budget(message: Message) -> None:
    price: str = message.text
    url: str = f"https://api.kinopoisk.dev/v1.4/movie?page=1&limit=10&budget.value={price}"
    headers: Dict = {
        "accept": "application/json",
        "X-API-KEY": API_KEY
    }
    response = requests.get(url, headers=headers)
    data = response.json()
    films = data.get('docs', [])
    bot.send_message(message.from_user.id, f'Подборка фильмов в диапозоне бюджета {price}')
    for index in range(10):
        film = films[index]
        name: str = film.get('name', 'Без названия')
        year:int = film.get('year', 'Год выпуска не указан')
        description: str = film.get("description", "Описание отсутствует.")
        rating: int = film.get("rating", {}).get("kp", "Нет рейтинга")

        with open('user_history_request.txt', 'a', encoding='utf-8') as f:
            f.write(f'Название: {name} \nГод выпуска : {year} \nОписание : {description} \nРейтинг : {rating}')


        with open('film_names.txt', 'a', encoding='utf-8') as file:
            if name:
                file.write(f'{index}) Название фильма: {name}' + '\n')

    with open('film_names.txt', 'r', encoding='utf-8') as file:
        bot.send_message(message.from_user.id, file.read())

    with open('film_names.txt', 'w') as file:
        pass


def big_budget(message: Message) -> None:
    price: str = message.text
    url: str = f"https://api.kinopoisk.dev/v1.4/movie?page=1&limit=10&budget.value={price}"
    headers: Dict = {
        "accept": "application/json",
        "X-API-KEY": API_KEY
    }
    response = requests.get(url, headers=headers)
    data = response.json()
    films = data.get('docs', [])
    bot.send_message(message.from_user.id, f'Подборка фильмов в диапозоне бюджета {price}')
    for index in range(10):
        film = films[index]
        name: str = film.get('name', 'Без названия')
        year: int = film.get('year', 'Год выпуска не указан')
        description: str = film.get("description", "Описание отсутствует.")
        rating: int = film.get("rating", {}).get("kp", "Нет рейтинга")
        with open('user_history_request.txt', 'a', encoding='utf-8') as f:
            f.write(f'Название: {name} \nГод выпуска : {year} \nОписание : {description} \nРейтинг : {rating}')


        with open('film_names.txt', 'a', encoding='utf-8') as file:
            if name:
                file.write(f'{index}) Название фильма: {name}' + '\n')

    with open('film_names.txt', 'r', encoding='utf-8') as file:
        bot.send_message(message.from_user.id, file.read())

    with open('film_names.txt', 'w') as file:
        pass


def name_film(message: Message) -> None:
    names: str = message.text
    headers: Dict = {"X-API-KEY": API_KEY}
    params: Dict = {"query": names, "limit": 1}
    response = requests.get('https://api.kinopoisk.dev/v1.4/movie/search', headers=headers, params=params)
    data = response.json()
    films = data.get("docs", [])
    film = films[0]

    if not films:
        bot.send_message(message.from_user.id, f'Фильм по названию {names} НЕ найден!')

    name: str = film.get("name", "Без названия")
    year: int = film.get("year", "Год неизвестен")
    description: str = film.get("description", "Описание отсутствует.")
    rating: int = film.get("rating", {}).get("kp", "Нет рейтинга")
    bot.send_message(message.from_user.id, f"{name} ({year})\nРейтинг: {rating}\n\nОписание:\n{description}")
    bot.send_message(message.from_user.id, 'Если хотите посмотреть ещё подборки, можете указать комманду в меню.')


    with open('user_history_request.txt', 'a', encoding='utf-8') as file:
        file.write(f'Название :{name} \n Год выпуска: {year} \nОписание: {description} \nРейтинг: {rating}' + '\n')
        lines: int = sum(1 for _ in file)
        if lines < 25:
            with open('user_history_request.txt', 'w') as f:
                pass


if __name__ == "__main__":
    bot.add_custom_filter(StateFilter(bot))
    bot.set_my_commands([BotCommand(*cmd) for cmd in DEFAULT_COMMAND])
    create_model()

bot.infinity_polling()

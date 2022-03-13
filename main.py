# Импортируем необходимые библиотеки.
from telegram.ext import Updater, MessageHandler, Filters
from telegram.ext import CommandHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup
import electronic_diary
from data import db_session
from data.users import User
from weather import get_weather
from config import api_token
import datetime

# Почти в каждой функции есть обработчик ошибки AttributeError, т.к. во время тестов я заметил, что если пользователь
# "лайкает" свое сообщение, там где есть команда, то он ее вызывает.
# Нужные мне переменные

ELECTRONIC_DIARY = None  # использую, чтобы хранить класс дневника
CITY = None
CHAT_ID = None  # будет храниться Id чата
db_session.global_init("db/blogs.db")


# вызывается при отправке команды /start
def start(update, context):
    try:
        global ELECTRONIC_DIARY, CHAT_ID
        ELECTRONIC_DIARY = None
        # добавляю все в БД
        user = User()
        user.phone = update.message.contact  # добавляю номер телефона
        user.chat_id = update.effective_chat.id  # добавляю Id чата
        db_sess = db_session.create_session()
        db_sess.add(user)
        db_sess.commit()
        # создаю клавиатуру
        CHAT_ID = update.effective_chat.id
        reply_keyboard = [['/help']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        update.message.reply_text(
            "Привет меня зовут Воппер. Меня написали, чтобы я помогал школьникам, учащимся в "
            "школах Республики Татарстан. Отправь мне /help, и я покажу на что способен.", reply_markup=markup)
    except AttributeError:
        pass


# вызывается при отправке команды /help
def help(update, context):
    try:
        update.message.reply_text("Мои возможности:\n"
                                  "/log_in - Авторизую тебя на сайте edu.tatar.ru, чтобы потом каждый день в 7 утра "
                                  "отправлять тебе расписание. \n"
                                  "/re_log_in - Сделаю все тоже самое, но с другим логином и паролем\n"
                                  "/num_fours_per_quarter - Отправлю тебе предметы, по которым у тебя средний бал "
                                  "меньше заданного (мой создатель по умолчанию поставил 4.60).\n"
                                  "/set_score - Поменяю бал на ваш из пункта выше.\n"
                                  "/get_lesson - Отправлю тебе уроки на сегодня.\n"
                                  "/set_city <ваш город> - Сохраню твой прекрасный город, чтобы позже каждое утро "
                                  "радовать тебя погодой\n"
                                  "/get_city_weather - Отправлю погоду в твоем городе.")
    except AttributeError:
        pass


# вызывается для смены бала
def set_score(update, context):
    try:
        update.message.reply_text("В следующем сообщении укажите нужный бал, не меньше 2-х и не больше 4.90")
        return 1
    except AttributeError:
        pass


def getting_score(update, context):
    try:
        num = update.message.text
        try:
            # Проверяю корректность числа
            if not 2 <= float(num) <= 4.90:
                raise ValueError
            # Если все нормально, то добавляем в число в БД
            update.message.reply_text(f"Теперь бал равен {num}")
            db_sess = db_session.create_session()
            user_score = db_sess.query(User).filter(User.chat_id == update.effective_chat.id
                                                    ).first()
            user_score.score = float(num)
            db_sess.commit()
            return ConversationHandler.END
        except ValueError:
            update.message.reply_text("К сожалению вы ввели не корректное значение. Отправьте нужный бал в "
                                      "следующем сообщении")
            return 1
    except AttributeError:
        pass


# нужен для перерегистрации
def re_log_in(update, context):
    global ELECTRONIC_DIARY
    try:
        if ELECTRONIC_DIARY:
            ELECTRONIC_DIARY = None
            update.message.reply_text("В следующем сообщении укажите логин от edu.tatar.ru")
            return 1
        else:
            update.message.reply_text("Вы и так не авторизованы.")
    except AttributeError:
        pass


# нужен для регистрации
def log_in(update, context):
    try:
        global ELECTRONIC_DIARY
        if ELECTRONIC_DIARY:
            update.message.reply_text("Вы уже регистрировались ранее. Чтобы сменить аккаунт воспользуйтесь командой"
                                      " /re_log_in")
        else:
            update.message.reply_text("В следующем сообщении укажите логин от edu.tatar.ru")
            return 1
    except AttributeError:
        pass


def login(update, context):
    try:
        update.message.reply_text("В следующем сообщении укажите пароль от edu.tatar.ru")
        context.user_data['login'] = update.message.text
        return 2
    except AttributeError:
        pass


def password(update, context):
    try:
        global ELECTRONIC_DIARY
        update.message.reply_text("Идет проверка правильности логина и пароля...")
        update.message.reply_text("Ждем ответа сервера...")
        context.user_data['password'] = update.message.text
        elec_diary = electronic_diary.ElectronicDiary(context.user_data["login"],
                                                      context.user_data["password"])
        if elec_diary.password_validation():
            update.message.reply_text("Вы успешно вошли в аккаунт!")
            ELECTRONIC_DIARY = elec_diary
            # Добавляем данные в БД
            db_sess = db_session.create_session()
            user = db_sess.query(User).filter(User.chat_id == update.effective_chat.id
                                              ).first()
            user.login_edu_tatar = context.user_data["login"]
            user.hashed_password_edu_tatar = context.user_data["password"]
            db_sess.commit()
            return ConversationHandler.END
        else:
            update.message.reply_text("Ой-ой, что-то пошло не так, проверьте правильность пароля или логина. "
                                      "В следующем сообщении укажите логин от edu.tatar.ru")
            return 1
    except AttributeError:
        pass


def stop(update, context):
    try:
        update.message.reply_text("Регистрация отменена.")
    except AttributeError:
        pass


# отправляет предметы по которым средний бал ниже указанного
def num_fours_per_quarter(update, context):
    try:
        global ELECTRONIC_DIARY
        if ELECTRONIC_DIARY:
            db_sess = db_session.create_session()
            user = db_sess.query(User).filter(User.chat_id == update.effective_chat.id
                                              ).first()
            ELECTRONIC_DIARY.get_score(user.score)
            text = ELECTRONIC_DIARY.get_num_fours()
            if text:
                update.message.reply_text(text)
            else:
                update.message.reply_text("счастью у вас не предметов ниже данного бала, продолжайте в том же духе.")
        else:
            update.message.reply_text("Вы не авторизовались!!! С авторизацией вам поможет команда /log_in")
    except AttributeError:
        pass


# добавляем город
def set_city(update, context):
    try:
        global CITY
        if context.args:
            message = get_weather(context.args[0])
            if "не найден" in message:
                update.message.reply_text(f"{message}")
            else:
                CITY = context.args[0]
                update.message.reply_text(f"Я сохранил этот город для вас. {message}")
                db_sess = db_session.create_session()
                user = db_sess.query(User).filter(User.chat_id == update.effective_chat.id
                                                  ).first()
                user.city = CITY
                db_sess.commit()
        else:
            update.message.reply_text("Вы не передали город. Чтобы сохранить ваш город напишите /set_city <ваш город>")
    except AttributeError:
        pass


# функция отвечает за рассылку погоды в определенное время
def get_city_weather_r(context):
    try:
        # проверяю вводил ли пользователь город
        if CITY:
            message = get_weather(CITY)
            context.bot.send_message(chat_id=CHAT_ID, text=message)
        else:
            context.bot.send_message(chat_id=CHAT_ID, text="Укажите свой прекрасный город и получайте погоду "
                                                           "ежедневно.")
    except AttributeError:
        pass


def get_city_weather(update, context):
    try:
        # проверяю вводил ли пользователь город
        if CITY:
            message = get_weather(CITY)
            update.message.reply_text(message)
        else:
            update.message.reply_text("Вы не указали свой город, в этом вам поможет функция /set_city")
    except AttributeError:
        pass


def get_lesson(update, context):
    global ELECTRONIC_DIARY
    try:
        if ELECTRONIC_DIARY:
            lessons = ELECTRONIC_DIARY.get_schedule_for_today()
            update.message.reply_text(lessons)
        else:
            update.message.reply_text("Вы не авторизованы.")
    except AttributeError:
        pass


def get_lesson_r(context):
    global ELECTRONIC_DIARY
    try:
        if ELECTRONIC_DIARY:
            lessons = ELECTRONIC_DIARY.get_schedule_for_today()
            context.bot.send_message(chat_id=CHAT_ID, text=lessons)
        else:
            context.bot.send_message(chat_id=CHAT_ID, text="Авторизуйтесь и получайте свое расписание в 7 утра.")
    except AttributeError:
        pass


def text(update, context):
    message = update.message.text.lower()
    if 'привет' == message:
        time = datetime.datetime.now()
        if time.hour < 10:
            update.message.reply_text("Доброе утро✋")
        else:
            update.message.reply_text("Привет✋")
    elif "погода" in message:
        get_city_weather(update, context)
    elif "уроки" in message or "расписание" in message:
        get_lesson(update, context)


# функция отвечает за отправку уроков в определенное время

def main():
    updater = Updater(api_token, use_context=True)
    dp = updater.dispatcher
    # добавляю в обработчик команды
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("set_city", set_city, pass_job_queue=True))
    dp.add_handler(CommandHandler("num_fours_per_quarter", num_fours_per_quarter))
    dp.add_handler(CommandHandler("get_city_weather", get_city_weather))
    dp.add_handler(CommandHandler("get_lesson", get_lesson))
    # создаю сценарии
    log_in_scenario = ConversationHandler(
        entry_points=[CommandHandler('log_in', log_in)],
        states={
            1: [MessageHandler(Filters.text, login, pass_user_data=True)],
            2: [MessageHandler(Filters.text, password, pass_user_data=True)]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )

    re_log_in_scenario = ConversationHandler(
        entry_points=[CommandHandler('re_log_in', re_log_in)],
        states={
            1: [MessageHandler(Filters.text, login, pass_user_data=True)],
            2: [MessageHandler(Filters.text, password, pass_user_data=True)]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )
    set_score_scenario = ConversationHandler(
        entry_points=[CommandHandler('set_score', set_score)],
        states={
            1: [MessageHandler(Filters.text, getting_score, pass_user_data=True)]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )
    # добавляю сценарии
    dp.add_handler(log_in_scenario)
    dp.add_handler(re_log_in_scenario)
    dp.add_handler(set_score_scenario)
    # создаю планировщик
    jq = updater.job_queue
    # добавляю планировщик
    job_weather = jq.run_daily(get_city_weather_r, time=datetime.time(4), days=(0, 1, 2, 3, 4, 5, 6))
    job_lessons = jq.run_daily(get_lesson_r, time=datetime.time(4), days=(0, 1, 2, 3, 4, 5))
    dp.add_handler(MessageHandler(Filters.text, text))
    updater.start_polling()
    updater.idle()


# Запускаем функцию main() в случае запуска скрипта.
if __name__ == '__main__':
    main()


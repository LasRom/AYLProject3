# Импортируем необходимые библиотеки.
import datetime
import os.path

from telegram import ReplyKeyboardMarkup
from telegram.ext import CommandHandler, ConversationHandler
from telegram.ext import Updater, MessageHandler, Filters

import electronic_diary
from config import api_token
from data import db_session
from data.users import User
from news import get_news
from weather import get_weather
from Backup import send_email, make_reserve_arc

# Почти в каждой функции есть обработчик ошибки AttributeError, т.к. во время тестов я заметил, что если пользователь
# "лайкает" свое сообщение(там где есть команда), то он ее вызывает.

db_session.global_init("db/blogs.db")
# Сообщения, которые я отправляю в случае ошибок связанные с базой данных и файлом с задачами.
ERROR_DB = "Я не могу найти тебя в своей базе данных. Скорее всего мой создатель перезагрузил меня. Пропиши /start," \
           " чтобы снова появиться в базе."
ERROR_FILE = "Я не могу найти твои задачи. Скорее всего мой создатель перезагрузил меня. Напиши /start"


def backup(context):
    make_reserve_arc('Jobs/', 'Jobs/Jobs.zip')
    # Использование функции send_email()
    addr_to = "lastuvkaroman38@gmail.com"  #
    send_email(addr_to, "Backup", str(datetime.datetime.now()), ['db/blogs.db', 'Jobs/Jobs.zip'])


# вызывается при отправке команды /start
def start(update, context):
    try:
        # добавляю все в БД
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.chat_id == update.effective_chat.id
                                          ).first()
        # создаю клавиатуру
        reply_keyboard = [['/help', '/donat', '/news'],
                          ["/log_in", "/re_log_in"],
                          ["/set_score", "/get_lesson"],
                          ["/num_fours_per_quarter"],
                          ["/set_city", "/get_city_weather"],
                          ["/add_job", "/get_job", "/del_job"]]
        markup = ReplyKeyboardMarkup(reply_keyboard)
        if user:
            update.message.reply_text("Привет, я тебя помню. Кратко расскажу о себе. Меня написали, "
                                      "чтобы я помогал школьникам, учащимся в школах Республики Татарстан. Отправь мне "
                                      "/help, и я покажу на что способен.", reply_markup=markup)
            result_jobs = "Твои задачи на сегодня:\n"
            # Подключаюсь к задачам пользователя, лежащие в директории Jobs
            file_jobs = open(f"Jobs/{update.effective_chat.id}.txt")
            for number, line in enumerate(file_jobs):
                result_jobs += f"{number + 1}:  {line}\n"
            if result_jobs == "Твои задачи на сегодня:\n":
                update.message.reply_text("Пока что у тебя нет задач, но ты можешь добавить их, используя "
                                          "команду /add_job", reply_markup=markup)
            else:
                update.message.reply_text(result_jobs, reply_markup=markup)
            # Закрываю файл
            file_jobs.close()
        else:
            # создаю файл для задач и сразу его закрываю
            f = open(f"Jobs/{update.effective_chat.id}.txt", "w+")
            f.close()
            user = User()
            user.phone = update.message.contact  # добавляю номер телефона
            user.chat_id = update.effective_chat.id  # добавляю Id чата
            db_sess.add(user)
            update.message.reply_text(
                "Привет меня зовут Воппер. Меня написали, чтобы я помогал школьникам, учащимся в "
                "школах Республики Татарстан. Отправь мне /help, и я покажу на что способен.", reply_markup=markup)
        # Закрываю БД
        db_sess.commit()
    except AttributeError:
        pass
    except BaseException as e:
        update.message.reply_text(f"Ой, что-то пошло не так. Ошибка - {e}")


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
                                  "/set_city <ваш город> - Сохраню твой город, чтобы позже каждое утро "
                                  "радовать тебя погодой\n"
                                  "/get_city_weather - Отправлю погоду в твоем городе.\n"
                                  "/get_job - Распечатаю все твои задачи.\n"
                                  "/add_job - Добавлю задачу к списку твоих дел.\n"
                                  "/del_job <номер задачи> - Удалю задачу под указанным номером.\n"
                                  "/donat - Отправлю тебе данные своего создателя, "
                                  "если ты захочешь поддержать его материально\n"
                                  "/news - Расскажу что происходит в мире.")
    except AttributeError:
        pass
    except BaseException as e:
        update.message.reply_text(f"Ой, что-то пошло не так. Ошибка - {e}")


# вызывается для смены бала
def set_score(update, context):
    try:
        update.message.reply_text("В следующем сообщении укажите нужный бал, не меньше 2-х и не больше 4.90")
        return 1
    except AttributeError:
        pass
    except BaseException as e:
        update.message.reply_text(f"Ой, что-то пошло не так. Ошибка - {e}")


def getting_score(update, context):
    try:
        # Принимаю число
        num = update.message.text
        try:
            # Проверяю корректность числа
            if not 2 <= float(num) <= 4.90:
                raise ValueError
            # Если все нормально, то добавляю в число в БД
            db_sess = db_session.create_session()
            user_score = db_sess.query(User).filter(User.chat_id == update.effective_chat.id
                                                    ).first()
            if user_score:
                user_score.score = float(num)  # Добавляю бал в БД
                update.message.reply_text(f"Теперь бал равен {num}")
            else:
                update.message.reply_text(ERROR_DB)  # Вывожу текст с ошибкой
            db_sess.commit()
            return ConversationHandler.END
        except ValueError:
            update.message.reply_text("К сожалению вы ввели не корректное значение. Отправьте нужный бал в "
                                      "следующем сообщении")
            return 1
    except AttributeError:
        pass
    except BaseException as e:
        update.message.reply_text(f"Ой, что-то пошло не так. Ошибка - {e}")


# нужен для перерегистрации
def re_log_in(update, context):
    try:
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.chat_id == update.effective_chat.id
                                          ).first()
        if user:
            update.message.reply_text("В следующем сообщении укажите логин от edu.tatar.ru")
            return 1
        else:
            update.message.reply_text("Вы и так не авторизованы.")
        db_sess.commit()
    except AttributeError:
        pass
    except BaseException as e:
        update.message.reply_text(f"Ой, что-то пошло не так. Ошибка - {e}")


# нужен для регистрации
def log_in(update, context):
    try:
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.chat_id == update.effective_chat.id
                                          ).first()
        if user:
            if user.login_edu_tatar:
                update.message.reply_text("Вы уже регистрировались ранее. Чтобы сменить аккаунт воспользуйтесь командой"
                                          " /re_log_in")
            else:
                update.message.reply_text("В следующем сообщении укажите логин от edu.tatar.ru")
                return 1
        else:
            update.message.reply_text(ERROR_DB)
        db_sess.commit()
    except AttributeError:
        pass
    except BaseException as e:
        update.message.reply_text(f"Ой, что-то пошло не так. Ошибка - {e}")


def login(update, context):
    try:
        update.message.reply_text("В следующем сообщении укажите пароль от edu.tatar.ru")
        context.user_data['login'] = update.message.text
        return 2
    except AttributeError:
        pass
    except BaseException as e:
        update.message.reply_text(f"Ой, что-то пошло не так. Ошибка - {e}")


def password(update, context):
    try:
        update.message.reply_text("Идет проверка правильности логина и пароля...")
        update.message.reply_text("Ждем ответа сервера...")
        context.user_data['password'] = update.message.text
        user_login = context.user_data["login"]
        user_password = context.user_data["password"]
        pass_valid_check = electronic_diary.password_validation(user_login, user_password)
        if pass_valid_check:
            # Добавляем данные в БД
            db_sess = db_session.create_session()
            user = db_sess.query(User).filter(User.chat_id == update.effective_chat.id
                                              ).first()
            if user:
                update.message.reply_text("Вы успешно вошли в аккаунт!")
                user.login_edu_tatar = user_login
                user.hashed_password_edu_tatar = user_password
            else:
                update.message.reply_text(ERROR_DB)
            db_sess.commit()
            return ConversationHandler.END
        else:
            update.message.reply_text("Ой-ой, что-то пошло не так, проверьте правильность пароля или логина. ")
            return ConversationHandler.END
    except AttributeError:
        pass
    except BaseException as e:
        update.message.reply_text(f"Ой, что-то пошло не так. Ошибка - {e}")


def stop(update, context):
    try:
        update.message.reply_text("Регистрация отменена.")
    except AttributeError:
        pass
    except BaseException as e:
        update.message.reply_text(f"Ой, что-то пошло не так. Ошибка - {e}")


# отправляет предметы по которым средний бал ниже указанного
def num_fours_per_quarter(update, context):
    try:
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.chat_id == update.effective_chat.id
                                          ).first()
        if user:
            if user.login_edu_tatar:
                message = electronic_diary.get_num_fours(user.login_edu_tatar,
                                                         user.hashed_password_edu_tatar, user.score)
                db_sess.commit()
                if message:
                    update.message.reply_text(message)
                else:
                    update.message.reply_text(f"Я не нашел предметы ниже балла {user.score}. "
                                              f"Чтобы поменять бал напишите "
                                              f"/set_score <Нужный бал>")
            else:
                update.message.reply_text("Вы не авторизовались!!! С авторизацией вам поможет команда /log_in")
        else:
            update.message.reply_text(ERROR_DB)
    except AttributeError:
        pass
    except BaseException as e:
        update.message.reply_text(f"Ой, что-то пошло не так. Ошибка - {e}")


# добавляем город
def set_city(update, context):
    try:
        if context.args:
            # Получаю сообщение с погодой
            message = get_weather(context.args[0])
            if "не найден" in message:
                update.message.reply_text(f"{message}")
            else:
                city = context.args[0]
                db_sess = db_session.create_session()
                user = db_sess.query(User).filter(User.chat_id == update.effective_chat.id
                                                  ).first()
                if user:
                    user.city = city  # добавляю в БД город
                    update.message.reply_text(f"Я сохранил этот город для вас. {message}")
                else:
                    update.message.reply_text(ERROR_DB)
                db_sess.commit()
        else:
            update.message.reply_text("Вы не передали город. Чтобы добавить ваш город напишите /set_city <ваш город>")
    except AttributeError:
        pass
    except BaseException as e:
        update.message.reply_text(f"Ой, что-то пошло не так. Ошибка - {e}")


# функция отвечает за рассылку погоды в определенное время
def get_city_weather_r(context):
    try:
        # проверяю ввёл ли пользователь город
        db_sess = db_session.create_session()
        for user in db_sess.query(User).all():
            print(user.chat_id, user.city)
            # Смотрю вводил ли пользователь свой город, если да то отправляю ему погоду
            if user.city:
                message = get_weather(user.city)
                context.bot.send_message(chat_id=user.chat_id, text=message)
            else:
                context.bot.send_message(chat_id=user.chat_id, text="Скажи мне свой город "
                                                                    "и я буду радовать тебя погодой в 7 утра")
        db_sess.commit()
    except BaseException as e:
        print(e)


def get_city_weather(update, context):
    try:
        # проверяю вводил ли пользователь город
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.chat_id == update.effective_chat.id
                                          ).first()
        if user:
            city = user.city
            if city:
                message = get_weather(city)
                update.message.reply_text(message)
            else:
                update.message.reply_text("Вы не указали свой город, в этом вам поможет функция /set_city")
        else:
            update.message.reply_text(ERROR_DB)
        db_sess.commit()
    except AttributeError:
        pass
    except BaseException as e:
        update.message.reply_text(f"Ой, что-то пошло не так. Ошибка - {e}")


def get_lesson(update, context):
    try:
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.chat_id == update.effective_chat.id
                                          ).first()
        if user:
            if user.login_edu_tatar:
                lessons = electronic_diary.get_schedule_for_today(user.login_edu_tatar, user.hashed_password_edu_tatar)
                update.message.reply_text(lessons)
            else:
                update.message.reply_text("Вы не авторизовались!!! С авторизацией вам поможет команда /log_in")
        else:
            update.message.reply_text(ERROR_DB)
    except AttributeError:
        pass
    except BaseException as e:
        update.message.reply_text(f"Ой, что-то пошло не так. Ошибка - {e}")


def get_lesson_r(context):
    try:
        db_sess = db_session.create_session()
        for user in db_sess.query(User).all():
            if user.login_edu_tatar:
                message = electronic_diary.get_schedule_for_today(user.login_edu_tatar, user.hashed_password_edu_tatar)
                context.bot.send_message(chat_id=user.chat_id, text=message)
            else:
                context.bot.send_message(chat_id=user.chat_id, text="Авторизуйтесь и получайте свое "
                                                                    "расписание в 7 утра.")
        db_sess.commit()
    except BaseException as e:
        print(e)


def add_job(update, context):
    try:
        update.message.reply_text("В следующем сообщении отправте задачу")
        return 1
    except AttributeError:
        pass
    except BaseException as e:
        update.message.reply_text(f"Ой, что-то пошло не так. Ошибка - {e}")


def write_job(update, context):
    try:
        job = update.message.text
        chat_id = update.effective_chat.id
        file_jobs = open(f"Jobs/{chat_id}.txt", "a+")
        file_jobs.write(job + "\n")
        file_jobs.close()
        update.message.reply_text("Я добавил твою задачу")
        return ConversationHandler.END
    except AttributeError:
        pass
    except BaseException as e:
        update.message.reply_text(f"Ой, что-то пошло не так. Ошибка - {e}")
        return ConversationHandler.END


def get_job(update, context):
    try:
        chat_id = update.effective_chat.id
        if os.path.exists(f'Jobs/{chat_id}.txt'):
            result_jobs = "Твои задачи на сегодня:\n"
            file_jobs = open(f"Jobs/{chat_id}.txt")
            for number, line in enumerate(file_jobs):
                result_jobs += f"{number + 1}:  {line}\n"
            if result_jobs == "Твои задачи на сегодня:\n":
                print(result_jobs)
                update.message.reply_text("Пока что у тебя нет задач, но ты можешь добавить их, используя "
                                          "команду /add_job")
            else:
                update.message.reply_text(result_jobs)
            file_jobs.close()
        else:
            update.message.reply_text(ERROR_FILE)
    except AttributeError:
        pass
    except BaseException as e:
        update.message.reply_text(f"Ой, что-то пошло не так. Ошибка - {e}")
        return ConversationHandler.END


def del_job(update, context):
    try:
        chat_id = update.effective_chat.id
        if os.path.exists(f'Jobs/{chat_id}.txt'):
            if context.args:
                numder_job = context.args[0]
                if not numder_job.isdigit():
                    update.message.reply_text("Ты отправил не число не число")
                else:
                    file_text_jobs = open(f"Jobs/{chat_id}.txt").read().split("\n")
                    flag_number = False
                    result_text = []
                    for number, line in enumerate(file_text_jobs):
                        if number + 1 == int(numder_job):
                            flag_number = True
                        else:
                            result_text.append(line)
                    file_jobs = open(f"Jobs/{chat_id}.txt", "w")
                    if not flag_number:
                        update.message.reply_text("Я не нашел задачу с таким номером")
                    else:
                        file_jobs.write('\n'.join(result_text))
                        update.message.reply_text("Я удалил эту задачу")
                    file_jobs.close()
            else:
                update.message.reply_text("Ты не сказал мне, какую задачу удалить. /del_job <номер задачи>")
        else:
            update.message.reply_text(ERROR_FILE)
    except AttributeError:
        pass
    except BaseException as e:
        update.message.reply_text(f"Ой, что-то пошло не так. Ошибка - {e}")
        return ConversationHandler.END


# функция отвечает за отправку уроков в определенное время
def donat(update, conext):
    try:
        update.message.reply_text("Если ты и правда хочешь отблагодарить моего создателя то держи данные:\n"
                                  "Tinkoff - https://www.tinkoff.ru/rm/lastuvka.roman1/TL4Si85540")
    except AttributeError:
        pass
    except BaseException as e:
        update.message.reply_text(f"Ой, что-то пошло не так. Ошибка - {e}")


def news(update, context):
    try:
        sp_news = get_news()
        if sp_news:
            for el in sp_news:
                update.message.reply_text(f"{el[0]} - {el[1]}")
            update.message.reply_text("Вся информация взята с сайта ria.ru")
        else:
            update.message.reply_text(f"Что-то пошло не так. Скорее всего сервис, с которого я брал информацию, "
                                      f"временно не работает.")
    except AttributeError:
        pass
    except BaseException as e:
        update.message.reply_text(f"Ой, что-то пошло не так. Ошибка - {e}")


def text(update, context):
    try:
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
        elif "новости" in message:
            news(update, message)
        elif "задач" in message:
            get_job(update, context)
    except BaseException as e:
        update.message.reply_text(f"Ой, что-то пошло не так. Ошибка - {e}")


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
    dp.add_handler(CommandHandler("get_job", get_job))
    dp.add_handler(CommandHandler("del_job", del_job, pass_job_queue=True))
    dp.add_handler(CommandHandler("donat", donat))
    dp.add_handler(CommandHandler("news", news))
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
    add_job_scenario = ConversationHandler(
        entry_points=[CommandHandler('add_job', add_job)],
        states={
            1: [MessageHandler(Filters.text, write_job, pass_user_data=True)]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )
    # добавляю сценарии
    dp.add_handler(log_in_scenario)
    dp.add_handler(re_log_in_scenario)
    dp.add_handler(set_score_scenario)
    dp.add_handler(add_job_scenario)
    # создаю планировщик
    jq = updater.job_queue
    # добавляю планы
    job_weather = jq.run_daily(get_city_weather_r, time=datetime.time(4), days=(0, 1, 2, 3, 4, 5, 6))
    job_lessons = jq.run_daily(get_lesson_r, time=datetime.time(4), days=(0, 1, 2, 3, 4, 5, 6))
    job_backup = jq.run_repeating(backup, 300)
    # Обрабатываю остальной текст
    dp.add_handler(MessageHandler(Filters.text, text))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

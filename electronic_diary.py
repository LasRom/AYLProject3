import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import datetime
from config import login_proxy, password_proxy

ua = UserAgent()
random_ua = ua.random
# Заголовки к запросу
head = {
    'Referer': 'https://edu.tatar.ru/logon',
    'User-Agent': random_ua
}
# Прокси нужен для того, что сайт edu.tatar принимает запросы только из РФ, поскольку сервер Западный,
# то и запросы блокируются(В данном случае использован русский прокси формата https c IPv-4).
proxies = {
    "https": f"http://{login_proxy}:{password_proxy}@194.242.127.92:8000"
}


# В данной функции делаю запрос на сайт и возвращаю cookie
def registration(login, password):
    url_logon = 'https://edu.tatar.ru/logon'
    params = {
        'main_login2': login,
        'main_password2': password
    }
    response_logon = requests.post(url_logon, params=params, headers=head, proxies=proxies)
    cookie = response_logon.cookies
    return cookie


# Отправляю уроки на сегодня
def get_schedule_for_today(login, password):
    cookie = registration(login, password)  # получаю cookie
    url = "https://edu.tatar.ru/user/diary/week"  # ссылка
    response_week = requests.get(url, cookies=cookie, proxies=proxies)  # делаю запрос, он не точный
    bs = BeautifulSoup(response_week.text, "html.parser")
    url_today = bs.find_all("a", class_="g-button")[0]["href"]
    weekday = datetime.datetime.weekday(datetime.datetime.now())  # узнаю какой сегодня день
    if weekday != 6:
        for _ in range(weekday % 3):
            response_fake_today = requests.get(url_today, cookies=cookie, proxies=proxies)
            bs_correct = BeautifulSoup(response_fake_today.text, "html.parser")
            url_next_day = bs_correct.find_all("span", class_="nextd")
            url_today = url_next_day[0].find_all("a")[0]["href"]
        response_real_today = requests.get(url_today, cookies=cookie, proxies=proxies)
        bs_today = BeautifulSoup(response_real_today.text, "html.parser")
        items = bs_today.find_all("td", style="vertical-align: middle;")

        sp_items = []
        for i in range(1, len(items), 4):
            sp_items.append(items[i].text)
        if sp_items:
            return "Твои уроки на сегодня:\n" + "\n".join(sp_items)
        else:
            return "Сегодня праздничный день, хорошего отдыха!!!"
    else:
        return "Сегодня выходной день, хорошего отдыха!!!"


def get_num_fours(login, password, score):
    try:
        cookie = registration(login, password)
        url_term = 'https://edu.tatar.ru/user/diary/term'
        response_2 = requests.get(url_term, cookies=cookie, proxies=proxies)

        bs = BeautifulSoup(response_2.text, "html.parser")
        tables = bs.find_all("table", {'class': 'table term-marks'})
        dictionary = {}
        for table in tables:
            for elem in table.find('tbody').find_all('tr')[:-1]:
                status = elem.find_all('td')
                # Берем промежуток от 1 до -3 т.к. там лежит не нужная информация
                for element in status[1:-3]:
                    if status[0].text in dictionary:
                        if element.text:
                            dictionary[status[0].text].append(int(element.text))
                    else:
                        if element.text:
                            dictionary[status[0].text] = [int(element.text)]
        dict_result = {}
        for key, value in dictionary.items():
            average_score = sum(value) / len(value)
            if average_score < score:
                sp = value.copy()
                while sum(sp) / len(sp) < score:
                    sp.append(5)
                dict_result[key] = [len(sp) - len(value), average_score]
        result_text = ''
        check = 0
        for key, value in dict_result.items():
            check += 1
            result_text += f"{key} \nНужное количество пятерок: {value[0]} \nТекущий балл: {round(value[1], 2)} \n\n"
        return result_text + f"\nКоличество предметов {check}"
    except BaseException as e:
        print(e)
        return "Что-то пошло не так. Попробуйте еще раз авторизоваться."


# проверяю верный ли логин и пароль ввел пользователь
def password_validation(login, password):
    url_logon = 'https://edu.tatar.ru/logon'
    params = {
        'main_login2': login,
        'main_password2': password
    }
    response_logon = requests.post(url_logon, params=params, headers=head, proxies=proxies)
    if response_logon.text[17] == "h" or not response_logon:
        return False
    else:
        return True

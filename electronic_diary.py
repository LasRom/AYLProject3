import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import datetime

ua = UserAgent()
random_ua = ua.random
head = {
    'Referer': 'https://edu.tatar.ru/logon',
    'User-Agent': random_ua
}



def registration(login, password):
    url_logon = 'https://edu.tatar.ru/logon'
    params = {
        'main_login2': login,
        'main_password2': password
    }
    response_logon = requests.post(url_logon, params=params, headers=head)
    cookie = response_logon.cookies
    return cookie


def get_schedule_for_today(login, password):
    cookie = registration(login, password)
    url = "https://edu.tatar.ru/user/diary/week"
    response_week = requests.get(url, cookies=cookie)
    bs = BeautifulSoup(response_week.text, "html.parser")
    url_today = bs.find_all("a", class_="g-button")[0]["href"]
    weekday = datetime.datetime.weekday(datetime.datetime.now())
    if weekday != 6:
        for _ in range(weekday % 3):
            response_fake_today = requests.get(url_today, cookies=cookie)
            bs_correct = BeautifulSoup(response_fake_today.text, "html.parser")
            url_next_day = bs_correct.find_all("span", class_="nextd")
            url_today = url_next_day[0].find_all("a")[0]["href"]
        response_real_today = requests.get(url_today, cookies=cookie)
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
        response_2 = requests.get(url_term, cookies=cookie)

        bs = BeautifulSoup(response_2.text, "html.parser")
        tables = bs.find_all("table", {'class': 'table term-marks'})

        dictionary = {}
        for table in tables:
            for elem in table.find('tbody').find_all('tr')[:-1]:
                status = elem.find_all('td')
                for element in status[1:-3]:
                    if status[0].text in dictionary:
                        try:
                            dictionary[status[0].text].append(int(element.text))
                        except BaseException as e:
                            continue
                    else:
                        try:
                            dictionary[status[0].text] = [int(element.text)]
                        except BaseException as e:
                            continue
        dict_result = {}
        for key, value in dictionary.items():
            average_score = sum(value) / len(value)
            if average_score < score:
                sp = value.copy()
                while sum(sp) / len(sp) < score:
                    sp.append(5)
                dict_result[key] = [len(sp) - len(value), average_score]
        result_text = ''
        schet = 0
        for key, value in dict_result.items():
            schet += 1
            result_text += f"{key} \nНужное количество пятерок: {value[0]} \nТекущий балл: {round(value[1], 2)} \n\n"
        return result_text + f"\nКоличество предметов {schet}"
    except BaseException as e:
        return "Что-то пошло не так. Попробуйте еще раз авторизоваться."


def password_validation(login, password):
    url_logon = 'https://edu.tatar.ru/logon'
    params = {
        'main_login2': login,
        'main_password2': password
    }
    response_logon = requests.post(url_logon, params=params, headers=head)
    if response_logon.text[17] == "h" or not response_logon:
        return False
    else:
        return True


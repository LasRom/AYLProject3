import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from config import login_proxy, password_proxy

ua = UserAgent()
random_ua = ua.random
head = {
    'User-Agent': random_ua
}
proxies = {
    "https": f"http://{login_proxy}:{password_proxy}@194.242.127.92:8000"
}


# Собираю новости с ria.ru под заголовком "главное"
def get_news():
    try:
        response = requests.get(url="https://ria.ru/", headers=head, proxies=proxies)
        bs = BeautifulSoup(response.text, "html.parser")
        raw_sp_news = bs.find_all("div", class_="cell-list__list")[0].find_all("div", class_="cell-list"
                                                                                             "__item m-no-image")
        end_sp_news = []
        for elem in raw_sp_news:
            news = elem.find_all("span", class_="share")
            end_sp_news.append([news[0]["data-title"], news[0]["data-url"]])
        return end_sp_news
    except BaseException as e:
        print(e)
        return False

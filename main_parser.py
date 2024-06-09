# Импортируем необходимые библиотеки
from bs4 import BeautifulSoup
import requests
import sqlite3
from concurrent.futures import ThreadPoolExecutor

# Константа с URL-адресом сайта
SITE_URL = 'https://lenta.ru'

# Заголовки для запросов
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/102.0.0.0 Safari/537.36'
}

# Функция для создания таблицы в базе данных SQLite
def create_table(conn):
    """
    Функция для создания таблицы в базе данных SQLite

    :param conn: подключение к базе данных
    """
    try:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS articles 
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                          title TEXT, 
                          category TEXT, 
                          create_date TEXT, 
                          body TEXT)''')
        conn.commit()
    except sqlite3.Error as e:
        print("Ошибка при создании таблицы:", e)

# Функция для добавления записи в базу данных SQLite
def insert_article(conn, title, category, create_date, body):
    """
    Функция для добавления записи в базу данных SQLite

    :param conn: подключение к базе данных
    :param title: заголовок новости
    :param category: категория новости
    :param create_date: дата создания новости
    :param body: текст новости
    """
    try:
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO articles (title, category, create_date, body) VALUES (?, ?, ?, ?)''', (title, category, create_date, "\n".join(body)))
        conn.commit()
    except sqlite3.Error as e:
        print("Ошибка при добавлении записи:", e)

# Функция для получения всех новостей на главной странице
def get_all_page_urls(site_url):
    """
    Функция для получения всех новостей на главной странице

    :param site_url: URL-адрес сайта
    :return: список URL-адресов новостей
    """
    response = requests.get(site_url, headers=headers)
    if response.ok:
        soup = BeautifulSoup(response.text, 'html.parser')
        urls_topnews = soup.find_all(class_='card-mini _topnews')
        urls_partners = soup.find_all(class_='card-big _slider _partners _news')
        urls_longgrid = soup.find_all(class_='card-mini _longgrid')
        urls_compact = soup.find_all(class_='card-mini _compact')
        total_urls = urls_topnews + urls_partners + urls_longgrid + urls_compact
        return [SITE_URL + item.get('href') for item in total_urls]
    else:
        print('Ошибка при запросе:', response.status_code)
        return []

# Функция для получения содержания статьи
def get_article_content(article_url):
    """
    Функция для получения содержания статьи

    :param article_url: URL-адрес статьи
    :return: заголовок, категория, дата создания и текст статьи
    """
    response = requests.get(article_url, headers=headers)
    if response.ok:
        soup = BeautifulSoup(response.text, 'html.parser')

        title = soup.find('h1').text if soup.find('h1') else 'None'
        body = [p.text for p in soup.find('body').find_all('p')]
        category_tag = soup.find('a', class_='topic-header__rubric')
        category = category_tag.text if category_tag else 'None'
        date_tag = soup.find(class_='topic-header__time')
        create_date = str(date_tag.contents) if date_tag else 'None'
        return title, category, create_date, body
    else:
        print('Ошибка при запросе:', response.status_code)
        return None, None, None, None

# Основная функция для обработки статей
def process_articles(title, category, create_date, body):
    """
    Основная функция для обработки статей

    :param title: заголовок новости
    :param category: категория новости
    :param create_date: дата создания новости
    :param body: текст новости
    """
    conn = sqlite3.connect('articles.db')

# Создаем соединение с базой данных в каждом потоке
    create_table(conn)
    insert_article(conn, title, category, create_date, body)

    conn.close()

def main():
    page_urls = get_all_page_urls(SITE_URL)  # Получаем страницы сайта
    print(page_urls)
    for article_url in page_urls:
        title, category, create_date, body = get_article_content(article_url)
        if title and category and create_date and body:
            #print(title)
            #print(category)
            #print(create_date)
            process_articles(title, category, create_date, body)

if __name__ == "__main__":
    main()
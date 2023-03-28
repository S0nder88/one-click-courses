import sqlite3

from aiogram import types


class UserDB:
    def __init__(self, swdatabase_file):
        self.connection = sqlite3.connect(swdatabase_file)
        self.cursor = self.connection.cursor()

    def user_exist(self, user_id):
        """Проверяем, есть ли юзер в базе"""
        with self.connection:
            result = self.cursor.execute("SELECT `id` FROM `users` WHERE `user_id` = ?", (user_id,))
            return bool(len(result.fetchall()))

    def add_user(self, user_id):
        """Добавляем юзера"""
        with self.connection:
            result = self.cursor.execute("INSERT INTO `users` (`user_id`) VALUES (?)", (user_id,))
            self.connection.commit()

    def get_user_count(self):
        with self.connection:
            result = self.cursor.execute("SELECT COUNT(*) FROM `users`")
            return result.fetchone()[0]

    def get_all_users(self):
        with self.connection:
            result = self.cursor.execute("SELECT `user_id` FROM `users`")
            user_ids = [row[0] for row in result.fetchall()]

            # Create User objects for each user ID
            users = []
            for user_id in user_ids:
                user = types.User(id=user_id)
                users.append(user)

            return users


class CourseDB:
    def __init__(self, swdatabase_file):
        self.connection = sqlite3.connect(swdatabase_file)
        self.cursor = self.connection.cursor()

    def add_link(self, link, title, download_link):
        with self.connection:
            result = self.cursor.execute("INSERT INTO `course` (`link`, `title`, `download_link`) VALUES (?, ?, ?)", (link, title, download_link))
            self.connection.commit()

    def get_course_count(self):
        with self.connection:
            result = self.cursor.execute("SELECT COUNT(*) FROM `course`")
            return result.fetchone()[0]

    def get_url(self, course_url):
        with self.connection:
            result = self.cursor.execute("SELECT `title`, `download_link` FROM `course` WHERE link = ?", (course_url,))
            return result.fetchone()



class RequestDB:
    def __init__(self, swdatabase_file):
        self.connection = sqlite3.connect(swdatabase_file)
        self.cursor = self.connection.cursor()

    def add_request(self, user_id):
        """Добавляем запрос"""
        with self.connection:
            result = self.cursor.execute("INSERT INTO `requests` (`request_date`, `request_time`, `user_id`) VALUES (date('now'), time('now'), ?)", (user_id,))
            self.connection.commit()

    def get_request_count_today(self):
        """Получаем кол-во запросов за сегодня"""
        with self.connection:
            result = self.cursor.execute("SELECT COUNT(*) FROM `requests` WHERE `request_date` = date('now')")
            return result.fetchone()[0]

    def get_request_count_total(self):
        """Получаем кол-во запросов за всё время"""
        with self.connection:
            result = self.cursor.execute("SELECT COUNT(*) FROM `requests`")
            return result.fetchone()[0]

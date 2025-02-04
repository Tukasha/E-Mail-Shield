import random 
import string
import time
import os
import json
import requests
import pyperclip

class BaseMail:
    """
    Базовый класс для работы с почтой.

    Этот класс предоставляет основные методы, такие как создание, проверка и удаление почтовых ящиков.
    Но эти методы должны быть переопределены в подклассе

    Attributes:
        api (str): URL API почтового сервиса.
        mail (str): Адрес электронной почты.
        domains (list): Список доменов почтового сервиса.

    Methods:
        get_domains(): Возвращает список доменов почтового сервиса.
        generate_username(): Генерирует случайное имя пользователя.
        create_mail(): Создает новый почтовый ящик (должен быть переопределен в подклассе).
        check_mail(): Проверяет почтовый ящик (должен быть переопределен в подклассе).
        delete_mail(): Удаляет почтовый ящик (должен быть переопределен в подклассе).
        is_code(some, length=6): Проверяет, является ли строка числовым кодом заданной длины.
        run(): Основной метод для запуска программы.
        run_site(site=''): Запускает сайт в инкогнито-режиме.
    """
    def __init__(self, api_url):
        # Инициализация класса с URL API
        self.api = api_url
        self.mail = ''
        self.domains = self.get_domains()

    def get_domains(self):
        # Метод для получения доменов (должен быть переопределен в подклассе)
        raise NotImplementedError("Этот метод должен быть реализован в подклассе.")

    def generate_username(self):
        # Генерация случайного имени пользователя
        return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(10))

    def create_mail(self):
        # Метод для создания почты (должен быть переопределен в подклассе)
        raise NotImplementedError("Этот метод должен быть реализован в подклассе.")

    def check_mail(self):
        # Метод для проверки почты (должен быть переопределен в подклассе)
        raise NotImplementedError("Этот метод должен быть реализован в подклассе.")

    def delete_mail(self):
        # Метод для удаления почты (должен быть переопределен в подклассе)
        raise NotImplementedError("Этот метод должен быть реализован в подклассе.")

    def is_code(self, some, length=6):
        # Проверка, является ли строка числовым кодом заданной длины
        if len(some) != length:
            return False
        else:
            try:
                int(some)
                return True
            except:
                return False

    def run(self):
        # Основной метод для запуска программы
        try:
            self.create_mail()
            while True:
                self.check_mail()
                time.sleep(5)
        except KeyboardInterrupt or KeyError:
            self.delete_mail()
            print("[X] Программа прервана!")
        except Exception as e:
            print(f"[X] Программа прервана!\n[E] Ошибка: {e}")

    def run_site(self, site=''):
        # Метод для запуска сайта в инкогнито-режиме для браузера Chrome
        os.system(f"start chrome {site} -incognito")


class MailGenerator(BaseMail):
    """Класс для создания и проверки почтовых ящиков с использованием сервиса 1secmail."""
    def __init__(self):
        super().__init__('https://www.1secmail.com/api/v1/')
        self.domains = [i for i in self.domains]
        self.domain = random.choice(self.domains)

    def get_domains(self):
        response = requests.get(f"{self.api}?action=getDomainList")
        try:
            return response.json()
        except:
            return self.get_domains()

    def create_mail(self):
        username = self.generate_username()
        self.mail = f'{username}@{self.domain}'
        print(f'[@] Ваш почтовый адрес: {self.mail}')
        pyperclip.copy(self.mail)

    def check_mail(self):
        req_link = f'{self.api}?action=getMessages&login={self.mail.split("@")[0]}&domain={self.mail.split("@")[1]}'
        r = requests.get(req_link)
        if r.headers['Content-Type'] != "application/json":
            print("[X] Ничего")
            return
        data = r.json()
        length = len(data)

        if length:
            id_list = []

            for i in data:
                id_list.append(i['id'])

            print(f'[+] У вас {length} входящих! Почта обновляется автоматически каждые 5 секунд!')

            for i in id_list:
                read_msg = f'{self.api}?action=readMessage&login={self.mail.split("@")[0]}&domain={self.mail.split("@")[1]}&id={i}'
                r = requests.get(read_msg).json()

                content = r.get('textBody')
                code = "".join([i for i in content.replace("\n", " ").replace(">", " ").replace("<", " ").split() if self.is_code(i)])
                if code:
                    print('[-] Код: ' + (code if code else "не найден"))
                    pyperclip.copy(code)
                else:
                    print("[X] Код не найден")
                
                print('[-] Текст: ' + (content if content else "не найден"))
                self.delete_mail()

    def delete_mail(self):
        url = 'https://www.1secmail.com/mailbox'
        data = {
            'action': 'deleteMailbox',
            'login': self.mail.split('@')[0],
            'domain': self.mail.split('@')[1]
        }
        requests.post(url, data=data)
        print(f'[X] Почтовый адрес {self.mail} - удален!')


class MailSmt(BaseMail):
    """Класс для создания и проверки почтовых ящиков для сервисов, с 2 идентичными api."""
    def __init__(self, api):
        super().__init__(api)
        self.domains = self.get_domains()
        self.domain = random.choice(self.domains)

    def create_mail(self):
        username = self.generate_username()
        address = f"{username}@{self.domain}"
        response = self._make_account_request("accounts", address)
        self.mail = {
            "id": response["id"],
            "address": response["address"],
            "password": response["address"].split("@")[1],
            "auth_headers": {
                "accept": "application/ld+json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._make_account_request('token', address)['token']}"
            }
        }
        print(f'[@] Ваш почтовый адрес: {self.mail["address"]}')
        pyperclip.copy(self.mail["address"])

    def _make_account_request(self, endpoint, address):
        mail = {"address": address, "password": address.split("@")[1]}
        headers = {
            "accept": "application/ld+json",
            "Content-Type": "application/json"
        }
        r = requests.post(f"{self.api}{endpoint}", data=json.dumps(mail), headers=headers)
        if r.status_code not in [200, 201]:
            raise Exception(f"HTTP {r.status_code}")
        return r.json()

    def check_mail(self):
        req_link = f'{self.api}messages?page=1'
        r = requests.get(req_link, headers=self.mail["auth_headers"])
        data = r.json()
        length = len(data["hydra:member"])

        if length:
            id_list = []

            for i in data["hydra:member"]:
                id_list.append(i["id"])

            print(f'[+] У вас {length} входящих! Почта обновляется автоматически каждые 5 секунд!')

            for i in id_list:
                read_msg = f'{self.api}messages/{i}'
                r = requests.get(read_msg, headers=self.mail["auth_headers"]).json()

                content = r["text"]
                code = "".join([i for i in content.replace("\n", " ").replace(">", " ").replace("<", " ").split() if self.is_code(i)])
                if code:
                    print('[-] Код: ' + (code if code else "не найден"))
                    pyperclip.copy(code)
                else:
                    print("[X] Код не найден")
                print('[-] Текст: ' + (content if content else "не найден"))
                self.delete_mail()

    def delete_mail(self):
        url = f'{self.api}accounts/{self.mail["id"]}'
        requests.delete(url, headers=self.mail["auth_headers"])
        print(f'[X] Почтовый адрес {self.mail["address"]} удален!')

    def get_domains(self):
        response = requests.get(f"{self.api}domains")
        try:
            return [domain['domain'] for domain in response.json()["hydra:member"]]
        except:
            return self.get_domains()


class MailTm(MailSmt):
    """Класс для создания и проверки почтовых ящиков для сервиса mail.tm"""
    def __init__(self):
        super().__init__('https://api.mail.tm/')


class MailGw(MailSmt):
    """Класс для создания и проверки почтовых ящиков для сервиса mail.gw"""
    def __init__(self):
        super().__init__('https://api.mail.gw/')


class TempMail(BaseMail):
    """Класс для создания и проверки почтовых ящиков для сервиса temp-mail.io"""
    def __init__(self):
        super().__init__('https://api.internal.temp-mail.io/api/v2/')
        self.id_list = []
        self.deleted = False

    def get_domains(self):
        url = f'{self.api}domains'
        return requests.get(url).json()["domains"]

    def create_mail(self):
        url = f'{self.api}email/new'
        data = {"min_name_length": 10, "max_name_length": 10}
        r = requests.post(url, json=data)
        self.mail = r.json()['email']
        print(f'[@] Ваш почтовый адрес: {self.mail}')
        pyperclip.copy(self.mail)

    def check_mail(self):
        url = f'{self.api}email/{self.mail}/messages'
        messages = requests.get(url).json()
        for message in messages:
            if message['id'] not in self.id_list:
                self.print_mail(message)
                self.id_list.append(message['id'])

    def print_mail(self, mail):
        content = mail['body_text']
        code = "".join([i for i in content.replace("\n", " ").replace(">", " ").replace("<", " ").split() if self.is_code(i)])
        if code:
            print('[-] Код: ' + (code if code else "не найден"))
            pyperclip.copy(code)
        else:
            print("[X] Код не найден")
        print(f"[-] Текст: {content}")
        self.delete_mail()

    def delete_mail(self):
        url = f'{self.api}email/{self.mail}'
        requests.delete(url)
        print(f'[X] Почтовый адрес {self.mail} - удален!')
        self.deleted = True


if __name__ == '__main__':
    # API сервиса, используемого в классе MailGenerator
    classes = [MailTm, MailGw, TempMail]

    # Количество доменов для каждого класса
    domains_count = {class_: len(class_().domains) for class_ in classes}

    # Общее количество доменов
    total_domains = sum(domains_count.values())
    chance = random.randint(0, total_domains - 1)

    # Теперь выберите класс, исходя из случайного числа
    selected_class = None
    current_sum = 0
    for class_, count in domains_count.items():
        current_sum += count
        if chance < current_sum:
            selected_class = class_
            break

    print("[+] Доступные домены:")
    for class_ in classes:
        print(f"{' ' * 3}[{len(class_().domains)}] {class_().api} - {class_().domains}")
    selected_class = MailGw
    selected_class().run_site('https://www.cyberforum.ru/')
    
    selected_class().run()
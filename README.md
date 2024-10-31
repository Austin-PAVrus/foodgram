[![Foodgram Main Workflow](https://github.com/Austin-PAVrus/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/Austin-PAVrus/foodgram/actions/workflows/main.yml)

# Foodrgam
Продуктовый помощник - один из ключевых проектов курса Backend-разработки в Яндекс Практикумке.

Проект представляет сервис публикации рецептов. Пользователи могут создавать свои и просматривать чужие рецепты, добавлять их в избранное и/или корзину, подписываться на авторов. Набор рецептов в корзине позволяет впоследстиве скачать список ингридиентов, необхожимых для приготовления всех добавленных в корзину блюд.

## Технологии
Сервис представляет собой фронтенд виде одностраничного приложения на REACT и REST API-бэкенд на Django + DjangoRestFramework. Для развёртывания проекта используется Docker. Образы можно собрать самостоятельно и загрузить на Dokcer Hub. Для жтого нужно отредактивроать и GitFlow (заменить учётные данные на свои) и использовать отредактированный docker-compose.production из папки imfra.

## Техностек бэкенда
- Python 3.9
- Django
- Django REST Framework
- Djoser


# Развертывание проекта

## Только бэкенд, на локальном компьютере

Для Windows предврительно необходимо утсновить:
- [Bash](https://gitforwindows.org)
- [Python](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads/win)

_Внимание! Команды ниже приведены для ОС Windows. для Mac и Linux вместо команды **python** нужно использовать **python3**_.

### Перейти в директорию бекенда из домашней директории
```
cd backend
```
### Создать виртуальное окружение
```
python -m venv venv
```
### Активировать виртуальное окружене
_Windows
```
source venv/Scripts/activate
```
_Mac и Linux
```
source venv/bin/activate
```
### Установить зависимости из файла requirements.text
```
python -m pip install --update pip
pip install -r requirements.txt
```
### Выполнить миграции
```
python manage.py migrate
```
### Создать суперпользователя
```
python manage.py createsuperuser
```
### Импортировать данные продуктов и ярлыков из json-файлов в базу данных
```
python manage.py fill_ingredients
python manage.py fill_tags
```
### Запустить проект
```
python manage.py runserver
```
___
_После выполнения указанных команд вы сможете успешно пользоваться функционалом бэкенда нашего проекта_ **foodgram**.

### В состянии отладки (включен по умолчаниб) документация по API доступна по адресу http://localhost:8000/api/docs/redoc.html


## Весь проект, на сервере или локальном компьютере c Docker

- Установите на сервере `docker` и `docker-compose`
- Создайте файл `/infra/.env`. Шаблон для заполнения файла нахоится в `/infra/.env.example`
- Выполните команду `docker-compose up -d --buld`
- Контейгер фронтенда после выполнения необходимых операций завершится. Это нормально.
- Создайте суперюзера `docker-compose exec -it backend python manage.py createsuperuser`
- Заполните базу ингредиентами и тэгами `docker-compose exec backend python manage.py fill_db`
- Для добавления ингрижиентов/тегов нужно поспользоваться админкой Django http://localhost/admin
- Рецепты и пользователи добавляются как через сам сайт, так и через админку
- Документация к API находится по адресу: http://localhost/api/docs/

#Автор реализации бэкенда
[Прохоров Александр](https://github.com/Austin-PAVrus)  


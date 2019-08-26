# Описание сервиса
https://yadi.sk/i/dA9umaGbQdMNLw

Реализованы все требования, в том числе опциональные

# Тестирование сервиса
По пути *contest2/APIapp/tests/test_views.py* находятся unittest'ы приложения. Для того, чтобы запустить
тестирование необходимо переключиться на виртуальную среду 
```
$ workon RestService
```
Перейти в корень проекта ***contest2*** (на одном уровне с manage.py) 
```
/home$ cd entrant/contest2
```
и выполнить команду
```
python manage.py test
```
Описание тестов есть в самом файле ***test.py***

Так же сервис был протестирован на обработку нескольких запросов одновременно с помощью терминала и команды
```
curl1 & curl2 & curl3 & curl4 ....
```
# Подготовка виртуальной машины и развертывание приложения:
На сервере используется ОС Ubuntu 18.04.3 LTS

Для работы сервиса REST Api будем использовать связку:

**Django, Django REST Framework, Nginx, Gunicorn, PostgreSQL, Supervisor**


Обновляем базу пакетов:
```
$ sudo apt update
$ sudo apt upgrade
```
Ставим необходимые пакеты
```
$ sudo apt-get install libpq-dev python3-dev wheel python3-venv python-pip python-dev build-essential libpq-dev postgresql postgresql-contrib nginx git virtualenv virtualenvwrapper
$ export LC_ALL="en_US.UTF-8"
$ pip3 install --upgrade pip
```
Настраиваем виртуальную среду
```
$ mkdir ~/.virtualenvs
$ export WORKON_HOME=~/.virtualenvs
```
Переходим в папку с виртуальными средами, создаем новую и активируем её
```
$ cd .virtualenvs
$ python3 -m venv RestService
$ workon RestService
```
Из окружения устанавливаем django, gunicorn и psycopg2
```
(virtual-env-name) $ pip3 install django gunicorn psycopg2
```
В дирректорию пользователя entrant копируем репозиторий
```
(virtual-env-name) $ git clone https://github.com/dmitrii-sim/contest2.git
```
Переходим в папку проекта и даем себе права (на всякий случай)
```
$ cd contest2
$ chmod 755 ./manage.py
```
Устанваливаем все зависимости из файла проекта requirements.txt
```
$ pip3 install -r requirements.txt
```
### Настраиваем ранее установленный PostgreSQL:
Открываем терминал psql
```
$ sudo -u postgres psql
```
Меняем пароль от суперюзера на нужный (к БД будем подключаться как суперюзер)
```
> ALTER USER postgres PASSWORD '*нужный пароль*';
```
Создаем БД restservice, пользователь дефолтный (postgres)
```
> CREATE DATABASE restservice; 
```
Теперь все данные совпадают с нашими settings.py в Django проекте.
Закрываем консоль postresql
```
> \q
```
Проводим миграции, отделяем базовые от приложения:
```
(virtual-env-name) $ python ./manage.py migrate
(virtual-env-name) $ python ./manage.py makemigrations
(virtual-env-name) $ python ./manage.py migrate
```

### Настраиваем Gunicorn + Supervisor
В качестве шлюза будем использовать gunicorn, supervisor для 
**поддержания и автоматического восстановления разорванного соединения** и мониторинга соединения.

Закрываем окружение и устанавливаем supervisor
```
$ deactivate
$ sudo apt-get install supervisor
```
Создаем конфигурационный файл supervisor и добавляем туда gunicorn для мониторинга
```
$ nano /etc/supervisor/conf.d/gunicorn.conf
```
Вставляем следующие строки
```
[program:gunicorn]
command=/home/entrant/.virtualenvs/RestService/bin/gunicorn --workers 3 --bind unix:/home/entrant/contest2/RestService/RestService.sock RestService.wsgi
directory=/home/entrant/contest2
autostart=true
autorestart=true
user=entrant
stderr_logfile=/var/log/gunicorn/gunicorn.out.log
stdout_logfile=/var/log/gunicorn/gunicorn.err.log
group=www-data
environment=LANG=en_US.UTF-8,LC_ALL=en_US.UTF-8

[group:guni]
programs:gunicorn
```
Далее создаем файл *gunicorn.conf* приложения supervisor
```
$ supervisorctl reread 
$ supervisorctl update
```
Проверяем состояние соединения
```
$ supervisorctl status
```

### Настраиваем Nginx
Создаем конфигурационный файл nginx
```
$ sudo nano /etc/nginx/site-available/app
```
Вписываем следующие строки
```
server { 
    listen 8080; 
    server_name 0.0.0.0; 
    location = /favicon.ico { access_log off; log_not_found off; } 
    location /static/ { 
        root /home/entrant/contest2/RestService; 
    } 
    location / { 
        include proxy_params; 
        proxy_pass http://unix:/home/entrant/contest2/RestService/RestService.sock; 
    } 
}
```
Создаем ссылку на текущий файл в *sites-enabled*:
```
$ ln -s /etc/nginx/sites-available/app /etc/nginx/sites-enabled
```
Проверяем соединение Nginx, оно должно прослушивать порт *0.0.0.0:8080*:
```
$ nginx -t
```
Убеждаемся, что все работает и перезагружаемся:
```
$ systemctl restart nginx
```
Вы великолепны!

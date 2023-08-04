# Установка
Руководство подразумевает, что его будет использовать Python разработчик знакомый с технологиями AWS и Docker.
Важно понимать, что версия Windows и прочие локальные настройки могут отличаться что может привести к непредвиденным ошибкам. 
В случае если какая-то команда не срабатывает - гугл в помощь. Личную поддержку оказываю только патронам.



## Локальный компьютер на Windows 10

### Примечание
Бот использует api [comlink](https://github.com/swgoh-utils/swgoh-comlink) и оно не доступно просто по ссылке.  
Чтобы comlink заработал нужно использовать локальный [Docker](https://docs.docker.com/desktop/install/windows-install/) и установить контейнер вручную. 
### Важно!
Docker не работает на версии Windows Enterprise. Если у вас таковая, то вы можете только разве что
переустановить Windows на PRO версию.

1. Скачайте [репозиторий](https://github.com/Shtierlitz/SWGOH-COMLINK-GUILD-CONTROL-BOT-SYSTEM-ru.git) в выбранную вами папку:
```bash
git clone https://github.com/Shtierlitz/SWGOH-COMLINK-GUILD-CONTROL-BOT-SYSTEM-ru.git
```
2. Создайте json файл и настройте .env файлы.
3. Скачайте [Postgres](https://www.postgresql.org/download/windows/) и через pgAdmin 4 создайте базу данных с именем `bot_database` (Остальные подробности базы данных в руководстве .env для патронов)
4. Создайте виртуальное окружение и установите все зависимости из requirements.txt 
5. Запустите команду запуска comlink:
```bash
docker run --name swgoh-comlink -d --restart always --env APP_NAME=shtierlitz_comlinc -p 3200:3000 ghcr.io/swgoh-utils/swgoh-comlink:latest
```
6. Перейдите в коренной каталог и выполните миграции:
```bash 
alembic upgrade head
```
7. Запустите файл `bot_telegram.py`  
Готово.

## Установка через Docker на локальном Windows

1. Скачайте [репозиторий](https://github.com/Shtierlitz/SWGOH-COMLINK-GUILD-CONTROL-BOT-SYSTEM-ru.git) в выбранную вами папку:
```bash
git clone https://github.com/Shtierlitz/SWGOH-COMLINK-GUILD-CONTROL-BOT-SYSTEM-ru.git
```
2. Создайте json файл и настройте .env файлы. (А лучше скопировать уже готовые, что доступно патронам.)
3. Перейдите в коренной каталог и выполните:
```bash
docker-compose -f docker-compose.yml up -d --build
```
4. Дождавшись окончания установки образа выполните следующую последовательность команд, чтобы провести миграции:  
```bash 
docker ps -a
docker exec -it container_id /bin/bash
alembic upgrade head
exit
```
где `container_id` замените на идентификатор контейнера бота который вы получите после команды `docker ps -a`  

Готово!

## Установка на удаленном сервере через docker

### Примечание
Я использовал бесплатный free tier период от AWS EC2. Вы можете выбрать другой хостинг.  
Важно лишь то, что у вас должен быть доступ к линукс-консоли вашего хостинга.  
Как зарегистрироваться на Amazon можно посмотреть [тут...](https://www.youtube.com/watch?v=tNeU-cr31hA)   
Как создать свой облачный сервер на Amazon можно посмотреть [тут...](https://www.youtube.com/watch?v=f1s6Eq4nx0g&t=808s)

### Установка
1. Сперва совершите все апгрейды стстемы и установите докер следующими командами:
```bash
sudo apt-get update
sudo apt-get install apt-transport-https ca-certificates curl gnupg-agent software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt-get update
sudo apt-get install docker-ce
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo usermod -aG docker $USER
docker-compose --version
docker --version 
```
Последние 2 команды должны показать версии установленного докера. Если показывает, значит установка прошла успешно.

2. Скачайте репозиторий:
```bash
git clone https://github.com/Shtierlitz/SWGOH-COMLINK-GUILD-CONTROL-BOT-SYSTEM-ru.git
```
3. Создайте или скопируйте в систему все необходимые .env и json файлы. (В готовом виде доступно только патронам)
4. Запустите сборку контейнера:
```bash
sudo docker-compose -f docker-compose.yml up -d --build 
```
5. После установки контейнера нужно провести миграции. Рекомендую сделать это быстро, так как через 5 минут после сборки контейнера бот попытается обновить базу данных и это может превести к ошибкам в контейнере.Ваполните следущие команды:
```bash 
sudo docker ps -a
sudo docker exec -it container_id /bin/bash
alembic upgrade head
exit
```
где `container_id` замените на идентификатор контейнера бота который вы получите после команды `sudo docker ps -a`


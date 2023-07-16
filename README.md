# ULTIMATE-WARRIORS-BOT
Telegram bot for the guild ULTIMATE WARIORS 

docker network create swgoh

docker run --name swgoh-comlink --network swgoh -d --restart always --env APP_NAME=shtierlitz_comlinc -p 3200:3000 ghcr.io/swgoh-utils/swgoh-comlink:latest

docker build -t swgoh-stats .

docker run --name=swgoh-stats --network swgoh -d --restart always --env-file .env swgoh-stats -p 3223:3223 -v $(pwd)/statCalcData:/app/statCalcData ghcr.io/swgoh-utils/swgoh-stats:latest

docker run --rm -it -p 3223:3223 --env-file .env swgoh-stats  





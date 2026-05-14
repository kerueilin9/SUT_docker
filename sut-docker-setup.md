# Are Autonomous Web Agents Good Testers? - Three SUT Docker Setup Notes

Last checked: 2026-05-12

This note summarizes the three SUTs discussed in the paper:

- Classified / Classifieds
- Postmill / Reddit-like forum
- OneStopShop / Shopping website

The Docker assets come from the WebArena / VisualWebArena environment setup documents.

## Quick Mapping

| Paper SUT | WebArena / VisualWebArena name | Main platform | Main language | Local URL |
|---|---|---|---|---|
| Classified | Classifieds | Osclass-style classified ads site | PHP | http://localhost:9980 |
| Postmill | Social Forum / Reddit | Postmill | PHP / Symfony | http://localhost:9999 |
| OneStopShop | Shopping Website | Magento Open Source | PHP | http://localhost:7770 |

## Prerequisites

- Docker Desktop / Docker Engine
- Docker Compose v2
- Enough disk space. These WebArena images can be large.
- For local setup, use `localhost` as the host name in the commands below.

Check Docker:

```powershell
docker --version
docker compose version
```

## 1. Classified / Classifieds

Source:

- VisualWebArena README: https://github.com/web-arena-x/visualwebarena/blob/main/environment_docker/README.md
- Archive.org mirror: https://archive.org/download/classifieds_docker_compose
- Direct zip: https://archive.org/download/classifieds_docker_compose/classifieds_docker_compose.zip

The compose file uses:

- `jykoh/classifieds:latest`
- `mysql:8.1`

Download and extract:

```powershell
Invoke-WebRequest `
  -Uri "https://archive.org/download/classifieds_docker_compose/classifieds_docker_compose.zip" `
  -OutFile "classifieds_docker_compose.zip"

Expand-Archive -LiteralPath "classifieds_docker_compose.zip" -DestinationPath "." -Force
cd classifieds_docker_compose\classifieds_docker_compose
```

Before starting, check `docker-compose.yml`.

For local use, make sure the `CLASSIFIEDS` environment variable is:

```yaml
CLASSIFIEDS=http://127.0.0.1:9980/
```

Start:

```powershell
docker compose up --build -d
```

Populate the database:

```powershell
docker exec classifieds_db mysql -u root -ppassword osclass -e "source docker-entrypoint-initdb.d/osclass_craigslist.sql"
```

Open:

```text
http://localhost:9980
```

Reset Classifieds:

```powershell
Invoke-WebRequest `
  -Method POST `
  -Uri "http://localhost:9980/index.php?page=reset" `
  -Body "token=4b61655535e7ed388f0d40a93600254c"
```

Stop and remove:

```powershell
docker compose down --volumes --rmi all --remove-orphans
```

## 2. Postmill / Social Forum / Reddit

Source:

- VisualWebArena README: https://github.com/web-arena-x/visualwebarena/blob/main/environment_docker/README.md
- WebArena README: https://github.com/web-arena-x/webarena/blob/main/environment_docker/README.md
- Archive.org mirror: https://archive.org/download/postmill-populated-exposed-withimg
- Direct tar: https://archive.org/download/postmill-populated-exposed-withimg/postmill-populated-exposed-withimg.tar

Download:

```powershell
Invoke-WebRequest `
  -Uri "https://archive.org/download/postmill-populated-exposed-withimg/postmill-populated-exposed-withimg.tar" `
  -OutFile "postmill-populated-exposed-withimg.tar"
```

Load image:

```powershell
docker load --input postmill-populated-exposed-withimg.tar
```

Start:

```powershell
docker run --name forum -p 9999:80 -d postmill-populated-exposed-withimg
```

Open:

```text
http://localhost:9999/
```

Stop and remove:

```powershell
docker stop forum
docker remove forum
```

Optional image removal:

```powershell
docker image rm postmill-populated-exposed-withimg
```

## 3. OneStopShop / Shopping Website

Source:

- VisualWebArena README: https://github.com/web-arena-x/visualwebarena/blob/main/environment_docker/README.md
- WebArena README: https://github.com/web-arena-x/webarena/blob/main/environment_docker/README.md
- Archive.org mirror: https://archive.org/download/webarena-env-shopping-image
- Direct tar: https://archive.org/download/webarena-env-shopping-image/shopping_final_0712.tar

Download:

```powershell
Invoke-WebRequest `
  -Uri "https://archive.org/download/webarena-env-shopping-image/shopping_final_0712.tar" `
  -OutFile "shopping_final_0712.tar"
```

Load image:

```powershell
docker load --input shopping_final_0712.tar
```

Start:

```powershell
docker run --name shopping -p 7770:80 -d shopping_final_0712
```

Wait about one minute, then configure the Magento base URL for local use:

```powershell
docker exec shopping /var/www/magento2/bin/magento setup:store-config:set --base-url="http://localhost:7770"

docker exec shopping mysql -u magentouser -pMyPassword magentodb -e "UPDATE core_config_data SET value='http://localhost:7770/' WHERE path = 'web/secure/base_url';"

docker exec shopping /var/www/magento2/bin/magento cache:flush
```

Disable selected Magento re-indexing jobs, as recommended by VisualWebArena:

```powershell
docker exec shopping /var/www/magento2/bin/magento indexer:set-mode schedule catalogrule_product
docker exec shopping /var/www/magento2/bin/magento indexer:set-mode schedule catalogrule_rule
docker exec shopping /var/www/magento2/bin/magento indexer:set-mode schedule catalogsearch_fulltext
docker exec shopping /var/www/magento2/bin/magento indexer:set-mode schedule catalog_category_product
docker exec shopping /var/www/magento2/bin/magento indexer:set-mode schedule customer_grid
docker exec shopping /var/www/magento2/bin/magento indexer:set-mode schedule design_config_grid
docker exec shopping /var/www/magento2/bin/magento indexer:set-mode schedule inventory
docker exec shopping /var/www/magento2/bin/magento indexer:set-mode schedule catalog_product_category
docker exec shopping /var/www/magento2/bin/magento indexer:set-mode schedule catalog_product_attribute
docker exec shopping /var/www/magento2/bin/magento indexer:set-mode schedule catalog_product_price
docker exec shopping /var/www/magento2/bin/magento indexer:set-mode schedule cataloginventory_stock
```

Open:

```text
http://localhost:7770
```

Stop and remove:

```powershell
docker stop shopping
docker remove shopping
```

Optional image removal:

```powershell
docker image rm shopping_final_0712
```

## Health Checks

```powershell
Invoke-WebRequest -Uri "http://localhost:9980" -UseBasicParsing
Invoke-WebRequest -Uri "http://localhost:9999/" -UseBasicParsing
Invoke-WebRequest -Uri "http://localhost:7770" -UseBasicParsing
```

Or list running containers:

```powershell
docker ps --filter name=classifieds
docker ps --filter name=forum
docker ps --filter name=shopping
```

## Full Cleanup

Use this only if you want to remove these three SUTs from Docker.

```powershell
docker stop classifieds classifieds_db forum shopping
docker remove classifieds classifieds_db forum shopping
docker image rm jykoh/classifieds:latest mysql:8.1 postmill-populated-exposed-withimg shopping_final_0712
docker volume rm classifieds_docker_compose_db_data
```

Some commands may print "No such container", "No such image", or "No such volume" if the item was not created. That is fine.

## Notes

- The paper footnote that points to SeeAct appears not to be the Docker asset source.
- The deployable SUT assets are in WebArena / VisualWebArena Docker environment documents.
- Use `localhost` only for local runs. If running on a server, replace `localhost` with the server hostname or IP.
- For OneStopShop, the Magento base URL must match the URL used by the browser.
- For Classifieds, keep the trailing slash in `CLASSIFIEDS=http://127.0.0.1:9980/`.


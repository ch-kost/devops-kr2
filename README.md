# Контрольная работа №2

Чугунов К. Н., ЭФБО-11-24. Исправление шаблона Flask + Redis и публикация через Nginx/TLS.

Шаблон: https://gitverse.ru/dgimatdinov/kr2-template, исходный `main` — `3ee6c4b`.
Репозиторий: https://github.com/ch-kost/devops-kr2.
Логика `app.py` и `requirements.txt` сохранены; добавляется только разрешённый комментарий с фамилией.

## Вариант

Номер в списке группы не предоставлен. Для воспроизводимой локальной проверки временно выбран вариант 1 (`api.devops.local`, порт 8001). Это не утверждение, что он назначен преподавателем. Подготовлены все четыре конфигурации `variants/1.env` … `variants/4.env`. Перед сдачей нужно подтвердить номер: `N = (номер_в_списке - 1) % 4 + 1`.

| Вариант | Домен | Порт |
|---|---|---|
| 1 | api.devops.local | 8001 |
| 2 | notes.devops.local | 8002 |
| 3 | stats.devops.local | 8003 |
| 4 | kv.devops.local | 8004 |

## Состав

- `Dockerfile` — Python 3.12 slim, UID 10001, кэш зависимостей, exec-форма Gunicorn.
- `docker-compose.yml` — app и Redis 7 Alpine, изолированная backend-сеть, именованный том, healthcheck, loopback-публикация. Приложение дополнительно подключено к отдельной ingress-сети для публикации порта; Redis остаётся только во внутренней backend-сети.
- `nginx/kr2.conf.template` — отдельный HTTPS-ресурс VM, HTTP→HTTPS и заголовки прокси.
- `scripts/init_env.py` — безопасная генерация нового секрета на Linux без вывода значения.
- `scripts/compose.sh N …` — запуск выбранного варианта без рассогласования пароля оболочки и env_file.
- `scripts/deploy.sh` — пробная доставка rsync, затем явная доставка с `--apply`.
- `scripts/audit-kr2.sh N` — пять проверок дополнительного раздела [6].
- `docs/defects.md` — ревизия исходного шаблона; `docs/defense-answers.md` — 14 ответов.
- `docker-compose.local-test.yml` и `scripts/local_lab.py` — отдельный проверочный стенд Docker Desktop.

## Развёртывание на существующей devops-vm

Выполнять на Ubuntu из ПР №5–7. До доставки проверить `scripts/audit.sh` прежнего репозитория, HTTPS-ресурсы и снимки VM; создать `06-before-kr2`, сохранить `sudo ufw status numbered > ~/ufw-before-kr2.txt`. Эти действия и снимки не подменяются контейнером Docker Desktop.

На хосте из репозитория:

```bash
bash scripts/deploy.sh devops
# Просмотреть dry-run; назначение фиксировано devops:kr2/.
bash scripts/deploy.sh devops --apply
```

На сервере (для подтверждённого варианта, здесь временно 1):

```bash
cd ~/kr2
python3 scripts/init_env.py
# Повторный запуск не перезаписывает существующий секрет.
bash scripts/compose.sh 1 up -d --build --wait
bash scripts/configure-nginx.sh 1
# Просмотреть конфигурацию; установка не меняет devops-site или правила UFW.
bash scripts/configure-nginx.sh 1 --apply
bash scripts/audit-kr2.sh 1
```

Пароль создаётся новым случайным значением (64 hex-символа), хранится только в серверном `.env` с правами 600. Закрытый TLS-ключ создаётся на сервере с владельцем root и правами 600. Существующие файлы скрипты не перезаписывают. Не выводить `docker compose config` или полный `docker inspect`: учебная передача `--requirepass` оставляет пароль в аргументах контейнера, доступных администратору Docker.

На хосте добавить `<Host-only IP> api.devops.local` в hosts, получить только публичный сертификат через `scp devops:/etc/ssl/certs/kr2.crt ~/kr2.crt`, затем проверить:

```bash
curl -I http://api.devops.local/
curl --cacert ~/kr2.crt https://api.devops.local/
curl --cacert ~/kr2.crt https://api.devops.local/whoami
curl -m 3 http://api.devops.local:8001/health
```

Проверка сохранности: `bash scripts/compose.sh 1 down`, затем `up -d --wait`; флаг `-v` не использовать. Завершить полным старым аудитом, сравнением правил UFW, проверкой ресурсов ПР №6–7 и снимком `07-kr2`. Pull Request не сливать до защиты.

## Локальная проверка на Docker Desktop

Локальный стенд проверяет приложение, Redis, сборку образа и TLS reverse proxy. Он не доказывает наличие devops-vm, SSH/UFW, прежних ресурсов или снимков гипервизора. Финальная конфигурация VM использует `127.0.0.1:<порт>`; nginx проверочного контейнера обращается к app по Docker DNS. Порты тестового nginx ограничены loopback: HTTP 18080 и HTTPS 18443.

```powershell
python scripts/local_lab.py 1 build-tools
python scripts/local_lab.py 1 start
python scripts/local_lab.py 1 ps
```

Секрет и TLS-ключ генерируются внутри Linux-томов `kr2-chugunov-local-work` и `kr2-chugunov-local-certs`, на Windows не копируются. Служебный контейнер CLI получает Docker socket только для управления этим проверочным проектом. Для остановки: `python scripts/local_lab.py 1 down`; тома сохраняются.

## Тесты без Docker

```bash
python -m venv .venv
# Активировать .venv для своей ОС.
python -m pip install -r requirements.txt PyYAML
python -m unittest discover -s tests -v
```

Тесты проверяют исходный контракт Flask без внешнего Redis и важные ограничения Docker/Compose/Nginx. Фактическое выполнение контейнеров проверяется отдельно.

## Документация

- https://docs.docker.com/reference/dockerfile/
- https://docs.docker.com/build/cache/
- https://docs.docker.com/reference/compose-file/services/
- https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/
- https://docs.docker.com/engine/network/packet-filtering-firewalls/
- https://hub.docker.com/_/redis
- https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/
- https://nginx.org/en/docs/http/ngx_http_proxy_module.html
- https://nginx.org/en/docs/http/configuring_https_servers.html

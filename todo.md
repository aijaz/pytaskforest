# TODO

- [x] Basic Loop
  - [x] Dependencies
  - [x] Queues
- [x] Status
- [ ] Docker
- [ ] Flask
- [ ] Script support
- [ ] Tokens
- [ ] Mark
- [ ] Hold
- [ ] Release Hold
- [ ] Release Dependencies


via: https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/rabbitmq.html#installing-rabbitmq-on-macos

To start rabbitmq now and restart at login:
  brew services start rabbitmq
Or, if you don't want/need a background service you can just run:
  CONF_ENV_FILE="/opt/homebrew/etc/rabbitmq/rabbitmq-env.conf" /opt/homebrew/opt/rabbitmq/sbin/rabbitmq-server


sudo scutil --set HostName obsidian.local
Added "127.0.0.1       localhost myhost myhost.local" to /etc/hosts
sudo rabbitmq-server -detached
sudo rabbitmqctl status

sudo rabbitmqctl add_user myuser mypassword
sudo rabbitmqctl add_vhost myvhost
sudo rabbitmqctl set_user_tags myuser mytag
sudo rabbitmqctl set_permissions -p myvhost myuser ".*" ".*" ".*"


celery -A pytf.pytf_worker worker --loglevel=INFO -Q default --concurrency=1
celery -A pytf.pytf_worker worker --loglevel=INFO -Q foobarq --concurrency=1

`ircbothist` - IRC Bot for persistent history

## Install (Debian-based system):

```
# apt update
# apt install python3 python3-venv python3-pip
# mkdir -p /opt/ircbothist
# wget -c "https://q3aql.dev/scripts/ircbothist.py" -O /opt/ircbothist/ircbothist.py
# python3 -m venv /opt/ircbothist
# source /opt/ircbothist/bin/activate
# pip install --upgrade pip
# pip install irc
# useradd -m -s /bin/bash ircbot
# chown ircbot:ircbot -R /opt/ircbothist
```

## Edit configuration:

```                                                                                                                                                                                                                  
# vim /opt/ircbothist/ircbothist.py                                                                                                                                                                       
```  

Replace these lines with your configuration:

```
######## CONFIGURATION (Edit with your settings)
SERVER   = "localhost"
PORT     = 6667
USE_TLS  = False
NICK     = "history-bot"
REALNAME = "IRC Message History"
CHANNELS = ["#support", "#linux"]
MAX_HISTORY = 200
PERSIST_FILE = "history.pkl"
SAVE_INTERVAL = 60
#########
```

## Add the bot at system startup:

Create de file `/etc/systemd/system/ircbothist.service` with the following:

```
[Unit]
Description=IRC history bot
After=network.target

[Service]
Type=simple
User=ircbot
Group=ircbot
WorkingDirectory=/opt/ircbothist
Environment=PATH=/opt/ircbothist/bin
ExecStart=/opt/ircbothist/bin/python3 /opt/ircbothist/ircbothist.py
Restart=on-failure
RestartSec=5s
KillMode=process

[Install]
WantedBy=multi-user.target
```

Add the service at startup and start it:

```
# systemctl daemon-reload
# systemctl enable ircbothist
# systemctl start ircbothist
```

## How to uninstall:

```
# rm -rf /opt/ircbothist
# rm -rf /etc/system/system/ircbothist.service
# deluser ircbot
```

## Dependencies
* python3
* python3-irc
* python3-pip


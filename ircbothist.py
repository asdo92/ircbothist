#!/usr/bin/env python3

################################################################
# IRC Bot – Persistent history (last 200 messages per channel) #
#                                                              #
# Created by q3aql (q3aql@duck.com)                            #
# Licensed by GPL v2.0                                         #
# Last update: 23-08-2025                                      #
#                                                              #
# Requirements:                                                #
#    pip install irc                                           #
################################################################

import sys
import time
import signal
import logging
import pickle
import os
from collections import defaultdict, deque
from threading import Event, Thread

import irc.client

######## CONFIGURATION (Edit with your settings)
SERVER   = "irc.example.net"
PORT     = 6667
USE_TLS  = False
NICK     = "history-bot"
REALNAME = "IRC Message History"
CHANNELS = ["#support", "#linux"]
MAX_HISTORY = 200
PERSIST_FILE = "history.pkl"
SAVE_INTERVAL = 60
#########

history = defaultdict(lambda: deque(maxlen=MAX_HISTORY))

def load_history() -> None:
    if os.path.isfile(PERSIST_FILE):
        try:
            with open(PERSIST_FILE, "rb") as f:
                data = pickle.load(f)
                for chan, msgs in data.items():
                    history[chan] = deque(msgs, maxlen=MAX_HISTORY)
            logging.info("History loaded from %s", PERSIST_FILE)
        except Exception as exc:
            logging.error("Error loading history: %s", exc)


def save_history() -> None:
    try:
        serializable = {chan: list(msgs) for chan, msgs in history.items()}
        with open(PERSIST_FILE, "wb") as f:
            pickle.dump(serializable, f)
        logging.info("History saved in %s", PERSIST_FILE)
    except Exception as exc:
        logging.error("Error saving history: %s", exc)

def periodic_saver(stop_event: Event) -> None:
    while not stop_event.is_set():
        stop_event.wait(SAVE_INTERVAL)
        if not stop_event.is_set():
            save_history()

def on_connect(conn, event):
    logging.info("Connected to %s:%s", SERVER, PORT)
    for chan in CHANNELS:
        conn.join(chan)
        logging.info("Joining %s", chan)

def on_join(conn, event):
    nick = irc.client.NickMask(event.source).nick
    channel = event.target

    if nick == NICK:
        return

    logging.info("%s has joined %s – sending history", nick, channel)

    if history[channel]:
        for idx, line in enumerate(history[channel], start=1):
            conn.privmsg(nick, f"[{channel}] ({idx}) {line}")
    else:
        conn.privmsg(nick, f"{channel}: No history yet.")


def on_pubmsg(conn, event):
    channel = event.target
    nick = irc.client.NickMask(event.source).nick
    message = event.arguments[0]

    formatted = f"<{nick}> {message}"
    history[channel].append(formatted)
    logging.debug("Saved in %s: %s", channel, formatted)


def on_disconnect(conn, event):
    logging.warning("Disconnected from the server – reconnecting in 10s...")
    time.sleep(10)
    try:
        connect_and_start()
    except Exception as exc:
        logging.error("Connection failure: %s", exc)
        logging.warning("Retrying connection in 10s...")
        time.sleep(10)
        connect_and_start()
        #sys.exit(1)


def on_error(conn, event):
    logging.error("ERROR from server: %s", event.arguments)

def connect_and_start():
    reactor = irc.client.Reactor()

    try:
        if USE_TLS:
            conn = reactor.server().connect_ssl(
                SERVER, PORT, NICK, password=None, ssl_verify=False
            )
        else:
            conn = reactor.server().connect(SERVER, PORT, NICK, password=None)
    except irc.client.ServerConnectionError as e:
        logging.error("Unable to connect: %s", e)
        logging.warning("Retrying connection in 10s...")
        time.sleep(10)
        connect_and_start()
        #sys.exit(1)

    conn.add_global_handler("welcome", on_connect)   # 001
    conn.add_global_handler("join", on_join)
    conn.add_global_handler("pubmsg", on_pubmsg)
    conn.add_global_handler("disconnect", on_disconnect)
    conn.add_global_handler("error", on_error)

    reactor.process_forever()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    load_history()

    stop_saver = Event()
    saver_thread = Thread(target=periodic_saver, args=(stop_saver,), daemon=True)
    saver_thread.start()

    def shutdown(signum, frame):
        logging.info("Termination signal received – saving history and exiting...")
        stop_saver.set()
        saver_thread.join()
        save_history()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        connect_and_start()
    finally:
        stop_saver.set()
        saver_thread.join()
        save_history()

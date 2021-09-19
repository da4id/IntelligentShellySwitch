import json
import logging.config
import os
import time
from datetime import datetime
import sys
import signal
from ShellyMqttMsgProcessor import ShellyMqttMsgProcessor

Server = "192.168.12.16"
Port = 1883
User = "david"
Password = "j4BURx801Avq9UuUXpoV"
ID = "ShellyAdapter" + str(datetime.now())

def setup_logging(
        default_path=os.path.dirname(os.path.abspath(__file__)) + '/logging.json',
        default_level=logging.INFO,
        env_key='LOG_CFG'
):
    """Setup logging configuration

    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        print("use default config, no config file found")
        logging.basicConfig(level=default_level)

def signal_term(signal, frame):
    shellyMqttMsgHandler.loop_stop(True)
    shellyMqttMsgHandler.stopTimer = True
    logging.shutdown()
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, signal_term)
    signal.signal(signal.SIGINT, signal_term)
    setup_logging()

    shellyMqttMsgHandler = ShellyMqttMsgProcessor(ID, clean_session=True)
    shellyMqttMsgHandler.run(User, Password, Server, Port)


    while (True):
        time.sleep(3600)

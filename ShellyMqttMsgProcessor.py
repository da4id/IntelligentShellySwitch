import json
import logging

import paho.mqtt.client as mqtt
from sqlalchemy.orm import sessionmaker

from Model import *

AnnounceTopic = "shellies/announce"

Base = declarative_base()
engine = DbConnection.create_shelly_engine()

# create tables
Base.metadata.create_all(engine)

# create a Session
Session = sessionmaker(bind=engine)
session = Session()


class ShellyMqttMsgProcessor(mqtt.Client):

    def __init__(self, client_id="", clean_session=True, userdata=None, protocol=mqtt.MQTTv311, transport="tcp"):
        super().__init__(client_id, clean_session, userdata, protocol, transport)
        self.logger = logging.getLogger(__name__)
        self.enable_logger(self.logger)

    def on_connect(self, mqttc, obj, flags, rc):
        self.logger.debug("rc: " + str(rc))

    def on_publish(self, mqttc, obj, mid):
        self.logger.debug("mid: " + str(mid))

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        self.logger.info("Subscribed: " + str(mid) + " " + str(granted_qos))

    def on_message(self, mqttc, obj, msg):
        try:
            self.logger.info(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
            payload = msg.payload.decode("utf-8")
            if msg.topic == AnnounceTopic:
                self._process_announce(payload)
            elif msg.topic.find("shellies/") != -1 and msg.topic.find("/relay/") != -1:
                deviceId = msg.topic[len("shellies/"):msg.topic.find("/relay/")]
                device = session.query(Device).filter_by(id=deviceId).first()
                if device is None:
                    self.logger.warning("nicht registriertes Device: " + deviceId)
                    return
                idx = msg.topic.find("/relay/") + len("/relay/")
                channelId = int(msg.topic[idx:idx + 1])

                self.logger.debug("device " + str(device.dbid))
                self.logger.debug("channelId " + str(channelId))

                channel = session.query(Channel).filter_by(series=device).filter_by(channelId=channelId).first()

                if channel is None:
                    channel = Channel(device, channelId, 0)
                    session.add(channel)
                    session.commit()
                self.logger.debug("Channel " + str(channel.channelId))

                if msg.topic.find("power") > 0:
                    self._process_power(payload, device, channel)
        except Exception as e:
            self.logger.warning(e)

    def _process_power(self, payload, device, channel):
        if channel is not None:
            pass
        else:
            self.logger.warning("channel is None Device: " + str(device.dbid))
        self.logger.debug("process_power " + payload)

    def _process_announce(self, payload):
        d = json.loads(payload)
        device = session.query(Device).filter_by(id=d["id"]).first()
        if device is None:
            device = Device(d["id"], d["model"], d["mac"], d["ip"], d["id"])
            session.add(device)
            self._subscribe_device(device)
        else:
            device.ip = d["ip"]

        session.commit()

    def _subscribe_device(self, device):
        if device.model == "SHSW-PM":
            self.logger.info("Subscribe Shelly 1PM: " + device.id)
            self.subscribe("shellies/" + device.id + "/relay/0/power", 0)
        elif device.model == "SHSW-25":
            self.logger.info("Subscribe Shelly 2.5: " + device.id)
            self.subscribe("shellies/" + device.id + "/relay/0/power", 0)
            self.subscribe("shellies/" + device.id + "/relay/1/power", 0)

    def run(self, username, password, server, port):
        self.logger.info("Connect to MqTT Broker")
        self.username_pw_set(username, password)
        self.connect(server, port, 60, bind_address="")

        self.loop_start()
        self.subscribe(AnnounceTopic, 0)

        for device in session.query(Device):
            self._subscribe_device(device)

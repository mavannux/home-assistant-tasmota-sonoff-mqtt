import homeassistant.loader as loader
import json
import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

# The domain of your component. Should be equal to the name of your component.
DOMAIN = "tasmota_sonoff_mqtt"

# List of integration names (string) your integration depends upon.
DEPENDENCIES = ["mqtt"]

CONF_TOPIC = "topic"
DEFAULT_TOPIC = "sonoff"

# validate configuration: Required CONF_TOPIC
CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({vol.Required(CONF_TOPIC): cv.string,})}, extra=vol.ALLOW_EXTRA
)


class TasmotaMqtt:
    attributes = {}
    state = ''

    def __init__(self, hass, config):
        self.hass = hass
        self.topic = config[DOMAIN].get(CONF_TOPIC, DEFAULT_TOPIC)
        self.entity_id = self.topic

        self.mqtt = hass.components.mqtt
        self.cmdtopic = "cmnd/%s" % self.topic
        result_topic = "stat/%s/RESULT" % self.topic

        # initial state: Unknonw
        self.hass.states.set(DOMAIN + "." + self.entity_id, '?')
        
        # Subscribe our listener to a topic.
        _LOGGER.info("SUBSCRIBE: " + result_topic)
        self.mqtt.subscribe(result_topic, self.message_received)

        # Set the initial state.
        _LOGGER.info("PUBLISH: %s/timers" % self.cmdtopic)
        self.mqtt.publish(self.cmdtopic + "/timers", '')

        # Register our service with Home Assistant.
        hass.services.register(DOMAIN, "set_state", self.set_state_service)

    # Listener to be called when we receive a message.
    # The msg parameter is a Message object with the following members:
    # - topic, payload, qos, retain
    def message_received(self, msg):
        """Handle new MQTT messages."""
        # payload = json
        payload = msg.payload
        _LOGGER.debug(payload)
        data = json.loads(payload)

        # https://www.home-assistant.io/docs/configuration/state_object/
        #state_obj = self.hass.states.get(self.entity_id)

        for k in data.keys():

            #{"Timers":"ON"}
            if (k == 'Timers'):
                TasmotaMqtt.attributes[k] = data[k]

            elif (k.startswith('Timers')):
                timers = data[k]
                for tk in timers:
                    TasmotaMqtt.attributes[tk] = timers[tk]
                    
        self.hass.states.set(DOMAIN + "." + self.entity_id, TasmotaMqtt.state, TasmotaMqtt.attributes)

    # Service to publish a message on MQTT.
    def set_state_service(self, call):
        """Service to send a message."""
        #self.mqtt.publish(self.topic, call.data.get("new_state"))

# https://developers.home-assistant.io/docs/dev_101_config
# If in configuration.yaml file:
# >tasmota_sonoff_mqtt:
# >  topic: boiler
# then config['tasmota_sonoff_mqtt'][topic] = 'boiler'
def setup(hass, config):
    """Set up the Hello MQTT component."""
    TasmotaMqtt(hass, config)
    return True

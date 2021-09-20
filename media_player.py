from .subscription.subscriber import Subscriber
from .subscription.updater import Updater
from .youtube_controller_adapter import YoutubeControllerAdapter
import asyncio
from homeassistant.helpers import entity_platform
from homeassistant.components.media_player import MediaPlayerEntity
from homeassistant.const import (
    STATE_IDLE,
    STATE_PAUSED,
    STATE_PLAYING,
    CONF_HOST,
    CONF_PORT,
)
from homeassistant.components.media_player.const import (
    ATTR_MEDIA_TITLE,
    ATTR_MEDIA_DURATION,
    ATTR_MEDIA_POSITION,
    DOMAIN,
    SUPPORT_PAUSE,
    SUPPORT_PLAY,
    SUPPORT_PLAY_MEDIA,
    SUPPORT_NEXT_TRACK,
    SUPPORT_PREVIOUS_TRACK,
)
from homeassistant.components.media_player import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
import logging
import traceback

_LOGGER = logging.getLogger(__name__)

ATTR_TO_PROPERTY = [
    ATTR_MEDIA_TITLE,
    ATTR_MEDIA_DURATION,
    ATTR_MEDIA_POSITION,
    'video_id',
    'instance_id'
]


SUPPORT_FEATURES = (
    SUPPORT_PAUSE
    | SUPPORT_PLAY
    | SUPPORT_PLAY_MEDIA
    | SUPPORT_NEXT_TRACK
    | SUPPORT_PREVIOUS_TRACK
)


DEFAULT_CONTROLLING_PORT = 7790
DEFAULT_SUBSCRIBING_PORT = 7792
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required("youtube_controller"): {
            vol.Required(CONF_HOST): cv.string,
            vol.Optional("controlling_port", default=DEFAULT_CONTROLLING_PORT): cv.port,
            vol.Optional("subscription_port", default=DEFAULT_SUBSCRIBING_PORT): cv.port,
        }
    }
)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    platform = entity_platform.current_platform.get()
    builder = YoutubeMediaPlayerBuilder(hass, config["youtube_controller"])
    updater = Updater(builder, platform, _LOGGER)

    def on_message(message):
        hass.async_create_task(updater.on_event(message))

    def on_error(error):
        _LOGGER.debug("Connection to youtube controller ended up with an error:")
        _LOGGER.debug(error)

    def on_close():
        _LOGGER.debug("Connection to youtube controller was closed.")
        hass.async_create_task(updater.on_lost_connection())

    youtube_controller_config = config["youtube_controller"]
    subscriber = Subscriber(youtube_controller_config["host"], youtube_controller_config["subscription_port"], on_message, on_error, on_close)
    await hass.async_add_executor_job(subscriber.async_start)


class YoutubeMediaPlayerBuilder:
    def __init__(self, hass, youtube_controller_config):
        self.__hass = hass
        youtube_controller_base_url = "http://{}:{}".format(youtube_controller_config["host"], youtube_controller_config["controlling_port"])
        self.__youtube_controller_adapter = YoutubeControllerAdapter(youtube_controller_base_url)

    def build(self, instance_id):
        return YoutubeMediaPlayer(self.__hass, instance_id, self.__youtube_controller_adapter)


class YoutubeMediaPlayer(MediaPlayerEntity):
    def __init__(self, hass, instance_id, __youtube_controller_adapter: YoutubeControllerAdapter):
        self.__hass = hass
        self.__state = {}
        self.__instance_id = instance_id
        self.__youtube_controller_adapter = __youtube_controller_adapter

    @property
    def name(self):
        return 'YoutubeMediaPlayer'

    @property
    def state(self):
        if not "video" in self.__state or not "isPlaying" in self.__state["video"]:
            return STATE_IDLE
        elif self.__state["video"]["isPlaying"]:
            return STATE_PLAYING
        else:
            return STATE_PAUSED
    
    @property
    def instance_id(self):
        return self.__instance_id
    
    @property
    def media_title(self):
        if "video" in self.__state and "title" in self.__state["video"]:
            return self.__state["video"]["title"]
        else:
            return None

    @property
    def media_duration(self):
        if "video" in self.__state and "duration" in self.__state["video"]:
            return self.__state["video"]["duration"]
        else:
            return None

    @property
    def media_position(self):
        if "video" in self.__state and "currentPosition" in self.__state["video"]:
            return self.__state["video"]["currentPosition"]
        else:
            return None

    @property
    def video_id(self):
        if "video" in self.__state and "videoId" in self.__state["video"]:
            return self.__state["video"]["videoId"]
        else:
            return None

    @property
    def supported_features(self):
        return SUPPORT_FEATURES

    @property
    def state_attributes(self):
        state_attr = {}
        for attr in ATTR_TO_PROPERTY:
            value = getattr(self, attr)
            if value is not None:
                state_attr[attr] = value
        return state_attr

    @property
    def should_poll(self):
        return False

    def media_play(self):
        """Send play command."""
        _LOGGER.debug("play {}".format(self.instance_id))
        self.__youtube_controller_adapter.play(self.instance_id)

    def media_pause(self):
        """Send pause command."""
        _LOGGER.debug("pause {}".format(self.instance_id))
        self.__youtube_controller_adapter.pause(self.instance_id)

    def play_media(self, media_type, media_id, **kwargs):
        """Play media specified by its id."""
        _LOGGER.debug("play media {}".format(self.instance_id))
        self.__youtube_controller_adapter.watch(self.instance_id, media_id)

    def media_previous_track(self):
        """Fire the media previous action."""
        _LOGGER.debug("watch previous {}".format(self.instance_id))
        self.__youtube_controller_adapter.watch_previous(self.instance_id)
    
    def media_next_track(self):
        """Fire the media next action."""
        _LOGGER.debug("watch next {}".format(self.instance_id))
        self.__youtube_controller_adapter.watch_next(self.instance_id)

    def handle_state_change(self, instance_info):
        self.__state["video"] = instance_info["videoInfo"]
        self.schedule_update_ha_state()
"""Platform for sensor integration."""
import websocket
import json
import asyncio
import requests
from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.entity import Entity
from homeassistant.helpers import entity_platform
from homeassistant.components.media_player import MediaPlayerEntity
from homeassistant.const import (
    STATE_IDLE,
    STATE_PAUSED,
    STATE_PLAYING,
)
from homeassistant.components.media_player.const import (
    ATTR_MEDIA_TITLE,
    ATTR_MEDIA_DURATION,
    ATTR_MEDIA_POSITION,
    DOMAIN,
    SUPPORT_PAUSE,
    SUPPORT_PLAY,
    SUPPORT_SELECT_SOURCE,
    SUPPORT_PLAY_MEDIA,
    SUPPORT_NEXT_TRACK,
    SUPPORT_PREVIOUS_TRACK,
)

import logging

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


import threading
import websocket


class Controller:
    def __init__(self, hass, config, platform):
        self.hass = hass
        self.config = config
        self.platform = platform
        self.youtube_instances = []

    async def handle_state_change(self, change):
        _LOGGER.debug(change["type"])
        if change["type"] == "YoutubeInstanceAdded":
            _LOGGER.debug("DAVID: adding new entity")
            instance = YoutubeMediaPlayer(self.hass, self.config, change["data"]["id"])
            self.youtube_instances.append(instance)
            await self.platform.async_add_entities([instance])
            
        elif change["type"] == "YoutubeInstanceRemoved":
            _LOGGER.debug("DAVID: removing entity")
            for index, instance in enumerate(self.youtube_instances):
                if instance.instance_id == change["data"]["id"]:
                    _LOGGER.debug(instance.entity_id)
                    await self.platform.async_remove_entity(instance.entity_id)
                    self.youtube_instances.pop(index)
                    break
            
        elif change["type"] == "YoutubeInstanceChanged":
            _LOGGER.debug("DAVID: updating entity")
            for index, instance in enumerate(self.youtube_instances):
                if instance.instance_id == change["data"]["id"]:
                    _LOGGER.debug(instance.entity_id)
                    instance.handle_state_change(change)
                    break

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    _LOGGER.debug("setting youtube")
    platform = entity_platform.current_platform.get()
    controller = Controller(hass, config, platform)

    def on_message(ws, message):
        asyncio.run(controller.handle_state_change(json.loads(message)))

    def on_error(ws, error):
        _LOGGER.debug(error)

    def on_close(ws):
        _LOGGER.debug("### closed ###")

    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("ws://localhost:9989",
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close)
    wst = threading.Thread(target=ws.run_forever)
    wst.daemon = True
    wst.start()


class YoutubeMediaPlayer(MediaPlayerEntity):
    """Representation of a Sensor."""

    def __init__(self, hass, config, instance_id):
        """Initialize the sensor."""
        self._state = {}
        self.hass = hass
        self._instance_id = instance_id
        self.youtubeControllerUrl = config['youtube_controller_url']

    @property
    def name(self):
        return 'YoutubeMediaPlayer'

    @property
    def state(self):
        if not "video" in self._state or not "isPlaying" in self._state["video"]:
            return STATE_IDLE
        elif self._state["video"]["isPlaying"]:
            return STATE_PLAYING
        else:
            return STATE_PAUSED
    
    @property
    def instance_id(self):
        return self._instance_id
    
    @property
    def media_title(self):
        if "video" in self._state and "title" in self._state["video"]:
            return self._state["video"]["title"]
        else:
            return None

    @property
    def media_duration(self):
        if "video" in self._state and "duration" in self._state["video"]:
            return self._state["video"]["duration"]
        else:
            return None

    @property
    def media_position(self):
        if "video" in self._state and "currentPosition" in self._state["video"]:
            return self._state["video"]["currentPosition"]
        else:
            return None

    @property
    def video_id(self):
        if "video" in self._state and "videoId" in self._state["video"]:
            return self._state["video"]["videoId"]
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
        requests.post(self.youtubeControllerUrl + '/play?youtubeInstanceId=' + str(self.instance_id))

    def media_pause(self):
        """Send pause command."""
        requests.post(self.youtubeControllerUrl + '/pause?youtubeInstanceId=' + str(self.instance_id))

    def play_media(self, media_type, media_id, **kwargs):
        """Play media from a URL or file."""
        requests.post(self.youtubeControllerUrl + '/watch?youtubeInstanceId=' + str(self.instance_id, json={'videoId':media_id}))

    async def async_media_previous_track(self):
        """Fire the media previous action."""
        requests.post(self.youtubeControllerUrl + '/watch-previous?youtubeInstanceId=' + str(self.instance_id))
    
    async def async_media_next_track(self):
        """Fire the media next action."""
        requests.post(self.youtubeControllerUrl + '/watch-next?youtubeInstanceId=' + str(self.instance_id))

    def handle_state_change(self, change):
        self._state["video"] = change["data"]["videoInfo"]
        self.schedule_update_ha_state()
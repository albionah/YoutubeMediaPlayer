"""Platform for sensor integration."""
import websockets
import json
import asyncio
import requests
from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.entity import Entity
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
    'video_ids',
    'instance_ids'
]


SUPPORT_FEATURES = (
    SUPPORT_PAUSE
    | SUPPORT_PLAY
    | SUPPORT_SELECT_SOURCE
    | SUPPORT_PLAY_MEDIA
    | SUPPORT_NEXT_TRACK
    | SUPPORT_PREVIOUS_TRACK
)

is_alive = True

async def alive():
    while is_alive:
        _LOGGER.debug('alive')
        await asyncio.sleep(300)


async def async_processing(callback):
    async with websockets.connect('ws://localhost:9989') as websocket:
        while True:
            try:
                message = await websocket.recv()
                _LOGGER.debug(message)
                callback(json.loads(message))

            except websockets.exceptions.ConnectionClosed:
                _LOGGER.error('ConnectionClosed')
                is_alive = False
                break


def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    _LOGGER.debug("setting youtube")
    instance = YoutubeMediaPlayer(hass, config, 5)
    async_add_entities([instance])
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    tasks = [
        asyncio.ensure_future(alive()),
        asyncio.ensure_future(async_processing(instance.handle_state_change))
    ]
    loop.run_until_complete(asyncio.wait(tasks))


class YoutubeMediaPlayer(MediaPlayerEntity):
    """Representation of a Sensor."""

    def __init__(self, hass, config, instanceId):
        """Initialize the sensor."""
        self._state = []
        self.hass = hass
        self.currentYoutubeInstanceId = "-1"
        self.instanceId = instanceId
        self.youtubeControllerUrl = config['youtube_controller_url']

    @property
    def name(self):
        return 'YoutubeMediaPlayer'

    @property
    def state(self):
        def callback(item):
            if not "video" in item or not "isPlaying" in item["video"]:
                return STATE_IDLE
            elif item["video"]["isPlaying"]:
                return STATE_PLAYING
            else:
                return STATE_PAUSED
        return json.dumps(self.do_for_all(callback))
    
    @property
    def instance_ids(self):
        def callback(item):
            if "instanceId" in item:
                return item["instanceId"]
            else:
                return None
        return self.do_for_all(callback)
    
    @property
    def media_title(self):
        def callback(item):
            if "video" in item and "title" in item["video"]:
                return item["video"]["title"]
            else:
                return None
        return self.do_for_all(callback)

    @property
    def media_duration(self):
        def callback(item):
            if "video" in item and "duration" in item["video"]:
                return item["video"]["duration"]
            else:
                return None
        return self.do_for_all(callback)

    @property
    def media_position(self):
        def callback(item):
            if "video" in item and "currentPosition" in item["video"]:
                return item["video"]["currentPosition"]
            else:
                return None
        return self.do_for_all(callback)

    @property
    def video_ids(self):
        def callback(item):
            if "video" in item and "videoId" in item["video"]:
                return item["video"]["videoId"]
            else:
                return None
        return self.do_for_all(callback)

    def do_for_all(self, fn):
        array = []
        for index, item in enumerate(self._state):
            array.append(fn(item))
        return array

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

    async def async_select_source(self, source):
        """Set the input source."""
        self.currentYoutubeInstanceId = source

    def media_play(self):
        """Send play command."""
        requests.post(self.youtubeControllerUrl + '/play?youtubeInstanceId=' + self.currentYoutubeInstanceId)

    def media_pause(self):
        """Send pause command."""
        requests.post(self.youtubeControllerUrl + '/pause?youtubeInstanceId=' + self.currentYoutubeInstanceId)

    def play_media(self, media_type, media_id, **kwargs):
        """Play media from a URL or file."""
        requests.post(self.youtubeControllerUrl + '/watch?youtubeInstanceId=' + self.currentYoutubeInstanceId, json={'videoId':media_id})

    async def async_media_previous_track(self):
        """Fire the media previous action."""
        requests.post(self.youtubeControllerUrl + '/watch-previous?youtubeInstanceId=' + self.currentYoutubeInstanceId)
    
    async def async_media_next_track(self):
        """Fire the media next action."""
        requests.post(self.youtubeControllerUrl + '/watch-next?youtubeInstanceId=' + self.currentYoutubeInstanceId)

    def handle_state_change(self, change):
        if change["type"] == "YoutubeInstanceAdded":
            self._state.append({"instanceId": change["data"]["id"]})
        if change["type"] == "YoutubeInstanceRemoved":
            for index, item in enumerate(self._state):
                if item["instanceId"] == change["data"]["id"]:
                    self._state.pop(index)
                    break
        if change["type"] == "YoutubeInstanceChanged":
            for index, item in enumerate(self._state):
                if item["instanceId"] == change["data"]["id"]:
                    self._state[index]["video"] = change["data"]["videoInfo"]
                    break
        self.schedule_update_ha_state()
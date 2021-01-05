"""Platform for sensor integration."""
import requests
from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.entity import Entity
from homeassistant.components.media_player import MediaPlayerEntity

from homeassistant.components.media_player.const import (
    ATTR_MEDIA_TITLE,
    DOMAIN,
    SUPPORT_PAUSE,
    SUPPORT_PLAY,
    SUPPORT_SELECT_SOURCE,
    SUPPORT_PLAY_MEDIA,
    SUPPORT_NEXT_TRACK,
    SUPPORT_PREVIOUS_TRACK,
)

ATTR_TO_PROPERTY = [
    ATTR_MEDIA_TITLE,
    'moje'
]


SUPPORT_VLC = (
    SUPPORT_PAUSE
    | SUPPORT_PLAY
    | SUPPORT_SELECT_SOURCE
    | SUPPORT_PLAY_MEDIA
    | SUPPORT_NEXT_TRACK
    | SUPPORT_PREVIOUS_TRACK
)

def setup_platform(hass, config, add_entities, discovery_info=None):
    add_entities([YoutubeMediaPlayer(hass, config)])


class YoutubeMediaPlayer(MediaPlayerEntity):
    """Representation of a Sensor."""

    def __init__(self, hass, config):
        """Initialize the sensor."""
        self._state = None
        self.hass = hass
        self.currentYoutubeInstanceId = "-1"
        self.youtubeControllerUrl = config['youtube_controller_url']

    @property
    def name(self):
        """Return the name of the sensor."""
        return 'YoutubeMediaPlayer'

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state
    
    @property
    def media_title(self):
        """Title of current playing media."""
        return self._state

    @property
    def moje(self):
        return 'david'

    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        return SUPPORT_VLC

    @property
    def state_attributes(self):
        """Return the state attributes."""
        state_attr = {}
        for attr in ATTR_TO_PROPERTY:
            value = getattr(self, attr)
            if value is not None:
                state_attr[attr] = value
        return state_attr

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

    def update(self):
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        self._state = requests.get(self.youtubeControllerUrl + '/show-youtube-instances?1').text
        return None

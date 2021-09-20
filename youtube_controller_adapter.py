import requests


class YoutubeControllerAdapter:
    def __init__(self, youtube_controller_base_url):
        self.__youtube_controller_base_url = youtube_controller_base_url

    def play(self, youtube_instance_id):
        self.__command({"command": "play", "youtubeInstanceId": youtube_instance_id})

    def pause(self, youtube_instance_id):
        self.__command({"command": "pause", "youtubeInstanceId": youtube_instance_id})

    def watch(self, youtube_instance_id, video_id):
        self.__command({"command": "watch", "youtubeInstanceId": youtube_instance_id, "videoId": video_id})

    def watch_previous(self, youtube_instance_id):
        self.__command({"command": "watch-previous", "youtubeInstanceId": youtube_instance_id})
    
    def watch_next(self, youtube_instance_id):
        self.__command({"command": "watch-next", "youtubeInstanceId": youtube_instance_id})

    def __command(self, route, body_data):
        requests.post(self.__youtube_controller_base_url + "/youtube-instances/commands", json=body_data)
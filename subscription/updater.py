class Updater:
    def __init__(self, youtube_media_player_builder, platform, logger):
        self.__youtube_media_player_builder = youtube_media_player_builder
        self.__platform = platform
        self.__instances = []
        self.__logger = logger

    async def on_event(self, event):
        if event["type"] == "InitialSyncMessage":
            await self.__on_initial_sync_message(event["data"])

        elif event["type"] == "YoutubeInstanceAdded":
            await self.__on_youtube_instance_added(event["data"]["youtubeInstanceId"])
            
        elif event["type"] == "YoutubeInstanceRemoved":
            await self.__on_youtube_instance_removed(event["data"]["youtubeInstanceId"])

        elif event["type"] == "YoutubeInstanceChanged":
            self.__on_youtube_instance_changed(event["data"])

    async def on_lost_connection(self):
        for instance in self.__instances:
            await self.__platform.async_remove_entity(instance.entity_id)
        self.__instances = []

    async def __on_initial_sync_message(self, instances_info):
        for instance_info in instances_info:
            await self.__on_youtube_instance_added(instance_info["youtubeInstanceId"])
            self.__on_youtube_instance_changed(instance_info)

    async def __on_youtube_instance_added(self, instance_id):
        youtube_instance = self.__youtube_media_player_builder.build(instance_id)
        self.__instances.append(youtube_instance)
        await self.__platform.async_add_entities([youtube_instance])

    def __on_youtube_instance_changed(self, instance_info):
        for instance in self.__instances:
            if instance.instance_id == instance_info["youtubeInstanceId"]:
                instance.handle_state_change(instance_info)
                break

    async def __on_youtube_instance_removed(self, instance_id):
        for index, youtube_instance in enumerate(self.__instances):
            if youtube_instance.instance_id == instance_id:
                await self.__platform.async_remove_entity(youtube_instance.entity_id)
                self.__instances.pop(index)
                break
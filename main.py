from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from audio_controller import AudioController
from data_classes.data_classes import MenuItem
from event_listeners import InteractionListener, KeywordListener
from menu_builder import MenuBuilder
from data_classes import (
    PlayerStatus,
    MediaPlaybackState,
    Actions,
    Theme,
    MuteState,
)
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class PlayerMain(Extension):
    __keep_open: list[Actions] = [Actions.NEXT, Actions.PREV, Actions.REPEAT]
    aliases = {
        "p": [MenuItem.PLAY_PAUSE],
        "n": [MenuItem.NEXT_TRACK, MenuItem.CURRENT_MEDIA],
        "b": [MenuItem.PREV_TRACK, MenuItem.CURRENT_MEDIA],
        "v": [MenuItem.VOLUME],
        "vol": [MenuItem.VOLUME],
        "m": [MenuItem.MUTE],
        "r": [MenuItem.REPEAT],
        "s": [MenuItem.SHUFFLE],
    }
    theme: Theme = Theme.LIGHT
    menu_builder: MenuBuilder

    mute_state: MuteState = MuteState(False)

    def __init__(self):
        super(PlayerMain, self).__init__()

        self.menu_builder = MenuBuilder(self)

        self.subscribe(KeywordQueryEvent, KeywordListener())
        self.subscribe(ItemEnterEvent, InteractionListener())

    def refresh_theme(self) -> None:
        self.theme = Theme.from_str(self.preferences["icon_theme"])
        self.menu_builder.set_icon_folder(self.theme)

    def render_error(self, title: str, message: str) -> RenderResultListAction:
        return RenderResultListAction([self.menu_builder.build_error(title, message)])

    def render_main_page(
        self, action: Actions | None = None, player_status: PlayerStatus | None = None
    ) -> RenderResultListAction:
        logger.info(f"Current directory: {Path.cwd()}")

        items: list[ExtensionResultItem] = []

        player_status = (
            AudioController.get_player_status() if not player_status else player_status
        )

        playback_state: MediaPlaybackState = player_status.playback_state
        logger.debug(f"Current status: {player_status}")

        if playback_state == MediaPlaybackState.ERROR:
            return RenderResultListAction([self.menu_builder.no_media_item()])

        if playback_state == MediaPlaybackState.NO_PLAYER:
            return RenderResultListAction(self.menu_builder.no_player_item())

        if action is Actions.NEXT:
            items.extend(
                self.menu_builder.build_menu(
                    [MenuItem.NEXT_TRACK, MenuItem.CURRENT_MEDIA]
                )
            )

        elif action is Actions.PREV:
            items.extend(
                self.menu_builder.build_menu(
                    [MenuItem.PREV_TRACK, MenuItem.CURRENT_MEDIA]
                )
            )

        elif action is Actions.REPEAT:
            repeat_item: list[ExtensionResultItem] = self.menu_builder.build_menu(
                [MenuItem.REPEAT]
            )

            if repeat_item:
                items.extend(repeat_item)

        if action in self.__keep_open:
            return RenderResultListAction(items)

        items.extend(self.menu_builder.build_main_menu())

        return RenderResultListAction(items)

    def render_players(self) -> RenderResultListAction:
        items = self.menu_builder.build_player_select_items()

        return RenderResultListAction(items)


if __name__ == "__main__":
    PlayerMain().run()

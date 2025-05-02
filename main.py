from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from audio_controller import AudioController
from event_listeners import InteractionListener, KeywordListener
from menu_builder import MenuBuilder
from data_classes import (
    PlayerStatus,
    MediaPlaybackState,
    Actions,
    CurrentMedia,
    Theme,
    MuteState,
)
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class PlayerMain(Extension):
    __keep_open: list[Actions] = [Actions.NEXT, Actions.PREV, Actions.REPEAT]
    __aliases = {
        # p: play/pause
        "n": "next",
        "b": "previous",
        "v": "volume",
        # m: mute/unmute
        "vol": "volume",
        "r": "repeat",
        "s": "shuffle",
    }
    theme: Theme = Theme.LIGHT
    menu_builder: MenuBuilder

    mute_state: MuteState = MuteState(False)

    def __init__(self):
        super(PlayerMain, self).__init__()

        self.menu_builder = MenuBuilder(self)

        self.subscribe(KeywordQueryEvent, KeywordListener())
        self.subscribe(ItemEnterEvent, InteractionListener())

    def get_aliases(self) -> dict[str, str]:
        player_status = AudioController.get_player_status()
        aliases = {
            "p": "play"
            if player_status.playback_state == MediaPlaybackState.PAUSED
            else "pause",
            "m": self.mute_state.get_next_action().lower(),
        }

        aliases.update(self.__aliases)

        return aliases

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
            items.append(self.menu_builder.build_next_track())
        elif action is Actions.PREV:
            items.append(self.menu_builder.build_previous_track())
        elif action is Actions.REPEAT:
            repeat_item = self.menu_builder.build_repeat(player_status)

            if repeat_item:
                items.append(repeat_item)

        current_media: CurrentMedia = AudioController.get_current_media()
        icon_path: Path = AudioController.get_media_thumbnail(current_media)

        current_media_title = f"{current_media.title}"
        album = f" | {current_media.album}" if current_media.album else ""
        current_media_desc = (
            f"By {current_media.artist}{album} | {current_media.player}"
        )
        items.append(
            ExtensionResultItem(
                icon=str(icon_path),
                name=current_media_title,
                description=current_media_desc,
                on_enter=DoNothingAction(),
            )
        )

        if action in self.__keep_open:
            return RenderResultListAction(items)

        items.extend(self.menu_builder.build_main_menu(player_status))

        return RenderResultListAction(items)

    def render_players(self) -> RenderResultListAction:
        items = self.menu_builder.build_player_select()

        return RenderResultListAction(items)


if __name__ == "__main__":
    PlayerMain().run()

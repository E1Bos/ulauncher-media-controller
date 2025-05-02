import logging
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from audio_controller import AudioController
from data_classes import (
    PlayerStatus,
    MediaPlaybackState,
    Actions,
    ShuffleState,
    RepeatState,
    Query,
    Theme,
    MuteState,
)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import PlayerMain

logger = logging.getLogger(__name__)


class MenuBuilder:
    """Builds menu items"""

    def __init__(self, extension: "PlayerMain"):
        """
        Initialize the MenuBuilder
        Args:
            extension (PlayerMain): The extension for the player
        """
        self.extension: "PlayerMain" = extension
        self.set_icon_folder(self.extension.theme)

    def set_icon_folder(self, theme: Theme) -> None:
        """
        Set the icon folder based on the theme

        Args:
            theme (Theme): The theme for the player
        """
        self.theme = theme
        self.icon_folder = f"images/{self.theme.value}"

    def build_play_pause(self, player_status: PlayerStatus) -> ExtensionResultItem:
        """
        Build the play/pause item

        Args:
            theme (Theme): The theme for the player
            player_status (PlayerStatus): The current status of the player

        Returns:
            ExtensionResultItem: The play/pause item
        """
        opposite_status: str = (
            MediaPlaybackState.PAUSED.value
            if player_status.playback_state == MediaPlaybackState.PLAYING
            else MediaPlaybackState.PLAYING.value
        )

        return ExtensionResultItem(
            icon=f"{self.icon_folder}/{opposite_status}.svg",
            name=str(opposite_status.capitalize()),
            description=f"{opposite_status.capitalize()} the current song/track",
            on_enter=ExtensionCustomAction({"action": Actions.PLAYPAUSE}),
        )

    def build_next_track(self) -> ExtensionResultItem:
        """
        Build the next track item

        Returns:
            ExtensionResultItem: The next track item
        """
        return ExtensionResultItem(
            icon=f"{self.icon_folder}/next.svg",
            name="Next Track",
            description="Go to the next song/track",
            on_enter=ExtensionCustomAction(
                {"action": Actions.NEXT}, keep_app_open=True
            ),
        )

    def build_previous_track(self) -> ExtensionResultItem:
        """
        Build the previous track item

        Returns:
            ExtensionResultItem: The previous track item
        """
        return ExtensionResultItem(
            icon=f"{self.icon_folder}/prev.svg",
            name="Previous Track",
            description="Go to the previous song/track",
            on_enter=ExtensionCustomAction(
                {"action": Actions.PREV}, keep_app_open=True
            ),
        )

    def build_shuffle(self, player_status: PlayerStatus) -> ExtensionResultItem | None:
        """
        Build the shuffle item

        Args:
            player_status (PlayerStatus): The current status of the player

        Returns:
            ExtensionResultItem | None: The shuffle item
        """

        if player_status.shuffle_state == ShuffleState.UNAVAILABLE:
            return None
            # return ExtensionResultItem(
            #     icon=f"{icon_folder}/shuffle.svg",
            #     name="Shuffle Unavailable",
            #     description="Current player does not support shuffle",
            #     on_enter=DoNothingAction(),
            # )

        shuffle_str: str = player_status.shuffle_state.name.lower()
        shuffle_opp: str = "off" if shuffle_str == "On" else "on"
        return ExtensionResultItem(
            icon=f"{self.icon_folder}/shuffle_{shuffle_str}.svg",
            name=f"Shuffle {shuffle_str}",
            description=f"Turn shuffle {shuffle_opp}",
            on_enter=ExtensionCustomAction({"action": Actions.SHUFFLE}),
        )

    def build_repeat(self, player_status: PlayerStatus) -> ExtensionResultItem | None:
        """
        Build the repeat item

        Args:
            player_status (PlayerStatus): The current status of the player

        Returns:
            ExtensionResultItem | None: The repeat item
        """

        if player_status.repeat_state == RepeatState.UNAVAILABLE:
            return None
            # return ExtensionResultItem(
            #     icon=f"{icon_folder}/repeat.svg",
            #     name="Repeat Unavailable",
            #     description="Current player does not support repeating",
            #     on_enter=DoNothingAction(),
            # )

        repeat_str: str = player_status.repeat_state.name.lower()
        repeat_nxt: str = player_status.repeat_state.next().name.lower()
        return ExtensionResultItem(
            icon=f"{self.icon_folder}/repeat_{repeat_str}.svg",
            name=f"Repeat: {repeat_str.capitalize()}",
            description=f"Switch to {repeat_nxt}",
            on_enter=ExtensionCustomAction(
                {"action": Actions.REPEAT}, keep_app_open=True
            ),
        )

    def build_volume_and_mute(
        self,
        mute_state: MuteState,
        query: Query | None = None,
    ) -> list[ExtensionResultItem]:
        """
        Build the volume and mute items

        Args:
            mute_state (MuteState): The current mute state
            query (Query | None, optional): The query object. Defaults to None.

        Returns:
            list[ExtensionResultItem]: The volume and mute items
        """

        items: list[ExtensionResultItem] = []
        items.append(
            ExtensionResultItem(
                icon=f"{self.icon_folder}/volume.svg",
                name="Volume",
                description="Set volume between 0-100",
                on_enter=ExtensionCustomAction(
                    {"action": Actions.SET_VOL, "query": query}
                ),
            )
        )

        mute_action: str = mute_state.get_next_action()
        items.append(
            ExtensionResultItem(
                icon=f"{self.icon_folder}/mute.svg",
                name=mute_action,
                description=f"{mute_action} global volume",
                on_enter=ExtensionCustomAction(
                    {"action": Actions.MUTE, "state": mute_state}
                ),
            )
        )

        return items

    def build_main_menu(
        self,
        player_status: PlayerStatus | None = None,
        query: Query | None = None,
    ) -> list[ExtensionResultItem]:
        """
        Build the main user interface, which contains the play/pause,
        next, previous, volume, mute, and change player items

        Args:
            player_status (PlayerStatus, optional): The current player status
            components (list[str], optional): Command components

        Returns:
            list[ExtensionResultItem]: The main user interface
        """
        items: list[ExtensionResultItem] = []
        if not query:
            query = Query("", [])

        player_status = (
            AudioController.get_player_status() if not player_status else player_status
        )

        items.append(self.build_play_pause(player_status))

        items.append(self.build_next_track())

        items.append(self.build_previous_track())

        items.extend(self.build_volume_and_mute(self.extension.mute_state, query))

        shuffle_item: ExtensionResultItem | None = self.build_shuffle(player_status)
        if shuffle_item:
            items.append(shuffle_item)

        loop_item: ExtensionResultItem | None = self.build_repeat(player_status)
        if loop_item:
            items.append(loop_item)

        items.append(
            ExtensionResultItem(
                icon=f"{self.icon_folder}/switch.svg",
                name="Change player",
                description="Change music player",
                on_enter=ExtensionCustomAction(
                    {"action": Actions.PLAYER_SELECT_MENU}, keep_app_open=True
                ),
            )
        )

        return items

    def build_player_select(self) -> list[ExtensionResultItem]:
        """
        Build the player select menu

        Returns:
            list[ExtensionResultItem]: The player select menu
        """
        players: list[ExtensionResultItem] = []

        for player in AudioController.get_media_players():
            players.append(
                ExtensionResultItem(
                    icon=f"{self.icon_folder}/switch.svg",
                    name=player.split(".")[0].capitalize(),
                    description="Press enter to select this player",
                    on_enter=ExtensionCustomAction(
                        {"action": Actions.SELECT_PLAYER, "player": player}
                    ),
                )
            )
        return players

    def no_media_item(self) -> ExtensionResultItem:
        """
        Build the no media item

        Returns:
            ExtensionResultItem: The no media item
        """
        return ExtensionResultItem(
            icon=f"{self.icon_folder}/icon.png",
            name="Could not fetch current media",
            description="Is playerctl installed?",
            on_enter=DoNothingAction(),
        )

    def no_player_item(self) -> list[ExtensionResultItem]:
        """
        Build the no player item

        Returns:
            ExtensionResultItem: The no player item
        """
        items: list[ExtensionResultItem] = []
        items.append(
            ExtensionResultItem(
                icon=f"{self.icon_folder}/icon.png",
                name="No Media Playing",
                description="Please start a music player",
                on_enter=HideWindowAction(),
            )
        )
        items.extend(self.build_volume_and_mute(self.extension.mute_state))
        return items

    def build_error(self, title: str, message: str) -> ExtensionResultItem:
        """
        Build an error item

        Args:
            title (str): The title of the error
            message (str): The error message
        """
        return ExtensionResultItem(
            icon=f"{self.icon_folder}/warning.svg",
            name=f"Error: {title}.",
            description=message,
            on_enter=HideWindowAction(),
        )

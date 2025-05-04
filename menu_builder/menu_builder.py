import logging
from pathlib import Path
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
    MenuItem,
    CurrentMedia,
)
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from main import PlayerMain

logger = logging.getLogger(__name__)


class MenuBuilder:
    """Builds menu items"""

    # Default order for the main menu
    DEFAULT_MENU_ORDER = [
        MenuItem.CURRENT_MEDIA,
        MenuItem.PLAY_PAUSE,
        MenuItem.NEXT_TRACK,
        MenuItem.PREV_TRACK,
        MenuItem.SHUFFLE,
        MenuItem.REPEAT,
        MenuItem.VOLUME,
        MenuItem.MUTE,
        MenuItem.PLAYER_SELECT_MENU,
    ]

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

    def build_current_media(self) -> ExtensionResultItem:
        """
        Build the current media item

        Returns:
            ExtensionResultItem: The current media item
        """

        current_media: CurrentMedia = AudioController.get_current_media()
        icon_path: Path = AudioController.get_media_thumbnail(current_media)

        current_media_title = f"{current_media.title}"
        album = f" | {current_media.album}" if current_media.album else ""
        current_media_desc = (
            f"By {current_media.artist}{album} | {current_media.player}"
        )

        return ExtensionResultItem(
            icon=str(icon_path),
            name=current_media_title,
            description=current_media_desc,
            on_enter=DoNothingAction(),
        )

    def build_play_pause(self, player_status: PlayerStatus) -> ExtensionResultItem:
        """
        Build the play/pause item

        Args:
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
            ExtensionResultItem | None: The shuffle item or None if unavailable
        """

        if player_status.shuffle_state == ShuffleState.UNAVAILABLE:
            return None

        is_on = player_status.shuffle_state == ShuffleState.ON
        state_str = "On" if is_on else "Off"
        icon = f"{self.icon_folder}/shuffle_{state_str.lower()}.svg"
        desc = f"Turn shuffle {'off' if is_on else 'on'}"

        return ExtensionResultItem(
            icon=icon,
            name=f"Shuffle {state_str}",
            description=desc,
            on_enter=ExtensionCustomAction({"action": Actions.SHUFFLE}),
        )

    def build_repeat(self, player_status: PlayerStatus) -> ExtensionResultItem | None:
        """
        Build the repeat item

        Args:
            player_status (PlayerStatus): The current status of the player

        Returns:
            ExtensionResultItem | None: The repeat item or None if unavailable
        """

        if player_status.repeat_state == RepeatState.UNAVAILABLE:
            return None

        current = player_status.repeat_state
        next_state = current.next()
        icon = f"{self.icon_folder}/repeat_{current.name.lower()}.svg"

        return ExtensionResultItem(
            icon=icon,
            name=f"Repeat: {current.name.capitalize()}",
            description=f"Switch to {next_state.name.lower()}",
            on_enter=ExtensionCustomAction(
                {"action": Actions.REPEAT}, keep_app_open=True
            ),
        )

    def build_volume(
        self,
        query: Query | None = None,
    ) -> ExtensionResultItem:
        """
        Build the volume item

        Args:
            query (Query | None, optional): The query object. Defaults to None.

        Returns:
            ExtensionResultItem: The volume item
        """

        action: ExtensionCustomAction | DoNothingAction = DoNothingAction()
        if query is not None and len(query.components) > 0:
            action = ExtensionCustomAction(
                {"action": Actions.SET_VOL, "query": query},
            )

        return ExtensionResultItem(
            icon=f"{self.icon_folder}/volume.svg",
            name="Volume",
            description="Set volume between 0-100",
            on_enter=action,
        )

    def build_mute(
        self,
        mute_state: MuteState,
    ) -> ExtensionResultItem:
        """
        Build the mute item

        Args:
            mute_state (MuteState): The current mute state

        Returns:
            ExtensionResultItem: The mute item
        """
        mute_action: str = mute_state.get_next_action()
        return ExtensionResultItem(
            icon=f"{self.icon_folder}/mute.svg",
            name=mute_action,
            description=f"{mute_action} global volume",
            on_enter=ExtensionCustomAction(
                {"action": Actions.MUTE, "state": mute_state}
            ),
        )

    def build_player_select(self) -> ExtensionResultItem:
        """
        Build the player select item

        Returns:
            ExtensionResultItem: The player select item
        """

        return ExtensionResultItem(
            icon=f"{self.icon_folder}/switch.svg",
            name="Change player",
            description="Change music player",
            on_enter=ExtensionCustomAction(
                {"action": Actions.PLAYER_SELECT_MENU}, keep_app_open=True
            ),
        )

    def build_player_select_items(self) -> list[ExtensionResultItem]:
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
        items.extend(self.build_menu([MenuItem.VOLUME, MenuItem.MUTE]))
        return items

    def build_error(self, title: str, message: str) -> ExtensionResultItem:
        """
        Build an error item

        Args:
            title (str): The title of the error
            message (str): The error message

        Returns:
            ExtensionResultItem: The error item
        """
        return ExtensionResultItem(
            icon=f"{self.icon_folder}/warning.svg",
            name=f"Error: {title}.",
            description=message,
            on_enter=HideWindowAction(),
        )

    def build_main_menu(
        self,
        query: Query | None = None,
    ) -> list[ExtensionResultItem]:
        """
        Build the main user interface, which contains the play/pause,
        next, previous, volume, mute, and change player items

        Args:
            query (Query | None, optional): The query object. Defaults to None.

        Returns:
            list[ExtensionResultItem]: The main user interface
        """
        if not query:
            query = Query("", [])

        main_menu = MenuBuilder.DEFAULT_MENU_ORDER

        return self.build_menu(main_menu, query)

    def build_menu(
        self,
        menu_order: list[MenuItem],
        query: Query | None = None,
    ) -> list[ExtensionResultItem]:
        """
        Build the menu based on the menu order

        Args:
            menu_order (list[MenuItem]): The menu order
            query (Query | None, optional): The query object. Defaults to None.

        Returns:
            list[ExtensionResultItem]: The menu items
        """
        items: list[ExtensionResultItem] = []

        player_status = AudioController.get_player_status()
        mute_state: MuteState = self.extension.mute_state

        for item in menu_order:
            match item:
                case MenuItem.CURRENT_MEDIA:
                    items.append(self.build_current_media())
                case MenuItem.PLAY_PAUSE:
                    items.append(self.build_play_pause(player_status))
                case MenuItem.NEXT_TRACK:
                    items.append(self.build_next_track())
                case MenuItem.PREV_TRACK:
                    items.append(self.build_previous_track())
                case MenuItem.SHUFFLE:
                    shuffle_item: ExtensionResultItem | None = self.build_shuffle(
                        player_status
                    )
                    if shuffle_item:
                        items.append(shuffle_item)
                case MenuItem.REPEAT:
                    repeat_item: ExtensionResultItem | None = self.build_repeat(
                        player_status
                    )
                    if repeat_item:
                        items.append(repeat_item)
                case MenuItem.VOLUME:
                    items.append(self.build_volume(query))
                case MenuItem.MUTE:
                    items.append(self.build_mute(mute_state))
                case MenuItem.PLAYER_SELECT_MENU:
                    items.append(self.build_player_select())
                case MenuItem.ERROR:
                    pass

        return items

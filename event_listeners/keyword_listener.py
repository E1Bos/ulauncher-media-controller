import logging
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from audio_controller import AudioController
from menu_builder import MenuBuilder
from data_classes import Query, MediaPlaybackState, PlayerStatus

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import PlayerMain

logger = logging.getLogger(__name__)


class KeywordListener(EventListener):
    """Listener for keyword queries"""

    def on_event(  # type: ignore
        self, event: KeywordQueryEvent, extension: "PlayerMain"
    ) -> RenderResultListAction:
        """
        Render the main page or search for a query

        Parameters:
            event (KeywordQueryEvent): The event that was triggered
            extension (PlayerMain): The main extension class

        Returns:
            RenderResultListAction: A list of items to render
        """
        extension.refresh_theme()

        menu_builder: MenuBuilder = extension.menu_builder
        arguments: None | str = event.get_argument()

        player_status: PlayerStatus = AudioController.get_player_status()
        playback_state: MediaPlaybackState = player_status.playback_state

        if arguments is None or playback_state == MediaPlaybackState.ERROR:
            return extension.render_main_page(player_status=player_status)

        command, *components = arguments.split()
        aliases = extension.get_aliases()

        # process split command (i.e. "vol50")
        if (
            command
            and any(c.isalpha() for c in command)
            and any(c.isdigit() for c in command)
        ):
            alpha_part = "".join(c for c in command if c.isalpha())
            digit_part = "".join(c for c in command if c.isdigit())

            # only process if we have both parts
            if alpha_part and digit_part:
                command = alpha_part
                components.append(digit_part)

        alpha_command: str = "".join(filter(str.isalpha, command.lower()))
        if alpha_command in aliases:
            decimal_command: str = "".join(filter(str.isdecimal, command))
            if decimal_command:
                components.append(decimal_command)
            command = aliases[alpha_command]

        render_items: list[ExtensionResultItem]
        query = Query(command, components)
        if playback_state == MediaPlaybackState.NO_PLAYER:
            render_items = menu_builder.build_volume_and_mute(
                extension.mute_state, query
            )
        else:
            render_items = menu_builder.build_main_menu(query=query)

        search_terms: list[str] = command.lower().split()
        matched_search: list[ExtensionResultItem] = [
            item
            for item in render_items
            if any(term in item.get_name().lower() for term in search_terms)
        ]

        return RenderResultListAction(matched_search)

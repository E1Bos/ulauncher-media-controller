import logging
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from audio_controller import AudioController
from menu_builder import MenuBuilder
from data_classes import Query, MediaPlaybackState, PlayerStatus, MenuItem

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

        query = Query.from_string(arguments)
        aliases = extension.aliases

        # Handle aliases
        alpha_command = "".join(filter(str.isalpha, query.command.lower()))
        if alpha_command in aliases:
            items = menu_builder.build_menu(aliases[alpha_command], query)
            return RenderResultListAction(items)

        if playback_state == MediaPlaybackState.NO_PLAYER:
            render_items = menu_builder.build_menu(
                [MenuItem.VOLUME, MenuItem.MUTE], query
            )
        else:
            render_items = menu_builder.build_main_menu(query=query)

        search_terms = arguments.lower().split()
        matched = [
            item
            for item in render_items
            if any(term in item.get_name().lower() for term in search_terms)
        ]

        return RenderResultListAction(matched)

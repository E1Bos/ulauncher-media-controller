from typing import TYPE_CHECKING, Any
import logging
import time
from subprocess import CalledProcessError
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import ItemEnterEvent
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction

from audio_controller import AudioController
from data_classes import Actions, Query, CurrentMedia, PlayerStatus

if TYPE_CHECKING:
    from main import PlayerMain

logger = logging.getLogger(__name__)


class InteractionListener(EventListener):
    """Listener for user interactions"""

    "Max wait time for media change in seconds"
    MAX_WAIT: int = 3

    @staticmethod
    def under_max_wait(start_time: float) -> bool:
        return (time.time() - start_time) < InteractionListener.MAX_WAIT

    def on_event(  # type: ignore
        self, event: ItemEnterEvent, extension: "PlayerMain"
    ) -> None | RenderResultListAction:
        """
        Handle user interactions

        Parameters:
            event (ItemEnterEvent): The event that was triggered
            extension (PlayerMain): The main extension class

        Returns:
            None | RenderResultListAction: Nothing or a list of items to render
        """
        data: dict[str, Any] = event.get_data()
        extension.logger.debug(str(data))

        action: Actions = data["action"]
        query: Query = data.get("query", Query("", []))
        player_status: PlayerStatus = AudioController.get_player_status()

        start_time = time.time()

        previous_media: CurrentMedia | None
        try:
            previous_media = AudioController.get_current_media()
        except CalledProcessError:
            previous_media = None

        if action == Actions.PLAYPAUSE:
            AudioController.playpause()
        elif action in [Actions.NEXT, Actions.PREV]:
            try:
                if previous_media is None:
                    logger.error("Something has gone very wrong")
                    raise ValueError("No previous media")

                if action == Actions.NEXT:
                    AudioController.next()
                else:
                    AudioController.prev()

                current_media = AudioController.get_current_media()
                if action == Actions.NEXT:
                    while InteractionListener.under_max_wait(start_time):
                        current_media = AudioController.get_current_media()

                        if current_media.title != previous_media.title:
                            break

                        time.sleep(0.1)
                elif action == Actions.PREV:
                    while InteractionListener.under_max_wait(start_time):
                        current_media = AudioController.get_current_media()

                        if current_media.title != previous_media.title:
                            break

                        new_pos = current_media.position
                        old_pos = previous_media.position

                        if new_pos is not None and old_pos is not None:
                            if new_pos < old_pos:
                                break

                        time.sleep(0.1)

                return extension.render_main_page(action)
            except CalledProcessError:
                return extension.render_error(
                    f"Could not play {'next' if action == Actions.NEXT else 'previous'} media",
                    "Does the player support this action?",
                )
        elif action == Actions.MUTE:
            if extension.mute_state.is_muted:
                extension.mute_state.is_muted = False
                AudioController.set_mute(False)
            else:
                extension.mute_state.is_muted = True
                AudioController.set_mute(True)
        elif action == Actions.SET_VOL:
            try:
                if len(query.components) == 0:
                    vol_component = query.command
                else:
                    vol_component = query.components[0]

                vol_amount_str: str = "".join(filter(str.isdigit, vol_component))

                if not vol_amount_str:
                    raise ValueError(f"{vol_component} is not a number")

                vol_int: int = int(vol_amount_str)
                AudioController.global_volume(vol_int)
            except (TypeError, ValueError) as e:
                logger.error(
                    f"Could not parse query: {query}: {e.with_traceback(None)}"
                )
        elif action == Actions.SHUFFLE:
            AudioController.shuffle()
        elif action == Actions.REPEAT:
            start_time = time.time()
            AudioController.repeat(player_status)

            while InteractionListener.under_max_wait(start_time):
                new_status = AudioController.get_player_status()
                if new_status.repeat_state != player_status.repeat_state:
                    break

                time.sleep(0.1)

            return extension.render_main_page(action)
        elif action == Actions.PLAYER_SELECT_MENU:
            return extension.render_players()
        elif action == Actions.SELECT_PLAYER:
            AudioController.change_player(data["player"])

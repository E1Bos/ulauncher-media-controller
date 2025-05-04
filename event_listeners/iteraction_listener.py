from typing import TYPE_CHECKING, Any
import logging
import time
from subprocess import CalledProcessError
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import ItemEnterEvent
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction

from audio_controller import AudioController
from data_classes import Actions, Query, CurrentMedia, PlayerStatus, RepeatState

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

    @staticmethod
    def _wait_for_media_change(
        start_time: float, previous_media: CurrentMedia, action: Actions
    ) -> None:
        """
        Wait until the media changes title or position based on action, up to MAX_WAIT.

        Args:
            start_time (float): The time when the action was triggered
            previous_media (CurrentMedia): The media before the action
            action (Actions): The action that was triggered
        """
        while InteractionListener.under_max_wait(start_time):
            current = AudioController.get_current_media()

            if action == Actions.NEXT and current.title != previous_media.title:
                break

            if action == Actions.PREV:
                if current.title != previous_media.title:
                    break
                if (
                    previous_media.position is not None
                    and current.position is not None
                    and current.position < previous_media.position
                ):
                    break

            time.sleep(0.1)

    @staticmethod
    def _wait_for_repeat_change(
        start_time: float, previous_repeat_state: RepeatState
    ) -> None:
        """
        Wait until the repeat state changes, up to MAX_WAIT.

        Args:
            start_time (float): The time when the action was triggered
            previous_repeat_state (RepeatState): The repeat state before the action
        """
        while InteractionListener.under_max_wait(start_time):
            new_status = AudioController.get_player_status().repeat_state
            if new_status != previous_repeat_state:
                break
            time.sleep(0.1)

    def on_event(  # type: ignore
        self, event: ItemEnterEvent, extension: "PlayerMain"
    ) -> None | RenderResultListAction:
        """
        Handle user interactions

        Args:
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
                    logger.error("No previous media to compare for NEXT/PREV action")
                    raise ValueError("No previous media")
                if action == Actions.NEXT:
                    AudioController.next()
                else:
                    AudioController.prev()

                InteractionListener._wait_for_media_change(
                    start_time, previous_media, action
                )
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

                if vol_int == 0:
                    extension.mute_state.is_muted = True
                else:
                    extension.mute_state.is_muted = False
            except (TypeError, ValueError) as e:
                logger.error(
                    f"Could not parse query: {query}: {e.with_traceback(None)}"
                )
        elif action == Actions.SHUFFLE:
            AudioController.shuffle()
        elif action == Actions.REPEAT:
            start_time = time.time()
            AudioController.repeat(player_status)

            InteractionListener._wait_for_repeat_change(
                start_time, player_status.repeat_state
            )
            return extension.render_main_page(action)
        elif action == Actions.PLAYER_SELECT_MENU:
            return extension.render_players()
        elif action == Actions.SELECT_PLAYER:
            AudioController.change_player(data["player"])

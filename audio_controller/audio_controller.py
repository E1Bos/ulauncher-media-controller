import glob
import os
from pathlib import Path
import subprocess
import logging
import re
import hashlib

from data_classes import (
    CurrentMedia,
    MediaPlaybackState,
    PlayerStatus,
    RepeatState,
    ShuffleState,
)

logger = logging.getLogger(__name__)


class AudioController:
    """Controller for audio actions"""

    # Default MPRIS controller name
    PLAYER = "playerctld"

    @staticmethod
    def _pc(args: list[str], check: bool = True) -> str:
        """
        Run a playerctl command for the default player.
        """
        return AudioController.__run_command(
            ["playerctl", "-p", AudioController.PLAYER, *args], check
        )

    @staticmethod
    def pause_all() -> None:
        """
        Pause all media players.
        """
        AudioController.__run_command(["playerctl", "--all-players", "pause"])

    @staticmethod
    def _pc_player(player: str, args: list[str], check: bool = True) -> str:
        """
        Run a playerctl command for a specific player.
        """
        return AudioController.__run_command(["playerctl", "-p", player, *args], check)

    media_cover_path: Path = Path("/tmp/ulauncher-media-player/media-thumbnails")

    @staticmethod
    def __run_command(command: list[str], check: bool = True) -> str:
        """
        Run a command and return the output
        """
        result = subprocess.run(
            command,
            check=check,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        logger.debug(result.stdout)
        return result.stdout

    @staticmethod
    def playpause() -> None:
        """Toggle play/pause"""
        AudioController._pc(["play-pause"])

    @staticmethod
    def next() -> None:
        """Skip to the next track"""
        AudioController._pc(["next"])

    @staticmethod
    def prev() -> None:
        """Skip to the previous track"""
        AudioController._pc(["previous"])

    @staticmethod
    def jump(pos: str) -> None:
        """Jump to a specific position in the track"""
        # TODO: Implement this
        AudioController._pc(["position", pos])

    @staticmethod
    def global_volume(set_vol: int) -> None:
        """
        Set the global volume

        Parameters:
            set_vol (int): The volume to set
        """
        cleaned_vol: str = str(max(0, min(set_vol, 100)))

        if cleaned_vol == "0":
            AudioController.set_mute(True)
        else:
            AudioController.set_mute(False)
            AudioController.__run_command(
                ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{cleaned_vol}%"]
            )

    @staticmethod
    def set_mute(mute: bool) -> None:
        """
        Mute or unmute the audio

        Parameters:
            mute (bool): Whether to mute or unmute
        """
        AudioController.__run_command(
            ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "1" if mute else "0"]
        )

    @staticmethod
    def shuffle() -> None:
        """Toggle shuffle"""
        AudioController._pc(["shuffle", "toggle"])

    @staticmethod
    def repeat(player_status: PlayerStatus) -> None:
        """Toggle repeat state"""
        next_state = player_status.repeat_state.next()
        AudioController._pc(["loop", next_state.value])

    @staticmethod
    def get_player_status() -> PlayerStatus:
        """
        Get the playing status of the player

        Parameters:
            player (str): The player to check, defaults to "playerctld"

        Returns:
            PlayerStatus: The status of the player
        """
        player_status = AudioController._pc(["status"], False)
        shuffle_status = AudioController._pc(["shuffle"], False)
        loop_status = AudioController._pc(["loop"], False)

        media_state: MediaPlaybackState = Parser.parse_media_state(player_status)
        shuffle_state: ShuffleState = Parser.parse_shuffle_state(shuffle_status)
        loop_state: RepeatState = Parser.parse_loop_state(loop_status)

        return PlayerStatus(
            playback_state=media_state,
            shuffle_state=shuffle_state,
            repeat_state=loop_state,
        )

    @staticmethod
    def get_media_players() -> list[str]:
        """
        Returns a list of media players that are currently running

        Returns:
            list[str]: A list of media players
        """
        return AudioController.__run_command(["playerctl", "-l"]).splitlines()

    @staticmethod
    def change_player(player: str) -> None:
        """
        Pauses all players and plays the specified player

        Parameters:
            player (str): The player
        """
        # Pause all players, then switch and resume selected player
        AudioController.pause_all()
        AudioController._pc_player(player, ["play"])
        AudioController._pc_player(player, ["pause"])
        AudioController._pc_player(player, ["play-pause"])

    @staticmethod
    def get_current_media() -> CurrentMedia:
        """
        Get the current playing media metadata

        Returns:
            CurrentMedia: The current playing media metadata
        """
        # Retrieve metadata for default player
        format_str = (
            "artUrl:{{mpris:artUrl}}\nartist:{{xesam:artist}}\n"
            "title:{{xesam:title}}\nalbum:{{xesam:album}}\n"
            "playerName:{{playerName}}\nposition:{{position}}"
        )
        result = AudioController._pc(["metadata", "--format", format_str])

        artUrl = Parser.extract_regex_item("artUrl", result)
        artist = Parser.extract_regex_item("artist", result)
        title = Parser.extract_regex_item("title", result)
        player = Parser.extract_regex_item("playerName", result).capitalize()
        album = Parser.extract_regex_item("album", result, ok_if_empty=True)
        position = Parser.extract_regex_item("position", result, ok_if_empty=True)

        return CurrentMedia(
            thumbnail_path=artUrl,
            artist=artist,
            title=title,
            player=player,
            album=album,
            position=int(position) if position else None,
        )

    @staticmethod
    def get_media_thumbnail(media: CurrentMedia) -> Path:
        """
        Get the media thumbnail

        Parameters:
            media (CurrentMedia): The current media

        Returns:
            Path: The path to the media thumbnail
        """
        cover_path: Path = AudioController.media_cover_path

        if not cover_path.exists():
            cover_path.mkdir(parents=True, exist_ok=True)

        hash_str = f"{media.title}-{media.artist}".encode("utf-8")
        hash_object = hashlib.md5(hash_str)
        hash_hex = hash_object.hexdigest()
        local_filename = Path(
            cover_path,
            f"{hash_hex}.png",
        )

        if local_filename.exists():
            return local_filename

        old_thumbnails = glob.glob(f"{cover_path}/*.png")
        if len(old_thumbnails) > 50:
            old_thumbnails.sort(key=os.path.getctime)
            for icon in old_thumbnails[:35]:
                os.remove(icon)

        if not os.path.exists(local_filename):
            thumbnail_url: str = media.thumbnail_path

            if thumbnail_url.startswith("file://"):
                local_filename = Path(thumbnail_url[7:])
            elif thumbnail_url.startswith("http"):
                AudioController.__download_thumbnail(media, local_filename)

        return local_filename if local_filename.exists() else Path("images/icon.png")

    @staticmethod
    def __download_thumbnail(media: CurrentMedia, local_filename: Path) -> None:
        """
        Download the thumbnail of the media

        Parameters:
            media (CurrentMedia): The current media
            local_filename (Path): The local filename to save the thumbnail
        """
        timeout_secs: float = 1
        tries: int = 3

        try:
            result = subprocess.run(
                [
                    "wget",
                    "-t",
                    str(tries),
                    "-T",
                    str(timeout_secs),
                    "-O",
                    str(local_filename),
                    media.thumbnail_path,
                ],
                check=True,
            )
            if result.returncode != 0:
                os.remove(local_filename)
                logger.error(f"Failed to download image from {media.thumbnail_path}")
        except subprocess.CalledProcessError as e:
            if local_filename.exists():
                os.remove(local_filename)
            logger.error(f"Failed to download image from {media.thumbnail_path}: {e}")


class Parser:
    @staticmethod
    def parse_media_state(player_status: str) -> MediaPlaybackState:
        if "No players found" in player_status:
            return MediaPlaybackState.NO_PLAYER

        if "Playing" in player_status:
            return MediaPlaybackState.PLAYING

        if "Paused" in player_status:
            return MediaPlaybackState.PAUSED

        return MediaPlaybackState.ERROR

    @staticmethod
    def parse_shuffle_state(shuffle_status: str) -> ShuffleState:
        if "On" in shuffle_status:
            return ShuffleState.ON

        if "Off" in shuffle_status:
            return ShuffleState.OFF

        return ShuffleState.UNAVAILABLE

    @staticmethod
    def parse_loop_state(loop_status: str) -> RepeatState:
        if "Track" in loop_status:
            return RepeatState.TRACK

        if "Playlist" in loop_status:
            return RepeatState.PLAYLIST

        if "None" in loop_status:
            return RepeatState.OFF

        return RepeatState.UNAVAILABLE

    @staticmethod
    def extract_regex_item(
        item: str, search_str: str, ok_if_empty: bool = False
    ) -> str:
        """
        Extract an item from a string using regex, used to extract metadata

        Parameters:
            item (str): The item to extract
            search_str (str): The string to search
            ok_if_empty (bool): Whether to return an empty string if the item is not found

        Returns:
            str: The extracted item string
        """

        match = re.search(rf"{item}:(.+)", search_str)

        if match is None:
            if ok_if_empty:
                return ""

            raise ValueError(f"Could not find {item} in result")

        return match.group(1)

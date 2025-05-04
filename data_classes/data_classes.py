from dataclasses import dataclass
from enum import Enum, auto


class MenuItem(Enum):
    """Represents the menu items for the player"""

    CURRENT_MEDIA = auto()
    PLAY_PAUSE = auto()
    NEXT_TRACK = auto()
    PREV_TRACK = auto()
    SHUFFLE = auto()
    REPEAT = auto()
    VOLUME = auto()
    MUTE = auto()
    PLAYER_SELECT_MENU = auto()
    SELECT_PLAYER = auto()
    NO_MEDIA = auto()
    ERROR = auto()


class MediaPlaybackState(Enum):
    """Represents the status of the player"""

    PLAYING = "play"
    PAUSED = "pause"
    ERROR = auto()
    NO_PLAYER = auto()


class ShuffleState(Enum):
    """Represents the shuffle status of the player"""

    ON = "On"
    OFF = "Off"
    UNAVAILABLE = auto()


class RepeatState(Enum):
    """Represents the loop of the player"""

    OFF = "None"
    PLAYLIST = "Playlist"
    TRACK = "Track"
    UNAVAILABLE = "Unavailable"

    def next(self) -> "RepeatState":
        order = [RepeatState.OFF, RepeatState.PLAYLIST, RepeatState.TRACK]

        if self == RepeatState.UNAVAILABLE:
            return RepeatState.UNAVAILABLE

        return order[(order.index(self) + 1) % len(order)]


class Actions(Enum):
    """Actions that can be performed"""

    PLAYPAUSE = auto()
    NEXT = auto()
    PREV = auto()
    MUTE = auto()
    SHUFFLE = auto()
    REPEAT = auto()
    SET_VOL = auto()
    JUMP = auto()
    PLAYER_SELECT_MENU = auto()
    SELECT_PLAYER = auto()


class Theme(Enum):
    """Theme for the player"""

    LIGHT = "light"
    DARK = "dark"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_str(cls, theme: str) -> "Theme":
        """Convert a string to a Theme enum"""
        if theme.lower() == "dark":
            return cls.DARK
        elif theme.lower() == "light":
            return cls.LIGHT
        else:
            raise ValueError(f"Invalid theme: {theme}")


@dataclass
class PlayerStatus:
    """Represents the status of the player"""

    playback_state: MediaPlaybackState
    shuffle_state: ShuffleState
    repeat_state: RepeatState


@dataclass
class CurrentMedia:
    """Represents the current media that is playing"""

    thumbnail_path: str
    artist: str
    title: str
    player: str
    album: str | None
    position: int | None


@dataclass
class Query:
    command: str
    components: list[str]

    @classmethod
    def from_string(cls, argument: str) -> "Query":
        """
        Parse a raw argument string into command and components,
        handling alpha-numeric parts like "vol50".
        """
        parts = argument.split()
        command, *components = parts

        # split command into letters and digits if it contains both
        # e.g. "vol50" -> command = "vol", components = ["50"]
        if (
            command
            and any(c.isalpha() for c in command)
            and any(c.isdigit() for c in command)
        ):
            alpha = "".join(c for c in command if c.isalpha())
            digit = "".join(c for c in command if c.isdigit())
            if alpha and digit:
                command = alpha
                components.insert(0, digit)
        return cls(command, components)


@dataclass
class MuteState:
    """Represents the mute state of the device"""

    is_muted: bool

    def get_next_action(self) -> str:
        """Get the next action for the mute state (The opposite of the current state)"""
        return "Unmute" if self.is_muted else "Mute"

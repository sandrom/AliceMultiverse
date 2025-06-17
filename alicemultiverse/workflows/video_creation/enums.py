"""Enumerations for video creation workflow."""

from enum import Enum


class CameraMotion(Enum):
    """Camera motion types for video generation."""
    STATIC = "static"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    TILT_UP = "tilt_up"
    TILT_DOWN = "tilt_down"
    AUTO = "auto"
    TRACK_FORWARD = "track_forward"
    TRACK_BACKWARD = "track_backward"
    ORBIT_LEFT = "orbit_left"
    ORBIT_RIGHT = "orbit_right"


class TransitionType(Enum):
    """Transition types between shots."""
    CUT = "cut"
    FADE = "fade"
    DISSOLVE = "dissolve"
    WIPE = "wipe"
    MOTION_BLUR = "motion_blur"
    MORPH = "morph"

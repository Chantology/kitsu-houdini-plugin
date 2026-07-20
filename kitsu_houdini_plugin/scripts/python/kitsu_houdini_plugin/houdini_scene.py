"""Houdini-side integration: everything that talks to Houdini itself.

This is the Houdini counterpart of what the Maya version of this plugin did
through `maya.cmds`/`maya.api.OpenMaya` (itself the counterpart of what the
Krita version did through `Krita.instance()`) — kept in one module so the
rest of the code (panel UI, Kitsu API wrapper, task detection, drawover
rendering) stays host-agnostic:

- the current scene's file path (for task detection + version parsing)
- a single-frame viewport capture (what gets published as the preview,
  the equivalent of Maya's "single-frame playblast")
- a viewport background image showing a review drawover (the equivalent
  of Maya's "Feedback_<revision> image plane" — Houdini has no scene node
  for this, it's per-viewport display state, so "replacing" it on
  re-click is automatic and there's nothing to delete afterwards; turning
  __Display Background Image__ off in the viewport hides it)
"""

import glob
import os
import re
import shutil
import tempfile

import hou
import toolutils


class HoudiniSceneError(Exception):
    """A specific, user-facing reason a Houdini-side operation failed."""


def scene_path():
    """Absolute path of the current scene, or None if it was never saved.

    Unlike most hosts, `hou.hipFile.path()` always returns a path (Houdini
    names an unsaved scene "untitled.hip") — `isNewFile()` is what actually
    distinguishes "never saved" from a real file.
    """
    if hou.hipFile.isNewFile():
        return None
    return hou.hipFile.path()


def scene_fps():
    """Frames per second of the scene's current time unit."""
    return hou.fps()


def playback_start():
    """First frame of the playback range — frame 0 of a published preview."""
    return int(hou.playbar.playbackRange()[0])


def playback_range():
    """(start, end) frames of the current playback range, inclusive —
    what a full-scene capture (see capture_viewport_sequence) covers."""
    start, end = hou.playbar.playbackRange()
    return int(start), int(end)


def _scene_viewer():
    try:
        return toolutils.sceneViewer()
    except hou.NotAvailable as exc:
        raise HoudiniSceneError(
            "No Scene Viewer pane tab is open — open one (e.g. a 3D "
            f"viewport) first: {exc}"
        ) from exc


def _active_viewport():
    return _scene_viewer().curViewport()


def viewport_resolution():
    """The active viewport's own pixel resolution (width, height)."""
    width, height = _active_viewport().resolutionInPixels()
    return int(width), int(height)


def capture_viewport(target_path):
    """Flipbook the current frame of the active viewport to `target_path`.

    Uses a single-frame flipbook rather than a renderer so what gets
    published is exactly what the artist sees in the viewport — the
    closest Houdini equivalent of Maya's single-frame playblast.
    """
    viewer = _scene_viewer()
    viewport = viewer.curViewport()
    frame = int(hou.frame())

    # Flipbook always expands a $F-style token in the output path, so
    # capture into a private temp dir with a padded pattern and move the
    # one produced file to the exact requested path, instead of predicting
    # the expanded name ourselves.
    capture_dir = tempfile.mkdtemp(prefix="kitsu_capture_")
    output_pattern = os.path.join(capture_dir, "capture.$F4.png")
    try:
        settings = viewer.flipbookSettings().stash()
        settings.output(output_pattern)
        settings.frameRange((frame, frame))
        settings.outputToMPlay(False)
        viewer.flipbook(viewport, settings)

        produced = sorted(glob.glob(os.path.join(capture_dir, "capture.*")))
        if not produced:
            raise HoudiniSceneError(
                "Flipbook produced no image — make sure a Scene Viewer "
                "pane tab is visible."
            )
        shutil.move(produced[0], target_path)
    finally:
        shutil.rmtree(capture_dir, ignore_errors=True)

    return target_path


def capture_viewport_sequence(directory, start_frame, end_frame):
    """Flipbook the active viewport over [start_frame, end_frame] as a PNG
    sequence into `directory`, for encoding into a full-scene video (see
    video_export.encode_h264_mp4).

    Returns (pattern, first_frame_number, frame_count): `pattern` is a
    printf-style ('%0Nd') path ffmpeg can consume directly. The exact
    zero-padding Houdini's flipbook writes isn't asserted upfront —
    instead the produced files are inspected after the fact and the
    pattern built to match, mirroring the Maya version's same defensive
    approach (not depending on flipbook naming behavior holding true
    across Houdini versions).
    """
    viewer = _scene_viewer()
    viewport = viewer.curViewport()

    output_pattern = os.path.join(directory, "capture.$F4.png")
    settings = viewer.flipbookSettings().stash()
    settings.output(output_pattern)
    settings.frameRange((start_frame, end_frame))
    settings.outputToMPlay(False)
    viewer.flipbook(viewport, settings)

    produced = sorted(glob.glob(os.path.join(directory, "capture.*")))
    if not produced:
        raise HoudiniSceneError(
            "Flipbook produced no frames — make sure a Scene Viewer pane "
            "tab is visible and the playback range is valid."
        )

    match = re.search(r"\.(\d+)\.(\w+)$", os.path.basename(produced[0]))
    if not match:
        raise HoudiniSceneError(
            f"Unexpected flipbook output file name: {os.path.basename(produced[0])!r}"
        )
    first_number_str, ext = match.groups()
    padding = len(first_number_str)
    pattern = os.path.join(directory, f"capture.%0{padding}d.{ext}")
    return pattern, int(first_number_str), len(produced)


def _bg_view_for_viewport(viewport):
    """The `hou.viewportBGImageView` matching what `viewport` is showing.

    `hou.geometryViewportType` has no separate "looking through a camera"
    value (camera-locked views are still reported as `Perspective`), so
    that distinction is made separately via `viewport.camera()`.
    """
    view_type = viewport.type()
    if view_type == hou.geometryViewportType.Perspective:
        return (
            hou.viewportBGImageView.Camera
            if viewport.camera() is not None
            else hou.viewportBGImageView.Perspective
        )
    # The orthographic views share their names between the two enums
    # (Top/Bottom/Front/Back/Left/Right/UV).
    return getattr(hou.viewportBGImageView, view_type.name())


def _configure_background(background):
    """Shared display settings for both the still-image and sequence cases."""
    background.setAutoPlace(True)
    # "Scale": uniformly scale to fit the viewport without distorting the
    # image, the closest match to Kitsu's own "contain" preview fit.
    background.setImageFitMode(hou.geometryViewportBackgroundImageFitMode.Scale)
    background.setEnvironmentMap(False)
    background.setOpacity(1.0)
    background.setBrightness(1.0)


def set_feedback_background_image(image_path):
    """Show `image_path` as the active viewport's background image.

    Re-clicking the same or a different revision simply replaces it — a
    viewport has only one background image per view, so unlike Maya's
    named image plane nodes there's nothing to accumulate or clean up.
    """
    viewport = _active_viewport()
    settings = viewport.settings()
    bg_view = _bg_view_for_viewport(viewport)

    background = settings.backgroundImage(bg_view, 1)
    background.setImageFile(image_path)
    _configure_background(background)
    settings.setDisplayBackgroundImage(True)


def set_feedback_drawover_sequence(sequence_pattern):
    """Show a per-frame drawover sequence as the viewport's background image.

    `sequence_pattern` is a Houdini `$F`-style path (e.g.
    ".../drawover.$F4.png") whose files are numbered by absolute frame
    number, one per frame in the covered range — annotated frames hold
    their drawover, every other frame holds a blank transparent image
    (the caller is responsible for writing both, see panel.py). Houdini's
    background image naturally re-reads the file matching the current
    frame, so no frame-mapping expression is needed here (unlike Maya's
    image plane, which needed one).
    """
    viewport = _active_viewport()
    settings = viewport.settings()
    bg_view = _bg_view_for_viewport(viewport)

    background = settings.backgroundImage(bg_view, 1)
    background.setImageFile(sequence_pattern)
    _configure_background(background)
    settings.setDisplayBackgroundImage(True)


_BOOKMARK_COLOR = (0.26, 0.71, 0.55)  # teal-green, distinct from Houdini's defaults


def set_timeline_bookmarks(prefix, frame_labels):
    """Create one single-frame animation bookmark per annotated frame.

    `frame_labels` maps a Houdini frame number to the bookmark's label. Any
    existing bookmark whose label starts with `prefix` is removed first,
    so re-clicking for the same revision replaces its markers instead of
    stacking duplicates (same contract as the feedback background image).

    Houdini's animation bookmarks show as colored bands on the playbar
    with their label on hover, are listed under the Bookmarks editor, and
    can be removed the same way (or via `hou.anim.clearBookmarks`).
    """
    for bookmark in hou.anim.bookmarks():
        if (bookmark.name() or "").startswith(prefix):
            hou.anim.removeBookmarks((bookmark,))

    created = []
    for frame, label in sorted(frame_labels.items()):
        bookmark = hou.anim.newBookmark(label, frame, frame + 1)
        bookmark.setColor(hou.Color(_BOOKMARK_COLOR))
        created.append(bookmark)
    return created

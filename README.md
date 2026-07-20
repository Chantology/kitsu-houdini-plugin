# Kitsu Houdini Plugin

A Houdini Python Panel that connects to a self-hosted Kitsu/Zou (CG Wire)
instance: it detects the task a scene belongs to from its folder
structure, shows feedback/comments (including drawover attachments), and
publishes new versions with a comment and status change.

This is the Houdini counterpart of the
[Kitsu Maya Plugin](../kitsu-maya-plugin) — same features, same UI
layout, same Kitsu-side behavior, with the host-specific pieces swapped
for their Houdini equivalents (viewport flipbook capture instead of a
Maya playblast, viewport background images instead of Maya image
planes).

All Kitsu/Zou protocol handling (auth, endpoints, uploads/downloads) is
delegated to CGWire's official [`gazu`](https://github.com/cgwire/gazu)
Python client. Houdini's bundled Python (hython) doesn't have `gazu` or
`requests`, so both are vendored inside
`kitsu_houdini_plugin/scripts/python/kitsu_houdini_plugin/vendor/` along
with `requests`'s own dependencies (`urllib3`, `certifi`, `idna`). No
manual `pip install` into Houdini's Python is required.

Built and tested against Houdini 20.5 (PySide2). The Qt binding is
imported through Houdini's own `hutil.PySide` shim rather than a fixed
`PySide2`/`PySide6` import, so it should keep working unchanged on a
future Qt6 Houdini build.

## Folder layout

Everything under `kitsu_houdini_plugin/` is exactly what gets copied into
Houdini's user preferences folder — a standard Houdini "plugin folder"
added to `$HOUDINI_PATH` via a small [package
file](https://www.sidefx.com/docs/houdini/ref/plugins.html):

```
packages/
  kitsu_houdini_plugin.json          # package descriptor Houdini reads at startup
kitsu_houdini_plugin/                # the plugin folder (added to $HOUDINI_PATH)
  python_panels/
    kitsu_houdini_plugin.pypanel     # registers the "Kitsu" Python Panel interface
  toolbar/
    kitsu_houdini_plugin.shelf       # "Kitsu" shelf tab: Open Kitsu Panel + Publish Capture
  config/
    Icons/
      kitsu_houdini_plugin.png      # shelf/panel icon: the Kitsu fox logo (32x32, plus @2x for HiDPI)
      kitsu_houdini_plugin@2x.png
  scripts/
    python/
      kitsu_houdini_plugin/          # the plugin package
        __init__.py
        qt.py                       # Qt binding shim (via Houdini's own hutil.PySide)
        panel.py                    # the panel UI (login, task, feedback, publish)
        collapsible_section.py      # collapsible header used for each panel section
        kitsu_api.py                # wraps vendored gazu for login/tasks/comments
        houdini_scene.py            # scene path, viewport capture, background images, bookmarks
        task_detection.py           # resolves asset/shot task from folder structure
        shelf integration           # see toolbar/kitsu_houdini_plugin.shelf
        publish_capture.py          # "Publish Capture" shelf tool: full-scene video export + Kitsu upload
        capture_dialog.py           # status/comment dialog shown before a Publish Capture export
        capture_naming.py           # studio review-file naming convention for Publish Capture
        video_export.py             # PNG sequence -> H.264 MP4 via ffmpeg
        settings.py                 # persists server URL / email / project id / collapsed sections
        versioning.py               # parses "_v###" filename versions
        annotations.py              # renders Kitsu drawovers (Fabric.js shapes) locally
        video_annotations.py        # per-frame drawover extraction for video previews
        vendor/
          gazu/                    # vendored CGWire gazu client
          requests/, urllib3/,     # vendored gazu runtime dependencies
          certifi/, idna/
          typing_extensions.py     # shim (Houdini's Python already has typing.Literal)
```

Unlike Maya's `.mod` file, the package file (`kitsu_houdini_plugin.json`)
is tiny — it just points `$HOUDINI_PATH` at the plugin folder, and
Houdini auto-discovers `python_panels/`, `toolbar/`, `config/Icons/`, and
`scripts/python/` inside it by their standard folder names:

```json
{
    "hpath": "$HOUDINI_USER_PREF_DIR/kitsu_houdini_plugin"
}
```

## Installation

### Automatically

Run the installer script for your OS from the repository root — each
copies `kitsu_houdini_plugin/` and `packages/kitsu_houdini_plugin.json`
into Houdini's user preferences folder(s) for you (removing any previous
install of the plugin's own folder first, so nothing stale from an older
version is left behind):

- **Windows**: double-click `install_windows.cmd` (installs into every
  `%USERPROFILE%\houdini<major>.<minor>` folder found, e.g.
  `houdini20.5`).
- **macOS**: double-click `install_mac.command` (installs into every
  `~/houdini<major>.<minor>` or
  `~/Library/Preferences/houdini/<major>.<minor>` folder found). If it
  won't open ("not executable"), run `chmod +x install_mac.command` once
  in Terminal first.
- **Linux**: run `./install_linux.sh` in a terminal (`chmod +x
  install_linux.sh` first if needed). Installs into every
  `~/houdini<major>.<minor>` folder found.

Houdini keys its user preferences folder by **major.minor** version, not
by exact build — so a single install already covers every point release
of that line (e.g. `20.5.550` and `20.5.684` both use `houdini20.5`), but
a different major.minor (e.g. `21.0`) needs its own folder, which the
installer picks up automatically as long as you've launched that Houdini
version at least once (so it exists). If you use a custom
`HOUDINI_USER_PREF_DIR`, pass that folder as an argument to the script
instead, e.g. `install_linux.sh /path/to/your/houdini20.5`.

### Manually

1. Copy the `kitsu_houdini_plugin/` folder into your Houdini user
   preferences folder (create it if it doesn't exist):
   - Windows/Linux: `$HOME/houdini<major>.<minor>` (e.g.
     `houdini20.5`)
   - macOS: `~/houdini<major>.<minor>`, or
     `~/Library/Preferences/houdini/<major>.<minor>` if the former
     doesn't exist
2. Copy `packages/kitsu_houdini_plugin.json` into a `packages/`
   subfolder there (create it if it doesn't exist), e.g.
   `houdini20.5/packages/kitsu_houdini_plugin.json`.
3. Restart Houdini.
4. A **"Kitsu"** shelf tab appears with **Kitsu** (opens the panel) and
   **Publish Capture** buttons. The panel is also always reachable via
   the **+** ("New Pane Tab Type") button on any pane's tab strip, under
   **Kitsu** — pick that to dock it anywhere, like the Parameter Editor
   or Outliner.

### If the plug-in fails to load

Open Houdini's **Python Shell** pane or the console it was launched
from — a traceback from a failed load prints there. Since `gazu` and
`requests` (plus their dependencies) are fully vendored, the panel
should build regardless of what's installed in Houdini's Python —
importing them is deferred until you actually click **Login**, so a
problem there only fails the login attempt with a specific message, not
the whole panel.

If you get an error like `module 'gazu.xyz' has no attribute '...'` for
something this plugin clearly uses, it means some *other* `gazu` package
is being found before this plugin's own vendored copy — e.g. a leftover
`pip install gazu` into Houdini's Python, or a studio-wide `PYTHONPATH`
entry pointing at a different version. The vendored copy is always
inserted first on `sys.path`, and every Login attempt also clears out
any *already-imported* `gazu` that didn't come from this plugin's own
`vendor/` folder — so this should self-heal on your very next Login
without needing to restart Houdini. If it still doesn't, run
`import gazu; print(gazu.__file__)` in the Python Shell — if the path
shown isn't inside this plugin's own `vendor/gazu/`, that confirms
something is re-importing its own `gazu` even more aggressively and
points at what to remove from your Python environment.

## Using the plugin

Each section (Connection, Task, Feedback, Publish) has a clickable title
that collapses/expands it — handy for reclaiming vertical space once you
don't need, say, the Connection or Task section visible anymore.
Collapsed/expanded state is remembered per section across Houdini
restarts.

1. Open the Kitsu panel and enter your server URL (e.g.
   `https://kitsu.yourstudio.com`), email + password (or an API token),
   and the project ID, then click **Login**.
   - The server URL is normalized to end in `/api` automatically (gazu's
     convention), matching how the official CGWire `gazu` client expects
     the host to be configured.
   - If login fails, the panel shows the *specific* reason (rejected
     credentials, a 404 route, a server error, etc.) instead of a generic
     failure — if you get a 404, it usually means the Zou API for this
     Kitsu instance lives at a different host/path than the web UI, and
     you'll need to ask whoever administers the server for the correct
     API URL.
   - Once logged in, a **"Welcome, `<your name>`"** greeting and your
     Kitsu avatar appear at the bottom of the Connection section, below
     the API token field — confirming at a glance which account you're
     connected as. Accounts without an avatar set on Kitsu just show the
     greeting.
   - Logging in with email/password automatically fills in and saves the
     **API token** field with a fresh refresh token. From then on, **every
     time you open the panel with a server URL, project ID, and that
     token already filled in, it logs in automatically** — no click
     needed at all, not even once. This token isn't your password (which
     is still never saved — see Notes on security) and it eventually
     expires on its own; if it has, the automatic attempt just fails
     quietly (shown in the status line, not a popup) and you log in with
     your password once more, which replaces it with a fresh one and
     resumes auto-login from there. There's nothing to manage by hand.
   - Once logged in, the project's **thumbnail and name** show at the top
     of the **Task** section, above the detected asset/shot breadcrumb —
     so you don't have to keep track of which hash belongs to which
     project, and glancing at the Task section alone tells you both which
     project and which task you're working on. Projects without a
     thumbnail set on Kitsu just show the name. Editing the Project ID
     field afterwards clears both until you log in again, so they never
     show stale info for a different project.
2. Open a scene and click **Detect Task** — the plugin resolves the
   Kitsu task from the scene's folder structure (folder names matched
   case-insensitively against Kitsu's names). Both **asset** and **shot**
   contexts are supported:

   | Context | Expected folder layout above the file |
   | --- | --- |
   | Asset | `.../<AssetType>/<AssetName>/<TaskType>/file.hip`<br>e.g. `assets/characters/Hero/modeling/Hero_modeling_v002.hip` |
   | Shot (movie / short / commercial) | `.../<Sequence>/<Shot>/<TaskType>/file.hip`<br>e.g. `shots/seq010/sh0100/animation/sh0100_animation_v003.hip` |
   | Shot (TV series, with episodes) | `.../<Episode>/<Sequence>/<Shot>/<TaskType>/file.hip`<br>e.g. `episodes/ep01/seq010/sh0100/animation/sh0100_animation_v003.hip` |

   The plugin decides **asset vs. shot** from an anchor folder anywhere in
   the path (case-insensitive): a folder named `assets`/`asset` means
   asset context, while `shots`/`shot`/`sequences`/`sequence`/`episodes`/
   `episode` means shot context. With no such anchor it assumes an asset
   (unchanged from before). It decides whether shots sit **under
   episodes** from the *project itself* — only a Kitsu `tvshow` production
   has episodes, so for a TV-show project the extra `<Episode>` level is
   required and for a movie/short/commercial it must be absent. The
   detected breadcrumb (e.g. `seq010 / sh0100 / animation` or
   `ep01 / seq010 / sh0100 / animation`) is shown in the Task section,
   along with the task's current **Status**, **Due Date** (both "Not set"
   / "Unknown" if Kitsu has none), and a **timesheet** for logging hours
   worked on this task today: a slider (0-12h, in half-hour steps),
   **1h / 4h / 8h** preset buttons that jump the slider straight to that
   value, and a **Log Time** button that submits it — matching Kitsu's
   own web timesheet slider. Submitting **sets** the day's total rather
   than adding to it (so it's safe to re-submit after adjusting the
   slider), and detecting a task you've already logged time on today (for
   the first time this session) starts the slider at that value instead
   of resetting to 0 — capped visually to 12h if you logged more than
   that elsewhere (e.g. on the web), with the true total still shown in
   the **Time logged today** line above the slider.

   The slider also **auto-advances** on its own: from the moment a task
   is first detected, it counts up in real time from whatever's already
   logged today, so after an hour of work it reads "1h" without you
   touching anything — click **Log Time** whenever you want to confirm
   it, or drag the slider (or click a preset) first to adjust the value,
   which pauses the auto-advance until it's restarted (see below), so it
   never fights a value you just set on purpose. While auto-advancing,
   the value label shows "(auto)" next to the time so it's clear it's
   still counting; that label switches to a plain value the moment you
   take control. This is a lightweight timer (checking every 30 seconds)
   piggybacking on Houdini's own UI event loop — no separate thread, no
   measurable CPU cost.

   Clicking **Detect Task** again for the *same* task — which is the
   common case, since it's easy to click it more than once out of habit
   — leaves the tracker completely alone, running or paused, exactly as
   it was: it does **not** reset the clock or discard a manual override.
   Only a genuine change of task (a different shot/asset) or a successful
   **Log Time** restarts the tracker, in each case from that task's own
   already-logged total.
3. Existing comments for that task show up in the **Feedback** section,
   each listed as `<STATUS> - <name>: <comment text>` — e.g.
   `WIP - Jane Doe: first initial test` — showing the status the comment
   set the task to (in caps, matching Kitsu's own status-badge style) and
   who wrote it. Older comments with no associated status just show
   `<name>: <comment text>`. If the comment introduced a **new published
   revision** (i.e. it has a preview attached, the same one shown below
   when you select it), it's prefixed with that revision number too:
   `Revision 5 - WIP - Jane Doe: first initial test`.

   The list also **auto-refreshes in the background** every 60 seconds
   while a task is detected, so a new comment or revision someone else
   posts on Kitsu shows up without clicking Detect Task — but only when
   something actually changed: if nothing new came in, the list is left
   completely alone, and if you have a comment selected when a new one
   does arrive, that same comment stays selected afterward rather than
   losing your place. A background check that fails (e.g. a brief
   connection drop) is silent and just retries on the next tick, so it
   never interrupts you with an error for something that will very likely
   succeed 60 seconds later. Select a comment to see, below the list:
   - Its **checklist**, if it has one, as tickable checkboxes — ticking or
     unticking one syncs that change back to Kitsu immediately. If the
     sync fails (e.g. connection drop), the checkbox reverts and you'll
     get a warning, so the UI never shows a checked state that isn't
     actually saved on the server.
   - Its **revisions**, embedded inline, with any Kitsu **drawover**
     (annotations drawn during a review session — shapes, arrows,
     freehand markup, text notes) composited directly on top of the
     image, labeled "(with drawover)". If a revision has a drawover,
     click **Show in Viewport Background** to show it in the active
     viewport as its background image. Clicking it again (for the same
     or a different revision) simply replaces it — a viewport has only
     one background image, so there's nothing to clean up afterwards;
     turn off **Display Background Image** in the viewport's own
     display options to hide it.
   - Its **attachments** (other reference images), embedded inline — no
     separate download step needed for viewing. Click **Save
     Attachment(s)** if you want a local copy.

### Frame-based feedback on video revisions

When a revision is a **video** (e.g. a published preview), reviewers in
Kitsu draw their notes on specific frames, and the panel shows the
revision as its thumbnail with the list of annotated frames plus two
buttons:

- **Add Timeline Bookmarks** creates a single-frame animation bookmark on
  every annotated frame — colored bands on the playbar, labeled `Kitsu
  r<revision> f<frame>`, also listed in Houdini's Bookmarks editor.
  Re-clicking replaces that revision's bookmarks instead of stacking
  duplicates; delete them from the Bookmarks editor when you're done
  with them.
- **Show Drawovers in Viewport** sets the active viewport's background
  image to a numbered image sequence that shows each frame's drawover
  **only on that exact frame** — every frame in the covered range gets
  its own file (annotated frames get the composited markup, every other
  frame gets a fully transparent image), so scrubbing the timeline shows
  the reviewer's strokes exactly on the frames they were drawn on and
  nothing on the rest. Re-clicking replaces the background image; turn
  off **Display Background Image** in the viewport when done.

Frame mapping: Kitsu counts video frames from 0, and frame 0 of a
published preview is the first frame of your playback range — so
bookmarks/sequence frames land at `playback start + Kitsu frame`. If you
publish previews of a different range than you work in, set the
playback range to the published range before adding bookmarks. The
frame⇄time conversion uses the Kitsu production's fps, falling back to
the scene's fps if the production doesn't define one.

4. To publish, pick a status, write a comment, and click **Publish** — the
   plugin captures the active viewport at the current frame (a
   single-frame flipbook, so what you see is what gets published) and
   publishes it as a proper Kitsu **preview/revision** (not just a plain
   comment attachment), so it shows up in the task's version history and
   can be drawn over in review sessions. If the scene filename ends in a
   `_v###`-style version (e.g. `Hero_modeling_v002.hip`), that number is
   used as the revision number on Kitsu too, so your local version and
   the Kitsu revision always match up.

   **Variations**: before clicking Publish, queue extra images with
   **+ From Viewport** (captures the current view right now, e.g. after
   toggling a display flag or a different render) or **+ From File...**
   (browse for an existing image, e.g. exported from another app) —
   listed above the Publish button, with **Remove Selected** to drop one
   before publishing. These are uploaded alongside the main capture as
   additional preview files on the **same revision/comment** (Kitsu's own
   multi-preview-per-revision support) — not separate revisions and not
   plain comment attachments, so they show up as flippable variations on
   that one revision, e.g. a beauty pass next to a wireframe or clay
   render of the same version. The queue is cleared as each variation
   uploads successfully; if the main publish fails, none are touched, and
   if publishing succeeds but a particular variation's upload fails, only
   that one stays queued (with a clear warning) so it's easy to retry
   without re-adding it.

### Publish Capture: full-scene video export

The Publish button above exports a single frame. For a full-scene H.264
MP4 of your current playback range, published to Kitsu as a new
revision, click **Publish Capture** on the **Kitsu** shelf tab.

1. **Requirements**: the panel must already be open, logged in, and have
   a task detected (Publish Capture reuses that state rather than asking
   you to log in again), and the scene must be saved. **`ffmpeg` must be
   on your system PATH** — Houdini's own flipbook writes an image
   sequence, not a video file directly, so this renders a PNG sequence
   via a flipbook and encodes it with `ffmpeg`. Most studios already have
   `ffmpeg` installed for exactly this; if it's missing, the error
   message says so explicitly. Get it from
   [ffmpeg.org](https://ffmpeg.org/) if you don't have it.
2. A small dialog asks for a **task status** and a **comment**, the same
   two fields the panel's own Publish section asks for.
3. The full current playback range is captured at the scene's frame
   rate, encoded to H.264, and saved locally, then **published to Kitsu
   as a new revision** on the detected task with the status/comment from
   the dialog — the video shows up in the task's version history exactly
   like the single-frame Publish button's PNG does. If the upload itself
   fails (e.g. a dropped connection), the video stays on disk and the
   error message says exactly where, so nothing is lost — only the
   exported file is deleted or wasted.

**Output**: saved as `<scene folder>/capture/<name>.mp4`. The file name
follows:

```
<Show>[_<Episode>]_<Sequence>_<Shot>_v<version>_<Initial><Lastname>.mp4
```

e.g. `MyShow_seq010_sh0100_v003_JDoe.mp4`, or with an episode for a TV
show, `MyShow_ep01_seq010_sh0100_v003_JDoe.mp4`. For an asset scene
(which has no episode/sequence/shot), the analogous fallback substitutes
the asset type and asset name, e.g. `MyShow_characters_Hero_v003_JDoe.mp4`.
The version number comes from the scene's own `_v###` filename (omitted
if there isn't one, and also used as the Kitsu revision number, matching
the single-frame Publish button's convention); the trailing name is the
logged-in Kitsu user's first initial + last name (e.g. "John Doe" →
"JDoe"), falling back to splitting `full_name` if an account has no
separate first/last name set.

Naming conventions are one of the most studio-specific parts of a
pipeline, so this is kept in its own small function — swap
`capture_naming.py`'s `build_capture_filename` if yours differs, without
touching the render/encode/upload logic in `publish_capture.py`.

### Drawover rendering limitations

Drawover markup is Kitsu's own Fabric.js canvas data (rectangles,
circles, arrows, freehand strokes, text notes), re-drawn locally in
[annotations.py](kitsu_houdini_plugin/scripts/python/kitsu_houdini_plugin/annotations.py)
with `QPainter` — this covers everything Kitsu's own drawover toolbar
produces. Not (yet) supported: the eraser tool's mask, nested groups,
and rotation on freehand strokes/lines/arrows specifically (rotation on
rectangles/circles/text works). A shape that can't be drawn is skipped
rather than breaking the rest of the drawover.

## Differences from the Maya version

Houdini's viewport doesn't have a scene-graph node for "an image plane
attached to a camera" the way Maya does, so the drawover-viewing feature
is built on Houdini's own **viewport background image** instead (per
[`GeometryViewportBackground`](https://www.sidefx.com/docs/houdini/hom/hou/GeometryViewportBackground.html)):

- There's no `Feedback_<revision>` node to find and delete afterwards —
  a viewport only ever has one background image, so showing a new one
  automatically replaces the last, and hiding it is just the viewport's
  own **Display Background Image** toggle.
- The per-frame video drawover sequence doesn't need Maya's custom
  frame-mapping expression — Houdini's background image already re-reads
  whichever numbered file matches the current frame, so the plugin just
  writes one file per frame (blank for unannotated frames) and points the
  background image at that sequence.
- Publishing (both the single-frame Publish button and Publish Capture's
  full-scene video) captures via a **flipbook** (Houdini's
  screenshot/preview-render mechanism) rather than a Maya playblast.
- Maya's "Add Shelf Button" menu action has no Houdini equivalent because
  it isn't needed: Houdini's shelf tool (`toolbar/kitsu_houdini_plugin.shelf`)
  is installed declaratively alongside the rest of the plugin and is
  already there — with both **Kitsu** and **Publish Capture** buttons —
  the moment the package loads, with nothing to add by hand.

## Notes on security

The account password is never written to disk — only the server URL,
email, project ID, and API token are persisted (via `QSettings`) across
Houdini restarts.

The API token field holds a **refresh token**, not your password: after
logging in with email/password, this plugin saves the refresh token
Kitsu's own auth system issued for that login, so future logins can use
it instead of typing the password again (see step 1 above) — you can
also paste one in yourself if you already have one. Unlike a password,
it's revocable and time-limited (expiring on its own after however long
the server allows, independent of anything this plugin controls); if it
ever expires or is revoked, logging in with email/password once more
simply gets and saves a fresh one. It's stored in plain text the same
way the other non-secret fields are, so treat it with the same care
you'd give any bearer credential — anyone with it can act as your
account until it expires.

#!/bin/bash
# Installs the Kitsu Houdini Plugin into Houdini's user preferences
# folder(s) on macOS.
#
# Usage: ./install_mac.command [custom user pref folder]
#   Double-click to run with no arguments: auto-detects every
#   "houdini<major>.<minor>" preferences folder under $HOME and under
#   $HOME/Library/Preferences/houdini (Houdini's two possible default
#   HOUDINI_USER_PREF_DIR locations on macOS) and installs into all of
#   them found. Houdini keys this folder by major.minor version, so e.g.
#   20.5.550 and 20.5.684 already share one folder ("houdini20.5") — only
#   a different major.minor (e.g. 21.0) needs its own. If you use a
#   custom HOUDINI_USER_PREF_DIR, pass that folder as an argument instead.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_PLUGIN="$SCRIPT_DIR/kitsu_houdini_plugin"
SOURCE_PACKAGE="$SCRIPT_DIR/packages/kitsu_houdini_plugin.json"

if [ ! -f "$SOURCE_PLUGIN/python_panels/kitsu_houdini_plugin.pypanel" ]; then
    echo "ERROR: $SOURCE_PLUGIN not found or incomplete."
    echo "Run this script from the repository root, or check your checkout."
    read -r -p "Press Enter to close this window..." _
    exit 1
fi

TARGETS=()
if [ "${1:-}" != "" ]; then
    TARGETS+=("$1")
else
    for dir in "$HOME"/houdini[0-9]*.[0-9]* "$HOME"/Library/Preferences/houdini/[0-9]*.[0-9]*; do
        [ -d "$dir" ] && TARGETS+=("$dir")
    done
fi

if [ "${#TARGETS[@]}" -eq 0 ]; then
    echo "ERROR: No Houdini user preferences folder found."
    echo "Launch Houdini at least once to create it, then re-run this"
    echo "script — or pass your HOUDINI_USER_PREF_DIR as an argument."
    read -r -p "Press Enter to close this window..." _
    exit 1
fi

for target in "${TARGETS[@]}"; do
    echo "Installing Kitsu Houdini Plugin"
    echo "  From: $SOURCE_PLUGIN"
    echo "  To:   $target/kitsu_houdini_plugin"
    echo

    mkdir -p "$target/packages"

    # Remove any previous install of this plugin's own folder first, for a
    # clean, idempotent install that never leaves stale files from an
    # older version behind.
    rm -rf "$target/kitsu_houdini_plugin"

    cp -R "$SOURCE_PLUGIN" "$target/kitsu_houdini_plugin"
    cp "$SOURCE_PACKAGE" "$target/packages/kitsu_houdini_plugin.json"
done

echo
echo "Done. Restart Houdini - the \"Kitsu\" shelf tool and Python Panel"
echo "interface should be available (also reachable via the \"+\" New Pane"
echo "Tab Type menu of any pane)."
read -r -p "Press Enter to close this window..." _

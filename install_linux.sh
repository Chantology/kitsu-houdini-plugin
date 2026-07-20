#!/bin/bash
# Installs the Kitsu Houdini Plugin into Houdini's user preferences
# folder(s) on Linux.
#
# Usage: ./install_linux.sh [custom user pref folder]
#   Run with no arguments to auto-detect every "houdini<major>.<minor>"
#   preferences folder under $HOME (Houdini's default
#   HOUDINI_USER_PREF_DIR) and install into all of them. Houdini keys
#   this folder by major.minor version, so e.g. 20.5.550 and 20.5.684
#   already share one folder ("houdini20.5") — only a different
#   major.minor (e.g. 21.0) needs its own. If you use a custom
#   HOUDINI_USER_PREF_DIR, pass that folder as an argument instead.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_PLUGIN="$SCRIPT_DIR/kitsu_houdini_plugin"
SOURCE_PACKAGE="$SCRIPT_DIR/packages/kitsu_houdini_plugin.json"

if [ ! -f "$SOURCE_PLUGIN/python_panels/kitsu_houdini_plugin.pypanel" ]; then
    echo "ERROR: $SOURCE_PLUGIN not found or incomplete."
    echo "Run this script from the repository root, or check your checkout."
    exit 1
fi

TARGETS=()
if [ "${1:-}" != "" ]; then
    TARGETS+=("$1")
else
    for dir in "$HOME"/houdini[0-9]*.[0-9]*; do
        [ -d "$dir" ] && TARGETS+=("$dir")
    done
fi

if [ "${#TARGETS[@]}" -eq 0 ]; then
    echo "ERROR: No \$HOME/houdini<version> folder found."
    echo "Launch Houdini at least once to create it, then re-run this"
    echo "script — or pass your HOUDINI_USER_PREF_DIR as an argument."
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

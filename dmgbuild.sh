#!/bin/sh
# Create a folder (named dmg) to prepare our DMG in (if it doesn't already exist).
mkdir -p dist/dmg
# Empty the dmg folder.
rm -rf dist/dmg/*
# Copy the app bundle to the dmg folder.
cp -r "dist/IP-Saver.app" dist/dmg
# If the DMG already exists, delete it.
test -f "dist/IP-Saver.dmg" && rm "dist/IP-Saver.dmg"
create-dmg \
  --volname "IP-Saver" \
  --volicon "assets/ip-saver.icns" \
  --window-pos 200 120 \
  --window-size 600 300 \
  --icon-size 100 \
  --icon "IP-Saver.app" 175 120 \
  --hide-extension "IP-Saver.app" \
  --app-drop-link 425 120 \
  "dist/IP-Saver.dmg" \
  "dist/dmg/"

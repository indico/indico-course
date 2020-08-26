#!/bin/sh

# Set up Python deps
rm -rf .venv
python3 -mvenv .venv
. ./.venv/bin/activate
pip install -r requirements.txt

# Set up JS deps
npm i

# Get Indico Docs
git submodule init

# Copy images
cp -R indico-user-docs/docs/assets src/course/en/images

rm src/course/en/{articles,blocks,components,contentObjects}.json
# Convert docs to adapt
python md_to_adapt.py indico-user-docs . \
    Categories \
    Lectures \
    Meetings \
    Conferences \
    "Room Booking"\
    "Event Surveys" \
    "Other Features/Webcast/Recording"

# Build actual HTML
npx grunt adapt build

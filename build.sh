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
git submodule update

# Copy images
cp -R indico-user-docs/docs/assets src/course/en/images

# Convert docs to adapt
python md_to_adapt.py --replace indico-user-docs .

# Install adapt components
npx adapt install
# Build actual HTML
npx grunt build

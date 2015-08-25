mkvirtualenv tidiscordbot
git clone https://github.com/Rapptz/discord.py.git
cd discord.py
echo -en "include README.md\ninclude LICENSE" > MANIFEST.in
pip install -e .

Good to go!
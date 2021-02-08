"""
Copyright (C) 2021  Marvin Lenk

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import json
import os, platform

class scryConf():
    default_settings = {
        'window': {
            'width': 1024,
            'height': 700,
            'xoffset': 0,
            'yoffset': 0,
            'zoomed' : None,
            'deckdir': os.getcwd()
            },
        'preview': {
            'prevtype': 'normal',
            'scale': 36
            },
        'searchflags':{
            'unique': 'prints',
            'game': 'paper',
            'order': 'released',
            'strict': 'True',
            'lang': 'en',
            'promo': ''
            }
        }

    settings = {}

    path = ''

    def checksetting(self, key1, key2=None):
        """Checks if a setting is present and adds the default value if not."""
        if key2 is None:
            try:
                self.settings[key1]
            except KeyError:
                self.settings[key1] = self.default_settings[key1]
                return False
        else:
            try:
                self.settings[key1][key2]
            except KeyError:
                self.settings[key1][key2] = self.default_settings[key1][key2]
                return False

        return True

    def completesetting(self):
        for key1 in self.default_settings:
            if self.checksetting(key1):
                for key2 in self.default_settings[key1]:
                    self.checksetting(key1, key2)

        return True

    def __init__(self, confpath=None):
        if confpath is None:
            os.makedirs(self.basepath(), exist_ok=True)
            self.path = self.standardpath()
        else:
            self.path = confpath

        if not os.path.isfile(self.path):
            print('The config file "' + self.path + '" does not exist, creating new file with default settings.')
            self.settings = self.default_settings
            self.save(self.path)
        else:
            self.load(self.path)

    def basepath(self):
        """Returns path to standard config folder."""
        base_path = os.getenv('APPDATA') + os.sep if platform.system() == 'Windows' else os.path.expanduser('~/.')
        return base_path + 'Scryfall_Downloader'

    def standardpath(self):
        """Returns path to standard config file."""
        return self.basepath() + os.sep + 'config.json'

    def load(self, confpath=None):
        """"Loads config file."""
        if confpath is None:
            path = self.path
        else:
            if os.path.isfile(confpath):
                path = confpath
            else:
                print("No valid file: " + confpath)
                raise ValueError

        with open(path, 'r') as fp:
            self.settings = json.load(fp)

        self.completesetting()

    def save(self, confpath=None):
        """Saves config file with specified settings. This will overwrite without raising!"""
        path = self.path if confpath is None else confpath

        with open(path, 'w') as fp:
            json.dump(self.settings, fp, indent=4)
        return

    def get_window(self, key, default=False):
        """Get window attribute by key."""
        return self.default_settings['window'][key] if default else self.settings['window'][key]

    def set_window(self, key, val):
        """Set window attribute 'key' to 'val'."""
        self.settings['window'][key] = val
        return True

    def get_preview(self, key, default=False):
        """Get preview image attribute by key."""
        return self.default_settings['preview'][key] if default else self.settings['preview'][key]

    def set_preview(self, key, val):
        """Set preview image attribute 'key' to 'val'."""
        self.settings['preview'][key] = val
        return True

    def get_searchflag(self, key, default=False):
        """Get search flag by key."""
        return self.default_settings['searchflags'][key] if default else self.settings['searchflags'][key]

    def set_searchflag(self, key, val):
        """Set search flag 'key' to 'val'."""
        self.settings['searchflags'][key] = val
        return True


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Show chromecast status"""


import argparse
import time
from dataclasses import dataclass
from typing import Iterator, List, Text

import pychromecast

DEFAULT_FMT = '{p.name}: {p.artist} - {p.title}'


@dataclass
class Player:
    _cast: pychromecast.Chromecast
    _controller: pychromecast.controllers.media.MediaController

    @property
    def name(self):
        return self._cast.name

    @property
    def album(self):
        return self._controller.status.album

    @property
    def artist(self):
        return self._controller.status.artist

    @property
    def title(self):
        return self._controller.status.title

    @property
    def is_active(self):
        return self._controller.is_active

    @property
    def player_state(self):
        return self._controller.status.player_state

    @property
    def status(self):
        status = self._controller.status.player_state
        return {
            'PLAYING': '> ',
            'PAUSED': '|| ',
            'IDLE': '# ',
            'BUFFERING': '8 ',
        }.get(status, status)

    @property
    def unicode_status(self):
        status = self._controller.status.player_state
        return {
            'PLAYING': '▶️  ',
            'PAUSED': '⏸️  ',
            'IDLE': '⏹️  ',
            'BUFFERING': '⌛ ',
        }.get(status, status)

    def play(self):
        return self._controller.play()

    def pause(self):
        return self._controller.pause()


class StatusMonitor:

    def __init__(self, chromecasts: List[pychromecast.Chromecast] = None):
        self.players = []
        for cast in chromecasts or pychromecast.get_chromecasts():
            controller = pychromecast.controllers.media.MediaController()
            cast.register_handler(controller)
            cast.wait()
            self.players.append(Player(cast, controller))

    @property
    def active_players(self) -> List[Player]:
        return [player for player in self.players
                if player.is_active and player.player_state != 'UNKNOWN']

    def scroller(self, fmt: Text) -> Iterator[Text]:
        while True:
            for player in self.active_players:
                yield fmt.format(p=player)
            # If nothing is active we never yield, so pause for a moment.
            if not self.active_players:
                yield ''
                time.sleep(1)

def main():
    """Run main."""
    parser = argparse.ArgumentParser(description='Show local chromecast status')
    parser.add_argument(
        '--period', metavar='SECONDS', default=10, type=int,
        help=('Duration to display current status before cycling to next'
              ' active chromecast.'))
    parser.add_argument(
        '--format', '-f', metavar='FORMAT', default=DEFAULT_FMT,
        help='Format string for status.')
    parser.add_argument(
        '--unicode', '-u', action='store_true',
        help='Use unicode glyphs for {p.status} in format.')

    args = parser.parse_args()

    fmt = args.format
    if args.unicode:
      fmt = fmt.replace('{p.status}', '{p.unicode_status}')

    s = StatusMonitor()
    for status in s.scroller(fmt):
        print(status, flush=True)
        time.sleep(args.period)
    return 0

if __name__ == '__main__':
    try:
        main()
    finally:
        # Ensure final output is empty
        print('', flush=True)

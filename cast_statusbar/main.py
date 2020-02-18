#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Show chromecast status"""


import argparse
import time
from dataclasses import dataclass
from typing import Iterator, List, Text

import pychromecast

DEFAULT_FMT = '{p.status_unicode}{p.cast.name}: {p.artist} - {p.title}'


@dataclass
class Player:
    _cast: pychromecast.Chromecast
    _controller: pychromecast.controllers.media.MediaController

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
    def status_unicode(self):
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
            self.players.append(Player(cast=cast, controller=controller))

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
                time.sleep(1)

def main():
    """Run main."""
    parser = argparse.ArgumentParser(description='Show local chromecast status')
    parser.add_argument(
        '--format', '-f', metavar='FORMAT', default=DEFAULT_FMT, type=str,
        help='Format string for status')
    parser.add_argument(
        '--period', metavar='SECONDS', default=10, type=int,
        help=('Duration to display current status before cycling to next'
              ' active chromecast.'))
    args = parser.parse_args()

    s = StatusMonitor()
    prev = ''
    for status in s.scroller(args.format):
        if prev != status:
            print(status)
            prev = status
        time.sleep(args.period)
    return 0

if __name__ == '__main__':
    main()

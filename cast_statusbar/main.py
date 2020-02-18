#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Show chromecast status"""


import argparse
import signal
import sys
import time
from dataclasses import dataclass
from typing import Iterator, List, Text, Tuple

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

    def status_rotator(self, fmt: Text) -> Iterator[Text]:
        while True:
            for player in self.active_players:
                yield fmt.format(p=player)
            # If nothing is active we never yield, so pause for a moment.
            if not self.active_players:
                yield ''
                time.sleep(1)


def window_marquee(text: Text, width=10) -> Iterator[Tuple[bool, Text]]:
    """Scroll the text back and forth.

    Yields: Tuple[bool, Text]
        bool: The text is currently at one extreme or the other.
        Text: The scrolled text.
    """
    max_i = len(text) - width
    i = 1
    while True:
        while i:
            i -= 1
            yield (i == 0, text[i:i+width])
        while i < max_i:
            i += 1
            yield (i == max_i, text[i:i+width])


def run(args):
    """Run main."""
    fmt = args.format
    if args.unicode:
      fmt = fmt.replace('{p.status}', '{p.unicode_status}')

    s = StatusMonitor()
    prev = None
    marquee = None
    for status in s.status_rotator(fmt):
        start = time.time()
        if status != prev:
            prev = status
            marquee = window_marquee(status, width=args.width)
        for endpoint, output in marquee:
            print(output, flush=True)
            if endpoint:
                time.sleep(args.marquee_pause)
            else:
                time.sleep(1/args.marquee_speed)
            if time.time() - start > args.period:
                break
    return 0


def main():
    parser = argparse.ArgumentParser(description='Show local chromecast status')
    parser.add_argument(
        '--period', metavar='SECONDS', default=10, type=int,
        help=('Duration to display the status before cycling to the'
              ' next active chromecast.'))
    parser.add_argument(
        '--format', '-f', metavar='FORMAT', default=DEFAULT_FMT,
        help='Format string for status.')
    parser.add_argument(
        '--unicode', '-u', action='store_true',
        help='Use unicode glyphs for {p.status} in format.')
    parser.add_argument(
        '--width', type=int, default=85,
        help='Output at most `width` unicode codepoints per line.')
    parser.add_argument(
        '--marquee_speed', type=float, metavar='CHARACTERS / SECOND',
        default=5, help='Number of characters to scroll per second')
    parser.add_argument(
        '--marquee_pause', type=float, metavar='SECONDS', default=1,
        help='Number of characters to scroll per second')

    args = parser.parse_args()

    def die(num=0, _frame=None):
        print('', flush=True)
        if num:
            sys.exit()

    # Try to ensure final output is empty
    signal.signal(signal.SIGTERM, die)
    try:
        return run(args)
    finally:
        die()


if __name__ == '__main__':
    main()

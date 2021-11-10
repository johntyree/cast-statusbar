#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Show chromecast status"""


import argparse
import datetime
import gc
import logging
import re
import signal
import sys
import time
from dataclasses import dataclass
from typing import Iterator, List, Optional, Text, Tuple

import humanize  # type: ignore
import pychromecast  # type: ignore

try:
    from twols import trace_with  # type: ignore
except ImportError:
    # No-op decorator
    def trace_with(func=None):
        return lambda x: x

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


@dataclass
class Player:
    _cast: pychromecast.Chromecast
    _controller: pychromecast.controllers.media.MediaController

    @property
    def name(self) -> Text:
        return self._cast.name or ''

    @property
    def app(self) -> Text:
        return self._cast.app_display_name or ''

    @property
    def album(self) -> Text:
        return self._controller.status.album or ''

    @property
    def artist(self) -> Text:
        return self._controller.status.artist or ''

    @property
    def title(self) -> Text:
        return self._controller.status.title or ''

    @property
    def is_active(self) -> Text:
        return self._controller.is_active or ''

    @property
    def player_state(self) -> Text:
        return self._controller.status.player_state or ''

    @property
    def status(self) -> Text:
        status = self._controller.status.player_state or ''
        return {
            'PLAYING': '> ',
            'PAUSED': '|| ',
            'IDLE': '# ',
            'BUFFERING': '8 ',
        }.get(status, status)

    @property
    def unicode_status(self) -> Text:
        status = self._controller.status.player_state or ''
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

    def pretty(self, fmt: Optional[Text]) -> Text:
        if fmt is None:
            fmt = self.name and '{p.name}'
            fmt += self.app and (fmt and ' : ') + '{p.app}'
            fmt += self.artist and (fmt and ' | ') + '{p.artist}'
            fmt += self.title and (fmt and ' - ') + '{p.title}'
        return fmt.format(p=self)


class StatusMonitor:

    def __init__(self, chromecasts: List[pychromecast.Chromecast] = None,
                 ttl=datetime.timedelta(minutes=3)):
        self.ttl = ttl
        self._players: List[Player] = []
        self.discover_time = datetime.datetime.fromtimestamp(0)

    @trace_with(LOGGER.debug)
    def discover(self, chromecasts: List[pychromecast.Chromecast] = None):
        LOGGER.info('Searching for chromecasts.')
        old_players = {p._cast.uuid: p for p in self._players}
        players = []
        for cast in chromecasts or pychromecast.get_chromecasts()[0]:
            player = old_players.get(cast.uuid)
            if player is not None:
                LOGGER.info('Keeping existing player for chromecast: %r', cast)
            else:
                LOGGER.info('Registering chromecast: %r', cast)
                controller = pychromecast.controllers.media.MediaController()
                cast.register_handler(controller)
                cast.wait(5)
                LOGGER.debug('Registered %r', cast)
                player = Player(cast, controller)
            players.append(player)
        self.discover_time = datetime.datetime.now()
        LOGGER.info('Found %d devices: %s',
                    len(players),
                    ', '.join(sorted(p.name for p in players)))
        # Run the GC here to make sure old sockets get closed.
        gc.collect()
        return players

    @property
    def chromecasts(self) -> List[pychromecast.Chromecast]:
        return [p._cast for p in self.players]

    @property
    def should_refresh(self) -> bool:
        return datetime.datetime.now() - self.discover_time > self.ttl

    @property
    def players(self) -> List[Player]:
        if self.should_refresh:
            LOGGER.info('Chromecast list expired, Refreshing...')
            self._players = self.discover(self.chromecasts)
            LOGGER.info('Next refresh in %s', humanize.naturaldelta(self.ttl))
        return self._players

    @property
    def active_players(self) -> List[Player]:
        return [player for player in self.players
                if player.is_active and player.player_state != 'UNKNOWN']

    def status_rotator(self, fmt: Optional[Text],
                       blacklist_regex: Text) -> Iterator[Text]:
        blacklist_matcher = re.compile(blacklist_regex)
        while True:
            for player in self.active_players:
                status = player.pretty(fmt)
                if blacklist_matcher and not blacklist_matcher.search(status):
                    yield status
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
    width = max(0, width)
    max_i = max(0, len(text) - width)
    while True:
        if max_i == 0:
            yield (True, text)
        else:
            for i in range(max_i * 2):
                idx = max_i - abs(max_i - i)
                yield (idx % max_i == 0, text[idx:idx+width])


def run(args):
    """Run main."""
    fmt = args.format
    if args.unicode:
        fmt = fmt.replace('{p.status}', '{p.unicode_status}')
    period = datetime.timedelta(seconds=args.period)

    s = StatusMonitor()
    previous_output = None
    previous_status = None
    marquee = None
    for status in s.status_rotator(fmt, args.blacklist_regex):
        start = datetime.datetime.now()
        if status != previous_status or marquee is None:
            previous_status = status
            marquee = window_marquee(status, width=args.width)
        for endpoint, output in marquee:
            if output != previous_output:
                previous_output = output
                print(output, flush=True)
            if endpoint:
                time.sleep(args.marquee_pause)
            else:
                time.sleep(1/args.marquee_speed)
            if datetime.datetime.now() - start > period and endpoint:
                break
    return 0


def main():
    parser = argparse.ArgumentParser(description='''
        Show local chromecast status in a format suitable for status bars.
    ''')
    parser.add_argument(
        '--period', metavar='SECONDS', default=10, type=int,
        help=('Duration to display the status before cycling to the'
              ' next active chromecast.'))
    parser.add_argument(
        '--format', '-f', metavar='FORMAT', help='Format string for status')
    parser.add_argument(
        '--unicode', '-u', action='store_true',
        help='Use unicode glyphs for {p.status} in format.')
    parser.add_argument(
        '--width', type=int, default=85,
        help='Output at most `width` unicode codepoints per line.')
    parser.add_argument(
        '--marquee_speed', type=float, metavar='CHARACTERS_PER_SECOND',
        default=5, help='Number of characters to scroll per second.')
    parser.add_argument(
        '--marquee_pause', type=float, metavar='SECONDS', default=2,
        help='Number of characters to scroll per second.')
    parser.add_argument(
        '--blacklist-regex', type=str, nargs='+', metavar='REGEX',
        default='^$', help='Ignore strings matching this regex.')
    log_arg_parser = parser.add_mutually_exclusive_group()

    LOG_LEVELS = ('DEBUG', 'INFO', 'WARNING')

    log_arg_parser.add_argument(
        '--log_level', type=str, choices=LOG_LEVELS, default='INFO')
    verbose = log_arg_parser.add_mutually_exclusive_group()
    verbose.add_argument('-v', '--verbose', action='count', default=0,
                         help='Log more.')
    verbose.add_argument('-q', '--quiet', action='count', default=0,
                         help='Log less.')

    args = parser.parse_args()

    verbosity = LOG_LEVELS.index(args.log_level) + args.quiet - args.verbose
    verbosity = max(0, min(len(LOG_LEVELS)-1, verbosity))
    log_level = LOG_LEVELS[verbosity]
    logging.basicConfig(level=log_level)

    def die(num=0, _frame=None):
        print('', flush=True)
        if num:
            sys.exit(num)

    # Try to ensure final output is empty
    signal.signal(signal.SIGTERM, die)
    try:
        return run(args)
    finally:
        die()


if __name__ == '__main__':
    main()

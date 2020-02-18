Caststatus
======

![](example-bar.png)

A read-only tool to show what's playing on local Chromecasts. Intended for use
with status bars.

```
$ cast-statusbar --help
usage: cast-statusbar [-h] [--period SECONDS] [--format FORMAT] [--unicode]
                      [--width WIDTH] [--marquee_speed CHARACTERS_PER_SECOND]
                      [--marquee_pause SECONDS]

Show local chromecast status

optional arguments:
  -h, --help            show this help message and exit
  --period SECONDS      Duration to display the status before cycling to the
                        next active chromecast.
  --format FORMAT, -f FORMAT
                        Format string for status. Default: '{p.name}:
                        {p.artist} - {p.title}'
  --unicode, -u         Use unicode glyphs for {p.status} in format.
  --width WIDTH         Output at most `width` unicode codepoints per line.
  --marquee_speed CHARACTERS_PER_SECOND
                        Number of characters to scroll per second
  --marquee_pause SECONDS
                        Number of characters to scroll per second
```

You might imagine this having two modes, one for piping to a fifo, for
reading into a status bar or somethig, and another that simply outputs a new
status whenever there's a change.

This is the former.

Two systemd unit files are included, expecting that you'll configure your
status bar to read from a FIFO at ~/.config/media-status-fifo.

```bash
$ mkdir -p ~/.config/systemd/user
$ ln -s $PWD/cast-statusbar.socket ~/.config/systemd/user
$ ln -s $PWD/cast-statusbar.service ~/.config/systemd/user
$ systemctl --user enable cast-statusbar
$ systemctl --user start cast-statusbar
```

If you want to be clever and your wm is hooked up through systemd, you could
depend on that instead.

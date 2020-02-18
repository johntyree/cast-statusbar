Caststatus
======

![](example-bar.png)

An experiment in reverse engineering the Griffin PowerMate USB jog
wheel/button on Linux.

A read-only tool to show what's playing on local Chromecasts. Intended for use
with status bars.

You might imagine this having two modes, one for piping to a fifo, for
reading into a status bar or somethig, and another that simply outputs a new
status whenever there's a change.

This is the former.

Two systemd unit files are included, expecting that you'll configure your
status bar to read from a FIFO at ~/.config/media-status-fifo.

```bash
$ mkdir -p ~/.config/media-status-fifo
$ mkdir -p ~/.config/systemd/user
$ ln -s $PWD/cast-statusbar.socket ~/.config/systemd/user
$ ln -s $PWD/cast-statusbar.service ~/.config/systemd/user
$ systemctl --user enable cast-statusbar
$ systemctl --user start cast-statusbar
```

If you want to be clever and your wm is hooked up through systemd, you could
depend on that instead.


# a8, the Abominade IDE #

(c) 2011, PIDA Authors
License GPL v3 (http://www.gnu.org/copyleft/gpl.html)



The One True IDE™, successor to the [http://pida.co.uk/ PIDA IDE]. An ultra-lightweight IDE, that embeds Vim, a terminal emulator, and a file browser and makes them work together.

* [Installation](#installation)

![a8 screenshot](https://lh4.googleusercontent.com/-PtipCpFvTcc/TvpPhtdtTeI/AAAAAAAADI0/tUVBvU3uLAA/s0-d/a8.png)


## Installation ##

⠠⠊⠝⠎⠞⠁⠇⠇⠁⠞⠊⠕⠝

```
$ pip install a8
```
Remember the system dependencies:
```
# apt-get install vim-gtk python-gtk2 python-vte python-dbus
```
(non debian distros, please drop me a line to add you.)

## Configuration


a8 is a bit configurable. Not so much because I never planned on using it in more than one way.

### Configuration file

Create a config file at ~/.a8/config.yaml

As the name suggests it will be in Yaml, as a map of key values:
```
foo1: blah
foo2:
    foo3: blah
```
etc.

### Terminal Configuration ###

Is the biggest bit, terminal options live under the `temrinal` key, and these
are them, with default values if they exist (or Unset otherwise):
```
  terminal:
    'color_foreground': Unset,
    'color_background': Unset,
    'backspace_binding': Unset,
    'cursor_blink_mode': Unset,
    'cursor_shape': Unset,
    'font': Unset,
    'allow_bold': Unset,
    'audible_bell': Unset,
    'emulation': Unset,
    'pointer_autohide': Unset,
    'scroll_on_keystroke': Unset,
    'scroll_on_output': Unset,
    'scrollback_lines': 1000,
    'visible_bell': Unset,
    'word_chars': '-A-Za-z0-9,./?%&#:_',
```

### Window Configuration ###

To turn on the toolbar:
```
toolbar: true
```

### Session Configuration ###

Abominade 0.11 supports 3 session types:
```
session_type: 'none'   # don't remember sessions (alias for "session: false")
session_type: 'local'  # stores session in the ./.a8 wherever abominade runs
session_type: 'user'   # default, stores session in ~/.a8
```
To turn off sessions in 0.10 and earlier:
```
session: false
```

### Terminals in a separate window ###

Useful for multiple screens:
```
terminal_window: true
```

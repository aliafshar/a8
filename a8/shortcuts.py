# -*- coding: utf-8 -*- 
# (c) 2005-2011 PIDA Authors
# vim: ft=python sw=2 ts=2 sts=2 tw=80

import gtk
from a8 import actions

commands = [
  actions.Action('shell', 'Shell', 'application_xp_terminal.png'),
]

shortcuts = {
  '<Control><Shift>t': 'shell',
}

def on_accel(group, acceleratable, keyval, modifier):
  print keyval, modifier

def create_accel_group():
  accel_group = gtk.AccelGroup()
  for shortcut, action in shortcuts.items():
    keyval, modifier = gtk.accelerator_parse(shortcut)
    accel_group.connect_group(keyval, modifier, gtk.ACCEL_VISIBLE, on_accel)
  return accel_group


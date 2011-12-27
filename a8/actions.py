# -*- coding: utf-8 -*- 
# (c) 2005-2011 PIDA Authors
# vim: ft=python sw=2 ts=2 sts=2 tw=80


import gtk
from a8 import resources


class Action(object):
  """Doing something in the IDE."""
  def __init__(self, key, label, icon):
    self.key = key
    self.label = label
    self.icon = icon

  def create_menuitem(self):
    """Create a menu item from an action."""
    item = gtk.ImageMenuItem()
    item.set_label(self.label)
    item.set_image(resources.load_icon(self.icon))
    item.set_always_show_image(True)
    item.set_data('action_key', self.key)
    return item


def create_action_menu(actions, callback):
  """Create a menu from actions."""
  menu = gtk.Menu()
  for action in actions:
    if action is not None:
      menuitem = action.create_menuitem()
      menuitem.connect('activate', callback)
    else:
      menuitem = gtk.SeparatorMenuItem()
    menu.append(menuitem)
  menu.show_all()
  return menu


class ActionRegistry(dict):
  """Registry of actions."""

  def add(self, action):
    self[action.key] = action

  def activate(self, key, **kw):
    self[key](**kw)


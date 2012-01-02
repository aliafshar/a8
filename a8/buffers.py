# -*- coding: utf-8 -*- 
# (c) 2005-2012 PIDA Authors
# vim: ft=python sw=2 ts=2 sts=2 tw=80


"""Buffer list."""


import os

import gtk, gtk.gdk
from pygtkhelpers.ui import objectlist

from a8 import resources, lists, contexts


class Buffer(lists.ListItem):
  """Loaded buffer."""

  MARKUP_TEMPLATE = '<b>{0}</b>\n<span size="x-small">{1}</span>'

  def __init__(self, model, filename):
    self.model = model
    self.filename = filename
    self.dirname = os.path.dirname(filename)
    self.basename = os.path.basename(filename)
    bookmark = self.model.bookmarks.shortest_path(filename)
    if bookmark:
      supname = self.dirname.replace(bookmark.target, '').lstrip('/')
      self.dispname = '{0}:{1}'.format(bookmark.basename, supname)
    else:
      self.dispname = self.dirname

  @property
  def markup_args(self):
    """Display in the buffer list."""
    return (self.basename, self.dispname)


class BufferManager(lists.ListView):
  """Buffer list."""

  LABEL = 'Buffers'
  ICON  = 'page_white_stack.png'

  def create_ui(self):
    lists.ListView.create_ui(self)
    if self.model.config.get('toolbar', False):
      self.stack.pack_start(self.model.shortcuts.create_tools(), expand=False)
    self.filenames = {}

  def append(self, filename):
    if filename not in self.filenames:
      self.filenames[filename] = buf = Buffer(self.model, filename)
      self.items.append(buf)
    if (self.items.get_selection() is None or
        not self.items.selected_item or
        self.items.selected_item.filename != filename):
      b = self.items.selected_item = self.filenames[filename]
      self.model.ui.set_title('{0}/{1}'.format(b.dispname, b.basename))

  def remove(self, filename):
    if filename in self.filenames:
      buf = self.filenames.pop(filename)
      self.items.remove(buf)

  def on_items__item_activated(self, items, item):
    self.model.vim.open_file(item.filename)
    self.model.vim.grab_focus()

  def on_items__item_right_clicked(self, items, item, event):
    context = contexts.LocalContext(self.model, None, item.filename)
    menu = context.create_menu()
    if menu is not None:
      menu.popup(None, None, None, event.button, event.time)


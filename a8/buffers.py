# -*- coding: utf-8 -*- 
# (c) 2005-2012 PIDA Authors
# vim: ft=python sw=2 ts=2 sts=2 tw=80


"""Buffer list."""


import os

from pygtkhelpers.ui import objectlist

from a8 import lists, contexts


class Buffer(lists.ListItem):
  """Loaded buffer."""

  MARKUP_TEMPLATE = '<b>{0}</b>\n<span size="x-small">{1}</span>'

  def __init__(self, model, filename, bufid):
    self.model = model
    self.filename = filename
    self.bufid = bufid
    self.dirname = os.path.dirname(filename)
    self.basename = os.path.basename(filename)
    self.update_dispname()

  @property
  def markup_args(self):
    """Display in the buffer list."""
    return (self.basename, self.dispname)

  @property
  def background(self):
    if self.model.vim.get_buffer_modified(self.bufid):
      return '#ffffbb'    # pale yellow
    return '#ffffff'    # white

  def update_dispname(self):
    """Set or reset display name based on path and bookmarks"""
    bookmark = self.model.bookmarks.shortest_path(self.filename)
    if bookmark:
      supname = self.dirname.replace(bookmark.target, '').lstrip('/')
      self.dispname = '{0}:{1}'.format(bookmark.basename, supname)
    else:
      self.dispname = self.dirname

  def rename(self, filename):
    self.model.buffers.remove(self.filename)
    self.filename = filename
    self.model.buffers.append(self.filename, self.bufid)

def background_mapper(cell, obj, renderer):
  renderer.set_property('background', obj.background)

class BufferManager(lists.ListView):
  """Buffer list."""

  LABEL = 'Buffers'
  ICON  = 'page_white_stack.png'

  COLUMNS = [objectlist.Column('markup', use_markup=True, mappers=[background_mapper]),
             objectlist.Column('bufid', visible=False),
             objectlist.Column('basename', visible=False, searchable=True)]

  def get_by_bufid(self, bufid):
    for buf in self.items:
      if buf.bufid == bufid:
        return buf
    return None

  def get_by_filename(self, filename):
    for buf in self.items:
      if buf.filename == filename:
        return buf
    return None

  def create_ui(self):
    lists.ListView.create_ui(self)
    if self.model.config['toolbar']:
      self.stack.pack_start(self.model.shortcuts.create_tools(), expand=False)

  def append(self, filename, bufid):
    buf = self.get_by_bufid(bufid)
    if buf is None:
      buf = Buffer(self.model, filename, bufid)
      self.items.append(buf)
    else:
      buf.filename = filename
    if (self.items.get_selection() is None or
        not self.items.selected_item or
        self.items.selected_item.filename != filename):
      self.items.selected_item = buf
    self.refresh_activated_item()

  def remove(self, bufid):
    buf = self.get_by_bufid(bufid)
    if buf is not None:
      self.items.remove(buf)
      self.refresh_activated_item()

  def refresh(self):
    for item in self.items:
      item.update_dispname()

  def get_activated_item(self):
    bufid = self.model.vim.get_current_buffer_id()
    item = self.get_by_bufid(bufid)
    return item

  def refresh_activated_item(self):
    b = self.get_activated_item()
    if b is not None:
      title = '{0}/{1}'.format(b.dispname, b.basename)
    else:
      title = ''
    self.model.ui.set_title(title)

  def on_items__item_activated(self, items, item):
    self.model.vim.open_file(item.filename)
    self.refresh_activated_item()
    self.model.vim.grab_focus()

  def on_items__item_right_clicked(self, items, item, event):
    context = contexts.LocalContext(self.model, None, item.filename)
    context.create_menu()   # force expanding path, etc.
    # only files should be here, and we want a menu even if file was deleted
    menu = context.create_file_menu()
    if menu is not None:
      menu.popup(None, None, None, event.button, event.time)

  def on_items__item_middle_clicked(self, items, item, event):
    self.model.vim.close(item.filename)


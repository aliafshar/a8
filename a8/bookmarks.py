# -*- coding: utf-8 -*- 
# (c) 2005-2012 PIDA Authors
# vim: ft=python sw=2 ts=2 sts=2 tw=80


import os
import gtk
import yaml

from a8 import lists, contexts, actions


class BookMark(lists.ListItem):

  MARKUP_TEMPLATE = '<b>{0}</b>\n<span size="xx-small">{1}</span>'

  def __init__(self, target):
    self.target = target
    self.basename = os.path.basename(target)
    self.dirname = os.path.dirname(target)

  @property
  def markup_args(self):
    return (self.basename, self.dirname)

  @property
  def type(self):
    print self.target
    if os.path.isdir(self.target):
      return 'dir'
    elif self.target.startswith('http'):
      return 'uri'
    else:
      return 'file'


class BookmarkManager(lists.ListView):

  LABEL = 'Bookmarks'
  ICON = 'star.png'

  remove_action = actions.Action('remove_bookmark', 'Remove Bookmark',
                                 'delete.png')

  def add(self, target):
    self.items.append(BookMark(target))
    self.model.emit('bookmark-item-added', filename=target)
    self.save()

  def create_ui(self):
    lists.ListView.create_ui(self)
    self.filename = self.model.home.path('bookmarks.yaml')
    self.load()

  def load(self):
    self.items.clear()
    if not os.path.exists(self.filename):
      return
    with open(self.filename) as f:
      data = f.read()
    if not data:
      return
    for item in yaml.load(data):
      self.items.append(BookMark(item))

  def shortest_path(self, path):
    match = None
    for item in self.items:
      if item.target in path and (not match or
        len(item.target) > len(match.target)):
        match = item
    return match

  def save(self):
    data = yaml.dump([item.target.encode('utf-8')
                     for item in self.items],
                     default_flow_style=False)
    with open(self.filename, 'w') as f:
      f.write(data)

  def activate(self, bookmark):
    dispatch = {
      'dir': self.activate_dir,
      'file': self.activate_file,
    }
    dispatch[bookmark.type](bookmark)

  def activate_dir(self, bookmark):
    self.model.files.browse(bookmark.target)

  def activate_file(self, bookmark):
    self.model.vim.open_file(bookmark.target)

  def on_items__item_right_clicked(self, items, item, event):
    context = contexts.LocalContext(self.model, None, item.target)
    menu = context.create_menu()
    self.extend_menu(menu)
    menu.show_all()
    menu.popup(None, None, None, event.button, event.time)

  def extend_menu(self, menu):
    menu.append(gtk.SeparatorMenuItem())
    remove_item = self.remove_action.create_menuitem()
    menu.append(remove_item)
    for menuitem in menu.get_children():
      if menuitem.get_data('action_key') == 'bookmark':
        menuitem.set_sensitive(False)
    remove_item.connect('activate', self.on_remove_item_activate)

  def on_remove_item_activate(self, menuitem):
    self.items.remove(self.items.selected_item)
    self.save()

  def on_items__item_activated(self, objectlist, item):
    self.activate(item)


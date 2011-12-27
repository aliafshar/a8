# -*- coding: utf-8 -*- 
# (c) 2005-2011 PIDA Authors
# vim: ft=python sw=2 ts=2 sts=2 tw=80

import os

import yaml

from a8 import lists


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

  def add(self, target):
    self.items.append(BookMark(target))
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

  def save(self):
    data = yaml.dump([item.target for item in self.items])
    with open(self.filename, 'w') as f:
      f.write(data)

  def activate(self, bookmark):
    dispatch = {
      'dir': self.activate_dir,
      'file': self.activate_file,
      'uri': self.activate_uri,
    }
    dispatch[bookmark.type](bookmark)

  def activate_dir(self, bookmark):
    self.model.files.browse(bookmark.target)

  def activate_file(self, bookmark):
    self.model.vim.open(bookmark.target)

  def activate_uri(self, bookmark):
    pass

  def on_items__item_activated(self, objectlist, item):
    self.activate(item)



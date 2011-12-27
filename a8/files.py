# -*- coding: utf-8 -*- 
# (c) 2005-2011 PIDA Authors
# vim: ft=python sw=2 ts=2 sts=2 tw=80

import os, re

import gtk
from pygtkhelpers.ui import objectlist
from pygtkhelpers import gthreads
gthreads.initial_setup()

from a8 import lists, resources


HIDDEN_MASKS = [
    '^\.+',
    '.+\.pyc$'
]
HIDDEN_PATTERN = re.compile('|'.join(HIDDEN_MASKS))


class File(object):

  folder_pixbuf = resources.load_icon('folder.png').get_pixbuf()
  file_pixbuf = resources.load_icon('page_white.png').get_pixbuf()

  def __init__(self, filename):
    self.filename = filename
    self.basename = os.path.basename(filename)
    self.lowname = self.basename.lower()
    self.isdir = os.path.isdir(self.filename)
    self.isdir_key = (self.isdir and 'a' or 'b', self.lowname)
    self.hidden = HIDDEN_PATTERN.match(self.basename)

  @property
  def markup(self):
    return self.basename

  @property
  def icon(self):
    if self.isdir:
      return self.folder_pixbuf
    else:
      return self.file_pixbuf


class FileManager(lists.ListView):
  """Files list."""

  LABEL = 'Files'

  ICON  = 'folder.png'
  COLUMNS = [
    objectlist.Column('icon', type=gtk.gdk.Pixbuf),
    objectlist.Column('markup')
  ]

  def create_ui(self):
    lists.ListView.create_ui(self)
    self.items.sort_by('isdir_key')

  def browse(self, path=os.getcwd()):
    self.items.clear()
    task = gthreads.GeneratorTask(self.browse_work, self.browse_item)
    task.start(path)

  def browse_work(self, path):
    parent = File(os.path.dirname(path))
    parent.basename = '..'
    parent.isdir_key = '1', '_'
    yield parent
    for filename in os.listdir(path):
      yield File(os.path.join(path, filename))

  def browse_item(self, item):
    if not item.hidden:
      self.items.append(item)

  def on_items__item_activated(self, items, item):
    if item.isdir:
      self.browse(item.filename)
    else:
      self.model.vim.open_file(item.filename)
      self.model.vim.grab_focus()



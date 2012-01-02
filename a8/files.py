# -*- coding: utf-8 -*- 
# (c) 2005-2012 PIDA Authors
# vim: ft=python sw=2 ts=2 sts=2 tw=80


import os, re
import gtk
from pygtkhelpers.ui import objectlist
from pygtkhelpers import gthreads
gthreads.initial_setup()

from a8 import lists, resources, contexts, actions


HIDDEN_MASKS = [
    '^\.+',
    '.+\.pyc$'
]
HIDDEN_PATTERN = re.compile('|'.join(HIDDEN_MASKS))


class File(lists.ListItem):

  folder_pixbuf = resources.load_icon('folder.png').get_pixbuf()
  file_pixbuf = resources.load_icon('page_white.png').get_pixbuf()

  MARKUP_TEMPLATE = '<b><tt>{0}</tt></b>{1}'

  def __init__(self, filename):
    self.filename = unicode(filename)
    self.basename = os.path.basename(self.filename)
    self.lowname = self.basename.lower()
    self.isdir = os.path.isdir(self.filename)
    self.isdir_key = (self.isdir and 'a' or 'b', self.lowname)
    self.hidden = HIDDEN_PATTERN.match(self.basename)
    self.annotation = ''

  @property
  def markup_args(self):
    return (self.annotation, self.basename)

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
    objectlist.Column('markup', use_markup=True),
  ]

  TOOL_ACTIONS = [
    actions.Action('refresh', 'Refresh', 'arrow_refresh_small.png')
  ]

  def create_ui(self):
    lists.ListView.create_ui(self)
    self.items.sort_by('isdir_key')

  def browse(self, path=os.getcwd()):
    self.items.clear()
    self.path = path
    task = gthreads.GeneratorTask(self.browse_work, self.browse_item)
    task.start(path)
    self.model.ui.focus_files()

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
      self.model.emit('file-item-added', item=item)

  def on_items__item_activated(self, items, item):
    if item.isdir:
      self.browse(item.filename)
    else:
      self.model.vim.open_file(item.filename)
      self.model.vim.grab_focus()

  def on_items__item_right_clicked(self, items, item, event):
    context = contexts.LocalContext(self.model, None, item.filename)
    menu = context.create_menu()
    menu.popup(None, None, None, event.button, event.time)

  def on_refresh_activate(self):
    self.browse(self.path)


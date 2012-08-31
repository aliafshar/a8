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

  def __init__(self, model, filename, expanded=False):
    self.model = model
    self.filename = unicode(filename)
    self.basename = os.path.basename(self.filename)
    if self.model.files.expanded:
      self.dispname = os.path.relpath(self.filename, self.model.files.path)
    else:
      self.dispname = self.basename
    self.lowname = self.dispname.lower()
    self.isdir = os.path.isdir(self.filename)
    self.isdir_key = (self.isdir and 'a' or 'b', self.lowname)
    self.hidden = HIDDEN_PATTERN.match(self.basename)
    self.annotation = ''

  @property
  def markup_args(self):
    return (self.annotation, self.dispname)

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
    objectlist.Column('dispname', visible=False, searchable=True),
  ]

  TOOL_ACTIONS = [
    actions.Action('refresh', 'Refresh', 'arrow_refresh_small.png'),
    actions.Action('expand_collapse', 'Expand Files'),
  ]

  def __init__(self, *args, **kw):
    super(FileManager, self).__init__(*args, **kw)
    self.task = None
    self.expanded = False

  def create_ui(self):
    lists.ListView.create_ui(self)
    self.items.sort_by('isdir_key')

  def browse(self, path=None, expanded=False):
    if self.task:
      self.task.stop()
    self.expanded = expanded
    self.TOOL_ACTIONS[1].label = self.expanded and 'Collapse Files' or 'Expand Files'
    if path is None:
      path = os.getcwd()
    self.items.clear()
    path = os.path.normpath(path)
    self.path = path
    browse_work = expanded and self._browse_expanded_work or self._browse_work
    self.task = gthreads.GeneratorTask(browse_work, self.browse_item)
    self.task.start(path)
    self.model.ui.focus_files()

  def _browse_work(self, path):
    parent = File(self.model, os.path.dirname(path))
    parent.dispname = '..'
    parent.isdir_key = '1', '_'
    yield parent
    for filename in os.listdir(path):
      yield File(self.model, os.path.join(path, filename))

  def _browse_expanded_work(self, path):
    for dirpath, dirnames, filenames in os.walk(path):
      # prune hidden dirs, and walk in sorting order
      dirnames[:] = sorted([d for d in dirnames if not HIDDEN_PATTERN.match(d)],
          key=lambda s: s.lower())
      for filename in filenames:
        yield File(self.model, os.path.join(dirpath, filename), expanded=True)

  def browse_item(self, item):
    if not item.hidden:
      self.items.append(item)
      self.model.emit('file-item-added', item=item)

  def expand(self):
    if not self.expanded:
      self.browse(self.path, expanded=True)

  def collapse(self):
    if self.expanded:
      self.browse(self.path, expanded=False)

  def toggle_expanded(self):
    if self.expanded:
      self.collapse()
    else:
      self.expand()

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

  def on_expand_collapse_activate(self):
    self.toggle_expanded()

  def on_items__key_press_event(self, items, event):
    if event.keyval == gtk.keysyms.Escape:
      self.collapse()

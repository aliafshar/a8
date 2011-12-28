# -*- coding: utf-8 -*- 
# (c) 2005-2011 PIDA Authors
# vim: ft=python sw=2 ts=2 sts=2 tw=80

"""Application contexts."""


import os

import gtk
import logbook

from a8 import actions

log = logbook.Logger('Contexts')
log.debug('Log start')


class BaseContext(object):
  """Base context superclass."""

  #: A regular expression to match the context
  expr = None
  name = 'Unnamed Context'

  def __init__(self, model, view, data):
    self.model = model
    self.data = data
    self.view = view

  def create_action_menu(self, acts):
    """Create a menu for the context."""
    return actions.create_action_menu(acts, self.on_menuitem_activate)

  def on_menuitem_activate(self, item):
    action_key = item.get_data('action_key')
    callback = getattr(self, 'on_%s_activate' % action_key, None)
    if callback is None:
      raise NotImplementedError(action_key)
    else:
      callback()


class LocalContext(BaseContext):
  """Context for files and directories."""

  expr = '\S+'
  name = 'Local filesystem context'

  dir_actions = [
    actions.Action(
      'browse_dir',
      'Browse Directory',
      'folder.png'
    ),
    actions.Action(
      'shell_dir',
      'Terminal in Directory',
      'application_xp_terminal.png'
    ),
    actions.Action(
      'bookmark',
      'Add bookmark',
      'star.png'
    )
  ]

  file_actions = [
    actions.Action(
      'open_file',
      'Open file',
      'page_white.png'
    ),
    None,
    actions.Action(
      'browse_file',
      'Browse parent',
      'folder.png',
    ),
    actions.Action(
      'shell_file',
      'Shell in parent',
      'application_xp_terminal.png',
    ),
    actions.Action(
      'bookmark',
      'Add bookmark',
      'star.png'
    )
  ]

  open_file_actions = [
    None, # Separator
    actions.Action(
      'close_document',
      'Close document',
      'cross.png',
    )
  ]

  def create_menu(self):
    """Create a menu for the context."""
    if not os.path.isabs(self.data) and self.view is not None:
      log.debug('relative to "{0}"', self.view.cwd)
      self.data = os.path.join(self.view.cwd, self.data)
    if os.path.isdir(self.data):
      log.debug('directory')
      return self.create_dir_menu()
    elif os.path.exists(self.data):
      log.debug('file')
      return self.create_file_menu()
    else:
      return self.create_non_menu(self.data)

  def create_dir_menu(self):
    return self.create_action_menu(self.dir_actions)

  def create_file_menu(self):
    actions = list(self.file_actions)
    if self.data in self.model.buffers.filenames:
      actions.extend(self.open_file_actions)
    return self.create_action_menu(actions)

  def on_browse_dir_activate(self):
    self.model.files.browse(self.data)

  def on_browse_file_activate(self):
    self.model.files.browse(os.path.dirname(self.data))

  def on_shell_dir_activate(self):
    self.model.terminals.execute(cwd=self.data)

  def on_shell_file_activate(self):
    self.model.terminals.execute(cwd=os.path.dirname(self.data))

  def on_bookmark_activate(self):
    self.model.bookmarks.add(self.data)

  def on_close_document_activate(self):
    self.model.vim.close(self.data)

  def on_open_file_activate(self):
    self.model.vim.open_file(self.data)


class UriContext(BaseContext):
  """Context for URIs."""

  expr = r'https{0,1}://\S+'


class IntegerContext(BaseContext):
  """Context for integers."""

  expr = r'\d+'


class ContextManager(object):
  context_order = [UriContext, IntegerContext, LocalContext]


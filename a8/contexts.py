# -*- coding: utf-8 -*- 
# (c) 2005-2012 PIDA Authors
# vim: ft=python sw=2 ts=2 sts=2 tw=80


"""Application contexts."""


import os
import re
import psutil
import logbook
import webbrowser
from a8 import actions


log = logbook.Logger('Contexts')
log.debug('Log start')


class BaseContext(object):
  """Base context superclass."""

  #: A regular expression to match the context
  ereg_expr = None
  name = 'Unnamed Context'

  def __init__(self, model, view, data):
    self.model = model
    self.data = data
    self.view = view

  def check_valid(self):
    """Determine whether context data actually represents actionable item.

    Note that this may be orthogonal to checking against the associated regex,
    which is only a heuristic, and may match things that are not actionable, or
    may miss things that are."""
    raise NotImplementedError()

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

  ereg_expr = (
      r'"([^"]|\\")+"|' + \
      r"'[^']+'|" + \
      r'(\\ |\\\(|\\\)|\\=|[^]\[[:space:]"\':\$()=])+'
  )
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
    ),
    None,
    actions.Action(
      'close_under',
      'Close any children',
      'cross.png',
    ),
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

  def __init__(self, model, view, data):
    super(LocalContext, self).__init__(model, view, data)
    raw_data = data
    # check literal, without interpreting quotes or backslash sequences
    self.data = self._expand_path(self.data)
    if self.check_valid():
      return
    eval_data = self._eval_quotes(raw_data)
    # check after interpreting quotes and backslash sequences
    if eval_data != raw_data:
      self.data = self._expand_path(eval_data)
      if self.check_valid():
        return
    # check for 'a/FOO' and 'b/FOO' formats commonly used in diffs
    # unescaped (e.g. from 'hg diff')
    if raw_data.startswith('a/') or raw_data.startswith('b/'):
      self.data = self._expand_path(raw_data[2:])
      if self.check_valid():
        return
    # escaped (e.g. from 'git diff')
    if eval_data != raw_data:
      if eval_data.startswith('a/') or eval_data.startswith('b/'):
        self.data = self._expand_path(eval_data[2:])

  def check_valid(self):
    return os.path.exists(self.data)

  def _eval_quotes(self, text):
    # double-quoted
    if re.match(r'".*"$', text):
      return re.sub(r'\\(["\\])', r'\1', text[1:-1])
    # single-quoted
    if re.match(r"'.*'$", text):
      return text[1:-1]
    # check if backslash-escaped
    if '\\' in text:
      # make sure all special characters are escaped, otherwise assume literal
      if not re.search(r'(?<!\\)[ ()\[\]=]', text):
        return re.sub(r'\\(.)', r'\1', text)
    return text

  def _expand_path(self, path):
    expanded = os.path.expanduser(path)
    if not os.path.isabs(expanded) and self.view is not None:
      log.debug('relative to "{0}"', self.view.cwd)
      expanded = os.path.join(self.view.cwd, expanded)
    return expanded

  def create_menu(self):
    """Create a menu for the context."""
    if os.path.isdir(self.data):
      log.debug('directory')
      return self.create_dir_menu()
    elif os.path.exists(self.data):
      log.debug('file')
      return self.create_file_menu()
    return None

  def create_dir_menu(self):
    return self.create_action_menu(self.dir_actions)

  def create_file_menu(self):
    actions = list(self.file_actions)
    if self.model.buffers.get_by_filename(self.data):
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

  def on_close_under_activate(self):
    self.model.vim.close_under(self.data)


class UriContext(BaseContext):
  """Context for URIs."""

  name = 'URI Context'
  expr = r'https{0,1}://\S+'
  ereg_expr = expr

  uri_actions = [
    actions.Action('browse_uri', 'Open', 'world_go.png'),
  ]

  def check_valid(self):
    # TODO(dbarnett): more sophisticated checks using urlparse
    m = re.match(self.expr + '$', self.data)
    return m is not None

  def on_browse_uri_activate(self):
    webbrowser.open_new_tab(self.data)

  def create_menu(self):
    return self.create_action_menu(self.uri_actions)


class IntegerContext(BaseContext):
  """Context for integers."""

  ereg_expr = r'\b[0-9]+\b'
  name = 'Integer context'

  int_actions = [
    actions.Action('term', 'SIGTERM', 'asterisk_yellow.png'),
    actions.Action('kill', 'SIGKILL', 'asterisk_orange.png'),
  ]

  def check_valid(self):
    try:
      pid = int(self.data)
      proc = psutil.Process(pid)
    except (ValueError, psutil.NoSuchProcess):
      return False
    return True

  def create_menu(self):
    try:
      pid = int(self.data)
      self.proc = psutil.Process(pid)
      menu = self.create_action_menu(self.int_actions)
    except (ValueError, psutil.NoSuchProcess):
      menu = None
    return menu

  def on_kill_activate(self):
    self.proc.kill()

  def on_term_activate(self):
    self.proc.terminate()


class ContextManager(object):
  context_order = [UriContext, IntegerContext, LocalContext]


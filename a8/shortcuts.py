# -*- coding: utf-8 -*- 
# (c) 2005-2012 PIDA Authors
# vim: ft=python sw=2 ts=2 sts=2 tw=80


import os
import gtk
import logbook

from a8 import actions, resources, config, terminals


log = logbook.Logger('shortcuts')


commands = [
  actions.Action('shell', 'Shell', 'application_xp_terminal.png'),
  actions.Action('browse_home', 'Browse home directory', 'house_go.png'),
  actions.Action('config', 'Edit configuration', 'cog.png'),
  None,
  actions.Action('close_all_buffers', 'Close all buffers', 'cross.png'),
]


shortcuts = {
  '<Alt>t': 'shell',
  '<Alt>e': 'focus_vim',
  '<Alt>r': 'focus_terminal',
  '<Alt>b': 'focus_buffers',
  '<Alt>m': 'focus_files',
  '<Alt>i': 'focus_terminals',
  '<Alt>k': 'focus_bookmarks',
  '<Alt>Up': 'prev_buffer',
  '<Alt>Down': 'next_buffer',
  '<Alt>Left': 'prev_terminal',
  '<Alt>Right': 'next_terminal',
  '<Alt>g': 'refresh_files',
  '<Alt>c': 'close_all_buffers',
  '<Alt>h': 'browse_home',
}


class CustomShortcut(object):

  def __init__(self):
    self.cmd = None
    self.cwd = None
    self.env = None


class ShortcutManager(object):

  def __init__(self, model):
    self.model = model
    self.config = self.model.home.load_shortcuts()

  def create_group(self):
    accel_group = gtk.AccelGroup()
    for shortcut, action in shortcuts.items():
      shortcut = self.config.opts.get(action, shortcut)
      keyval, modifier = gtk.accelerator_parse(shortcut)
      accel_group.connect_group(keyval, modifier, gtk.ACCEL_VISIBLE,
                                self.accel_callback(action))
    for shortcut, custom in self.get_customs():
      keyval, modifier = gtk.accelerator_parse(shortcut)
      accel_group.connect_group(keyval, modifier, gtk.ACCEL_VISIBLE,
                                self.custom_callback(custom))
    return accel_group

  def get_customs(self):
    custom_data = self.config.get('custom', None)
    if not custom_data or not isinstance(custom_data, list):
      return
    for custom_datum in custom_data:
      if not isinstance(custom_datum, dict):
        continue
      shortcut = custom_datum.get('key')
      if not shortcut:
        continue
      custom = CustomShortcut()
      custom.cmd = custom_datum.get('cmd')
      custom.cwd = custom_datum.get('cwd')
      custom.env = custom_datum.get('env')
      yield shortcut, custom

  def create_tools(self):
    bar = gtk.HBox()
    for action in commands:
      if action is None:
        bar.pack_start(gtk.Alignment())
      else:
        button = resources.load_button(action.icon, action.label)
        bar.pack_start(button, expand=False)
        button.connect('clicked', self.on_button, action.key)
    bar.show_all()
    return bar

  def on_button(self, button, action_key):
    self.activate(action_key)

  def accel_callback(self, action_key):
    def on_accel(group, acceleratable, keyval, modifier,
                 self=self, action_key=action_key):
      try:
        self.activate(action_key)
      except NotImplementedError, e:
        log.error('NotImplemented: {0}', e)
      except Exception, e:
        raise
        log.error('Unhandled: {0}', e)
      return True
    return on_accel

  def custom_callback(self, custom):
    def on_accel(group, acceleratable, keyval, modifier,
                 self=self, custom=custom):
      self.model.terminals.execute(
        [terminals.get_default_shell(), '-c', custom.cmd],
        custom.cwd, custom.env)
      return True
    return on_accel

  def activate(self, action_key):
    callback = getattr(self, 'on_%s_activate' % action_key, None)
    if callback is None:
      raise NotImplementedError(action_key)
    else:
      callback()

  def on_shell_activate(self):
    self.model.terminals.execute()

  def on_focus_vim_activate(self):
    self.model.vim.grab_focus()

  def on_focus_terminal_activate(self):
    self.model.terminals.grab_focus()

  def on_prev_buffer_activate(self):
    self.model.vim.prev()

  def on_next_buffer_activate(self):
    self.model.vim.next()

  def on_prev_terminal_activate(self):
    self.model.terminals.prev()

  def on_next_terminal_activate(self):
    self.model.terminals.next()

  def on_focus_buffers_activate(self):
    self.model.ui.focus_buffers()

  def on_focus_bookmarks_activate(self):
    self.model.ui.focus_bookmarks()

  def on_focus_files_activate(self):
    self.model.ui.focus_files()

  def on_focus_terminals_activate(self):
    self.model.ui.focus_terminals()

  def on_refresh_files_activate(self):
    self.model.files.on_refresh_activate()

  def on_close_all_buffers_activate(self):
    self.model.vim.close_all()

  def on_browse_home_activate(self):
    self.model.files.browse(os.path.expanduser('~'))

  def on_config_activate(self):
    self.model.vim.open_file(self.model.home.config_path)

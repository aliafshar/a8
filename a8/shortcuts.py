# -*- coding: utf-8 -*- 
# (c) 2005-2011 PIDA Authors
# vim: ft=python sw=2 ts=2 sts=2 tw=80


import gtk
import logbook

from a8 import actions, resources


log = logbook.Logger('shortcuts')


commands = [
  actions.Action('shell', 'Shell', 'application_xp_terminal.png'),
]


actions = {}
for action in commands:
  actions[action.key] = action


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
}


class ShortcutManager(object):

  def __init__(self, model):
    self.model = model

  def create_group(self):
    accel_group = gtk.AccelGroup()
    for shortcut, action in shortcuts.items():
      keyval, modifier = gtk.accelerator_parse(shortcut)
      accel_group.connect_group(keyval, modifier, gtk.ACCEL_VISIBLE,
                                self.accel_callback(action))
    return accel_group

  def create_tools(self):
    bar = gtk.HBox()
    bar.set_spacing(3)
    for action in commands:
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


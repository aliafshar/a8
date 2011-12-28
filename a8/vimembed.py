# -*- coding: utf-8 -*- 
# (c) 2005-2011 PIDA Authors
# vim: ft=python sw=2 ts=2 sts=2 tw=80


"""A library to embed vim in a gtk socket."""


import os, subprocess

import gtk, gobject
import logbook
from pygtkhelpers import delegates

from a8 import bus, resources


log = logbook.Logger('Vim')


class VimManager(delegates.SlaveView):
  """Embed and communicate with Vim."""

  null_callback = {
    'reply_handler': lambda *args: None,
    'error_handler': lambda *args: None,
  }

  def create_ui(self):
    self.holder = gtk.EventBox()
    self.holder.add_events(gtk.gdk.KEY_PRESS_MASK)
    self.widget.add(self.holder)
    self.widget.set_size_request(200, 200)
    self.socket = gtk.Socket()
    self.holder.add(self.socket)
    self.widget.show_all()
    self.vim_command = 'gvim'
    self.vim = None
    self.vim_proc = None
    self.vim_pid = None

  def connect_vim(self):
    log.debug('Connect')
    self.vim = bus.connect('vim')
    self.connect_vim_signals()

  def stop(self):
    self.vim.quit(**self.null_callback)

  def get_vim_env(self):
    env = os.environ.copy()
    env['PYTHONPATH'] = os.path.dirname(os.path.dirname(__file__))
    return env

  def get_vim_args(self):
    return [
      self.vim_command,
      '--cmd', 'let A8_EMBEDDED=1',
      '--cmd', 'let A8_UID="{uid}"'.format(uid=bus.A8_UID),
      '--cmd', 'so {script}'.format(script=self.get_vim_script()),
      '--socketid', str(self.xid),
    ]

  def get_vim_script(self):
    return resources.get_resource_path('a8.vim')

  def execute_vim(self):
    self.vim_proc = subprocess.Popen(
      self.get_vim_args(),
      env=self.get_vim_env(),
      close_fds=True
    )

  def start(self):
    log.debug('Start')
    self.xid = self.socket.get_id()
    if self.vim_pid is not None:
      log.warn('Already started at pid={0}'.format(self.vim_pid))
    try:
      self.execute_vim()
      self.widget.show_all()
      self.connect_vim()
    except OSError, e:
      pass #XXX Warn

  def grab_focus(self):
    gobject.idle_add(self.holder.child_focus, gtk.DIR_TAB_FORWARD)

  def open_file(self, filename):
    self.vim.open_file(filename)

  def close(self, filename):
    self.vim.close_buffer(filename)

  def goto_line(self, line):
    self.vim.goto_line(line)

  def next(self):
    self.vim.next()

  def prev(self):
    self.vim.prev()

  def connect_vim_signals(self):
    for k in dir(self):
      if k.startswith('onvim_'):
        self.vim.connect_to_signal(k[6:], getattr(self, k))

  def onvim_VimEnter(self):
    log.debug('Signal: Enter')
    for filename in self.model.args.files:
      self.open_file(filename)
    self.grab_focus()

  def onvim_BufEnter(self, bufid, filename):
    log.debug('Signal: Buffer {0} {1}'.format(bufid, filename))
    path = unicode(filename)
    if not path or os.path.isdir(path):
      path = ''
    else:
      if not os.path.abspath(path):
        cwd = self.vim.get_cwd()
        path = os.path.join(cwd, path)
      path = os.path.realpath(path)
      bufid = int(bufid)
      self.model.buffers.append(path)
    self.model.ui.set_title(path)

  def onvim_BufNew(self, bufid):
    log.debug('New {0}', bufid)

  def onvim_BufDelete(self, bufid, filename):
    path = unicode(filename)
    if not path:
      return
    self.model.buffers.remove(path)

  def onvim_VimLeave(self):
    log.debug('Signal: Leave')
    gtk.main_quit()

  def onvim_BufWritePost(self, bufid):
    print bufid, 'saved'



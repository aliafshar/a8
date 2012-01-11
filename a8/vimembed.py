# -*- coding: utf-8 -*- 
# (c) 2005-2012 PIDA Authors
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

  def save_session(self):
    self.vim.command('mks! {0}'.format(self.get_vim_session()))

  def stop(self):
    self.grab_focus()
    self.vim.quit(**self.null_callback)

  def get_vim_env(self):
    env = os.environ.copy()
    env['PYTHONPATH'] = os.path.dirname(os.path.dirname(__file__))
    return env

  def get_vim_args(self):
    args = [
      self.vim_command,
      '--cmd', 'let A8_EMBEDDED=1',
      '--cmd', 'let A8_UID="{uid}"'.format(uid=bus.A8_UID),
      '--cmd', 'so {script}'.format(script=self.get_vim_script()),
      '--socketid', str(self.xid),
    ]
    if self.model.config.get('session', True):
      args.extend(['-S', self.get_vim_session()])
    return args

  def get_vim_session(self):
    path = self.model.home.path('a8_vim_session.vim')
    if not os.path.exists(path):
      f = open(path, 'w')
      f.close()
    return path

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
    self.vim.open_file(filename, **self.null_callback)

  def close(self, filename):
    self.grab_focus()
    self.vim.close_buffer(filename, **self.null_callback)

  def close_all(self):
    self.grab_focus()
    self.vim.close_all_buffers(**self.null_callback)

  def close_under(self, path):
    self.grab_focus()
    self.vim.close_buffers_under(path)

  def goto_line(self, line):
    self.vim.goto_line(line, **self.null_callback)

  def next(self):
    self.vim.next(**self.null_callback)

  def prev(self):
    self.vim.prev(**self.null_callback)

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
    self.onvim_BufAdd(bufid, filename)

  def onvim_BufAdd(self, bufid, filename):
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
    self.model.emit('file-opened', filename=filename)

  def onvim_BufNew(self, bufid):
    log.debug('New {0}', bufid)

  def onvim_BufDelete(self, bufid, filename):
    path = unicode(filename)
    if not path:
      return
    self.model.buffers.remove(path)
    self.model.emit('file-closed', filename=filename)

  def onvim_VimLeave(self):
    log.debug('Signal: Leave')
    gtk.main_quit()

  def onvim_BufWritePost(self, bufid, filename):
    self.model.emit('file-saved', filename=filename)



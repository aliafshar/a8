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
    # NOTE: Setting a size request on self.widget prevents vim from propagating
    #       its own size requests up when gvim adds UI elements and resizes
    self.socket = gtk.Socket()
    self.holder.add(self.socket)
    self.widget.show_all()
    self.vim_command = 'gvim'
    self.vim = None
    self.vim_proc = None
    self.vim_pid = None
    self.vim_running = False    # to prevent accessing vim after close

  def on_holder__button_press_event(self, eventbox, event):
    self.grab_focus()

  def connect_vim(self):
    log.debug('Connect')
    self.vim = bus.connect('vim')
    self.vim_running = True
    self.connect_vim_signals()

  def save_session(self, polite=False):
    """Save vim session if sessions enabled.

    If polite=True and vim is in certain interactive modes, don't save session
    so we don't blank out certain vim output (see
    http://code.google.com/p/abominade/issues/detail?id=18)."""
    vim_session = self.get_vim_session()
    if vim_session is None:
      return
    if polite:
      cur_vim_mode = self.vim.eval('mode("full")')
      # Don't save from Hit-enter mode or Command-line mode
      if cur_vim_mode in ('r', 'rm', 'c'):
        return
    self.vim.command('mks! {0}'.format(self.get_vim_session()))

  def stop(self):
    log.debug('Stopping Vim')
    self.grab_focus()
    self.vim_running = False
    self.vim.quit(**self.null_callback)

  def get_vim_env(self):
    env = os.environ.copy()
    env['PYTHONPATH'] = os.path.dirname(os.path.dirname(__file__))
    return env

  def get_vim_args(self):
    args = [
      self.vim_command,
      '-f',
      '--cmd', 'let A8_EMBEDDED=1',
      '--cmd', 'let A8_UID="{uid}"'.format(uid=bus.A8_UID),
      '--cmd', 'so {script}'.format(script=self.get_vim_script()),
      '--socketid', str(self.xid),
    ]
    if self.model.sessions.filename is not None:
      args.extend(['-S', self.get_vim_session()])
    return args

  def get_vim_session(self):
    path = self.model.sessions.session_path('a8_vim_session.vim')
    if path and not os.path.exists(path):
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
    bufid = self.model.buffers.get_by_filename(filename).bufid
    self.vim.close_buffer_id(bufid, **self.null_callback)

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

  def get_current_buffer_id(self):
    return self.vim.get_current_buffer_id()

  def get_buffer_modified(self, bufid):
    if self.vim_running:
      return self.vim.get_buffer_modified(bufid)
    return None

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
    if not int(self.vim.eval('buflisted(%s)'%bufid)):
      # ignore unlisted buffers
      return
    log.debug('Signal: Buffer {0} {1}'.format(bufid, filename))
    path = unicode(filename)
    if not path or os.path.isdir(path):
      path = ''
    else:
      if not os.path.isabs(path):
        cwd = self.vim.get_cwd()
        path = os.path.join(cwd, path)
      path = os.path.realpath(path)
      bufid = int(bufid)
      self.model.buffers.append(path, bufid)
    self.model.emit('file-opened', filename=filename)

  def onvim_BufNew(self, bufid):
    log.debug('New {0}', bufid)

  def onvim_BufDelete(self, bufid, filename):
    bufid = int(bufid)
    self.model.buffers.remove(bufid)
    self.model.emit('file-closed', filename=filename)

  def onvim_VimLeave(self):
    log.debug('Signal: Leave')
    gtk.main_quit()

  def onvim_BufWritePost(self, bufid, filename):
    self.model.emit('file-saved', filename=filename)

  def onvim_BufFilePost(self, bufid, filename):
    log.debug('Signal: BufFilePost {0} {1}', bufid, filename)
    bufid = int(bufid)
    path = unicode(filename)
    if path:
      path = os.path.abspath(path)
    buf = self.model.buffers.get_by_bufid(bufid)
    if buf:
      buf.rename(path)


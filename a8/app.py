# -*- coding: utf-8 -*- 
# (c) 2005-2012 PIDA Authors
# vim: ft=python sw=2 ts=2 sts=2 tw=80


"""Abominade Monolith."""

import collections
import argparse
import os

from a8 import (terminals, files, buffers, vimembed, window, config, bookmarks,
                shortcuts, extensions, sessions)

class Abominade(object):
  """Abominade Monolith"""

  def __init__(self):
    self.signals = collections.defaultdict(list)
    self.home = config.InstanceDirectory()
    self.config = self.home.load_config()
    self.parse_args()
    if self.args.directory:
      os.chdir(self.args.directory)
    self.shortcuts = shortcuts.ShortcutManager(self)
    self.files = files.FileManager(self)
    self.buffers = buffers.BufferManager(self)
    self.terminals = terminals.TerminalManager(self)
    self.bookmarks = bookmarks.BookmarkManager(self)
    self.vim = vimembed.VimManager(self)
    self.ui = window.ApplicationWindow(self)
    self.ui.widget.maximize()
    # do this after show so the window appears after abominade in launcher
    if self.config['terminal_window']:
      self.terminals.popinout()
    self.sessions = sessions.SessionManager(self)
    self.sessions.start()
    extensions.load_extensions(self)

  def parse_args(self):
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--directory', help='Working directory to start in.')
    parser.add_argument('files', nargs='*', help='Files to open.')
    parser.add_argument('-s', '--session', action='store',
        choices=('user', 'local', 'none'),
        default=None,
        help='Maintain session per-user, per-working-dir, or no session.')
    parser.add_argument('--no-session', action='store_const', dest='session',
        const='none', help='Alias for --session=none.')
    parser.add_argument('--show-toolbar', action='store_true')
    self.args = parser.parse_args()
    if self.args.session is not None:
      self.config.opts['session_type'] = self.args.session
    if self.args.show_toolbar:
      self.config.opts['toolbar'] = True

  def start(self):
    """Start a8"""
    self.vim.start()
    self.files.browse()
    self.ui.start()

  def stop(self):
    """Stop a8"""
    self.sessions.save_session(polite=False)
    self.vim.stop()
    self.terminals.stop()

  def emit(self, signal, **kw):
    for callback in self.signals[signal]:
      callback(**kw)

  def connect(self, signal, callback):
    self.signals[signal].append(callback)

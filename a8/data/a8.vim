" (c) 2011 Abominade Authors


" Vim Remote Communication
" Requires +python PyGTK and Python DBUS

set nocompatible

silent function! VimSignal(name, ...)
    python call_signal(vim.eval('a:name'), vim.eval('a:000'))
endfunction


python << endpython
# Do this before we even breath
import vim

import os
import sys
# just in case, our pida might not be in the default path

import gtk, gobject
import dbus
from dbus import SessionBus
from dbus.service import Object, method, signal, BusName

# handles the main dbus loop
from a8 import bus


VIM_NAME = 'vim'
VIM_NS = bus.get_ns(VIM_NAME)
VIM_PATH = bus.get_path(VIM_NAME)
VIM_UID = vim.eval('A8_UID')
VIM_BUSNAME = bus.get_busname(VIM_NAME, VIM_UID)
VIM_RUNTIME = vim.eval('$VIMRUNTIME')
VIM_DOCS = os.path.join(VIM_RUNTIME, 'doc')


class VimDBUSService(Object):

  def __init__(self):
    busname = BusName(VIM_BUSNAME, bus=SessionBus())
    dbus.service.Object.__init__(self, busname, VIM_PATH)

  @method(VIM_NS, in_signature='s')
  def command(self, c):
    return vim.command(c)

  @method(VIM_NS, in_signature='s')
  def eval(self, e):
    return vim.eval(e)

  @method(VIM_NS, in_signature='s')
  def echo(self, s):
    vim.command('echo "%s"' % s)

  @method(VIM_NS)
  def new_file(self):
    buf = vim.current.buffer
    #XXX yet another vim hack
    if len(buf) == 1 and buf[0:1] == [''] and buf.name is None:
      buf[0] = 'a'
      vim.command('confirm enew')
      buf[0] = ''
    else:
      vim.command('confirm enew')

  @method(VIM_NS, in_signature='s')
  def open_file(self, path):
    vim.command('silent confirm e %s' % path)

  @method(VIM_NS, in_signature='as')
  def open_files(self, paths):
    for path in paths:
      self.open_file(path)

  @method(VIM_NS, out_signature='as')
  def get_buffer_list(self):
    # vim's buffer list also contains unlisted buffers
    # we don't want those
    return [
      buffer.name for buffer in vim.buffers
      if int(vim.eval("buflisted(%s)" % buffer.number))
    ]

  @method(VIM_NS, in_signature='s', out_signature='i')
  def get_buffer_number(self, path):
    return int(vim.eval("bufnr('%s')" % path))

  @method(VIM_NS, in_signature='s')
  def open_buffer(self, path):
    vim.command('b!%s' % self.get_buffer_number(path))

  @method(VIM_NS, in_signature='i')
  def open_buffer_id(self, bufid):
    vim.command('b!%s' % bufid)

  @method(VIM_NS)
  def save_current_buffer(self):
    vim.command('w')

  @method(VIM_NS, in_signature='s')
  def save_as_current_buffer(self, path):
    vim.command('saveas! %s' % path)

  @method(VIM_NS, in_signature='s')
  def close_buffer(self, path):
    vim.command('confirm bd%s' % path)

  @method(VIM_NS, in_signature='i')
  def close_buffer_id(self, bufid):
    if int(vim.eval("bufexists(%s)" % bufid)):
      vim.command('confirm bd%s' % bufid)
  
  @method(VIM_NS)
  def close_all_buffers(self):
    for path in self.get_buffer_list():
      self.close_buffer(path)

  @method(VIM_NS, in_signature='s')
  def close_buffers_under(self, under_path):
    for path in self.get_buffer_list():
      if path.startswith(under_path):
        self.close_buffer(path)

  @method(VIM_NS)
  def close_current_buffer(self):
    vim.command('confirm bd')

  @method(VIM_NS, out_signature='ai')
  def get_cursor(self):
    return vim.current.window.cursor

  @method(VIM_NS, in_signature='ii')
  def set_cursor(self, row, column):
    vim.current.window.cursor = (row, column)

  @method(VIM_NS, out_signature='s')
  def get_current_buffer(self):
    return vim.current.buffer.name or ''

  @method(VIM_NS, out_signature='i')
  def get_current_buffer_id(self):
    return int(vim.current.buffer.number)

  @method(VIM_NS)
  def quit(self):
    vim.command('confirm qall')

  @method(VIM_NS)
  def get_current_line(self):
    return vim.current.buffer[vim.current.window.cursor[0] - 1]

  @method(VIM_NS)
  def get_current_linenumber(self):
    return vim.current.window.cursor[0] - 1

  @method(VIM_NS)
  def get_current_character(self):
    y, x = vim.current.window.cursor
    return self.get_current_line()[x]

  @method(VIM_NS, in_signature='s')
  def insert_at_cursor(self, text):
    vim.command("normal i%s" % text)

  @method(VIM_NS, in_signature='s')
  def append_at_cursor(self, text):
    vim.command("normal a%s" % text)

  @method(VIM_NS, in_signature='s')
  def insert_at_linestart(VIM_NS, text):
    vim.command("normal I%s" % text)

  @method(VIM_NS, in_signature='s')
  def append_at_lineend(VIM_NS, text):
    vim.command("normal A%s" % text)

  @method(VIM_NS, in_signature='i')
  def goto_line(self, linenumber):
    vim.command('%s' % linenumber)
    vim.command('normal zzzv')

  @method(VIM_NS, out_signature='s')
  def get_current_word(self):
    return vim.eval('expand("<cword>")')

  @method(VIM_NS, out_signature='s')
  def get_cwd(self):
    return vim.eval('getcwd()')

  @method(VIM_NS, in_signature='s')
  def cut_current_word(self, text):
    vim.command('normal ciw%s' % text)

  @method(VIM_NS, in_signature='s')
  def replace_current_word(self, text):
    vim.command('normal ciw%s' % text)

  @method(VIM_NS, in_signature='s', out_signature='s')
  def get_register(self, name):
    return vim.eval('getreg("%s")' % name)

  @method(VIM_NS)
  def select_current_word(self):
    vim.command('normal viw')

  @method(VIM_NS, out_signature='s')
  def get_selection(self):
    return self.get_register('*')

  @method(VIM_NS)
  def copy(self):
    vim.command('normal "+y')

  @method(VIM_NS)
  def cut(self):
    vim.command('normal "+x')

  @method(VIM_NS)
  def paste(self):
    vim.command('normal "+p')

  @method(VIM_NS)
  def undo(self):
    vim.command('undo')

  @method(VIM_NS)
  def redo(self):
    vim.command('redo')

  @method(VIM_NS)
  def next(self):
    vim.command('bn')

  @method(VIM_NS)
  def prev(self):
    vim.command('bp')

  @method(VIM_NS, in_signature='s')
  def set_colorscheme(self, name):
    vim.command('colorscheme %s' % name)

  @method(VIM_NS, in_signature='si')
  def set_font(self, name, size):
    vim.command('set guifont=%s\\ %s' % (name, size))

  @method(VIM_NS, in_signature='s')
  def cd(self, path):
    vim.command('cd %s' % path)

  @method(VIM_NS, in_signature='i')
  def set_cursor_offset(self, offset):
    vim.current.window.cursor = offset_to_position(offset)

  @method(VIM_NS, out_signature='i')
  def get_cursor_offset(self):
    return get_offset()

  @method(VIM_NS, out_signature='s')
  def get_buffer_contents(self):
    return '\n'.join(vim.current.buffer)

  @signal(VIM_NS, signature='ss')
  def BufEnter(self, bufid, filename):
    pass

  @signal(VIM_NS, signature='s')
  def BufNew(self, bufid):
    pass

  @signal(VIM_NS, signature='ss')
  def BufDelete(self, bufid, filename):
    pass

  @signal(VIM_NS, signature='s')
  def BufWipeout(self, bufid):
    pass

  @signal(VIM_NS, signature='s')
  def BufLeave(self, bufid):
    pass

  @signal(VIM_NS, signature='s')
  def BufUnload(self, bufid):
    pass

  @signal(VIM_NS, signature='s')
  def BufHidden(self, bufid):
    pass

  @signal(VIM_NS, signature='ss')
  def BufAdd(self, bufid, filename):
    pass

  @signal(VIM_NS, signature='s')
  def BufNewFile(self, bufid):
    pass

  @signal(VIM_NS)
  def VimEnter(self):
    pass

  @signal(VIM_NS)
  def VimLeave(self):
    pass

  @signal(VIM_NS)
  def BufWritePre(self, signature='s'):
    pass

  @signal(VIM_NS, signature='ss')
  def BufWritePost(self, bufid, filename):
    pass

  @signal(VIM_NS)
  def BufReadPre(self, bufid):
    pass

  @signal(VIM_NS)
  def BufReadPost(self, bufid):
    pass

  @signal(VIM_NS)
  def CursorMoved(self):
    pass

  @signal(VIM_NS)
  def SwapExists(self):
    pass


def get_offset():
  return position_to_offset(*vim.current.window.cursor)


def position_to_offset(lineno, colno):
  result = colno
  for line in vim.current.buffer[:lineno-1]:
    result += len(line) + 1
  return result


def offset_to_position(offset):
  text = '\n'.join(vim.current.buffer) + '\n'
  lineno = text.count('\n', 0, offset) + 1
  try:
    colno = offset - text.rindex('\n', 0, offset) - 1
  except ValueError:
    colno = offset
  return lineno, colno


def clean_signal_args(args):
  args = list(args)
  for i, arg in enumerate(args):
    if arg is None or arg.startswith(VIM_DOCS):
      args[i] = ''
  return args


def call_signal(name, args):
  args = clean_signal_args(args)
  method = getattr(service, name)
  method(*args)


service = VimDBUSService()

endpython


" Now the vim events
silent augroup VimCommsDBus
silent au! VimCommsDBus
silent au VimCommsDBus BufEnter * silent call VimSignal('BufEnter', expand('<abuf>'), expand('<amatch>'))
silent au VimCommsDBus BufNew * silent call VimSignal('BufNew', expand('<abuf>'))
silent au VimCommsDBus BufNewFile * silent call VimSignal('BufNewFile', expand('<abuf>'))
silent au VimCommsDBus BufReadPre * silent call VimSignal('BufReadPre', expand('<abuf>'))
silent au VimCommsDBus BufReadPost * silent call VimSignal('BufReadPost', expand('<abuf>'))
silent au VimCommsDBus BufWritePre * silent call VimSignal('BufWritePre', expand('<abuf>'))
silent au VimCommsDBus BufWritePost * silent call VimSignal('BufWritePost', expand('<abuf>'), expand('<amatch>'))
silent au VimCommsDBus BufAdd * silent call VimSignal('BufAdd', expand('<abuf>'), expand('<amatch>'))
silent au VimCommsDBus BufDelete * silent call VimSignal('BufDelete', expand('<abuf>'), expand('<amatch>'))
silent au VimCommsDBus BufUnload * silent call VimSignal('BufUnload', expand('<abuf>'))
silent au VimCommsDBus BufUnload * silent call VimSignal('BufHidden', expand('<abuf>'))
silent au VimCommsDBus BufWipeout * silent call VimSignal('BufWipeout', expand('<abuf>'))
silent au VimCommsDBus VimLeave * silent call VimSignal('VimLeave')
silent au VimCommsDBus VimEnter * silent call VimSignal('VimEnter')
silent au VimCommsDBus CursorMovedI,CursorMoved * silent call VimSignal('CursorMoved')
silent au VimCommsDBus SwapExists * let v:swapchoice='d'

set hidden

" Some UI Stuffs
set nomore
set guioptions-=T
set guioptions-=m
set guioptions+=c
set ssop=buffers,winsize,tabpages



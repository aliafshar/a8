# -*- coding: utf-8 -*- 
# (c) 2005-2012 PIDA Authors
# vim: ft=python sw=2 ts=2 sts=2 tw=80

"""Terminal emulator."""

import os, re, pwd

import logbook
import gtk, gobject, gtk.gdk, pango, vte
import psutil
from pygtkhelpers import delegates

from a8 import resources, lists, contexts, window


log = logbook.Logger('Terminal')


def get_default_shell():
  """Returns the default shell for the user"""
  # Environ, or fallback to login shell
  return os.environ.get('SHELL', pwd.getpwuid(os.getuid())[-1])


class Unset(object):
  """Indicates an unset, i.e. default, option."""


class TerminalWindow(window.A8Window):

  def create_ui(self):
    self.post_configure()

  def post_configure(self):
    super(TerminalWindow, self).post_configure()
    self.set_title('Terminals')

  def on_widget__delete_event(self, window, event):
    # emulate closing by closing all terminals and hiding, but don't destroy
    # widgets so we don't have to manage re-creating them and setting up state
    for terminal in self.model.terminals.items:
      terminal.close()
    self.hide()
    return True


class TerminalConfiguration(object):
  """Configures a terminal."""

  default_opts = {
    'color_foreground': Unset,
    'color_background': Unset,
    'backspace_binding': Unset,
    'cursor_blink_mode': Unset,
    'cursor_shape': Unset,
    'font': Unset,
    'allow_bold': Unset,
    'audible_bell': Unset,
    'emulation': Unset,
    'pointer_autohide': Unset,
    'scroll_on_keystroke': Unset,
    'scroll_on_output': Unset,
    'scrollback_lines': 1000,
    'visible_bell': Unset,
    'word_chars': '-A-Za-z0-9,./?%&#:_',
  }

  erase_enum = {
    'auto': vte.ERASE_AUTO,
    'ascii_backspace': vte.ERASE_ASCII_BACKSPACE,
    'ascii_delete': vte.ERASE_ASCII_DELETE,
    'delete_sequence': vte.ERASE_DELETE_SEQUENCE,
    'tty': vte.ERASE_TTY,
  }

  cursor_shape_enum = {
    'block': vte.CURSOR_SHAPE_BLOCK,
    'ibeam': vte.CURSOR_SHAPE_IBEAM,
    'underline': vte.CURSOR_SHAPE_UNDERLINE,
  }

  cursor_blink_enum = {
    'system': vte.CURSOR_BLINK_SYSTEM,
    'on': vte.CURSOR_BLINK_ON,
    'off': vte.CURSOR_BLINK_OFF,
  }

  def __init__(self):
    """Create a new configuration."""
    self.opts = self.default_opts.copy()

  def update(self, options):
    """Update the options from a dict-like or list of tuple-pairs."""
    self.opts.update(options)

  def configure(self, term):
    """Configure the terminal to the stored options."""
    self.set_color_option(term, 'color_foreground')
    self.set_color_option(term, 'color_background')
    self.set_enum_option(term, self.erase_enum, 'backspace_binding')
    self.set_enum_option(term, self.cursor_shape_enum, 'cursor_shape')
    self.set_enum_option(term, self.cursor_blink_enum, 'cursor_blink_mode')
    self.set_font_option(term, 'font')
    self.set_simple_option(term, 'allow_bold')
    self.set_simple_option(term, 'audible_bell')
    self.set_simple_option(term, 'emulation')
    self.set_simple_option(term, 'pointer_autohide')
    self.set_simple_option(term, 'scroll_on_keystroke')
    self.set_simple_option(term, 'scroll_on_output')
    self.set_simple_option(term, 'scrollback_lines')
    self.set_simple_option(term, 'visible_bell')
    self.set_simple_option(term, 'word_chars')

  def set_enum_option(self, term, enum, opt):
    """Set an enum-based option."""
    val = self.opts.get(opt, Unset)
    if val is Unset:
      return
    enumval = enum.get(val, Unset)
    self.set_option(term, opt, enumval)

  def set_font_option(self, term, opt):
    """Set a font option."""
    val = self.opts.get(opt, Unset)
    if val is Unset:
      return
    fontdesc = pango.FontDescription(val)
    self.set_option(term, opt, fontdesc)

  def set_color_option(self, term, opt):
    """Set a color option."""
    val = self.opts.get(opt, Unset)
    if val is Unset:
      return
    color = gtk.gdk.color_parse(val)
    self.set_option(term, opt, color)

  def set_simple_option(self, term, opt):
    """Set a simple option."""
    val = self.opts.get(opt, Unset)
    if val is Unset:
      return
    self.set_option(term, opt, val)

  def set_option(self, term, opt, val):
    """Set an option."""
    if val is Unset:
      return
    setter = getattr(term, 'set_%s' % opt, None)
    if setter is not None:
      setter(val)
    else:
      raise KeyError('bad configuration key "%s".' % opt)


class TerminalView(delegates.SlaveView, lists.ListItem):
  """A8 Terminal Emulator."""

  MARKUP_TEMPLATE = '<b>{0}</b> (<b>{1}</b>)\n<span size="xx-small">{2}</span>'

  @property
  def markup_args(self):
    return (
      os.path.basename(self.cwd),
      self.pid,
      os.path.dirname(self.cwd)
    )

  def __init__(self, *args, **kw):
    super(TerminalView, self).__init__(*args, **kw)
    self.prompt_lines = set()

  def create_ui(self):
    self.widget.set_data('delegate', self)
    self.pid = None
    self.cwd = None
    self.box = gtk.HBox()
    self.box.set_spacing(3)
    self.widget.add(self.box)
    self.tools = gtk.VBox()
    self.tools2 = gtk.VBox()
    self.box.pack_start(self.tools, expand=False)
    self.stack = gtk.VBox()
    self.box.pack_start(self.stack)
    self.terminal = vte.Terminal()
    self.config = TerminalConfiguration()
    self.config.update(self.model.config.get('terminal', {}))
    self.config.configure(self.terminal)
    self.add_contexts()
    # Fix the size because by default it is huge.
    self.terminal.set_size_request(50, 50)
    self.stack.pack_start(self.terminal)
    self.scrollbar = gtk.VScrollbar()
    self.scrollbar.set_adjustment(self.terminal.get_adjustment())
    self.box.pack_start(self.scrollbar, expand=False)
    self.box.pack_start(self.tools2, expand=False)
    self.create_tools()
    self.create_finder()

  def create_tools(self):
    self.popinout_button = resources.load_button('terminal_pop_out.png',
      'Pop out terminals')
    self.update_popinout_button()
    self.close_button = resources.load_button('cross.png',
      'Close terminal window')
    self.browse_button = resources.load_button('folder.png',
      'Browse working directory')
    self.shell_button = resources.load_button('application_xp_terminal.png',
      'Open a shell in working directory')
    self.bookmark_button = resources.load_button('star.png',
      'Bookmark working directory')
    self.copy_button = resources.load_button('page_white_copy.png',
      'Copy selection')
    self.paste_button = resources.load_button('paste_plain.png',
      'Paste clipboard')
    self.selectall_button = resources.load_button('textfield_add.png',
      'Select all')
    self.selectnone_button = resources.load_button('textfield_delete.png',
      'Select None')
    self.find_button = resources.load_button('find.png',
      'Search for text', gtk.ToggleButton)
    self.tools2.pack_start(self.popinout_button, expand=False)
    self.tools2.pack_start(self.close_button, expand=False)
    self.tools.pack_start(self.browse_button, expand=False)
    self.tools.pack_start(self.shell_button, expand=False)
    self.tools.pack_start(self.bookmark_button, expand=False)
    self.tools2.pack_start(self.copy_button, expand=False)
    self.tools2.pack_start(self.paste_button, expand=False)
    self.tools2.pack_start(self.selectall_button, expand=False)
    self.tools2.pack_start(self.selectnone_button, expand=False)
    self.copy_button.set_sensitive(False)
    self.create_killer()
    self.create_confirmer()
    # This should work in VTE 0.26+ but doesn't in python-vte 0.28
    # so we make it conditional
    # TODO(afshar): fix this when python-vte is updated
    if hasattr(self.terminal, 'search_set_gregex'):
      self.tools.pack_start(self.find_button, expand=False)

  def create_finder(self):
    self.finder = gtk.HBox()
    self.finder.set_spacing(3)
    self.stack.pack_start(self.finder, expand=False)
    self.finder.set_no_show_all(True)
    self.find_text = gtk.Entry()
    self.findnext_button = resources.load_button('resultset_next.png',
      'Find next')
    self.findprev_button = resources.load_button('resultset_previous.png',
      'Find previous')
    self.finder.pack_start(self.findprev_button, expand=False)
    self.finder.pack_start(self.findnext_button, expand=False)
    self.finder.pack_start(gtk.Label('re'), expand=False)
    self.finder.pack_start(self.find_text)
    for child in self.finder.get_children():
      child.show()

  def create_confirmer(self):
    self.confirmer = gtk.HBox()
    self.confirmer.set_spacing(3)
    self.confirmer.set_border_width(3)
    self.stack.pack_start(self.confirmer, expand=False)
    self.confirmer.set_no_show_all(True)
    self.confirm_label = gtk.Label()
    self.confirm_label.set_alignment(1, 0.5)
    self.confirmer.pack_start(self.confirm_label)
    self.confirm_yes_button = resources.load_button('tick.png', 'Yes, kill')
    self.confirm_no_button = resources.load_button('cross.png', 'No, save')
    self.confirmer.pack_start(self.confirm_yes_button, expand=False)
    self.confirmer.pack_start(self.confirm_no_button, expand=False)
    for child in self.confirmer.get_children():
      child.show()

  def create_killer(self):
    self.killer_menu = gtk.Menu()
    signums = [
      ('SIGTERM', 15),
      ('SIGKILL', 9),
      ('SIGINT', 2),
      ('SIGABRT', 6),
    ]
    for signame, signum in signums:
      menuitem = gtk.MenuItem()
      menuitem.set_label('{0} ({1})'.format(signame, signum))
      self.killer_menu.append(menuitem)
      menuitem.set_data('signum', signum)
      menuitem.connect('activate', self.on_killer_activate)
    self.killer_menu.show_all()
    self.killer_button = resources.load_button(
      'script_lightning.png', 'Send signal to children')
    self.tools.pack_start(self.killer_button, expand=False)
    self.killer_shell_menu = gtk.Menu()
    for signame, signum in signums:
      menuitem = gtk.MenuItem()
      menuitem.set_label('{0} ({1})'.format(signame, signum))
      self.killer_shell_menu.append(menuitem)
      menuitem.set_data('signum', signum)
      menuitem.connect('activate', self.on_killer_shell_activate)
    self.killer_shell_menu.show_all()
    self.killer_shell_button = resources.load_button(
      'application_lightning.png', 'Send signal to shell')
    self.tools.pack_start(self.killer_shell_button, expand=False)

  def create_tab_widget(self):
    self.tab_box = gtk.HBox()
    self.tab_box.set_spacing(1)
    self.icon = resources.load_icon('application_xp_terminal.png')
    self.tab_box.pack_start(self.icon, expand=False)
    self.label = gtk.Label('Terminal')
    self.label.set_ellipsize(pango.ELLIPSIZE_START)
    small = pango.AttrScale(pango.SCALE_X_SMALL, 0, -1)
    self.label_attributes = pango.AttrList()
    self.label_attributes.insert(small)
    self.label.set_attributes(self.label_attributes)
    self.label.set_width_chars(9)
    self.tab_box.pack_start(self.label)
    self.tab_box.show_all()
    return self.tab_box

  def execute(self, argv=None, env=None, cwd=None):
    if argv is None:
      shell_prog = os.environ.get('SHELL', 'bash')
      argv = [shell_prog]
    if env is None:
      env = self.env_map_to_list(os.environ.copy())
    if cwd is None:
      cwd = os.getcwd()
    log.debug('Start {0} {1}'.format(argv, cwd))
    self.pid = self.terminal.fork_command(argv[0], argv, env, cwd)
    log.debug('Started pid {0}'.format(self.pid))
    self.cwd = cwd
    gobject.timeout_add(500, self.calculate_cwd)

  def env_map_to_list(self, env):
    return ['%s=%s' % (k, v) for (k, v) in env.items()]

  def calculate_cwd(self):
    """Calculate and store the CWD for the running process."""
    if self.pid is None:
      # The return value indicates whether gobject should continue polling.
      return False
    else:
      try:
        self.cwd = psutil.Process(self.pid).cwd()
        self.label.set_text(self.cwd)
        return True
      except psutil.AccessDenied:
        # The process already vanished
        return False

  def add_contexts(self):
    self.contexts = {}
    for context in contexts.ContextManager.context_order:
      self.add_context(context)

  def add_context(self, context):
    matchnum = self.terminal.match_add(context.ereg_expr)
    self.contexts[matchnum] = context

  def update_popinout_button(self):
    in_out = (self.model.terminals.popped_out and 'in' or 'out')
    self.popinout_button.set_image(resources.load_icon('terminal_pop_%s.png' % in_out))
    self.popinout_button.set_tooltip_text('Pop %s terminals' % in_out)

  def get_selection_text(self):
    if self.terminal.get_has_selection():
      # Get the selection value from the primary buffer
      clipboard = gtk.clipboard_get(gtk.gdk.SELECTION_PRIMARY)
      selection = clipboard.wait_for_text()
      return selection
    return None

  def pos_is_on_text(self, col, row, text):
    """Test whether the given coordinates match on the given text."""
    # check for a match by swapping in the selection value as the only match
    self.terminal.match_clear_all()
    self.terminal.match_add(re.escape(text))
    match = self.terminal.match_check(col, row)
    self.terminal.match_clear_all()
    self.add_contexts()   # swap original matches back in
    return match is not None

  def get_contexts_for_text(self, text):
    for context_type in contexts.ContextManager.context_order:
      context = context_type(self.model, self, text)
      if context.check_valid():
        yield context

  def on_terminal__child_exited(self, terminal):
    self.pid = None
    self.terminal.feed('\x1b[0;1;34mExited, status: \x1b[0;1;31m{0}'.format(
      self.terminal.get_child_exit_status()))
    self.terminal.connect('key-press-event', self._on_keypress_after_exit)

  def _on_keypress_after_exit(self, terminal, event):
    if event.keyval == gtk.keysyms.Return:
      self.close()

  def on_terminal__window_title_changed(self, terminal):
    pass

  def on_terminal__button_press_event(self, terminal, event):
    col, row = self.get_position_from_pointer(event.x, event.y)
    contexts = []
    # check text selection
    selection_text = self.get_selection_text()
    if selection_text and self.pos_is_on_text(col, row, selection_text):
      contexts = list(self.get_contexts_for_text(selection_text))
      self.on_match(selection_text, contexts, event)
    else:
      # check regular matches
      match = self.terminal.match_check(col, row)
      if match is not None:
        match_string, match_index = match
        contexts = list(self.get_contexts_for_text(match_string))
        self.on_match(match_string, contexts, event)

  def on_terminal__key_press_event(self, terminal, event):
    terminal_adj = terminal.get_adjustment()
    # Shift + Up
    if event.state & gtk.gdk.SHIFT_MASK and event.keyval == gtk.keysyms.Up:
      # scroll up to previous prompt (or location of previous Return keypress)
      input_lines_above = [x for x in sorted(self.prompt_lines, reverse=True) if
          x < terminal_adj.value and x >= terminal_adj.get_lower()]
      if len(input_lines_above):
        terminal_adj.value = input_lines_above[0]
      return True   # don't propagate (just writes garbage character)
    # Shift + Down
    if event.state & gtk.gdk.SHIFT_MASK and event.keyval == gtk.keysyms.Down:
      # scroll down to next prompt (or location of next Return keypress)
      input_lines_below = [x for x in sorted(self.prompt_lines) if x > terminal_adj.value]
      if len(input_lines_below):
        terminal_adj.value = input_lines_below[0]
      else:
        col, row = terminal.get_cursor_position()
        terminal_adj.value = row
      return True   # don't propagate (just writes garbage character)
    # Return
    if event.keyval == gtk.keysyms.Return:
      # record Return keypress as prompt line
      col, row = terminal.get_cursor_position()
      if row not in self.prompt_lines:
        self.prompt_lines.add(row)
      return False    # propagate

  def get_position_from_pointer(self, x, y):
    """Get the row/column position for a pointer position."""
    cw = self.terminal.get_char_width()
    ch = self.terminal.get_char_height()
    return int(x / cw), int(y / ch)

  def on_match(self, match_string, contexts, event):
    match_menus = []
    # get menus for all matching contexts
    for context in contexts:
      log.debug('Matched "{0}" as {1}', context.data, context.name)
      if event.button == 3:   # right click
        context_menu = self.get_match_menu(context, event)
        if context_menu is not None:
          match_menus.append(context_menu)
      elif event.state & gtk.gdk.CONTROL_MASK:
        self.on_match_default(context, event)
    if match_menus:
      match_menu = match_menus[0]
      # combine other menu items into first menu
      for other_match_menu in match_menus[1:]:
        match_menu.append(gtk.SeparatorMenuItem())
        for menu_item in other_match_menu.get_children():
          menu_item.reparent(match_menu)
      match_menu.popup(None, None, None, event.button, event.time)

  def get_match_menu(self, context, event):
    return context.create_menu()

  def on_match_default(self, context, event):
    pass

  def on_close_button__clicked(self, button):
    if self.pid:
      msg = 'Really? pid{0} is running. We will kill -9'.format(self.pid)
      self.confirm_label.set_text(msg)
      self.confirmer.show()
    else:
      self.close()

  def on_confirm_yes_button__clicked(self, button):
    psutil.Process(self.pid).send_signal(9)
    self.close()

  def on_confirm_no_button__clicked(self, button):
    self.confirmer.hide()

  def close(self):
    self.model.terminals.remove_tab(self)

  def on_popinout_button__clicked(self, button):
    self.model.terminals.popinout()

  def on_browse_button__clicked(self, button):
    self.model.files.browse(self.cwd)

  def on_shell_button__clicked(self, button):
    self.model.terminals.execute(cwd=self.cwd)

  def on_bookmark_button__clicked(self, button):
    self.model.bookmarks.add(self.cwd)

  def on_terminal__selection_changed(self, terminal):
    self.copy_button.set_sensitive(self.terminal.get_has_selection())

  def on_copy_button__clicked(self, button):
    self.terminal.copy_clipboard()

  def on_paste_button__clicked(self, button):
    self.terminal.paste_clipboard()

  def on_selectall_button__clicked(self, button):
    self.terminal.select_all()

  def on_selectnone_button__clicked(self, button):
    self.terminal.select_none()

  def on_killer_button__button_press_event(self, button, event):
    self.killer_menu.popup(None, None, None, event.button, event.time)

  def on_killer_shell_button__button_press_event(self, button, event):
    self.killer_shell_menu.popup(None, None, None, event.button, event.time)

  def on_killer_activate(self, menuitem):
    signum = menuitem.get_data('signum')
    for child in psutil.Process(self.pid).get_children():
      child.send_signal(signum)

  def on_killer_shell_activate(self, menuitem):
    signum = menuitem.get_data('signum')
    psutil.Process(self.pid).send_signal(signum)

  def on_find_button__clicked(self, button):
    if button.get_active():
      self.finder.show()
    else:
      self.finder.hide()

  def on_findnext_button__clicked(self, button):
    self.terminal.search_find_next()

  def on_findprev_button__clicked(self, button):
    self.terminal.search_find_previous()

  def on_find_text__changed(self, text):
    self.terminal.search_set_gregex(text.get_text())




class TerminalManager(lists.ListView):
  """Tabs containing terminals."""

  LABEL = 'Terminals'

  def __init__(self, model):
    super(TerminalManager, self).__init__(model)
    self.terminals_window = None
    self.popped_out = False

  def create_ui(self):
    lists.ListView.create_ui(self)
    self.book = gtk.Notebook()
    self.book.set_tab_pos(gtk.POS_BOTTOM)

  def stop(self):
    for item in self.items:
      # close terminals cleanly (see issue 22)
      try:
        os.close(item.terminal.get_pty())
      except OSError:
        pass

  def add_tab(self, delegate):
    self.book.append_page(delegate.widget, delegate.create_tab_widget())
    self.book.set_tab_reorderable(delegate.widget, True)
    self.book.show_all()
    self.book.set_current_page(self.book.page_num(delegate.widget))
    self.items.append(delegate)
    if self.popped_out:
      self.terminals_window.show()
      # unminimize and bring to front
      self.terminals_window.widget.window.show()

  def remove_tab(self, delegate):
    self.book.remove_page(self.book.page_num(delegate.widget))
    self.items.remove(delegate)

  @property
  def current_page(self):
    return self.book.get_nth_page(self.book.get_current_page())

  @property
  def current_view(self):
    return self.current_page.get_data('delegate')

  def execute(self, argv=None, env=None, cwd=None):
    t = TerminalView(self.model)
    t.execute(argv, env, cwd)
    self.add_tab(t)
    self.model.emit('terminal-executed', argv=argv, env=env, cwd=cwd)

  def on_items__item_activated(self, objectlist, item):
    self.book.set_current_page(self.book.page_num(item.widget))

  def grab_focus(self):
    self.current_view.terminal.grab_focus()

  def next(self):
    current = self.book.get_current_page()
    if current == self.book.get_n_pages() - 1:
      update = 0
    else:
      update = current + 1
    self.book.set_current_page(update)
    self.grab_focus()

  def prev(self):
    current = self.book.get_current_page()
    if current == 0:
      update = self.book.get_n_pages() - 1
    else:
      update = current - 1
    self.book.set_current_page(update)
    self.grab_focus()

  def popinout(self):
    if self.popped_out:
      # pop in
      self.terminals_window.widget.remove(self.book)
      self.model.ui.vpaned.pack2(self.book, resize=False, shrink=False)
      self.terminals_window.hide()
      self.popped_out = False
    else:
      # pop out
      if self.terminals_window is None:
        self.terminals_window = TerminalWindow(self.model)
      self.book.reparent(self.terminals_window.widget)
      self.terminals_window.show()
      self.popped_out = True
    self.update_popinout_button()

  def update_popinout_button(self):
    for tab in self.items:
      tab.update_popinout_button()

# -*- coding: utf-8 -*- 
# (c) 2005-2011 PIDA Authors
# vim: ft=python sw=2 ts=2 sts=2 tw=80


import gtk

from pygtkhelpers import delegates, utils

from a8 import shortcuts, resources


gtk.window_set_default_icon(resources.load_icon('a8.png').get_pixbuf())


class SplashScreen(object):
  """Splash screen."""
  def __init__(self):
    self.window = gtk.Window()
    self.window.set_decorated(False)
    self.window.set_position(gtk.WIN_POS_CENTER_ALWAYS)
    b = gtk.VBox()
    b.set_border_width(40)
    b.set_spacing(3)
    self.window.add(b)
    b.pack_start(resources.load_icon('a8.png'))
    l = gtk.Label()
    l.set_markup('<small>abominade <b><tt>&#9829;</tt></b> you</small>')
    l.set_use_markup(True)
    b.pack_start(l, expand=False)

  def start(self):
    """Launch the splash screen."""
    self.window.show_all()
    utils.refresh_gui()

  def stop(self):
    """Stop the splash screen."""
    self.window.hide()
    self.window.destroy()


class ApplicationWindow(delegates.WindowView):
  """Main application window."""

  def create_ui(self):
    """Create the user interface."""
    self.splash = SplashScreen()
    self.splash.start()
    self.hpaned = gtk.HPaned()
    self.widget.add(self.hpaned)
    self.vpaned = gtk.VPaned()
    self.hpaned.pack2(self.vpaned)
    self.hpaned.set_position(200)
    self.plugins = PluginTabs()
    self.hpaned.pack1(self.plugins.widget)
    self.plugins.add_main(self.model.buffers)
    self.plugins.add_tab(self.model.files)
    self.plugins.add_tab(self.model.bookmarks)
    self.plugins.add_tab(self.model.terminals)
    self.vpaned.pack1(self.model.vim.widget, resize=True, shrink=False)
    self.vpaned.pack2(self.model.terminals.book, resize=False, shrink=False)
    self.widget.set_title('Abominade loves you.')
    self.accel_group = self.model.shortcuts.create_group()
    self.widget.add_accel_group(self.accel_group)
    self.splash.stop()
    self.set_title('')
    self.widget.resize(640, 480)
    self.widget.show_all()

  def on_widget__delete_event(self, window, event):
    self.model.stop()

  def start(self):
    self.show_and_run()

  def set_title(self, filename):
    self.widget.set_title(u'a8♥u {0}'.format(filename))

  def focus_files(self):
    self.plugins.focus_delegate(self.model.files)

  def focus_bookmarks(self):
    self.plugins.focus_delegate(self.model.bookmarks)

  def focus_terminals(self):
    self.plugins.focus_delegate(self.model.terminals)

  def focus_buffers(self):
    self.models.buffers.items.grab_focus()


class PluginTabs(delegates.SlaveView):
  """Tabs containing the main plugins."""

  TAB_POS = gtk.POS_TOP

  def create_ui(self):
    self.stack = gtk.VPaned()
    self.widget.add(self.stack)
    self.book = gtk.Notebook()
    self.book.set_tab_pos(self.TAB_POS)
    self.stack.pack2(self.book, resize=True, shrink=False)

  def add_main(self, delegate):
    self.stack.pack1(delegate.widget, resize=True, shrink=False)

  def add_tab(self, delegate):
    self.book.append_page(delegate.widget, delegate.create_tab_widget())

  def focus_delegate(self, delegate):
    self.book.set_current_page(self.book.page_num(delegate.widget))
    delegate.items.grab_focus()


if __name__ == '__main__':
  w = ApplicationWindow()
  w.widget.resize(400, 400)
  w.show_and_run()

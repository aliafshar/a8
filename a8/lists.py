# -*- coding: utf-8 -*- 
# (c) 2005-2011 PIDA Authors
# vim: ft=python sw=2 ts=2 sts=2 tw=80

"""Buffer list."""

import cgi

import gtk
from pygtkhelpers import delegates
from pygtkhelpers.ui import objectlist

from a8 import resources


class ListItem(object):

  MARKUP_TEMPLATE = ''

  @property
  def markup_args(self):
    return ()

  @property
  def markup(self):
    return self.MARKUP_TEMPLATE.format(
      *(cgi.escape(str(i)) for i in self.markup_args))


class ListView(delegates.SlaveView):

  LABEL   = 'Unnamed'
  ICON    = 'application_xp_terminal.png'
  COLUMNS = [objectlist.Column('markup', use_markup=True)]

  def create_ui(self):
    """Create the user interface."""
    self.stack = gtk.VBox()
    self.widget.add(self.stack)
    self.scroll = gtk.ScrolledWindow()
    self.scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    self.stack.pack_end(self.scroll)
    self.items = objectlist.ObjectList(self.COLUMNS)
    self.items.set_headers_visible(False)
    self.scroll.add(self.items)

  def create_tab_widget(self):
    """Create the tab widget."""
    vb = gtk.VBox()
    vb.set_spacing(3)
    icon = resources.load_icon(self.ICON)
    icon.set_tooltip_text(self.LABEL)
    vb.pack_start(icon, expand=False)
    vb.show_all()
    return vb

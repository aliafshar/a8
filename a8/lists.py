# -*- coding: utf-8 -*- 
# (c) 2005-2011 PIDA Authors
# vim: ft=python sw=2 ts=2 sts=2 tw=80

"""Buffer list."""

import gtk
from pygtkhelpers import delegates
from pygtkhelpers.ui import objectlist

from a8 import resources


class ListView(delegates.SlaveView):

  LABEL   = 'Unnamed'
  ICON    = 'application_xp_terminal.png'
  COLUMNS = [objectlist.Column('markup', use_markup=True)]

  def create_ui(self):
    """Create the user interface."""
    self.scroll = gtk.ScrolledWindow()
    self.scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    self.widget.add(self.scroll)
    self.items = objectlist.ObjectList(self.COLUMNS)
    self.items.set_headers_visible(False)
    self.scroll.add(self.items)

  def create_tab_widget(self):
    """Create the tab widget."""
    vb = gtk.VBox()
    vb.set_spacing(3)
    icon = resources.load_icon(self.ICON)
    label = gtk.Label(self.LABEL)
    label.set_angle(90)
    vb.pack_start(label)
    vb.pack_start(icon, expand=False)
    vb.show_all()
    return vb

# -*- coding: utf-8 -*- 
# (c) 2005-2012 PIDA Authors
# vim: ft=python sw=2 ts=2 sts=2 tw=80


"""Buffer list."""


import cgi
import gtk, gtk.gdk
from pygtkhelpers import delegates
from pygtkhelpers.ui import objectlist

from a8 import resources, actions


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

  TOOL_ACTIONS = []

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
    self.tab_icon = resources.load_icon(self.ICON)
    self.tab_icon.set_tooltip_text(self.LABEL)
    self.tab_holder = gtk.EventBox()
    self.tab_holder.add(self.tab_icon)
    self.tab_icon.set_can_focus(False)
    self.tab_holder.set_can_focus(False)
    self.tab_holder.add_events(gtk.gdk.BUTTON_PRESS_MASK)
    self.tab_holder.connect('button-press-event', self.on_tab_icon_button)
    vb.pack_start(self.tab_holder, expand=False)
    vb.show_all()
    return vb

  def create_tool_menu(self):
    return actions.create_action_menu(self.TOOL_ACTIONS,
                                      self.on_tool_activate)

  def on_tool_activate(self, item):
    action_key = item.get_data('action_key')
    callback = getattr(self, 'on_%s_activate' % action_key, None)
    if callback is None:
      raise NotImplementedError(action_key)
    else:
      callback()

  def on_tab_icon_button(self, icon, event):
    if event.button == 3 and self.TOOL_ACTIONS:
      menu = self.create_tool_menu()
      menu.show_all()
      menu.popup(None, None, None, event.button, event.time)

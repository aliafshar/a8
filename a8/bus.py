# -*- coding: utf-8 -*- 
# (c) 2005-2012 PIDA Authors
# vim: ft=python sw=2 ts=2 sts=2 tw=80


import os

import gtk, dbus

# Configure our mainloop
from dbus.mainloop.glib import DBusGMainLoop
mainloop = DBusGMainLoop(set_as_default=True)


A8_UID = 'a8_{uid}'.format(uid=os.getpid())
NS_TEMPLATE = 'uk.co.pida.{name}'
BUS_TEMPLATE = 'uk.co.pida.{name}.{uid}'
PATH_TEMPLATE = '/{name}'


def get_ns(name):
  return NS_TEMPLATE.format(name=name)


def get_busname(name, uid=A8_UID):
  return BUS_TEMPLATE.format(name=name, uid=uid)


def get_path(name):
  return PATH_TEMPLATE.format(name=name)


def create_session(busname):
  def on_watch(busname):
    if busname:
      gtk.main_quit()
  session = dbus.SessionBus()
  watch = session.watch_name_owner(busname, on_watch)
  gtk.main()
  return session


def connect(name):
  busname = get_busname(name)
  session = create_session(busname)
  busobj = session.get_object(busname, get_path(name))
  return dbus.Interface(busobj, get_ns(name))


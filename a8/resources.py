# -*- coding: utf-8 -*- 
# (c) 2005-2012 PIDA Authors
# vim: ft=python sw=2 ts=2 sts=2 tw=80


import os
import gtk


def get_resource_directory():
  """Get the resource directory."""
  return os.path.join(os.path.dirname(__file__), 'data')


def get_resource_path(path):
  """Get a resource path relative to the resource directory."""
  return os.path.join(get_resource_directory(), path)


def get_icon_path(name):
  """Get the path to an icon file."""
  return get_resource_path(os.path.join('icons', name))


def load_icon(name):
  """Create an image from an icon name."""
  img = gtk.Image()
  img.set_from_file(get_icon_path(name))
  return img


def load_button(name, tooltip, button_type=gtk.Button):
  """Create an image button from an icon name."""
  button = button_type()
  button.set_image(load_icon(name))
  button.set_tooltip_text(tooltip)
  return button



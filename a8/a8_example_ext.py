# -*- coding: utf-8 -*- 
# (c) 2005-2011 PIDA Authors
# vim: ft=python sw=2 ts=2 sts=2 tw=80

"""Example a8 extension."""


from datetime import datetime

from a8 import lists


class SaveLogItem(lists.ListItem):

  MARKUP_TEMPLATE = '<b>{0}</b>\n{1}'

  def __init__(self, name):
    self.name = name
    self.time = datetime.now()

  @property
  def markup_args(self):
    return (self.name, self.time)


class SaveLog(lists.ListView):

  ICON = 'lorry.png'

  def save(self, filename):
    self.items.append(SaveLogItem(filename))


def annotate_file(item):
  """Annotate files with the first letter of their name."""
  item.annotation = item.basename[0] + ' '


def setup(app):
  # Simple signal handler to annotate files
  app.connect('file-item-added', annotate_file)
  # Plugin list item
  save_log = SaveLog(app)
  app.connect('file-saved', save_log.save)
  save_log.items.append(SaveLogItem('Started'))
  app.ui.plugins.add_tab(save_log)


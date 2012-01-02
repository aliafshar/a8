# -*- coding: utf-8 -*- 
# (c) 2005-2012 PIDA Authors
# vim: ft=python sw=2 ts=2 sts=2 tw=80

import os
import yaml
import gobject
import logbook

log = logbook.Logger('Sessions')


class SessionManager(object):

  def __init__(self, model):
    self.model = model
    self.filename = self.model.home.path('session.yaml')
    self.session = self.load()
    if self.session is None:
      self.session = {'terminals': []}

  def save_session(self):
    self.session['terminals'] = [t.cwd for t in self.model.terminals.items]
    self.model.vim.save_session()
    self.save()
    return True

  def load(self):
    if not os.path.exists(self.filename):
      return
    with open(self.filename) as f:
      data = f.read()
    if not data:
      log.error('Empty file')
      return
    session = yaml.load(data)
    if not isinstance(session, dict):
      log.error('Bad file')
      return
    return session

  def start(self):
    if not self.model.config.get('session', True):
      self.model.terminals.execute()
      return
    terminals = self.session.get('terminals', [])
    if terminals:
      for cwd in terminals:
        self.model.terminals.execute(cwd=cwd)
    else:
      self.model.terminals.execute()
    gobject.timeout_add(5000, self.save_session)

  def save(self):
    data = yaml.dump(self.session, default_flow_style=False)
    with open(self.filename, 'w') as f:
      f.write(data)



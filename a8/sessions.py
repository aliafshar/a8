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
    self.filename = self.session_path('session.yaml')
    if self.filename:
      session_path = os.path.dirname(self.filename)
      log.info('Using session path %s' % session_path)
      if not os.path.exists(session_path):
        os.mkdir(session_path)
    else:
      log.info('Session disabled')
    self.session = self.load()
    if self.session is None:
      self.session = {'terminals': []}

  def session_path(self, filename):
    session_type = self.model.config['session_type']
    if session_type == 'local':
      return os.path.join(os.getcwd(), '.a8', filename)
    elif session_type == 'user':
      return self.model.home.path(filename)
    return None

  def save_session(self, polite=False):
    """Save abominade and vim sessions if sessions enabled.

    If polite=True and vim is in certain interactive modes, skip saving vim
    session to avoid causing mode glitches."""
    self.session['terminals'] = [t.cwd for t in self.model.terminals.items]
    self.model.vim.save_session(polite=polite)
    self.save()
    return True

  def load(self):
    if not self.filename or not os.path.exists(self.filename):
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
    if self.filename is None:
      self.model.terminals.execute()
      return
    terminals = self.session.get('terminals', [])
    if terminals:
      for cwd in terminals:
        self.model.terminals.execute(cwd=cwd)
    else:
      self.model.terminals.execute()
    gobject.timeout_add(5000, self.save_session, True)

  def save(self):
    if self.filename is not None:
      data = yaml.dump(self.session, default_flow_style=False)
      with open(self.filename, 'w') as f:
        f.write(data)



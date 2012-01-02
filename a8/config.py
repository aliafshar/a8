# -*- coding: utf-8 -*- 
# (c) 2005-2012 PIDA Authors
# vim: ft=python sw=2 ts=2 sts=2 tw=80


"""YAML-based configuration."""


import os
import argparse
import yaml


class ConfigError(ValueError):
  """An error in the configuration."""


class Config(object):
  """Configuration object"""
  def __init__(self):
    self.opts = {}

  def get(self, k, default=None):
    return self.opts.get(k, default)

  def load_from_file(self, path):
    """Load options from a file."""
    if os.path.exists(path):
      with open(path) as f:
        opts = yaml.load(f)
        self.load_from(opts)

  def load_from(self, opts):
    """Load options from a dict-like or list of pairs."""
    if not opts:
      return
    try:
      self.opts.update(opts)
    except ValueError:
      raise ConfigError('Options are not a k/v map.')


class InstanceDirectory(object):
  """Where user data is stored."""

  def __init__(self, user_path=os.path.expanduser('~/.a8')):
    self.user_path = user_path
    self.create()
    self.config_path = self.path('config.yaml')
    self.shortcuts_path = self.path('shortcuts.yaml')

  def create(self):
    if not os.path.exists(self.user_path):
      os.mkdir(self.user_path)

  def path(self, filename):
    return os.path.join(self.user_path, filename)

  def load_config(self):
    config = Config()
    config.load_from_file(self.config_path)
    return config

  def load_shortcuts(self):
    config = Config()
    config.load_from_file(self.shortcuts_path)
    return config

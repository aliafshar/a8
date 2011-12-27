# (c) 2005-2011 PIDA Authors
# vim: ft=python sw=2 ts=2 sts=2 tw=80

import pytest
from pida.core import config


def test_missing():
  with pytest.raises(config.ConfigError):
    c = config.Config()
    c.load_from_file('/banana')


def test_nondict():
  with pytest.raises(config.ConfigError):
    c = config.Config()
    c.load_from('123')


# -*- coding: utf-8 -*- 
# (c) 2005-2012 PIDA Authors
# vim: ft=python sw=2 ts=2 sts=2 tw=80


import logbook
log = logbook.Logger('Extensions')


def import_string(import_name):
  if ':' in import_name:
    module, obj = import_name.split(':', 1)
  elif '.' in import_name:
    items = import_name.split('.')
    module = '.'.join(items[:-1])
    obj = items[-1]
  else:
    return __import__(import_name)
  return getattr(__import__(module, None, None, [obj]), obj)


def load_extension(model, import_name):
  try:
    extension = import_string(import_name)
    extension.setup(model)
    log.debug('Loaded: {0}', import_name)
  except Exception, e:
    log.error('Failed: {0} {1}', import_name, e)


def load_extensions(model):
  extension_names = model.config.get('extensions', [])
  for import_name in extension_names:
    load_extension(model, import_name)

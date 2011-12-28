# -*- coding: utf-8 -*- 
# (c) 2005-2011 PIDA Authors
# vim: ft=python sw=2 ts=2 sts=2 tw=80


"""Main Abominade entry point script."""


from a8 import app


def main():
  """Run Abominade."""
  a8 = app.Abominade()
  a8.start()


if __name__ == '__main__':
  main()

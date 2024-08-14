#!/usr/bin/env python

import sqlite3
import sys


if __name__ == '__main__':
  db = sqlite3.connect('./db.sqlite')
  db.execute("""
    insert into note(when_iso, what)
    values(strftime('%Y-%m-%dT%H:%M:%fZ'), ?);
  """, (sys.stdin.read(),))
  db.commit()


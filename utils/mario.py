#!/usr/bin/env python
# pipe handler

from sys import stdin, stdout

def pull(class_type, pipe=stdin):
    """pull(pipe, [class_type=stdin]) -> g

    Reads from a pipe (defaulting to sys.stdin) and yields objects of
    type 'class_type'.
    """
    return (obj_class(line) for line in pipe)

def push(objects, pipe=stdout):
    """push(objects, [pipe=stdin]) -> None

    Takes in an iterator or generator of objects and dumps them to a
    pipe (defaulting to sys.stdout"""
    for o in objects:
        pipe.write(o + '\n')

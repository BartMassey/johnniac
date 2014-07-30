# Copyright © 2014 Bart Massey
# Quick implementation of Warren Harrison's
# Johnniac architecture.

# Number of words of machine storage.
memory_size = 26

import re
from sys import stderr

# Error message printer.
def error(*args, **kwargs):
    kwargs["file"] = stderr
    print(*args, **kwargs)

# Actual storage.
memory = [0]*memory_size

# Regex to match comments in decimal dumps.
comment = re.compile("#.*")

# Return the "tens-complement" string of a digit string.
def tens_complement(ds):
    result = ""
    for d in ds:
        nd = str(9 - int(d))
        result += nd
    return str(int(nd) + 1)

# Return the value of a decimal word string. Throw an error
# on bad inputs. Relies on int() to do most of the work.
# Negative inputs are treated as "tens-complement".
def parse_word(s):
    if s[0] == '-':
        s = tens_complement(s[1:])
    return int(s)

# Load a "decimal dump" from a file.
# Format is either <word> or <address> <word>
def load(filename):
    global memory
    try:
        f = open(filename, "r")
    except:
        error("%s: open failed" % (filename,))
        return
    temp_memory = memory.copy()
    addr = 0
    line = 1
    for w in f:
        uw = comment.sub(w, '')
        ws = uw.split()
        if len(ws) == 0:
            continue
        if len(ws) > 2:
            error("line %d: malformed line" % (line,))
            return
        if len(ws) == 2:
            try:
                addr = parse_word(ws[0])
            except:
                error("line %d: malformed address" % (line,))
                return
        try:
            if len(ws) == 2:
                data = parse_word(ws[1])
            else:
                data = parse_word(ws[0])
        except:
                error("line %d: malformed data word" % (line,))
                return
        temp_memory[addr] = data
        addr += 1
        line += 1
    memory = temp_memory

# True when main loop is supposed to keep running.
running = True

# Command: exit the main loop.
def command_exit(args):
    global running
    if (args != []):
        error("usage: exit")
        return
    running = False

# Command: load a program.
def command_load(args):
    if (len(args) != 1):
        error("usage: load <filename>")
        return
    load(args[0])

commands = { \
    "exit" : command_exit, \
    "l" : command_load, \
    "load" : command_load, \
}

# Interactive command loop.
while running:
    try:
        todo = input("? ")
    except EOFError:
        print()
        running = False
        continue
    except:
        error("interrupted")
        continue
    command = todo.split()
    if len(command) == 0:
        continue
    if command[0] not in commands:
        error("%s: unknown command" % command[0])
        continue
    commands[command[0]](command[1:])

# Copyright © 2014 Bart Massey
# [This program is licensed under the "MIT License"]
# Please see the file COPYING in the source
# distribution of this software for license terms.

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

# Machine state.
memory = [0]*memory_size
pc = 0
acc = 0

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
    if len(s) > 5 or (len(s) > 0 and s[0] == '-'):
        raise OverflowError()
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
        uw = comment.sub('', w)
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
        print("+ %05d %05d" % (addr, data))
        temp_memory[addr] = data
        addr += 1
        line += 1
    memory = temp_memory

# Actually run the Johnniac emulator.
def go(addr=0):
    global acc, pc
    pc = addr
    while True:
        if pc < 0 or pc >= len(memory):
            error("%d: illegal pc" % (pc,))
            return
        insn = memory[pc]
        if insn < 0 or insn >= 11000:
            error("%d: %d: illegal instruction" % (pc, insn))
            return
        op = insn // 1000
        operand = insn % 1000
        print("+ %05d: %02d %03d" % (pc, op, operand))
        if   op ==  0:   # HALT
            return
        elif op ==  1:   # LOAD
            if operand >= len(memory):
                error("%d: LOAD %d: illegal address" % (pc, operand))
                return
            acc = memory[operand]
        elif op == 2:    # STORE
            if operand >= len(memory):
                error("%d: STORE %d: illegal address" % (pc, operand))
                return
            memory[operand] = acc
        elif op == 3:    # ADD
            if operand >= len(memory):
                error("%d: ADD %d: illegal address" % (pc, operand))
                return
            acc += memory[operand]
            acc %= 100000
        elif op == 4:    # MULTIPLY
            if operand >= len(memory):
                error("%d: MULTIPLY %d: illegal address" % (pc, operand))
                return
            acc *= memory[operand]
            acc %= 100000
        elif op == 5:    # DIVIDE
            if operand >= len(memory):
                error("%d: DIVIDE %d: illegal address" % (pc, operand))
                return
            if acc == 0:
                error("%d: DIVIDE by 0" % (pc,))
                return
            acc = memory[operand] / acc
        elif op == 6:    # SUBTRACT
            if operand >= len(memory):
                error("%d: DIVIDE %d: illegal address" % (pc, operand))
                return
            acc -= memory[operand]
            if acc < 0:
                acc += 100000
        elif op == 7:    # TEST
            if operand >= len(memory):
                error("%d: TEST %d: illegal destination" % (pc, operand))
                return
            if acc == 0:
                pc = operand
        elif op == 8:    # GET
            if operand >= len(memory):
                error("%d: GET %d: illegal address" % (pc, operand))
                return
            while True:
                got = input("> ")
                try:
                    num = parse_word(got)
                except:
                    error("%s: bad word", (got,))
                    continue
                break
            memory[operand] = got
        elif op == 9:     # PUT
            if operand >= len(memory):
                error("%d: PUT %d: illegal address" % (pc, operand))
                return
            outword = memory[operand]
            print(format(outword, "05d"))
        elif op == 10:    # NOOP
            pass
        else:
            error("%d: illegal instruction" % (pc,))
            return
        pc += 1


# True when main loop is supposed to keep running.
running = True

# Command: exit the main loop.
def command_exit(args):
    global running
    if args != []:
        error("usage: exit")
        return
    running = False

# Command: load a program.
def command_load(args):
    if len(args) != 1:
        error("usage: load <filename>")
        return
    load(args[0])

# Command: run a program.
def command_go(args):
    if len(args) > 1:
        error("usage: go [<address>]")
        return
    if len(args) == 1:
        addr = parse_word(args[0])
    else:
        addr = 0
    go(addr)

commands = { \
    "exit" : command_exit, \
    "l" : command_load, \
    "load" : command_load, \
    "g" : command_go, \
    "go" : command_go, \
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

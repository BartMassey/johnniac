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

# Johnniac load exception class.
# XXX Arguably, this should be subclassed
# for various kinds of load exception.
class LoadException(Exception):
    def __init__(self, msg):
        self.value = msg

# Load a "decimal dump" from a file.
# Format is either <word> or <address> <word>.
# Comments started with "#" extend to end-of-line.
# Passes through any exception generated by open(filename).
# Raises a LoadException if something else goes wrong
# with the load.
def load(filename):
    global memory
    f = open(filename, "r")
    temp_memory = memory.copy()
    addr = 0
    line = 1
    for w in f:
        uw = comment.sub('', w)
        ws = uw.split()
        if len(ws) == 0:
            continue
        if len(ws) > 2:
            raise LoadException("line %d: malformed line" % (line,))
        if len(ws) == 2:
            try:
                addr = parse_word(ws[0])
            except:
                raise LoadException("line %d: malformed address" % (line,))
        try:
            if len(ws) == 2:
                data = parse_word(ws[1])
            else:
                data = parse_word(ws[0])
        except:
                raise LoadException("line %d: malformed data word" % (line,))
        print("+ %05d %05d" % (addr, data))
        temp_memory[addr] = data
        addr += 1
        line += 1
    memory = temp_memory

# Johnniac execution exception class.
# XXX Arguably, this should be subclassed
# for various kinds of execution exception.
class ExecException(Exception):
    def __init__(self, msg):
        self.value = msg

# Check whether the given operand is a valid address.
def check_address(operand, insn_name):
    global pc
    if operand < 0 or operand >= len(memory):
        raise ExecException("%d: %s %d: illegal address" % \
                            (pc, insn_name, operand))

# Actually run the Johnniac emulator.
# Raises ExecException if something goes wrong.
def go(addr=None):
    global acc, pc

    if addr != None:
        pc = addr
    while True:
        if pc < 0 or pc >= len(memory):
            raise ExecException("%d: illegal pc" % (pc,))
        insn = memory[pc]
        op = insn // 1000
        operand = insn % 1000
        print("+ %05d: %02d %03d" % (pc, op, operand))
        if   op ==  0:   # HALT
            return
        elif op ==  1:   # LOAD
            check_address(operand, "LOAD")
            acc = memory[operand]
        elif op == 2:    # STORE
            check_address(operand, "STORE")
            memory[operand] = acc
        elif op == 3:    # ADD
            check_address(operand, "ADD")
            acc += memory[operand]
            acc %= 100000
        elif op == 4:    # MULTIPLY
            check_address(operand, "MULTIPLY")
            acc *= memory[operand]
            acc %= 100000
        elif op == 5:    # DIVIDE
            check_address(operand, "DIVIDE")
            if acc == 0:
                raise ExecException("%d: DIVIDE by 0" % (pc,))
            acc = memory[operand] / acc
        elif op == 6:    # SUBTRACT
            check_address(operand, "SUBTRACT")
            acc -= memory[operand]
            if acc < 0:
                acc += 100000
        elif op == 7:    # TEST
            if acc == 0:
                if operand >= len(memory):
                    raise ExecException("%d: TEST %d: illegal destination" % \
                                        (pc, operand))
                pc = operand
        elif op == 8:    # GET
            check_address(operand, "GET")
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
            check_address(operand, "PUT")
            outword = memory[operand]
            print(format(outword, "05d"))
        elif op == 10:    # NOOP
            pass
        else:
            raise ExecException("%d: illegal instruction" % (pc,))
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
    try:
        load(args[0])
    except LoadException as e:
        error(e.value)
    except:
        error("%s: open failed" % (args[0],))

# Command: run a program.
def command_go(args):
    if len(args) > 1:
        error("usage: go [<address>]")
        return
    if len(args) == 1:
        try:
            addr = parse_word(args[0])
        except:
            error("%s: bad address" % (args[0],))
            return
    else:
        addr = 0
    try:
        go(addr)
    except ExecException as e:
        error(e.value)

# Command: continue execution at current PC
def command_continue(args):
    global pc
    if len(args) != 0:
        error("usage: continue")
        return
    go(pc)
# Command: print machine state.
def command_print(args):
    global pc, acc
    if len(args) > 1:
        error("usage: print [<thing>]")
        return
    if len(args) == 1:
        if args[0] == "%acc":
            print("%05d" % (acc,))
            return
        if args[0] == "%pc":
            print("%05d" % (pc,))
            return
        try:
            addr = parse_word(args[0])
        except:
            error("%s: not a source address" % (args[0]))
            return
        try:
            check_address(addr, "source")
        except ExecException:
            error("%03d: invalid source address" % (addr,))
            return
        print("%03d: %05d" % (addr, memory[addr]))
        return
    print("%%pc=%05d" % (pc,))
    print("%%acc=%05d" % (acc,))
    for a in range(len(memory)):
        print("%03d: %05d" % (a, memory[a]))

def command_set(args):
    global pc, acc
    if len(args) != 2:
        error("usage: set <target> <value>")
        return
    try:
        value = parse_word(args[1])
    except:
        error("%s: bad value" % (args[1],))
        return
    if args[0] == "%acc":
        acc = value
        return
    if args[0] == "%pc":
        pc = value
        return
    try:
        addr = parse_word(args[0])
    except:
        error("%s: not a target address" % (args[0]))
        return
    try:
        check_address(addr, "target")
    except ExecException:
        error("%03d: invalid target address" % (addr,))
        return
    memory[addr] = value

commands = { \
    "exit" : command_exit, \
    "l" : command_load, \
    "load" : command_load, \
    "g" : command_go, \
    "go" : command_go, \
    "c" : command_continue, \
    "cont" : command_continue, \
    "continue" : command_continue, \
    "p" : command_print, \
    "print" : command_print, \
    "s" : command_set, \
    "set" : command_set, \
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

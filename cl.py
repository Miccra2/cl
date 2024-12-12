#!/usr/bin/env python3.12
from dataclasses import dataclass, field
from copy import deepcopy
import sys

IOTA_COUNTER: int = 0
def iota(reset: bool = False) -> int:
    global IOTA_COUNTER
    if reset:
        IOTA_COUNTER = 0
    result: int = IOTA_COUNTER
    IOTA_COUNTER += 1
    return result

@dataclass
class Position:
    line:     int = 1
    column:   int = 1
    line_off: int = 0
    offset:   int = 0

@dataclass
class TokenKind:
    undefined: int = iota(True)

    label:     int = iota()
    digits:    int = iota()

    plus:      int = iota()

    dollar:    int = iota()
    colon:     int = iota()

    l_paren:   int = iota()
    r_paren:   int = iota()

    count:     int = iota()

@dataclass
class Token:
    kind:  TokenKind = TokenKind.undefined
    start: Position  = field(default_factory=Position())
    end:   Position  = field(default_factory=Position())

@dataclass
class Lexer:
    path: str = ""
    text: str = ""

    pos: Position = field(default_factory=Position())

    char_index: int = 0
    curr_char: str = ""
    next_char: str = ""

@dataclass
class Ins:
    undefined: int = iota(True)

    macro_call: int = iota()

    l_paren: int = iota()
    r_paren: int = iota()

    count: int = iota()

def usage() -> None:
    print("Usage: python cl.py [file]")
    print("    file - path to source file, with `.mcs` extension")

def error(msg: str, errcode: int = 1, showusage: bool = True) -> None:
    print(f"ERROR: {msg}")
    if showusage:
        usage()
    sys.exit(errcode)

def waring(msg: str, showusage: bool = False) -> None:
    print(f"WARING: {msg}")
    if showusage:
        usage()

def info(msg: str, showusage: bool = False) -> None:
    print(f"INFO: {msg}")
    if showusage:
        usage()

def lexer_next(lexer: Lexer) -> None:
    lexer.curr_char = lexer.next_char
    lexer.next_char = lexer.text[lexer.char_index] if lexer.char_index < len(lexer.text) else None
    lexer.char_index += 1

def lexer_advance(lexer: Lexer) -> None:
    if lexer.curr_char == '\n':
        lexer.pos.line += 1
        lexer.pos.line_off = lexer.pos.offset + 1
        lexer.pos.column = 0
    lexer.pos.column += 1
    lexer.pos.offset += 1
    lexer_next(lexer)

def lexer_new(path: str) -> Lexer:
    text: str = ""
    try:
        with open(path, "r") as file:
            text = file.read()
    except FileNotFoundError:
        error(f"Invalid file path `{path}` provided, please provide a valide file path!")
    lexer: Lexer = Lexer(path, text, Position(), 0, "", "")
    lexer_next(lexer)
    lexer_next(lexer)
    return lexer

def isdigit(char: str) -> bool:
    return ord(char) >= ord('0') and ord(char) <= ord('9')

def islabelstart(char: str) -> bool:
    return char == '_' or (ord(char) >= ord('A') and ord(char) <= ord('Z')) or (ord(char) >= ord('a') and ord(char) <= ord('z'))

def islabel(char: str) -> bool:
    return isdigit(char) or islabelstart(char)

def lexer_next_token(lexer: Lexer) -> Token:
    while True:
        if lexer.curr_char == ' ' or lexer.curr_char == '\n' or lexer.curr_char == '\r' or lexer.curr_char == '\t':
            lexer_advance(lexer)
        elif lexer.curr_char == '/' and lexer.next_char == '/':
            while isinstance(lexer.curr_char, str) and lexer.curr_char != '\n':
                lexer_advance(lexer)
        elif lexer.curr_char == '/' and lexer.next_char == '*':
            while isinstance(lexer.curr_char, str) and lexer.curr_char != '*' and lexer.next_char != '/':
                lexer_advance(lexer)
            lexer_advance(lexer)
            lexer_advance(lexer)
        else:
            break
    if not isinstance(lexer.curr_char, str):
        return None
    pos: Position = deepcopy(lexer.pos)
    if lexer.curr_char == '+':
        lexer_advance(lexer)
        return Token(TokenKind.plus, pos, deepcopy(lexer.pos))
    elif lexer.curr_char == '$':
        lexer_advance(lexer)
        return Token(TokenKind.dollar, pos, deepcopy(lexer.pos))
    elif lexer.curr_char == ';':
        lexer_advance(lexer)
        return Token(TokenKind.dollar, pos, deepcopy(lexer.pos))
    elif lexer.curr_char == '(':
        lexer_advance(lexer)
        return Token(TokenKind.l_paren, pos, deepcopy(lexer.pos))
    elif lexer.curr_char == ')':
        lexer_advance(lexer)
        return Token(TokenKind.r_paren, pos, deepcopy(lexer.pos))
    elif isdigit(lexer.curr_char):
        while isinstance(lexer.curr_char, str) and isdigit(lexer.curr_char):
            lexer_advance(lexer)
        return Token(TokenKind.digits, pos, deepcopy(lexer.pos))
    elif islabelstart(lexer.curr_char):
        while isinstance(lexer.curr_char, str) and islabel(lexer.curr_char):
            lexer_advance(lexer)
        return Token(TokenKind.label, pos, deepcopy(lexer.pos))
    else:
        error(f"Encountered an invalid token `{lexer.curr_char}` while lexing!")

def lex_file(lexer: Lexer) -> list[Token]:
    tokens: list = []
    token: Token = lexer_next_token(lexer)
    while isinstance(token, Token):
        tokens.append(token)
        token = lexer_next_token(lexer)
    return tokens

def parser(tokens: list, lexer: Lexer) -> list:
    call_stack: list = []
    work_stack: list = []
    ast: list = []
    i: int = 0
    while i < len(tokens):
        token: Token = tokens[i]
        if token.kind == TokenKind.plus:
            assert False, "Not implemented!"
        elif token.kind == TokenKind.dollar:
            i += 1
            if i >= len(tokens):
                error(f"Expacted more tokens after token `$` ({TokenKind.dollar}) while parsing!")
            token = tokens[i]
            if token.kind != TokenKind.label:
                error(f"Expacted token of kind `label` ({TokenKind.label}) after token `$` ({TokenKind.dollar}), but found token of kind ({token.kind}) while parsing!")
            macro_call: tuple = (Ins.macro_call, lexer.text[token.start.offset:token.end.offset], [])
            ast.append(macro_call)
            call_stack.append(macro_call)
        elif token.kind == TokenKind.colon:
            while len(stack) > 0:
                ast.append(stack.pop())
        elif token.kind == TokenKind.l_paren:
            work_stack.append((Ins.l_paren,))
        elif token.kind == TokenKind.r_paren:
            if ast[-1][0] == Ins.macro_call:
                while work_stack[-1][0] != Ins.l_paren:
                    ast[-1][2].append(work_stack.pop())
            else:
                while work_stack[-1][0] != Ins.l_paren:
                    ast.append(work_stack.pop())
        elif token.kind == TokenKind.digits:
            assert False, "Not implemented!"
        elif token.kind == TokenKind.label:
            assert False, "Not implemented!"
        else:
            error(f"Encountered an invalide token `{lexer.text[token.start.offset:token.end.offset]}` while parsing!")
        i += 1
    if len(stack) > 0:
        ast.append(stack.pop())
    return ast

if __name__ == "__main__":
    if len(sys.argv) < 2:
        error("To few input arguments given, please provide more input arguments!")
    lexer: Lexer = lexer_new(sys.argv[1])
    tokens: list = lex_file(lexer)
    ast: list = parser(tokens, lexer)

    print(TokenKind())
    for token in tokens:
        print(token)

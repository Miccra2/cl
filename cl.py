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
    start: Position  = field(default_factory=Position)
    end:   Position  = field(default_factory=Position)

@dataclass
class Lexer:
    path: str = ""
    text: str = ""

    pos: Position = field(default_factory=Position)

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

@dataclass
class Parser:
    lexer:      Lexer = field(default_factory=Lexer)
    prev_token: Token = field(default_factory=Token)
    curr_token: Token = field(default_factory=Token)

@dataclass
class Ast:
    _types: list = field(default_factory=[])
    _macros: list = field(default_factory=[])
    _globals: list = field(default_factory=[])
    _functions: list = field(default_factory=[])

def usage() -> None:
    print("Usage: python cl.py [file]")
    print("    file - path to source file, with `.sc` extension")

def error(msg: str, errcode: int = 1, showusage: bool = True) -> None:
    print(f"ERROR: {msg}")
    if showusage:
        usage()
    sys.exit(errcode)

def lexer_get_token(token: Token, lexer: Lexer) -> str:
    return lexer.text[token.start.offset:token.end.offset]

def lexer_token_info(token: Token, lexer: Lexer) -> str:
    return f"{lexer.path}:{token.start.line}:{token.start.column}"

def lexer_error(msg: str, token: Token, lexer: Lexer) -> None:
    error(f"{lexer_token_info(token, lexer)}: {msg} while lexing!")

def parser_get_token(parser: Parser) -> str:
    return parser.lexer.text[parser.curr_token.start.offset:parser.curr_token.end.offset]

def parser_token_info(parser: Parser) -> str:
    return f"{parser.lexer.path}:{parser.curr_token.start.line}:{parser.curr_token.start.column}"

def parser_error(msg: str, parser: Parser) -> None:
    error(f"{parser_token_info(parser)}: {msg} while parsing!")

def parser_unimplemented_error(parser: Parser) -> None:
    parser_error(f"Encountered unimplemented token `{parser_get_token(parser)}` ({parser.curr_token.kind})", parser)

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
        lexer_error(f"Encountered an invalid token `{lexer.curr_char}`!")

def lex_entire_file(lexer: Lexer) -> list[Token]:
    tokens: list = []
    token: Token = lexer_next_token(lexer)
    while isinstance(token, Token):
        tokens.append(token)
        token = lexer_next_token(lexer)
    return tokens

def parser_next(parser: Parser) -> None:
    parser.prev_token = parser.curr_token
    parser.curr_token = lexer_next_token(parser.lexer)

def parser_new(path: str) -> Parser:
    parser: Parser = Parser(lexer_new(path), Token(), Token())
    parser_next(parser)
    return parser

def parser_get_token(parser: Parser) -> str:
    return parser.lexer.text[parser.curr_token.start.offset:parser.curr_token.end.offset]

def parser_get_macro_call(parser: Parser) -> tuple:
    parser_next(parser)
    macro: list = [Ins.macro_call,]
    if parser.curr_token != TokenKind.label:
        parser_error(f"Expacted token ({TokenKind.label}) after token ({TokenKind.dollar}), but found token ({parser.curr_token.kind})", parser)
    macro.append(parser_get_token(parser))
    token: Token = deepcopy(parser.prev_token)
    parser_next(parser)
    if parser.curr_token
    return macro

def parser_expact_tokens(parser: Parser, tokens: tuple[TokenKind]) -> bool:
    parser_state: Parser = deepcopy(parser)
    result: bool = True
    for token in tokens:
        parser_next(parser)
    if result:
        return True
    parser.lexer = pareser_state.lexer
    paresr.prev_char = parser_state.prev_char
    parser.curr_char = parser_state.curr_char
    return False

def parser_parse(parser: Parser) -> Ast:
    if TokenKind.count != 8:
        parser_error(f"Unimplemented tokens TokenKind.count: {TokenKind.count}", parser)
    ast: Ast = Ast([], [], [])
    while parser.curr_token:
        if parser.curr_token.kind == TokenKind.undefined:
            parser_error(f"Encountered undefined token `{parser_get_token(parser)}` ({parser.curr_token.kind})!", parser)
        elif parser.curr_token.kind == TokenKind.plus:
            parser_unimplemented_error(parser)
        elif parser.curr_token.kind == TokenKind.dollar:
            # encoutered macro call $ label (l_paren (arguemnt (comma ...)) r_paren)
            parser_unimplemented_error(parser)
        elif parser.curr_token.kind == TokenKind.colon:
            parser_unimplemented_error(parser)
        elif parser.curr_token.kind == TokenKind.l_paren:
            parser_unimplemented_error(parser)
        elif parser.curr_token.kind == TokenKind.r_paren:
            parser_unimplemented_error(parser)
        elif parser.curr_token.kind == TokenKind.label:
            parser_unimplemented_error(parser)
        elif parser.curr_token.kind == TokenKind.digits:
            parser_unimplemented_error(parser)
        else:
            parser_error(f"Encountered invalid token `{parser_get_token(parser)}` ({parser.curr_token.kind})", parser)
        parser_next(parser)
    return ast

if __name__ == "__main__":
    if len(sys.argv) < 2:
        error("To few input arguments given, please provide more input arguments!")
    parser: Parser = parser_new(sys.argv[1])
    ast: Ast = parser_parse(parser)

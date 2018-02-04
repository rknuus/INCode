#!/usr/bin/env python3

from clang.cindex import *


def get_caller(call, parents):
    parent = parents[call.hash]
    while parent is not None and parent.kind != CursorKind.FUNCTION_DECL:
        parent = parents[parent.hash]
    return parent


def is_function_call_of(funcdecl, call):
    # TODO(KNR): figure out how to navigate to the FunctionDecl:
    # | `-FunctionDecl 0x7f8e63765d00 <line:9:5, line:11:5> line:9:10 f 'void (void)'
    # |   `-CompoundStmt 0x7f8e63765ed8 <col:14, line:11:5>
    # |     `-CallExpr 0x7f8e63765ea0 <line:10:9, col:22> 'int'
    # |       |-ImplicitCastExpr 0x7f8e63765e88 <col:9> 'int (*)(int, int)' <FunctionToPointerDecay>
    # |       | `-DeclRefExpr 0x7f8e63765e30 <col:9> 'int (int, int)' lvalue Function 0x7f8e63765b58 'addition' 'int (int, int)'
    # |       |-IntegerLiteral 0x7f8e63765df0 <col:18> 'int' 2
    # |       `-IntegerLiteral 0x7f8e63765e10 <col:21> 'int' 3

    defn = call.get_definition()
    return (defn is not None) and (defn == funcdecl)


def fully_qualify(call):
    res = call.spelling
    call = call.semantic_parent
    while call is not None and call.kind != CursorKind.TRANSLATION_UNIT:
        res = call.spelling + '::' + res
        call = call.semantic_parent
    return res


def _get_dbg_info(node):
    if node is None:
        return ''
    return '{} ({})'.format(node.displayname, node.kind)


def find_funcs_and_calls(tu):
    filename = tu.cursor.spelling
    funcs = []
    calls = []
    parents = {}
    for node in tu.cursor.walk_preorder():
        for child in node.get_children():
            parents[child.hash] = node
        if node.location.file is None:
            pass
        elif node.location.file.name != filename:
            pass
        elif node.kind == CursorKind.CALL_EXPR:
            calls.append(node)
        elif node.kind == CursorKind.FUNCTION_DECL:
            funcs.append(node)
    return funcs, calls, parents


idx = Index.create()
args = '-x c++ --std=c++11'.split()
tu = idx.parse('tmp.cpp', args=args)
funcs, calls, parents = find_funcs_and_calls(tu)
for func in funcs:
    print(fully_qualify(func), func.location)
    for call in calls:
        if is_function_call_of(func, call):
            caller = get_caller(call, parents)
            print('- called by ', fully_qualify(caller), call.location)
    print()

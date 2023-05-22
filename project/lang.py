from antlr4 import *
from pydot import *

from project.RaisingErrorListener import *
from project.parser.langLexer import langLexer as LangLexer
from project.parser.langParser import langParser as LangParser
from project.parser.langVisitor import langVisitor as LangVisitor


def parse_stream(stream: InputStream):
    """
    Run ANTLR4 parser for language from rule program on specified stream and return parsing tree.

    If any error produced, raises RecognitionError.
    """

    lexer = LangLexer(stream)

    lexer.removeErrorListeners()
    lexer.addErrorListener(RaisingErrorListener.INSTANCE)

    parser = LangParser(CommonTokenStream(lexer))

    parser.removeErrorListeners()
    parser.addErrorListener(RaisingErrorListener.INSTANCE)

    return parser.program()


def parse(text: str = None, *, filename: str = None, encoding: str = "utf-8"):
    """
    Runs parse_stream with one of streams:

        - InputStream, if text passed,
        - FileStream, if filename passed,
        - StdinStream, if both not passed.

    Parameter encoding passed into FileStream and StdinStream.
    """

    if text is not None and filename is not None:
        raise ValueError("cannot specify both text and filename")

    if text is not None:
        stream = InputStream(text)

    elif filename is not None:
        stream = FileStream(filename, encoding=encoding)

    else:
        stream = StdinStream(encoding=encoding)

    return parse_stream(stream)


def check_syntax(text: str = None, *, filename: str = None, encoding: str = "utf-8"):
    """
    Checks is parser can recognize syntax. Parameters are similar to parse function.
    """

    try:
        parse(text=text, filename=filename, encoding=encoding)
        return True

    except RecognitionError:
        return False


def write_to_dot(tree: ParserRuleContext, filename: str):
    """
    Draws specified parsing tree and writes to DOT file with specified filename.
    """

    visitor = DotTreeVisitor()
    tree.accept(visitor)

    visitor.graph.write_dot(filename)


class DotTreeVisitor(LangVisitor):
    def __init__(self):
        self.graph = Dot("lang parse tree")
        self.node_number = 0

    def next_node_number(self):
        self.node_number += 1

        return str(self.node_number)

    # Visit a parse tree produced by langParser#program.
    def visitProgram(self, ctx: LangParser.ProgramContext):
        node = Node(self.next_node_number(), label="program")
        self.graph.add_node(node)

        for i, stmt in enumerate(ctx.stmts):
            child = stmt.accept(self)

            self.graph.add_edge(Edge(node, child, label=str(i)))

        return node

    # Visit a parse tree produced by langParser#stmt__let.
    def visitStmt__let(self, ctx: LangParser.Stmt__letContext):
        node = Node(self.next_node_number(), label="let")
        self.graph.add_node(node)

        child = Node(self.next_node_number(), label=ctx.name.text)
        self.graph.add_node(child)

        self.graph.add_edge(Edge(node, child, label="name"))

        child = ctx.value.accept(self)
        self.graph.add_edge(Edge(node, child, label="value"))

        return node

    # Visit a parse tree produced by langParser#stmt__expr.
    def visitStmt__expr(self, ctx: LangParser.Stmt__exprContext):
        node = Node(self.next_node_number(), label="print")
        self.graph.add_node(node)

        child = ctx.value.accept(self)
        self.graph.add_edge(Edge(node, child, label="expr"))

        return node

    # Visit a parse tree produced by langParser#expr__parens.
    def visitExpr__parens(self, ctx: LangParser.Expr__parensContext):
        node = Node(self.next_node_number(), label="()")
        self.graph.add_node(node)

        child = ctx.expr_.accept(self)
        self.graph.add_edge(Edge(node, child, label="expr"))

        return node

    # Visit a parse tree produced by langParser#expr__name.
    def visitExpr__name(self, ctx: LangParser.Expr__nameContext):
        rec = "rec " if ctx.rec is not None else ""

        node = Node(self.next_node_number(), label=f"{rec}name")
        self.graph.add_node(node)

        child = Node(self.next_node_number(), label=ctx.name.text)
        self.graph.add_node(child)

        self.graph.add_edge(Edge(node, child, label="name"))

        return node

    # Visit a parse tree produced by langParser#expr__literal.
    def visitExpr__literal(self, ctx: LangParser.Expr__literalContext):
        node = Node(self.next_node_number(), label="literal")
        self.graph.add_node(node)

        child = ctx.value.accept(self)
        self.graph.add_edge(Edge(node, child, label="value"))

        return node

    # Visit a parse tree produced by langParser#expr__load.
    def visitExpr__load(self, ctx: LangParser.Expr__loadContext):
        node = Node(self.next_node_number(), label="load")
        self.graph.add_node(node)

        child = Node(self.next_node_number(), label=repr(ctx.name.text))
        self.graph.add_node(child)

        self.graph.add_edge(Edge(node, child, label="name"))

        return node

    # Visit a parse tree produced by langParser#expr__unary_op.
    def visitExpr__unary_op(self, ctx: LangParser.Expr__unary_opContext):
        node = Node(self.next_node_number(), label=ctx.op.text)
        self.graph.add_node(node)

        child = ctx.value.accept(self)
        self.graph.add_edge(Edge(node, child, label="value"))

        return node

    # Visit a parse tree produced by langParser#expr__binary_op.
    def visitExpr__binary_op(self, ctx: LangParser.Expr__binary_opContext):
        node = Node(
            self.next_node_number(),
            label="not in" if ctx.op.type == LangLexer.NOT_IN else ctx.op.text,
        )

        self.graph.add_node(node)

        child = ctx.left.accept(self)
        self.graph.add_edge(Edge(node, child, label="left"))

        child = ctx.right.accept(self)
        self.graph.add_edge(Edge(node, child, label="right"))

        return node

    # Visit a parse tree produced by langParser#expr__set.
    def visitExpr__set(self, ctx: LangParser.Expr__setContext):
        node = Node(self.next_node_number(), label="with")
        self.graph.add_node(node)

        child = ctx.sm.accept(self)
        self.graph.add_edge(Edge(node, child, label="sm"))

        child = ctx.what.accept(self)
        self.graph.add_edge(Edge(node, child, label="what"))

        child = ctx.what_value.accept(self)
        self.graph.add_edge(Edge(node, child, label="what_value"))

        return node

    # Visit a parse tree produced by langParser#expr__get.
    def visitExpr__get(self, ctx: LangParser.Expr__getContext):
        node = Node(self.next_node_number(), label="of")
        self.graph.add_node(node)

        child = ctx.what.accept(self)
        self.graph.add_edge(Edge(node, child, label="what"))

        child = ctx.sm.accept(self)
        self.graph.add_edge(Edge(node, child, label="sm"))

        return node

    # Visit a parse tree produced by langParser#expr__map_filter.
    def visitExpr__map_filter(self, ctx: LangParser.Expr__map_filterContext):
        node = Node(self.next_node_number(), label=ctx.op.text + " with")
        self.graph.add_node(node)

        child = ctx.value.accept(self)
        self.graph.add_edge(Edge(node, child, label="value"))

        child = ctx.f.accept(self)
        self.graph.add_edge(Edge(node, child, label="f"))

        return node

    # Visit a parse tree produced by langParser#expr_set_clause__set_start_states.
    def visitExpr_set_clause__set_start_states(
        self,
        ctx: LangParser.Expr_set_clause__set_start_statesContext,
    ):
        node = Node(self.next_node_number(), label="only start states")
        self.graph.add_node(node)

        return node

    # Visit a parse tree produced by langParser#expr_set_clause__set_final_states.
    def visitExpr_set_clause__set_final_states(
        self,
        ctx: LangParser.Expr_set_clause__set_final_statesContext,
    ):
        node = Node(self.next_node_number(), label="only final states")
        self.graph.add_node(node)

        return node

    # Visit a parse tree produced by langParser#expr_set_clause__add_start_states.
    def visitExpr_set_clause__add_start_states(
        self,
        ctx: LangParser.Expr_set_clause__add_start_statesContext,
    ):
        node = Node(self.next_node_number(), label="additional start states")
        self.graph.add_node(node)

        return node

    # Visit a parse tree produced by langParser#expr_set_clause__add_final_states.
    def visitExpr_set_clause__add_final_states(
        self,
        ctx: LangParser.Expr_set_clause__add_final_statesContext,
    ):
        node = Node(self.next_node_number(), label="additional final states")
        self.graph.add_node(node)

        return node

    # Visit a parse tree produced by langParser#expr_get_clause__start_states.
    def visitExpr_get_clause__start_states(
        self,
        ctx: LangParser.Expr_get_clause__start_statesContext,
    ):
        node = Node(self.next_node_number(), label="start states")
        self.graph.add_node(node)

        return node

    # Visit a parse tree produced by langParser#expr_get_clause__final_states.
    def visitExpr_get_clause__final_states(
        self,
        ctx: LangParser.Expr_get_clause__final_statesContext,
    ):
        node = Node(self.next_node_number(), label="final states")
        self.graph.add_node(node)

        return node

    # Visit a parse tree produced by langParser#expr_get_clause__reachable_states.
    def visitExpr_get_clause__reachable_states(
        self,
        ctx: LangParser.Expr_get_clause__reachable_statesContext,
    ):
        node = Node(self.next_node_number(), label="reachable states")
        self.graph.add_node(node)

        return node

    # Visit a parse tree produced by langParser#expr_get_clause__nodes.
    def visitExpr_get_clause__nodes(
        self,
        ctx: LangParser.Expr_get_clause__nodesContext,
    ):
        node = Node(self.next_node_number(), label="nodes")
        self.graph.add_node(node)

        return node

    # Visit a parse tree produced by langParser#expr_get_clause__edges.
    def visitExpr_get_clause__edges(
        self,
        ctx: LangParser.Expr_get_clause__edgesContext,
    ):
        node = Node(self.next_node_number(), label="edges")
        self.graph.add_node(node)

        return node

    # Visit a parse tree produced by langParser#expr_get_clause__labels.
    def visitExpr_get_clause__labels(
        self,
        ctx: LangParser.Expr_get_clause__labelsContext,
    ):
        node = Node(self.next_node_number(), label="labels")
        self.graph.add_node(node)

        return node

    # Visit a parse tree produced by langParser#literal__string.
    def visitLiteral__string(self, ctx: LangParser.Literal__stringContext):
        node = Node(self.next_node_number(), label="string")
        self.graph.add_node(node)

        child = Node(self.next_node_number(), label=repr(ctx.value.text))
        self.graph.add_node(child)

        self.graph.add_edge(Edge(node, child, label="value"))

        return node

    # Visit a parse tree produced by langParser#literal__int.
    def visitLiteral__int(self, ctx: LangParser.Literal__intContext):
        node = Node(self.next_node_number(), label="int")
        self.graph.add_node(node)

        child = Node(self.next_node_number(), label=ctx.value.text)
        self.graph.add_node(child)

        self.graph.add_edge(Edge(node, child, label="value"))

        return node

    # Visit a parse tree produced by langParser#literal__real.
    def visitLiteral__real(self, ctx: LangParser.Literal__realContext):
        node = Node(self.next_node_number(), label="real")
        self.graph.add_node(node)

        child = Node(self.next_node_number(), label=ctx.value.text)
        self.graph.add_node(child)

        self.graph.add_edge(Edge(node, child, label="value"))

        return node

    # Visit a parse tree produced by langParser#literal__range.
    def visitLiteral__range(self, ctx: LangParser.Literal__rangeContext):
        node = Node(self.next_node_number(), label="..")
        self.graph.add_node(node)

        child = Node(self.next_node_number(), label=ctx.from_.text)
        self.graph.add_node(child)

        self.graph.add_edge(Edge(node, child, label="from"))

        child = Node(self.next_node_number(), label=ctx.to.text)
        self.graph.add_node(child)

        self.graph.add_edge(Edge(node, child, label="to"))

        return node

    # Visit a parse tree produced by langParser#literal__set.
    def visitLiteral__set(self, ctx: LangParser.Literal__setContext):
        node = Node(self.next_node_number(), label="{,,,}")
        self.graph.add_node(node)

        for elem in ctx.elems:
            child = elem.accept(self)
            self.graph.add_edge(Edge(node, child, label="elem"))

        return node

    # Visit a parse tree produced by langParser#literal__lambda.
    def visitLiteral__lambda(self, ctx: LangParser.Literal__lambdaContext):
        node = Node(self.next_node_number(), label="\\\\ ->")
        self.graph.add_node(node)

        child = ctx.param.accept(self)
        self.graph.add_edge(Edge(node, child, label="param"))

        child = ctx.body.accept(self)
        self.graph.add_edge(Edge(node, child, label="body"))

        return node

    # Visit a parse tree produced by langParser#pattern__name.
    def visitPattern__name(self, ctx: LangParser.Pattern__nameContext):
        node = Node(self.next_node_number(), label="name")
        self.graph.add_node(node)

        child = Node(self.next_node_number(), label=ctx.name.text)
        self.graph.add_node(child)

        self.graph.add_edge(Edge(node, child, label="name"))

        return node

    # Visit a parse tree produced by langParser#pattern__tuple.
    def visitPattern__tuple(self, ctx: LangParser.Pattern__tupleContext):
        node = Node(self.next_node_number(), label="(,,,)")
        self.graph.add_node(node)

        for i, elem in enumerate(ctx.elems):
            child = elem.accept(self)
            self.graph.add_edge(Edge(node, child, label=str(i)))

        return node

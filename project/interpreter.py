from pyformlang.finite_automaton import EpsilonNFA
from collections import namedtuple
from typing import Iterable
from antlr4 import *

from project.parser.langLexer import langLexer as LangLexer
from project.parser.langParser import langParser as LangParser
from project.parser.langVisitor import langVisitor as LangVisitor


LangValueBoolean = namedtuple("LangValueBoolean", ["value", "ctx"])
LangValueInt = namedtuple("LangValueInt", ["value", "ctx"])
LangValueReal = namedtuple("LangValueReal", ["value", "ctx"])
LangValueString = namedtuple("LangValueString", ["value", "ctx"])
LangValueTuple = namedtuple("LangValueTuple", ["value", "ctx"])
LangValueSet = namedtuple("LangValueSet", ["value", "ctx"])
LangValueFA = namedtuple("LangValueFA", ["value", "ctx"])
LangValueLambda = namedtuple("LangValueLambda", ["value", "ctx"])

LangValueBoolean.typename = "boolean"
LangValueInt.typename = "int"
LangValueReal.typename = "real"
LangValueString.typename = "string"
LangValueTuple.typename = "tuple"
LangValueSet.typename = "set"
LangValueFA.typename = "FA"
LangValueLambda.typename = "lambda"

LangValue = (
    LangValueBoolean
    | LangValueInt
    | LangValueReal
    | LangValueString
    | LangValueTuple
    | LangValueSet
    | LangValueFA
    | LangValueLambda
)


def interpret(program: ParserRuleContext, out=None):
    """ """

    visitor = InterpretVisitor(out=out)

    try:
        return program.accept(visitor)

    except Exception as e:
        raise InterpretError(e, visitor.ctx) from e


def ctx_location(ctx: ParserRuleContext) -> str:
    return f"{ctx.start.line}:{ctx.start.column + 1}"


def value_to_string(value: LangValue):
    if isinstance(value, LangValueTuple):
        return f'({", ".join([value_to_string(x) for x in value.value])})'

    if isinstance(value, LangValueSet):
        return "{" + f'{", ".join([value_to_string(x) for x in value.value])}' + "}"

    if isinstance(value, LangValueFA):
        return f"FA created on {ctx_location(value.ctx)}"

    if isinstance(value, LangValueLambda):
        return f"lambda created on {ctx_location(value.ctx)}"

    return repr(value.value)


def type_error(value: LangValue, expected: str | Iterable[str]) -> ValueError:
    return ValueError(
        f"""\
{value_to_string(value)} created on {ctx_location(value.ctx)} is of type \
{type(value).typename} while (one of) {expected} is expected\
"""
    )


def parse_token(token: Token) -> int | float | str:
    if token.type not in {
        LangLexer.INT_NUMBER,
        LangLexer.REAL_NUMBER,
        LangLexer.STRING,
    }:
        raise ValueError("token must be INT_NUMBER, REAL_NUMBER or STRING")

    return eval(token.text)


def python_value_to_value(value: any, ctx: ParserRuleContext) -> LangValue:
    if isinstance(value, int):
        return LangValueInt(value=value, ctx=ctx)

    if isinstance(value, float):
        return LangValueReal(value=value, ctx=ctx)

    if isinstance(value, str):
        return LangValueString(value=value, ctx=ctx)

    if isinstance(value, tuple):
        return LangValueTuple(
            value=tuple([python_value_to_value(x, ctx) for x in value]),
            ctx=ctx,
        )

    try:
        iter(value)

        return LangValueSet(
            value={python_value_to_value(x, ctx) for x in set(value)},
            ctx=ctx,
        )

    except TypeError:
        pass

    return LangValueString(value=str(value), ctx=ctx)


def value_to_python_value(value: LangValue) -> any:
    if isinstance(value, LangValueBoolean):
        return value.value

    elif isinstance(value, LangValueInt):
        return value.value

    elif isinstance(value, LangValueReal):
        return value.value

    elif isinstance(value, LangValueString):
        return value.value

    elif isinstance(value, LangValueTuple):
        return tuple([value_to_python_value(x) for x in value.value])

    elif isinstance(value, LangValueSet):
        return {value_to_python_value(x) for x in value.value}

    elif isinstance(value, LangValueFA):
        return value.value

    elif isinstance(value, LangValueLambda):
        raise ValueError("lambda conversion is not supported")

    raise ValueError("unknown type of value")


def cast_string_to_FA(value: LangValue, ctx: ParserRuleContext) -> LangValue:
    if not isinstance(value, LangValueString):
        return value

    fa = EpsilonNFA()
    fa.add_transition(0, value.value, 1)
    fa.add_start_state(0)
    fa.add_final_state(1)

    return LangValueFA(value=fa, ctx=ctx)


class InterpretError(Exception):
    def __init__(self, ex, ctx):
        self.ex = ex
        self.ctx = ctx

    def __str__(self):
        if self.ctx is None:
            return str(self.ex)

        return f"{ctx_location(self.ctx)}: {self.ex}"


class InterpretVisitor(LangVisitor):
    def __init__(self, out=None):
        self.ctx_stack = list()
        self.scopes = [dict()]

        self.out = out

    @property
    def ctx(self) -> ParserRuleContext:
        if len(self.ctx_stack) == 0:
            return None

        return self.ctx_stack[-1]

    def _enter_ctx(self, ctx: ParserRuleContext):
        self.ctx_stack.append(ctx)

    def _exit_ctx(self):
        self.ctx_stack.pop()

    # Visit a parse tree produced by LangParser#program.
    def visitProgram(self, ctx: LangParser.ProgramContext):
        self._enter_ctx(ctx)

        for stmt in ctx.stmts:
            stmt.accept(self)

        self._exit_ctx()

    # Visit a parse tree produced by LangParser#stmt__let.
    def visitStmt__let(self, ctx: LangParser.Stmt__letContext):
        self._enter_ctx(ctx)

        self.scopes[0][ctx.name] = ctx.value.accept(self)

        self._exit_ctx()

    # Visit a parse tree produced by LangParser#stmt__expr.
    def visitStmt__expr(self, ctx: LangParser.Stmt__exprContext):
        self._enter_ctx(ctx)

        print(value_to_string(ctx.value.accept(self)), file=self.out)

        self._exit_ctx()

    # Visit a parse tree produced by LangParser#expr__parens.
    def visitExpr__parens(self, ctx: LangParser.Expr__parensContext):
        self._enter_ctx(ctx)

        value = ctx.expr_.accept(self)

        self._exit_ctx()

        return value

    # Visit a parse tree produced by LangParser#expr__set.
    def visitExpr__set(self, ctx: LangParser.Expr__setContext):
        self._enter_ctx(ctx)

        sm = ctx.sm.accept(self)

        casted_sm = cast_string_to_FA(sm, ctx)
        if not isinstance(casted_sm, LangValueFA):
            raise type_error(sm, "FA")

        what_value = ctx.what_value.accept(self)

        result = casted_sm.value.copy()

        ctx.what.accept(self)(result, what_value)

        result = LangValueFA(value=result, ctx=ctx)

        self._exit_ctx()

        return result

    # Visit a parse tree produced by LangParser#expr__get.
    def visitExpr__get(self, ctx: LangParser.Expr__getContext):
        self._enter_ctx(ctx)

        # delegate logic
        value = ctx.what.accept(self)

        self._exit_ctx()

        return value

    # Visit a parse tree produced by LangParser#expr__map_filter.
    def visitExpr__map_filter(self, ctx: LangParser.Expr__map_filterContext):
        self._enter_ctx(ctx)

        value = ctx.value.accept(self)

        # T-Map, T-Filter
        if not isinstance(value, LangValueSet):
            raise type_error(value, "set")

        f = ctx.f.accept(self)

        # T-Map, T-Filter
        if not isinstance(f, LangValueLambda):
            raise type_error(f, "lambda")

        if ctx.op.text == "mapped":
            result = {f.value(x) for x in value.value}

        elif ctx.op.text == "filtered":
            result = {x for x in value.value if f.value(x)}

        else:
            raise ValueError("unknown operator")

        self._exit_ctx()

        return LangValueSet(value=result, ctx=ctx)

    # Visit a parse tree produced by LangParser#expr__unary_op.
    def visitExpr__unary_op(self, ctx: LangParser.Expr__unary_opContext):
        self._enter_ctx(ctx)

        value = ctx.value.accept(self)

        if ctx.op.text == "*":
            # T-KleeneStar

            casted_value = cast_string_to_FA(value, ctx)
            if not isinstance(casted_value, LangValueFA):
                raise type_error(value, "FA")

            raise NotImplementedError

        elif ctx.op.text == "-":
            if isinstance(value, LangValueInt):
                # T-UnaryMinusI

                result = LangValueInt(value=-value.value, ctx=ctx)

            elif isinstance(value, LangValueReal):
                # T-UnaryMinusR

                result = LangValueReal(value=-value.value, ctx=ctx)

            else:
                raise type_error(value, ["int", "real"])

        elif ctx.op.text == "not":
            # T-Not

            if not isinstance(value, LangValueBoolean):
                raise type_error(value, "boolean")

            result = LangValueBoolean(value=not value.value, ctx=ctx)

        else:
            raise ValueError("unknown operator")

        self._exit_ctx()

        return result

    # Visit a parse tree produced by LangParser#expr__binary_op.
    def visitExpr__binary_op(self, ctx: LangParser.Expr__binary_opContext):
        self._enter_ctx(ctx)

        left = ctx.left.accept(self)
        right = ctx.right.accept(self)

        if ctx.op.text == "*":
            if isinstance(left, LangValueInt):
                if isinstance(right, LangValueInt):
                    # T-MulII

                    result = LangValueInt(value=left.value * right.value, ctx=ctx)

                elif isinstance(right, LangValueReal):
                    # T-MulIR

                    result = LangValueReal(value=left.value * right.value, ctx=ctx)

                elif isinstance(right, LangValueString):
                    # T-MulIS

                    result = LangValueString(value=left.value * right.value, ctx=ctx)

                else:
                    raise type_error(right, ["int", "real", "string"])

            elif isinstance(left, LangValueReal):
                if isinstance(right, LangValueInt):
                    # T-MulRI

                    result = LangValueReal(value=left.value * right.value, ctx=ctx)

                elif isinstance(right, LangValueReal):
                    # T-MulRR

                    result = LangValueReal(value=left.value * right.value, ctx=ctx)

                else:
                    raise type_error(right, ["int", "real"])

            elif isinstance(left, LangValueString):
                # T-MulSI

                if not isinstance(right, LangValueInt):
                    raise type_error(right, "int")

                result = LangValueString(value=left.value * right.value, ctx=ctx)

            else:
                raise type_error(left, ["int", "real", "string"])

        elif ctx.op.text == "/":
            if isinstance(left, LangValueInt):
                if isinstance(right, LangValueInt):
                    if left.value % right.value == 0:
                        # T-DivIII

                        result = LangValueInt(value=left.value // right.value, ctx=ctx)

                    else:
                        # T-DivIIR

                        result = LangValueReal(value=left.value / right.value, ctx=ctx)

                elif isinstance(right, LangValueReal):
                    # T-DivIR

                    result = LangValueReal(value=left.value / right.value, ctx=ctx)

                else:
                    raise type_error(right, ["int", "real"])

            elif isinstance(left, LangValueReal):
                if isinstance(right, LangValueInt):
                    # T-DivRI

                    result = LangValueReal(value=left.value / right.value, ctx=ctx)

                elif isinstance(right, LangValueReal):
                    if left.value % right.value == 0:
                        # T-DivRRI

                        result = LangValueInt(
                            value=round(left.value / right.value),
                            ctx=ctx,
                        )

                    else:
                        # T-DivRRR

                        result = LangValueReal(value=left.value / right.value, ctx=ctx)

                else:
                    raise type_error(right, ["int", "real"])

            else:
                raise type_error(left, ["int", "real"])

        elif ctx.op.text == "&":
            if isinstance(left, LangValueInt):
                # T-BitwiseAnd

                if not isinstance(right, LangValueInt):
                    raise type_error(right, "int")

                result = LangValueInt(value=left.value & right.value, ctx=ctx)

            elif isinstance(left, LangValueSet):
                # T-SetIntersect

                if not isinstance(right, LangValueSet):
                    raise type_error(right, "set")

                result = LangValueSet(value=left.value & right.value, ctx=ctx)

            elif isinstance(casted_left := cast_string_to_FA(left, ctx), LangValueFA):
                # T-FAIntersect

                casted_right = cast_string_to_FA(right, ctx)
                if not isinstance(casted_right, LangValueFA):
                    raise type_error(right, "FA")

                result = LangValueFA(
                    value=casted_left.value & casted_right.value,
                    ctx=ctx,
                )

            else:
                raise type_error(left, ["int", "set", "FA"])

        elif ctx.op.text == "+":
            if isinstance(left, LangValueString) or isinstance(right, LangValueString):
                # T-Concat1, T-Concat2

                result = LangValueString(value=f"{left.value}{right.value}", ctx=ctx)

            elif isinstance(left, LangValueInt):
                if isinstance(right, LangValueInt):
                    # T-AddII

                    result = LangValueInt(value=left.value + right.value, ctx=ctx)

                elif isinstance(right, LangValueReal):
                    # T-AddIR

                    result = LangValueReal(value=left.value + right.value, ctx=ctx)

                else:
                    raise type_error(right, ["string", "int", "real"])

            elif isinstance(left, LangValueReal):
                if isinstance(right, LangValueInt):
                    # T-AddRI

                    result = LangValueReal(value=left.value + right.value, ctx=ctx)

                elif isinstance(right, LangValueReal):
                    # T-AddRR

                    result = LangValueReal(value=left.value + right.value, ctx=ctx)

                else:
                    raise type_error(right, ["string", "int", "real"])

            elif isinstance(casted_left := cast_string_to_FA(left, ctx), LangValueFA):
                # T-ConcatFA

                casted_right = cast_string_to_FA(right, ctx)
                if not isinstance(casted_right, LangValueFA):
                    raise type_error(right, ["string", "FA"])

                raise NotImplementedError

            else:
                raise type_error(left, ["string", "int", "real", "FA"])

        elif ctx.op.text == "-":
            if isinstance(left, LangValueInt):
                if isinstance(right, LangValueInt):
                    # T-SubII

                    result = LangValueInt(value=left.value - right.value, ctx=ctx)

                elif isinstance(right, LangValueReal):
                    # T-SubIR

                    result = LangValueReal(value=left.value - right.value, ctx=ctx)

                else:
                    raise type_error(right, ["int", "real"])

            elif isinstance(left, LangValueReal):
                if isinstance(right, LangValueInt):
                    # T-SubRI

                    result = LangValueReal(value=left.value - right.value, ctx=ctx)

                elif isinstance(right, LangValueReal):
                    # T-SubRR

                    result = LangValueReal(value=left.value - right.value, ctx=ctx)

                else:
                    raise type_error(right, ["int", "real"])

            else:
                raise type_error(left, ["int", "real"])

        elif ctx.op.text == "|":
            if isinstance(left, LangValueInt):
                # T-BitwiseOr

                if not isinstance(right, LangValueInt):
                    raise type_error(right, "int")

                result = LangValueInt(value=left.value | right.value, ctx=ctx)

            elif isinstance(left, LangValueSet):
                # T-SetUnion

                if not isinstance(right, LangValueSet):
                    raise type_error(right, "set")

                result = LangValueSet(value=left.value | right.value, ctx=ctx)

            elif isinstance(casted_left := cast_string_to_FA(left, ctx), LangValueFA):
                # T-FAUnion

                casted_right = cast_string_to_FA(right, ctx)
                if not isinstance(casted_right, LangValueFA):
                    raise type_error(right, "FA")

                raise NotImplementedError

            else:
                raise type_error(left, ["int", "set", "FA"])

        elif ctx.op.text == "==":
            result = LangValueBoolean(value=left.value == right.value, ctx=ctx)

        elif ctx.op.text == "!=":
            result = LangValueBoolean(value=left.value != right.value, ctx=ctx)

        elif ctx.op.text == "<":
            result = LangValueBoolean(value=left.value < right.value, ctx=ctx)

        elif ctx.op.text == ">":
            result = LangValueBoolean(value=left.value > right.value, ctx=ctx)

        elif ctx.op.text == "<=":
            result = LangValueBoolean(value=left.value <= right.value, ctx=ctx)

        elif ctx.op.text == ">=":
            result = LangValueBoolean(value=left.value >= right.value, ctx=ctx)

        elif ctx.op.text == "in":
            result = LangValueBoolean(
                value=any([left.value == x.value for x in right.value]),
                ctx=ctx,
            )

        elif ctx.op.type == LangLexer.NOT_IN:
            result = LangValueBoolean(
                value=all([left.value != x.value for x in right.value]),
                ctx=ctx,
            )

        else:
            raise ValueError("unknown operator")

        self._exit_ctx()

        return result

    # Visit a parse tree produced by LangParser#expr__load.
    def visitExpr__load(self, ctx: LangParser.Expr__loadContext):
        self._enter_ctx(ctx)

        raise NotImplementedError

    # Visit a parse tree produced by LangParser#expr__name.
    def visitExpr__name(self, ctx: LangParser.Expr__nameContext):
        self._enter_ctx(ctx)

        try:
            result = self.scopes[-1][ctx.name.text]

        except KeyError as e:
            raise ValueError(f'name "{ctx.name.text}" is not in scope') from e

        self._exit_ctx()

        return result

    # Visit a parse tree produced by LangParser#expr__literal.
    def visitExpr__literal(self, ctx: LangParser.Expr__literalContext):
        self._enter_ctx(ctx)

        value = ctx.value.accept(self)

        self._exit_ctx()

        return value

    # Visit a parse tree produced by LangParser#expr_set_clause__set_start_states.
    def visitExpr_set_clause__set_start_states(
        self,
        ctx: LangParser.Expr_set_clause__set_start_statesContext,
    ):
        def result(sm, states):
            if not isinstance(states, LangValueSet):
                raise type_error(states, "set")

            for s in set(sm.start_states):
                sm.remove_start_state(s)

            for s in value_to_python_value(states):
                sm.add_start_state(s)

        return result

    # Visit a parse tree produced by LangParser#expr_set_clause__set_final_states.
    def visitExpr_set_clause__set_final_states(
        self,
        ctx: LangParser.Expr_set_clause__set_final_statesContext,
    ):
        def result(sm, states):
            if not isinstance(states, LangValueSet):
                raise type_error(states, "set")

            for s in set(sm.final_states):
                sm.remove_final_state(s)

            for s in value_to_python_value(states):
                sm.add_final_state(s)

        return result

    # Visit a parse tree produced by LangParser#expr_set_clause__add_start_states.
    def visitExpr_set_clause__add_start_states(
        self,
        ctx: LangParser.Expr_set_clause__add_start_statesContext,
    ):
        def result(sm, states):
            if not isinstance(states, LangValueSet):
                raise type_error(states, "set")

            for s in value_to_python_value(states):
                sm.add_start_state(s)

        return result

    # Visit a parse tree produced by LangParser#expr_set_clause__add_final_states.
    def visitExpr_set_clause__add_final_states(
        self,
        ctx: LangParser.Expr_set_clause__add_final_statesContext,
    ):
        def result(sm, states):
            if not isinstance(states, LangValueSet):
                raise type_error(states, "set")

            for s in value_to_python_value(states):
                sm.add_final_state(s)

        return result

    # Visit a parse tree produced by LangParser#expr_get_clause__start_states.
    def visitExpr_get_clause__start_states(
        self,
        ctx: LangParser.Expr_get_clause__start_statesContext,
    ):
        expr_ctx = ctx.parentCtx

        if not isinstance(expr_ctx, LangParser.Expr__getContext):
            raise ValueError("cannot interpret without parent expr context")

        # use expt ctx to access value
        value = expr_ctx.sm.accept(self)

        # T-StartStatesOf
        if not isinstance(value, LangValueFA):
            raise type_error(value, "FA")

        return LangValueSet(
            value={
                python_value_to_value(x.value, expr_ctx)
                for x in value.value.start_states
            },
            ctx=expr_ctx,
        )

    # Visit a parse tree produced by LangParser#expr_get_clause__final_states.
    def visitExpr_get_clause__final_states(
        self,
        ctx: LangParser.Expr_get_clause__final_statesContext,
    ):
        expr_ctx = ctx.parentCtx

        if not isinstance(expr_ctx, LangParser.Expr__getContext):
            raise ValueError("cannot interpret without parent expr context")

        # use expt ctx to access value
        value = expr_ctx.sm.accept(self)

        # T-FinalStatesOf
        if not isinstance(value, LangValueFA):
            raise type_error(value, "FA")

        return LangValueSet(
            value={
                python_value_to_value(x.value, expr_ctx)
                for x in value.value.final_states
            },
            ctx=expr_ctx,
        )

    # Visit a parse tree produced by LangParser#expr_get_clause__reachable_states.
    def visitExpr_get_clause__reachable_states(
        self,
        ctx: LangParser.Expr_get_clause__reachable_statesContext,
    ):
        self._enter_ctx(ctx)

        raise NotImplementedError

    # Visit a parse tree produced by LangParser#expr_get_clause__nodes.
    def visitExpr_get_clause__nodes(
        self,
        ctx: LangParser.Expr_get_clause__nodesContext,
    ):
        expr_ctx = ctx.parentCtx

        if not isinstance(expr_ctx, LangParser.Expr__getContext):
            raise ValueError("cannot interpret without parent expr context")

        # use expt ctx to access value
        value = expr_ctx.sm.accept(self)

        # T-NodesOf
        if not isinstance(value, LangValueFA):
            raise type_error(value, "FA")

        return LangValueSet(
            value={
                python_value_to_value(x.value, expr_ctx) for x in value.value.states
            },
            ctx=expr_ctx,
        )

    # Visit a parse tree produced by LangParser#expr_get_clause__edges.
    def visitExpr_get_clause__edges(
        self,
        ctx: LangParser.Expr_get_clause__edgesContext,
    ):
        expr_ctx = ctx.parentCtx

        if not isinstance(expr_ctx, LangParser.Expr__getContext):
            raise ValueError("cannot interpret without parent expr context")

        # use expt ctx to access value
        value = expr_ctx.sm.accept(self)

        # T-EdgesOf
        if not isinstance(value, LangValueFA):
            raise type_error(value, "FA")

        return LangValueSet(
            value={
                python_value_to_value((u.value, l.value, v.value), expr_ctx)
                for u, x in value.value.to_dict().items()
                for l, v in x.items()
            },
            ctx=expr_ctx,
        )

    # Visit a parse tree produced by LangParser#expr_get_clause__labels.
    def visitExpr_get_clause__labels(
        self,
        ctx: LangParser.Expr_get_clause__labelsContext,
    ):
        expr_ctx = ctx.parentCtx

        if not isinstance(expr_ctx, LangParser.Expr__getContext):
            raise ValueError("cannot interpret without parent expr context")

        # use expt ctx to access value
        value = expr_ctx.sm.accept(self)

        # T-LabelsOf
        if not isinstance(value, LangValueFA):
            raise type_error(value, "FA")

        return LangValueSet(
            value={
                python_value_to_value(x.value, expr_ctx) for x in value.value.symbols
            },
            ctx=expr_ctx,
        )

    # Visit a parse tree produced by LangParser#literal__string.
    def visitLiteral__string(self, ctx: LangParser.Literal__stringContext):
        self._enter_ctx(ctx)

        result = LangValueString(value=parse_token(ctx.value), ctx=ctx)

        self._exit_ctx()

        return result

    # Visit a parse tree produced by LangParser#literal__int.
    def visitLiteral__int(self, ctx: LangParser.Literal__intContext):
        self._enter_ctx(ctx)

        result = LangValueInt(value=parse_token(ctx.value), ctx=ctx)

        self._exit_ctx()

        return result

    # Visit a parse tree produced by LangParser#literal__real.
    def visitLiteral__real(self, ctx: LangParser.Literal__realContext):
        self._enter_ctx(ctx)

        result = LangValueReal(value=parse_token(ctx.value), ctx=ctx)

        self._exit_ctx()

        return result

    # Visit a parse tree produced by LangParser#literal__range.
    def visitLiteral__range(self, ctx: LangParser.Literal__rangeContext):
        self._enter_ctx(ctx)

        from_ = parse_token(ctx.from_)
        to = parse_token(ctx.to)

        result = LangValueSet(
            value={LangValueInt(value=x, ctx=ctx) for x in range(from_, to)},
            ctx=ctx,
        )

        self._exit_ctx()

        return result

    # Visit a parse tree produced by LangParser#literal__set.
    def visitLiteral__set(self, ctx: LangParser.Literal__setContext):
        self._enter_ctx(ctx)

        result = LangValueSet(
            value={x.accept(self) for x in ctx.elems},
            ctx=ctx,
        )

        self._exit_ctx()

        return result

    # Visit a parse tree produced by LangParser#literal__lambda.
    def visitLiteral__lambda(self, ctx: LangParser.Literal__lambdaContext):
        self._enter_ctx(ctx)

        raise NotImplementedError

    # Visit a parse tree produced by LangParser#pattern__name.
    def visitPattern__name(self, ctx: LangParser.Pattern__nameContext):
        self._enter_ctx(ctx)

        raise NotImplementedError

    # Visit a parse tree produced by LangParser#pattern__tuple.
    def visitPattern__tuple(self, ctx: LangParser.Pattern__tupleContext):
        self._enter_ctx(ctx)

        raise NotImplementedError

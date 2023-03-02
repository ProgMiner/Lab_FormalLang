import project.graphs as g
import cfpq_data as cfpq
import tempfile
import pytest


def test_summary():
    graph = cfpq.labeled_cycle_graph(42, "x")
    summary = g.summary(graph)

    assert summary == (42, 42, {"x"})


def test_load_by_name():
    graph = g.load_by_name("bzip")
    summary = g.summary(graph)

    assert summary == (632, 556, {"a", "d"})


def test_load_summary_by_name():
    assert g.load_summary_by_name("bzip") == (632, 556, {"a", "d"})


def test_build_two_cycles():
    graph = g.build_two_cycles(3, 5, ("x", "y"))
    summary = g.summary(graph)

    assert summary == (9, 10, {"x", "y"})


def test_write_dot():
    graph = cfpq.labeled_cycle_graph(42, "x")

    with tempfile.TemporaryFile(mode="w+") as f:
        g.write_dot(graph, f)

        f.seek(0)
        content = f.read()

    assert (
        content
        == """digraph  {
0;
1;
2;
3;
4;
5;
6;
7;
8;
9;
10;
11;
12;
13;
14;
15;
16;
17;
18;
19;
20;
21;
22;
23;
24;
25;
26;
27;
28;
29;
30;
31;
32;
33;
34;
35;
36;
37;
38;
39;
40;
41;
0 -> 1  [key=0, label=x];
1 -> 2  [key=0, label=x];
2 -> 3  [key=0, label=x];
3 -> 4  [key=0, label=x];
4 -> 5  [key=0, label=x];
5 -> 6  [key=0, label=x];
6 -> 7  [key=0, label=x];
7 -> 8  [key=0, label=x];
8 -> 9  [key=0, label=x];
9 -> 10  [key=0, label=x];
10 -> 11  [key=0, label=x];
11 -> 12  [key=0, label=x];
12 -> 13  [key=0, label=x];
13 -> 14  [key=0, label=x];
14 -> 15  [key=0, label=x];
15 -> 16  [key=0, label=x];
16 -> 17  [key=0, label=x];
17 -> 18  [key=0, label=x];
18 -> 19  [key=0, label=x];
19 -> 20  [key=0, label=x];
20 -> 21  [key=0, label=x];
21 -> 22  [key=0, label=x];
22 -> 23  [key=0, label=x];
23 -> 24  [key=0, label=x];
24 -> 25  [key=0, label=x];
25 -> 26  [key=0, label=x];
26 -> 27  [key=0, label=x];
27 -> 28  [key=0, label=x];
28 -> 29  [key=0, label=x];
29 -> 30  [key=0, label=x];
30 -> 31  [key=0, label=x];
31 -> 32  [key=0, label=x];
32 -> 33  [key=0, label=x];
33 -> 34  [key=0, label=x];
34 -> 35  [key=0, label=x];
35 -> 36  [key=0, label=x];
36 -> 37  [key=0, label=x];
37 -> 38  [key=0, label=x];
38 -> 39  [key=0, label=x];
39 -> 40  [key=0, label=x];
40 -> 41  [key=0, label=x];
41 -> 0  [key=0, label=x];
}
"""
    )


def test_build_two_cycles_and_write_dot():
    with tempfile.TemporaryFile(mode="w+") as f:
        g.build_two_cycles_and_write_dot(2, 3, ("x", "y"), f)

        f.seek(0)
        content = f.read()

    assert (
        content
        == """digraph  {
1;
2;
0;
3;
4;
5;
1 -> 2  [key=0, label=x];
2 -> 0  [key=0, label=x];
0 -> 1  [key=0, label=x];
0 -> 3  [key=0, label=y];
3 -> 4  [key=0, label=y];
4 -> 5  [key=0, label=y];
5 -> 0  [key=0, label=y];
}
"""
    )

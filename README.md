## Описание языка

Описание синтаксиса
```ebnf
program = {stmt ";"} EOF.

stmt = "let" NAME "=" expr | ["print" | ">>>"] expr.

expr
    = "(" expr ")"
    | expr "with" expr_set_clause
    | expr_get_clause "of" expr
    | expr "mapped" "with" expr
    | expr "filtered" "with" expr
    | "load" STRING
    | "-" expr
    | expr "+" expr
    | expr "-" expr
    | expr "*" expr
    | expr "/" expr
    | expr "|" expr
    | expr "&" expr
    | expr "*"
    | expr "==" expr
    | expr "!=" expr
    | expr "<" expr
    | expr ">" expr
    | expr "<=" expr
    | expr ">=" expr
    | expr "or" expr
    | expr "and" expr
    | "not" expr
    | expr "in" expr
    | expr "not" "in" expr
    | NAME
    | literal
    .

expr_set_clause
    = "only" "start" "states" expr
    | "only" "final" "states" expr
    | ["additional"] "start" "states" expr
    | ["additional"] "final" "states" expr
    .

expr_get_clause
    = "start" "states"
    | "final" "states"
    | "reachable" "states"
    | "nodes"
    | "edges"
    | "labels"
    .

literal
    = STRING | INT_NUMBER | REAL_NUMBER
    | INT_NUMBER ".." INT_NUMBER
    | "{" [{ expr "," } expr] "}"
    | "\\" pattern "->" expr
    .

pattern = NAME | "(" {pattern ","} pattern ")".
```

Токены описаны в синтаксисе ANTLR4 для удобства чтения:

```antlr
fragment W: [a-zA-Z_];
fragment D: [0-9];
fragment WD: (W|D);
fragment S: [ \t\r\n\u000C];

INT_NUMBER: [1-9][0-9]*|'0';
REAL_NUMBER: ([1-9][0-9]*)?'.'([0-9]*[1-9]([eE]'-'?[1-9][0-9]*)?|'0')|[1-9][0-9]*[eE]'-'?[1-9][0-9]*;
STRING: '"' ('\\'. | (~'"')+)* '"';
NAME: W WD*;

BLOCK_COMMENT: '/*' (BLOCK_COMMENT|.)*? '*/';
COMMENT: '//' .*? '\n';
WS: S+;
```

### Текст программы

Программа на языке является упорядоченным списком предложений (statement).

После каждого предложения обязательно ставится символ `;` (точка с запятой). Это необходимо для
устранения возможных неоднозначностей при анализе текста программы.

При выполнении каждое предложение обрабатывается последовательно в том же порядке, в котором
написаны в программе с учётом эффектов, внесённых выполнением предыдущих предложений.

Всякая программа должна состоять из предложений и только из них. Не допускается использование
сторонних символов до списка предложений, между ними, или после них (кроме комментариев,
которые могут находиться в любой части программы).

### Предложения (statements)

Предложения бывают двух видов:

- Определение имени, предложение let

    Определение имени делает новое имя, указанное в предложении, видимым и доступным для
    использования во всех предложениях, идущих после определения (не включая его). Если указанное
    в предложении имя уже было определено ранее, начиная со следующего предложения оно будет
    переопределено новым значением без возможности использования старого значения. При определении
    имени, выражение, связываемое с именем, вычисляется до конца (используется энергичная семантика
    вычислений).

- Вывод на экран

    Предложение вывода на экран вычисляет значение выражения и выводит его результат на экран.
    Допускается две формы записи, в стиле Python 2: `print <expr>` и в сокращённом стиле:
    `>>> <expr>`. Также можно просто написать выражение в качестве предложения и его результат
    будет выведен на экран.

### Выражения

Выражения — ключевая синтаксическая категория языка, основной строительный блок для всех
вычислений. Допустимы следующие виды выражений:

- Выражение, окружённое круглыми скобками

    Круглые скобки используются для группировки выражений и удаления неоднозначности из программы.
    С точки зрения вычисления они не несут ценности.

- Выражение `with`

    Данное выражение позволяет конфигурировать существующие конечные автоматы. В частности,

    - `<expr> with only start states <expr>` — переопределяет множество стартовых состояний КА,
    - `<expr> with only final states <expr>` — переопределяет множество конечных состояний КА,
    - `<expr> with [additional] start states <expr>` — дополняет множество стартовых состояний КА,
    - `<expr> with [additional] final states <expr>` — дополняет множество конечных состояний КА.

    Важно, что выражение `with` при вычислении не изменяет конфигурируемый КА, а лишь порождает на
    его основе новый КА с изменённой конфигурацией и возвращает его в качестве результата.

- Выражение `of`

    Позволяет получить свойства КА, такие как:

    - `start states of <expr>` — множество стартовых состояний КА,
    - `final states of <expr>` — множество конечных состояний КА,
    - `reachable states of <expr>` — множество пар достижимых состояний КА (пара `(a, b)` значит,
        что состояние `b` достижимо из `a`),
    - `nodes of <expr>` — множество вершин (состояний) КА,
    - `edges of <expr>` — множество рёбер (переходов) КА, где каждое ребро есть тройка
        `(u, label, v)`,
    - `labels of <expr>` — алфавит (множество меток на рёбрах) КА.

- Выражение `mapped with`

    Аналог функции `map` из функциональных языков программирования. Требует, чтобы на входе были
    множество и лямбда-функция. Результаты применения переданной лямбда-функции к каждому из
    элементов переданного множества будут собраны в новое множество и возвращены в качестве
    результата выражения.

- Выражение `filtered with`

    Аналог функции `filter` из функциональных языков программирования. Требует, чтобы на входе
    были множество и лямбда-фукнция. Переданная лямбда функция будет применена к каждому из
    элементов переданного множества. Требуется, чтобы результатом применения было булево значение.
    Те элементы, для которых результат применения будет `True`, будут собраны в новое множество и
    возвращены в качестве результата выражения.

- Выражение `load`

    Загружает граф по имени. Сначала граф ищется в текущей рабочей директории как файл, используя
    переданное имя как путь до файла. Если файл не был найден, будет попытка загрузить граф из
    датасета.

    Формат файла пока не специфицирован.

- Математические операции

    Определено 3 унарных и 12 бинарных математических операторов:

    - Для булевых значений:
        - операторы сравнения: `<expr> < <expr>`, `<=`, `>`, `>=`, `==`, `!=`,
        - логическое ИЛИ: `<expr> or <expr>`,
        - логическое И: `<expr> and <expr>`,
        - логическое НЕ: `not <expr>`.

    - Для чисел:
        - операторы сравнения: `<expr> < <expr>`, `<=`, `>`, `>=`, `==`, `!=`,
        - унарный минус: `- <expr>`,
        - сложение: `<expr> + <expr>`,
        - вычитание: `<expr> - <expr>`,
        - умножение: `<expr> * <expr>`,
        - деление: `<expr> / <expr>`,
        - побитовое ИЛИ: `<expr> | <expr>` (только для целых чисел),
        - побитовое И: `<expr> & <expr>` (только для целых чисел).

    - Для строк:
        - операторы сравнения: `<expr> < <expr>`, `<=`, `>`, `>=`, `==`, `!=`,
        - конкатенация: `<expr> + <expr>` (допустима конкатенация строки с числом),
        - повторение: `<expr> * <expr>` (один операнд строковый, другой целочисленный).

    - Для конечных автоматов:
        - конкатенация языков: `<expr> + <expr>`,
        - объединение языков: `<expr> | <expr>`,
        - пересечение языков: `<expr> & <expr>`,
        - звезда Клини: `<expr> *`.

    - Для множеств:
        - операторы сравнения: `<expr> == <expr>`, `!=`,
        - объединение множеств: `<expr> | <expr>`,
        - пересечение множеств: `<expr> & <expr>`,
        - проверка вхождения в множество: `<expr> in <expr>`, `<expr> not in <expr>`.

    Важное исключение из вышеописанных правил, что операторы, определённые на конечных автоматах,
    будучи применёнными к строке, вызывают неявное преобразование строки в автомат с одним
    переходом. Это сделано для удобства определения автоматов в языке. Это лишь частично относится
    к оператору конкатенации `+`, потому что будучи применённым к двум строкам он породит также
    строку, а будучи применённым к автомату и строке, он вызовет неявное преобразование.

- Имя

    Любое, определённое выше (в предыдущих предложениях) с помощью предложения `let`, имя
    может быть использовано в качестве выражения.

- Литерал

    Литералом называется значение времени выполнения, записанное напрямую в коде программы.
    Предусмотрены следующие виды литералов:

    - Целое число
    - Вещественное число
    - Строка
    - Диапазон
    - Множество
    - Лямбда-выражение

    Синтаксис каждого из перечисленных выше видов литералов описан в формальной нотации в начале.

    Каждый из видов литералов порождает отдельный вид значений времени выполнения.
    Подробнее они описаны ниже в разделе Значения.

    Синтаксис диапазонов является сокращённой записью для литерала множества, состоящего из целых
    чисел с шагом 1 от первого (включительно) до второго (не включительно).

    Синтаксис set comprehension намерено не добавлен в язык, чтобы не создавать излишней сложности,
    потому что все необходимые операции могут быть выражены с помощью выражений `mapped with` и
    `filtered with`.

### Значения

Значения времени выполнения бывают 8 типов:

- `boolean` — Булево значение, `True` или `False`
- `int` — Целое число, целое число неограниченного размера
- `real` — Вещественное число, вещественное число, ограниченное представлением вещественных чисел
    языка Python
- `string` — Строка
- $`\texttt{(} T_1, ..., T_n \texttt{)}`$ — Кортеж, пара или тройка. Не могут порождаться
    напрямую в языке, а используются только для представления рёбер и множества достижимых вершин
- `set` — Множество значений любых из перечисленных типов, множества **гетерогенны**,
    то есть одно множество может содержать значения разных типов
- `FA` — Конечный автомат
- $`T \rightarrow S`$ — Лямбда-функция

#### Лямбда-функция

Лямбда-функции могут принимать только ровно один параметр.

Допустимо вместо имени параметра использовать шаблон кортежа, где каждое из значений также
может сопоставляться с шаблоном или назначаться имени. Вместо имени допустимо использовать символ
`_` (нижнее подчёркивание) для пометки, что значение не будет использоваться.

Шаблоны в качестве параметра лямбда-функции — это единственный допустимый в языке способ
обращения к полям кортежей.


### Система типов

В языке используется **строгая динамическая** типизация, типы проверяются **во время выполнения**
программы. Система типов недостаточно мощная, чтобы выразить все требования к корректным
программам. Кроме того, некоторые решения о типизации принимаются в зависимости от значений
операндов, а не только их типов.

Предложения (statements) не типизируются, но каждое предложение `let` вносит в контекст $`\Gamma`$
новую переменную, или заменяет существующую.

Правила типизации шаблонов:

$$\texttt{NAME} : T \Rightarrow \texttt{NAME} : T \quad \text{(PT — Name)}$$

$$\frac{p_1 : T_1 \Rightarrow \Delta_1 \quad ... \quad p_n : T_n \Rightarrow \Delta_n}{\texttt{(} p_1, ..., p_n \texttt{)} : \texttt{(} T_1, ..., T_n \texttt{)} \Rightarrow \Delta_1, ..., \Delta_n} \quad \text{(PT — Tuple)}$$

Правила типизации выражений:

$$\Gamma \vdash \texttt{STRING} : \texttt{string} \quad \text{(T — String)}$$

$$\Gamma \vdash \texttt{INT\\_NUMBER} : \texttt{int} \quad \text{(T — Int)}$$

$$\Gamma \vdash \texttt{REAL\\_NUMBER} : \texttt{real} \quad \text{(T — Real)}$$

$$\Gamma \vdash \texttt{INT\\_NUMBER} \texttt{..} \texttt{INT\\_NUMBER} : \texttt{set} \quad \text{(T — Range)}$$

$$\Gamma \vdash \texttt{load STRING} : \texttt{FA}$$

$$\frac{\texttt{NAME} : T \in \Gamma}{\Gamma \vdash \texttt{NAME} : T} \quad \text{(T — Name)}$$

$$\frac{\Gamma \vdash t : \texttt{string}}{\Gamma \vdash t : \texttt{FA}} \quad \text{(T — Smb)}$$

$$\frac{\Gamma \vdash t_1 : T_1 \quad ... \quad \Gamma \vdash t_n : T_n}{\Gamma \vdash \texttt{\\{} t_1, ..., t_n \texttt{\\}} : \texttt{set}} \quad \text{(T — Set)}$$

$$\frac{p : T \Rightarrow \Delta \quad \Gamma, \Delta \vdash t : S}{\Gamma \vdash \texttt{\\\\} p ~ \texttt{->} ~ t : T \rightarrow S} \quad \text{(T — Lambda)}$$

$$\frac{\Gamma \vdash t_1 : \texttt{FA} \quad \Gamma \vdash t_2 : \texttt{set}}{\Gamma \vdash t_1 ~ \texttt{with only start states} ~ t_2 : \texttt{FA}} \quad \text{(T — WithOnlyStartStates)}$$

$$\frac{\Gamma \vdash t_1 : \texttt{FA} \quad \Gamma \vdash t_2 : \texttt{set}}{\Gamma \vdash t_1 ~ \texttt{with only final states} ~ t_2 : \texttt{FA}} \quad \text{(T — WithOnlyFinalStates)}$$

$$\frac{\Gamma \vdash t_1 : \texttt{FA} \quad \Gamma \vdash t_2 : \texttt{set}}{\Gamma \vdash t_1 ~ \texttt{with [additional] start states} ~ t_2 : \texttt{FA}} \quad \text{(T — WithStartStates)}$$

$$\frac{\Gamma \vdash t_1 : \texttt{FA} \quad \Gamma \vdash t_2 : \texttt{set}}{\Gamma \vdash t_1 ~ \texttt{with [additional] final states} ~ t_2 : \texttt{FA}} \quad \text{(T — WithFinalStates)}$$

$$\frac{\Gamma \vdash t : \texttt{FA}}{\Gamma \vdash \texttt{start states of} ~ t : \texttt{set}} \quad \text{(T — StartStatesOf)}$$

$$\frac{\Gamma \vdash t : \texttt{FA}}{\Gamma \vdash \texttt{final states of} ~ t : \texttt{set}} \quad \text{(T — FinalStatesOf)}$$

$$\frac{\Gamma \vdash t : \texttt{FA}}{\Gamma \vdash \texttt{reachable states of} ~ t : \texttt{set}} \quad \text{(T — ReachableStatesOf)}$$

$$\frac{\Gamma \vdash t : \texttt{FA}}{\Gamma \vdash \texttt{nodes of} ~ t : \texttt{set}} \quad \text{(T — NodesStatesOf)}$$

$$\frac{\Gamma \vdash t : \texttt{FA}}{\Gamma \vdash \texttt{edges of} ~ t : \texttt{set}} \quad \text{(T — EdgesStatesOf)}$$

$$\frac{\Gamma \vdash t : \texttt{FA}}{\Gamma \vdash \texttt{labels of} ~ t : \texttt{set}} \quad \text{(T — LabelsStatesOf)}$$

$$\frac{\Gamma \vdash t_1 : \texttt{FA} \quad \Gamma \vdash t_2 : T \rightarrow S}{\Gamma \vdash t_1 ~ \texttt{mapped with} ~ t_2 : \texttt{set}} \quad \text{(T — Map)}$$

$$\frac{\Gamma \vdash t_1 : \texttt{FA} \quad \Gamma \vdash t_2 : T \rightarrow \texttt{boolean}}{\Gamma \vdash t_1 ~ \texttt{filtered with} ~ t_2 : \texttt{set}} \quad \text{(T — Filter)}$$

$$\frac{\Gamma \vdash t : \texttt{FA}}{\Gamma \vdash t* : \texttt{FA}} \quad \text{(T — KleeneStar)}$$

$$\frac{\Gamma \vdash t : \texttt{int}}{\Gamma \vdash -t : \texttt{int}} \quad \text{(T — UnaryMinusI)}$$

$$\frac{\Gamma \vdash t : \texttt{real}}{\Gamma \vdash -t : \texttt{real}} \quad \text{(T — UnaryMinusR)}$$

$$\frac{\Gamma \vdash t : \texttt{boolean}}{\Gamma \vdash \texttt{not} ~ t : \texttt{boolean}} \quad \text{(T — Not)}$$

$$\frac{\Gamma \vdash t_1 : \texttt{int} \quad \Gamma \vdash t_2 : \texttt{int}}{\Gamma \vdash t_1 * t_2 : \texttt{int}} \quad \text{(T — MulII)}$$

$$\frac{\Gamma \vdash t_1 : \texttt{int} \quad \Gamma \vdash t_2 : \texttt{real}}{\Gamma \vdash t_1 * t_2 : \texttt{real}} \quad \text{(T — MulIR)}$$

$$\frac{\Gamma \vdash t_1 : \texttt{real} \quad \Gamma \vdash t_2 : \texttt{int}}{\Gamma \vdash t_1 * t_2 : \texttt{real}} \quad \text{(T — MulRI)}$$

$$\frac{\Gamma \vdash t_1 : \texttt{real} \quad \Gamma \vdash t_2 : \texttt{real}}{\Gamma \vdash t_1 * t_2 : \texttt{real}} \quad \text{(T — MulRR)}$$

$$\frac{\Gamma \vdash t_1 : \texttt{int} \quad \Gamma \vdash t_2 : \texttt{string}}{\Gamma \vdash t_1 * t_2 : \texttt{string}} \quad \text{(T — MulIS)}$$

$$\frac{\Gamma \vdash t_1 : \texttt{string} \quad \Gamma \vdash t_2 : \texttt{int}}{\Gamma \vdash t_1 * t_2 : \texttt{string}} \quad \text{(T — MulSI)}$$

$$\frac{\Gamma \vdash t_1 : \texttt{int} \quad \Gamma \vdash t_2 : \texttt{int}}{\Gamma \vdash t_1 / t_2 : \texttt{int}} \quad \text{(T — DivIII)}$$

$$\frac{\Gamma \vdash t_1 : \texttt{int} \quad \Gamma \vdash t_2 : \texttt{int}}{\Gamma \vdash t_1 / t_2 : \texttt{real}} \quad \text{(T — DivIIR)}$$

$$\frac{\Gamma \vdash t_1 : \texttt{int} \quad \Gamma \vdash t_2 : \texttt{real}}{\Gamma \vdash t_1 / t_2 : \texttt{real}} \quad \text{(T — DivIR)}$$

$$\frac{\Gamma \vdash t_1 : \texttt{real} \quad \Gamma \vdash t_2 : \texttt{int}}{\Gamma \vdash t_1 / t_2 : \texttt{real}} \quad \text{(T — DivRI)}$$

$$\frac{\Gamma \vdash t_1 : \texttt{real} \quad \Gamma \vdash t_2 : \texttt{real}}{\Gamma \vdash t_1 / t_2 : \texttt{int}} \quad \text{(T — DivRRI)}$$

$$\frac{\Gamma \vdash t_1 : \texttt{real} \quad \Gamma \vdash t_2 : \texttt{real}}{\Gamma \vdash t_1 / t_2 : \texttt{real}} \quad \text{(T — DivRRR)}$$

$$\frac{\Gamma \vdash t_1 : \texttt{real} \quad \Gamma \vdash t_2 : \texttt{real}}{\Gamma \vdash t_1 / t_2 : \texttt{real}} \quad \text{(T — DivRRR)}$$

$$\frac{\Gamma \vdash t_1 : \texttt{int} \quad \Gamma \vdash t_2 : \texttt{int}}{\Gamma \vdash t_1 \\& t_2 : \texttt{int}} \quad \text{(T — BitwiseAnd)}$$

$$\frac{\Gamma \vdash t_1 : \texttt{set} \quad \Gamma \vdash t_2 : \texttt{set}}{\Gamma \vdash t_1 \\& t_2 : \texttt{set}} \quad \text{(T — SetIntersect)}$$

$$\frac{\Gamma \vdash t_1 : \texttt{FA} \quad \Gamma \vdash t_2 : \texttt{FA}}{\Gamma \vdash t_1 \\& t_2 : \texttt{FA}} \quad \text{(T — FAIntersect)}$$

$$\frac{\Gamma \vdash t_1 : \texttt{int} \quad \Gamma \vdash t_2 : \texttt{int}}{\Gamma \vdash t_1 + t_2 : \texttt{int}} \quad \text{(T — AddII)}$$

$$\frac{\Gamma \vdash t_1 : \texttt{int} \quad \Gamma \vdash t_2 : \texttt{real}}{\Gamma \vdash t_1 + t_2 : \texttt{real}} \quad \text{(T — AddIR)}$$

$$\frac{\Gamma \vdash t_1 : \texttt{real} \quad \Gamma \vdash t_2 : \texttt{int}}{\Gamma \vdash t_1 + t_2 : \texttt{real}} \quad \text{(T — AddRI)}$$

$$\frac{\Gamma \vdash t_1 : \texttt{real} \quad \Gamma \vdash t_2 : \texttt{real}}{\Gamma \vdash t_1 + t_2 : \texttt{real}} \quad \text{(T — AddRR)}$$

$$\frac{\Gamma \vdash t_1 : T \quad \Gamma \vdash t_2 : \texttt{string}}{\Gamma \vdash t_1 + t_2 : \texttt{string}} \quad \text{(T — ConcatS1)}$$

$$\frac{\Gamma \vdash t_1 : \texttt{string} \quad \Gamma \vdash t_2 : T}{\Gamma \vdash t_1 + t_2 : \texttt{string}} \quad \text{(T — ConcatS2)}$$

$$\frac{\Gamma \vdash t_1 : \texttt{FA} \quad \Gamma \vdash t_2 : \texttt{FA}}{\Gamma \vdash t_1 + t_2 : \texttt{FA}} \quad \text{(T — ConcatFA)}$$

$$\frac{\Gamma \vdash t_1 : \texttt{int} \quad \Gamma \vdash t_2 : \texttt{int}}{\Gamma \vdash t_1 - t_2 : \texttt{int}} \quad \text{(T — SubII)}$$

$$\frac{\Gamma \vdash t_1 : \texttt{int} \quad \Gamma \vdash t_2 : \texttt{real}}{\Gamma \vdash t_1 - t_2 : \texttt{real}} \quad \text{(T — SubIR)}$$

$$\frac{\Gamma \vdash t_1 : \texttt{real} \quad \Gamma \vdash t_2 : \texttt{int}}{\Gamma \vdash t_1 - t_2 : \texttt{real}} \quad \text{(T — SubRI)}$$

$$\frac{\Gamma \vdash t_1 : \texttt{real} \quad \Gamma \vdash t_2 : \texttt{real}}{\Gamma \vdash t_1 - t_2 : \texttt{real}} \quad \text{(T — SubRR)}$$

$$\frac{\Gamma \vdash t_1 : \texttt{int} \quad \Gamma \vdash t_2 : \texttt{int}}{\Gamma \vdash t_1 | t_2 : \texttt{int}} \quad \text{(T — BitwiseOr)}$$

$$\frac{\Gamma \vdash t_1 : \texttt{set} \quad \Gamma \vdash t_2 : \texttt{set}}{\Gamma \vdash t_1 | t_2 : \texttt{set}} \quad \text{(T — SetUnion)}$$

$$\frac{\Gamma \vdash t_1 : \texttt{FA} \quad \Gamma \vdash t_2 : \texttt{FA}}{\Gamma \vdash t_1 | t_2 : \texttt{FA}} \quad \text{(T — FAUnion)}$$

$$\frac{\Gamma \vdash t_1 : T \quad \Gamma \vdash t_2 : S}{\Gamma \vdash t_1 == t_2 : \texttt{boolean}} \quad \text{(T — Equals)}$$

$$\frac{\Gamma \vdash t_1 : T \quad \Gamma \vdash t_2 : S}{\Gamma \vdash t_1 ~ != ~ t_2 : \texttt{boolean}} \quad \text{(T — NotEquals)}$$

$$\frac{\Gamma \vdash t_1 : T \quad \Gamma \vdash t_2 : S}{\Gamma \vdash t_1 < t_2 : \texttt{boolean}} \quad \text{(T — Less)}$$

$$\frac{\Gamma \vdash t_1 : T \quad \Gamma \vdash t_2 : S}{\Gamma \vdash t_1 > t_2 : \texttt{boolean}} \quad \text{(T — Greater)}$$

$$\frac{\Gamma \vdash t_1 : T \quad \Gamma \vdash t_2 : S}{\Gamma \vdash t_1 <= t_2 : \texttt{boolean}} \quad \text{(T — LessEqual)}$$

$$\frac{\Gamma \vdash t_1 : T \quad \Gamma \vdash t_2 : S}{\Gamma \vdash t_1 >= t_2 : \texttt{boolean}} \quad \text{(T — GreaterEqual)}$$

$$\frac{\Gamma \vdash t_1 : T \quad \Gamma \vdash t_2 : \texttt{set}}{\Gamma \vdash t_1 ~ in ~ t_2 : \texttt{boolean}} \quad \text{(T — In)}$$

$$\frac{\Gamma \vdash t_1 : T \quad \Gamma \vdash t_2 : \texttt{set}}{\Gamma \vdash t_1 ~ not ~ in ~ t_2 : \texttt{boolean}} \quad \text{(T — NotIn)}$$

$$\frac{\Gamma \vdash t_1 : \texttt{boolean} \quad \Gamma \vdash t_2 : \texttt{boolean}}{\Gamma \vdash t_1 ~ and ~ t_2 : \texttt{boolean}} \quad \text{(T — And)}$$

$$\frac{\Gamma \vdash t_1 : \texttt{boolean} \quad \Gamma \vdash t_2 : \texttt{boolean}}{\Gamma \vdash t_1 ~ or ~ t_2 : \texttt{boolean}} \quad \text{(T — Or)}$$


## Примеры кода

```
// загрузка графа generations и связывание с именем g

let g = load "generations";

// вывод множества вершин, рёбер и меток графа g
>>> nodes of g;
>>> edges of g;
>>> labels of g;

// связывание имени g с новым графом, образованным из g путём установки множества конечных состояний
let g = g with only final states { 21 };

// определение КА и связывание с именем q
let q = ("equivalentClass" | "first") + "type"* + "type";

// вывод пар достижимых вершин в пересечении g и q
>>> reachable states of (g & q);

// порождение множества из диапазона с помощью mapped with и filtered with
>>> 0..10
    mapped with (\x -> x * 2)
    mapped with (\x -> x + 3)
    filtered with (\x -> 0 < x and x < 5)
    ;
```

## Сборка парсера

Для сборки парсера необходимо предварительно установить библиотеки из файла `requirements.txt`.

Затем убедитесь, что у вас установлена Java 11+, или не установлена никакая версия Java.
Во втором случае нужная версия будет скачана автоматически при необходимости.

Для удобства в проекте существует скрипт, выполняющий всю работу по генерации парсера:
```bash
./scripts/build_parser.py
```


# Formal Language Course

[![Check code style](https://github.com/FormalLanguageConstrainedPathQuerying/formal-lang-course/actions/workflows/code_style.yml/badge.svg)](https://github.com/FormalLanguageConstrainedPathQuerying/formal-lang-course/actions/workflows/code_style.yml)
[![Code style](https://img.shields.io/badge/Code%20style-black-000000.svg)](https://github.com/psf/black)

---

Курс по формальным языкам: шаблон структуры репозитория для выполнения домашних работ,
а также материалы курса и другая сопутствующая информация.

Актуальное:
- [Таблица с текущими результатами](https://docs.google.com/spreadsheets/d/14h6hUWGMfVhwkxCb9KmRc_yt4VgeecyMEIMDC6zg95c/edit?usp=sharing)
- [Список задач](https://github.com/FormalLanguageConstrainedPathQuerying/formal-lang-course/tree/main/tasks)
- [Стиль кода как референс](https://www.python.org/dev/peps/pep-0008/)
- [Материалы по курсу](https://github.com/FormalLanguageConstrainedPathQuerying/formal-lang-course/blob/main/docs/lecture_notes/Formal_language_course.pdf)
- [О достижимости с ограничениями в терминах формальных языков](https://github.com/FormalLanguageConstrainedPathQuerying/FormalLanguageConstrainedReachability-LectureNotes)
- Классика по алгоритмам синтаксического анализа: [Dick Grune, Ceriel J. H. Jacobs, "Parsing Techniques A Practical Guide"](https://link.springer.com/book/10.1007/978-0-387-68954-8#bibliographic-information)
- Классика по теории формальных языков: [M. A. Harrison. 1978. Introduction to Formal Language Theory](https://dl.acm.org/doi/book/10.5555/578595)

Технологии:
- Python 3.8+
- Pytest для unit тестирования
- GitHub Actions для CI
- Google Colab для постановки и оформления экспериментов
- Сторонние пакеты из `requirements.txt` файла
- Английский язык для документации или самодокументирующийся код

## Работа с проектом

- Для выполнения домашних практических работ необходимо сделать `fork` этого репозитория к себе в `GitHub`.
- Рекомендуется установить [`pre-commit`](https://pre-commit.com/#install) для поддержания проекта в адекватном состоянии.
  - Установить `pre-commit` можно выполнив следующую команду в корне вашего проекта:
    ```shell
    pre-commit install
    ```
  - Отформатировать код в соответствии с принятым стилем можно выполнив следующую команду в корне вашего проекта:
    ```shell
    pre-commit run --all-files
    ```
- Ссылка на свой `fork` репозитория размещается в [таблице](https://docs.google.com/spreadsheets/d/14h6hUWGMfVhwkxCb9KmRc_yt4VgeecyMEIMDC6zg95c/edit?usp=sharing) курса с результатами.
- В свой репозиторий необходимо добавить проверяющих с `admin` правами на чтение, редактирование и проверку `pull-request`'ов.

## Домашние практические работы

### Дедлайны

- **мягкий**: TODO 23:59
- **жёсткий**: TODO 23:59

### Выполнение домашнего задания

- Каждое домашнее задание выполняется в отдельной ветке. Ветка должна иметь осмысленное консистентное название.
- При выполнении домашнего задания в новой ветке необходимо открыть соответствующий `pull-request` в `main` вашего `fork`.
- `Pull-request` снабдить понятным названием и описанием с соответствующими пунктами прогресса.
- Проверка заданий осуществляется посредством `review` вашего `pull-request`.
- Как только вы считаете, что задание выполнено, вы можете запросить `review` у проверяющего.
  - Если `review` запрошено **до мягкого дедлайна**, то вам гарантированна дополнительная проверка (до жёсткого дедлайна), позволяющая исправить замечания до наступления жёсткого дедлайна.
  - Если `review` запрошено **после мягкого дедлайна**, но **до жесткого дедлайна**, задание будет проверено, но нет гарантий, что вы успеете его исправить.
- Когда проверка будет пройдена, и задание **зачтено**, его необходимо `merge` в `main` вашего `fork`.
- Результаты выполненных заданий будут повторно использоваться в последующих домашних работах.

### Опциональные домашние задания
Часть задач, связанных с работой с GPGPU, будет помечена как опциональная. Это означает что и без их выполнения (при идеальном выполнении остальных задач) можно набрать полный балл за курс.

### Получение оценки за домашнюю работу

- Если ваша работа **зачтена** _до_ **жёсткого дедлайна**, то вы получаете **полный балл за домашнюю работу**.
- Если ваша работа **зачтена** _после_ **жёсткого дедлайна**, то вы получаете **половину полного балла за домашнюю работу**.
  - Если ревью было запрошено _до_ **жёсткого дедлайна** и задача зачтена сразу без замечаний, то вы всё ещё получаете **полный балл за домашнюю работу**.

## Код

- Исходный код практических задач по программированию размещайте в папке `project`.
- Файлам и модулям даем осмысленные имена, в соответствии с официально принятым стилем.
- Структурируем код, используем как классы, так и отдельно оформленные функции. Чем понятнее код, тем быстрее его проверять и тем больше у вас будет шансов получить полный балл.

## Тесты

- Тесты для домашних заданий размещайте в папке `tests`.
- Формат именования файлов с тестами `test_[какой модуль\класс\функцию тестирует].py`.
- Для работы с тестами рекомендуется использовать [`pytest`](https://docs.pytest.org/en/6.2.x/).
- Для запуска тестов необходимо из корня проекта выполнить следующую команду:
  ```shell
  python ./scripts/run_tests.py
  ```

## Эксперименты

- Для выполнения экспериментов потребуется не только код, но окружение и некоторая его настройка.
- Эксперименты должны быть воспроизводимыми (например, проверяющими).
- Эксперимент (настройка, замеры, результаты, анализ результатов) оформляется как Python-ноутбук, который публикуется на GitHub.
  - В качестве окружения для экспериментов с GPGPU (опциональные задачи) можно использовать [`Google Colab`](https://research.google.com/colaboratory/) ноутбуки. Для его создания требуется только учетная запись `Google`.
  - В `Google Colab` ноутбуке выполняется вся настройка, пишется код для экспериментов, подготовки отчетов и графиков.

## Структура репозитория

```text
.
├── .github - файлы для настройки CI и проверок
├── docs - текстовые документы и материалы по курсу
├── project - исходный код домашних работ
├── scripts - вспомогательные скрипты для автоматизации разработки
├── tasks - файлы с описанием домашних заданий
├── tests - директория для unit-тестов домашних работ
├── README.md - основная информация о проекте
└── requirements.txt - зависимости для настройки репозитория
```

## Контакты

- Семен Григорьев [@gsvgit](https://github.com/gsvgit)
- Егор Орачев [@EgorOrachyov](https://github.com/EgorOrachyov)
- Вадим Абзалов [@vdshk](https://github.com/vdshk)
- Рустам Азимов [@rustam-azimov](https://github.com/rustam-azimov)
- Екатерина Шеметова [@katyacyfra](https://github.com/katyacyfra)

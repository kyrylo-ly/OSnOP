# Лабораторна робота 12 — Частина 3
# Операторне виконання: присвоєння і print()
# Базується на extarithexpr.py з розширеним інтерпретатором формул

"""
---------- граматика мінімальної Python-подібної мови ----------
prog        ::= stmt *
stmt        ::= assign_stmt | print_stmt
assign_stmt ::= name "=" arith_expr
print_stmt  ::= "print(" arith_expr ")"
name        ::= letter ( letter | digit ) *

arith_expr ::= term ( ( "+" | "-" ) term ) *
term       ::= factor ( ( "*" | "/" | "//" | "%" ) factor ) *
factor     ::= ["+" | "-"] ( number | name | "(" arith_expr ")" | function )
               [ "**" factor ]
function   ::= "sin(" arith_expr ")" | "cos(" arith_expr ")"
number     ::= digit+ ["." digit+] [("e"|"E") ["+"| "-"] digit+]
digit      ::= "0" | "1" | ... | "9"
letter     ::= "a" | ... | "z" | "A" | ... | "Z" | "_"
----------------------------------------------------------------
Змінні зберігаються в таблиці (словник) і можуть використовуватись
у наступних виразах після присвоєння.
"""

import math


class errorexpr(Exception):
    """Допоміжний клас для збудження винятків при помилках розбору."""
    pass


class ExtArithexprAssInterpret:
    """Розширений інтерпретатор формул з підтримкою змінних і операторів.

    Підтримує:
      - Всі можливості extarithexpr.py (бінарні/унарні операції, **, sin/cos, дійсні числа)
      - Оператор присвоєння: x = <вираз>
      - Оператор виведення: print(<вираз>)
      - Змінні в виразах (ідентифікатори)
    """

    # ---------- коди лексем ----------
    empty        = 0   # '#' — обмежувач
    number       = 1   # числова константа
    funcname     = 2   # ім'я функції: sin, cos
    openbracket  = 3   # '('
    closebracket = 4   # ')'
    add          = 5   # '+'
    subtract     = 6   # '-'
    multiply     = 7   # '*'
    divide       = 8   # '/'
    floordiv     = 9   # '//'
    modulo       = 10  # '%'
    power        = 11  # '**'
    varname      = 12  # ім'я змінної (ідентифікатор)
    assign       = 13  # '='
    kw_print     = 14  # ключове слово 'print'

    # ---------- підтримувані математичні функції ----------
    FUNCTIONS = {'sin', 'cos'}

    def __init__(self):
        """Конструктор: ініціалізувати таблицю змінних і стан."""
        self.vars = {}    # таблиця змінних: ім'я - значення
        # стан сканування поточного рядка
        self.text = ''
        self.leks = []
        self.i = 0
        self.k = 0

    # ==================== ОПЕРАТОРНЕ ВИКОНАННЯ ====================

    def run_program(self, source):
        """Виконати програму — послідовність операторів.

        Аргумент source — рядок або список рядків.
        Кожен рядок — окремий оператор.
        """
        # розбити текст програми на рядки
        if isinstance(source, str):
            lines = source.split('\n')
        else:
            lines = source

        for lineno, line in enumerate(lines, start=1):
            line = line.strip()
            if not line or line.startswith('#'):
                # порожні рядки і коментарі пропустити
                continue
            ok, msg = self.exec_stmt(line, lineno)
            if not ok:
                print(f'  [Рядок {lineno}] Помилка: {msg}')

    def exec_stmt(self, line, lineno=0):
        """Виконати один оператор.

        Розпізнає:
          - assign_stmt: name = arith_expr
          - print_stmt:  print(arith_expr)

        Повертає (True, None) або (False, повідомлення_про_помилку).
        """
        # ---- підготовка сканера ----
        self.text = line.replace(' ', '')   # прибрати пропуски
        self.leks = []
        self.i = 0
        self.k = 0

        # ---- сканування оператора ----
        if not self.scanner():
            return (False, f'Помилка сканування: {line}')

        # ---- розбір і виконання ----
        try:
            if self.leks[0][0] == self.kw_print:
                # print(arith_expr)
                self._exec_print()
            elif self.leks[0][0] == self.varname and \
                 len(self.leks) > 1 and self.leks[1][0] == self.assign:
                # name = arith_expr
                self._exec_assign()
            else:
                return (False, f'Невідомий оператор: {line}')
        except errorexpr as e:
            return (False, str(e))
        except Exception as e:
            return (False, str(e))

        return (True, None)

    def _exec_assign(self):
        """Виконати оператор присвоєння: name = arith_expr."""
        var = self.leks[self.k][1]   # ім'я змінної
        self.GetNextToken()           # перейти до '='
        self.GetNextToken()           # перейти до першої лексеми виразу
        value = self.arithexpr()
        self.vars[var] = value        # зберегти результат у таблиці змінних
        # (не виводимо — присвоєння мовчазне)

    def _exec_print(self):
        """Виконати оператор print(arith_expr)."""
        self.GetNextToken()  # перейти до '('
        if self.leks[self.k][0] != self.openbracket:
            raise errorexpr("Очікується '(' після print")
        self.GetNextToken()  # перейти до першої лексеми виразу
        value = self.arithexpr()
        if self.leks[self.k][0] != self.closebracket:
            raise errorexpr("Очікується ')' після аргументу print")
        self.GetNextToken()
        # вивести результат
        print(value)

    # ==================== СКАНУВАННЯ ====================

    def scanner(self):
        """Сканувати рядок оператора і побудувати список лексем."""
        while self.i < len(self.text):
            ch = self.text[self.i]

            if ch == '(':
                self.leks.append((self.openbracket, '('))
            elif ch == ')':
                self.leks.append((self.closebracket, ')'))
            elif ch == '+':
                self.leks.append((self.add, '+'))
            elif ch == '-':
                self.leks.append((self.subtract, '-'))
            elif ch == '%':
                self.leks.append((self.modulo, '%'))
            elif ch == '=':
                self.leks.append((self.assign, '='))
            elif ch == '*':
                if self.i + 1 < len(self.text) and self.text[self.i + 1] == '*':
                    self.leks.append((self.power, '**'))
                    self.i += 1
                else:
                    self.leks.append((self.multiply, '*'))
            elif ch == '/':
                if self.i + 1 < len(self.text) and self.text[self.i + 1] == '/':
                    self.leks.append((self.floordiv, '//'))
                    self.i += 1
                else:
                    self.leks.append((self.divide, '/'))
            elif ch.isdigit():
                self.onenumber()
                self.i -= 1
            elif ch.isalpha() or ch == '_':
                # читати ідентифікатор (ім'я змінної, функція або print)
                if not self.scan_identifier():
                    return False
            else:
                return False  # недопустимий символ

            self.i += 1

        self.leks.append((self.empty, '#'))
        return True

    def onenumber(self):
        """Прочитати числову константу (ціле або дійсне)."""
        num_str = ''
        # ціла частина
        while self.i < len(self.text) and self.text[self.i].isdigit():
            num_str += self.text[self.i]
            self.i += 1
        # дробова частина
        if self.i < len(self.text) and self.text[self.i] == '.':
            num_str += '.'
            self.i += 1
            while self.i < len(self.text) and self.text[self.i].isdigit():
                num_str += self.text[self.i]
                self.i += 1
        # експоненціальна частина
        if self.i < len(self.text) and self.text[self.i] in ('e', 'E'):
            num_str += self.text[self.i]
            self.i += 1
            if self.i < len(self.text) and self.text[self.i] in ('+', '-'):
                num_str += self.text[self.i]
                self.i += 1
            while self.i < len(self.text) and self.text[self.i].isdigit():
                num_str += self.text[self.i]
                self.i += 1
        value = float(num_str) if ('.' in num_str or 'e' in num_str or 'E' in num_str) \
                else int(num_str)
        self.leks.append((self.number, value))

    def scan_identifier(self):
        """Прочитати ідентифікатор і класифікувати: функція, print чи змінна."""
        name = ''
        while self.i < len(self.text) and (self.text[self.i].isalnum() or self.text[self.i] == '_'):
            name += self.text[self.i]
            self.i += 1

        if name == 'print':
            self.leks.append((self.kw_print, 'print'))
        elif name in self.FUNCTIONS:
            self.leks.append((self.funcname, name))
        else:
            # ім'я змінної
            self.leks.append((self.varname, name))

        self.i -= 1  # повернутися на символ після імені (буде +1 в основному циклі)
        return True

    # ==================== РЕКУРСИВНИЙ СПУСК ====================

    def arithexpr(self):
        """arith_expr ::= term ( ( "+" | "-" ) term ) *"""
        y = self.term()
        while self.leks[self.k][0] in (self.add, self.subtract):
            opr = self.leks[self.k][0]
            self.GetNextToken()
            if opr == self.add:
                y = y + self.term()
            else:
                y = y - self.term()
        return y

    def term(self):
        """term ::= factor ( ( "*" | "/" | "//" | "%" ) factor ) *"""
        z = self.factor()
        while self.leks[self.k][0] in (self.multiply, self.divide,
                                        self.floordiv, self.modulo):
            opr = self.leks[self.k][0]
            self.GetNextToken()
            right = self.factor()
            if opr == self.multiply:
                z = z * right
            elif opr == self.divide:
                if right == 0:
                    raise errorexpr('Ділення на нуль')
                z = z / right
            elif opr == self.floordiv:
                if right == 0:
                    raise errorexpr('Ціле ділення на нуль')
                z = z // right
            else:
                if right == 0:
                    raise errorexpr('Остача від ділення на нуль')
                z = z % right
        return z

    def factor(self):
        """factor ::= ["+" | "-"] ( number | name | "(" arith_expr ")" | function )
                      [ "**" factor ]

        Додатково (порівняно з Частиною 2): розпізнавання змінних (varname).
        Унарний знак реалізований рекурсивним викликом factor() -- так само
        як у extarithexpr.py, що забезпечує вищий пріоритет ** над унарним:
          -a**2 = -(a**2),  --a = a
        """
        # п.5.4: унарний + або - -- рекурсивний виклик для правильного пріоритету **
        if self.leks[self.k][0] == self.add:
            self.GetNextToken()
            return +self.factor()
        elif self.leks[self.k][0] == self.subtract:
            self.GetNextToken()
            return -self.factor()

        if self.leks[self.k][0] == self.number:
            self.GetNextToken()
            val = self.leks[self.k - 1][1]

        elif self.leks[self.k][0] == self.varname:
            # змінна -- отримати її значення з таблиці
            vname = self.leks[self.k][1]
            if vname not in self.vars:
                raise errorexpr(f"Невизначена змінна: '{vname}'")
            self.GetNextToken()
            val = self.vars[vname]

        elif self.leks[self.k][0] == self.openbracket:
            self.GetNextToken()
            val = self.arithexpr()
            if self.leks[self.k][0] == self.closebracket:
                self.GetNextToken()
            else:
                raise errorexpr("Очікується закриваюча дужка ')'")

        elif self.leks[self.k][0] == self.funcname:
            fname = self.leks[self.k][1]
            self.GetNextToken()
            if self.leks[self.k][0] != self.openbracket:
                raise errorexpr(f"Очікується '(' після функції {fname}")
            self.GetNextToken()
            arg = self.arithexpr()
            if self.leks[self.k][0] == self.closebracket:
                self.GetNextToken()
            else:
                raise errorexpr("Очікується ')' після аргументу функції")
            if fname == 'sin':
                val = math.sin(arg)
            elif fname == 'cos':
                val = math.cos(arg)
            else:
                raise errorexpr(f'Невідома функція: {fname}')

        else:
            raise errorexpr(f"Очікується число, змінна або '(' : "
                            f"отримано '{self.leks[self.k][1]}'")

        # п.5.2: правоасоціативне піднесення до степеня (вищий пріоритет від унарного)
        if self.leks[self.k][0] == self.power:
            self.GetNextToken()
            exponent = self.factor()
            val = val ** exponent

        return val

    def GetNextToken(self):
        """Перейти до наступної лексеми."""
        if self.k < len(self.leks) - 1:
            self.k += 1
        else:
            raise errorexpr('Несподіваний кінець виразу')


# ==================== ТЕСТОВІ ПРОГРАМИ ====================

# --- Тестовий приклад 1 ---
TEST_PROGRAM_1 = """\
# Тест 1: арифметичні операції, змінні, print
x = 10
y = 3.5
z = x * y - 2 ** 3
print(z)
print(x // y)
print(x % 3)
w = sin(3.14159265358979 / 2)
print(w)
"""

# Очікуваний результат Тесту 1 (стандартний Python):
#   x = 10,  y = 3.5
#   z = 10 * 3.5 - 2**3 = 35.0 - 8 = 27.0
#   print(z)         → 27.0
#   print(x // y)    → 2.0       (10 // 3.5 у Python = 2.0)
#   print(x % 3)     → 1
#   w = sin(π/2) ≈ 1.0
#   print(w)         → ~1.0

# --- Тестовий приклад 2 ---
TEST_PROGRAM_2 = """\
# Тест 2: унарні операції, степені, тригонометрія, складені вирази
a = 5
b = a ** 2
c = -a + b
print(c)
d = cos(0) + sin(0)
print(d)
e = (a + 3) // 2
f = (a + 3) % 2
print(e)
print(f)
result = a ** 3 - 3 * a ** 2 + 3 * a - 1
print(result)
"""

# Очікуваний результат Тесту 2 (стандартний Python):
#   a = 5
#   b = 25
#   c = -5 + 25 = 20
#   print(c)              → 20
#   d = cos(0) + sin(0) = 1.0 + 0.0 = 1.0
#   print(d)              → 1.0
#   e = (5+3) // 2 = 4
#   f = (5+3) % 2 = 0
#   print(e)              → 4
#   print(f)              → 0
#   result = 125 - 75 + 15 - 1 = 64
#   print(result)         → 64


if __name__ == '__main__':
    print('╔══════════════════════════════════════════════════════╗')
    print('║  Лабораторна робота 12 — Частина 3                  ║')
    print('║  Операторне виконання: присвоєння і print()         ║')
    print('╚══════════════════════════════════════════════════════╝')

    # ---- Тест 1 ----
    print('\n' + '═' * 55)
    print('ТЕСТОВА ПРОГРАМА 1')
    print('═' * 55)
    print('Вхідний текст програми:')
    print(TEST_PROGRAM_1)
    print('Результат виконання інтерпретатора:')
    print('─' * 30)
    interp1 = ExtArithexprAssInterpret()
    interp1.run_program(TEST_PROGRAM_1)
    print('─' * 30)
    print('Очікуваний результат (Python):')
    print('  27.0')
    print('  2.0')
    print('  1')
    print('  ~1.0 (sin(π/2))')

    # ---- Тест 2 ----
    print('\n' + '═' * 55)
    print('ТЕСТОВА ПРОГРАМА 2')
    print('═' * 55)
    print('Вхідний текст програми:')
    print(TEST_PROGRAM_2)
    print('Результат виконання інтерпретатора:')
    print('─' * 30)
    interp2 = ExtArithexprAssInterpret()
    interp2.run_program(TEST_PROGRAM_2)
    print('─' * 30)
    print('Очікуваний результат (Python):')
    print('  20')
    print('  1.0')
    print('  4')
    print('  0')
    print('  64')

    # ---- Верифікація через стандартний Python ----
    print('\n' + '═' * 55)
    print('ВЕРИФІКАЦІЯ (стандартний Python)')
    print('═' * 55)
    print('Тест 1 (стандартний Python):')
    x = 10;  y = 3.5
    z = x * y - 2 ** 3
    print(z)
    print(x // y)
    print(x % 3)
    w = math.sin(3.14159265358979 / 2)
    print(w)

    print('\nТест 2 (стандартний Python):')
    a = 5
    b = a ** 2
    c = -a + b
    print(c)
    d = math.cos(0) + math.sin(0)
    print(d)
    e = (a + 3) // 2
    f = (a + 3) % 2
    print(e)
    print(f)
    result = a ** 3 - 3 * a ** 2 + 3 * a - 1
    print(result)

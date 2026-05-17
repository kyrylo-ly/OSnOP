# Лабораторна робота 12 — Частина 2
# Розширений інтерпретатор алгебраїчних формул
# Базується на arithexpr.py з доповненнями згідно п.5-6 завдання

"""
---------- розширене синтаксичне визначення формули ----------
arith_expr ::= term ( ( "+" | "-" ) term ) *
term       ::= factor ( ( "*" | "/" | "//" | "%" ) factor ) *
factor     ::= ["+" | "-"] ( number | "(" arith_expr ")" | function )
               [ "**" factor ]
function   ::= "sin(" arith_expr ")" | "cos(" arith_expr ")"
number     ::= digit+ ["." digit+] [("e"|"E") ["+"| "-"] digit+]
digit      ::= "0" | "1" | ... | "9"
--------------------------------------------------------------
Пріоритети операцій (від найнижчого до найвищого):
  1. + - (бінарні)                   -- arith_expr
  2. * / // % (мультиплікативні)     -- term
  3. + - (унарні) -> via factor()    -- ** вищий за унарний: -2**2 = -(2**2)
  4. ** (степінь, правоасоціативне)  -- factor (рекурсія)
  5. sin(), cos() (функції)          -- factor (атом)
"""

import math


class errorexpr(Exception):
    """Допоміжний клас для збудження винятків при помилках розбору."""
    pass


class ExtArithexprInterpret:
    """Розширений інтерпретатор алгебраїчних формул.

    Підтримує:
      - бінарні операції: + - * / // %
      - степінь: ** (правоасоціативне, вищий пріоритет ніж унарні)
      - математичні функції: sin(), cos()
      - унарні операції: + і - (можна кілька підряд: --5 = 5)
      - числа: цілі та дійсні (45.02, 1.0e-5, 28e4)
      - дужки для групування
    """

    # ---------- коди лексем ----------
    empty        = 0   # '#' -- обмежувач кінця списку лексем
    number       = 1   # числова константа (int або float)
    funcname     = 2   # ім'я функції: sin, cos
    openbracket  = 3   # '('
    closebracket = 4   # ')'
    add          = 5   # '+'
    subtract     = 6   # '-'
    multiply     = 7   # '*'
    divide       = 8   # '/'
    floordiv     = 9   # '//' -- ділення на ціло (п.5.1)
    modulo       = 10  # '%'  -- остача від ділення (п.5.1)
    power        = 11  # '**' -- піднесення до степеня (п.5.2)

    # ---------- повідомлення про помилки ----------
    errscan = 'Помилка сканування формули:\n'
    errcalc = 'Помилка обчислення виразу:\n'

    def __init__(self, text):
        """Конструктор: зберегти текст формули, ініціалізувати стан."""
        self.text = text
        self.leks = []
        self.i = 0
        self.k = 0

    # ==================== ГОЛОВНИЙ МЕТОД ====================

    def calc(self):
        """Виконати повну процедуру обчислення формули.

        Повертає (True, результат) або (False, повідомлення_про_помилку).
        """
        self.delblank()
        print(f'Формула: {self.text}')

        # перший перегляд -- сканування
        if not self.scanner():
            return (False, self.errscan + self.text[:self.i] +
                    "  '" + (self.text[self.i] if self.i < len(self.text) else '?') + "'")

        print(f'Лексеми: {self.leks}')

        # другий перегляд -- розбір і обчислення
        res = None
        try:
            res = self.arithexpr()
        except Exception:
            temp = ''.join(str(m[1]) for m in self.leks[:self.k])
            return (False, self.errcalc + temp + "  '" + str(self.leks[self.k][1]) + "'")

        if self.k < len(self.leks) - 1:
            temp = ''.join(str(m[1]) for m in self.leks[:self.k])
            return (False, self.errcalc + temp + "  '" + str(self.leks[self.k][1]) + "'")

        return (True, res)

    # ==================== ПІДГОТОВКА ТЕКСТУ ====================

    def delblank(self):
        """Видалити всі пропуски з тексту формули."""
        self.text = self.text.replace(' ', '')

    # ==================== СКАНУВАННЯ (перший перегляд) ====================

    def scanner(self):
        """Сканувати формулу і побудувати список лексем.

        В кінці додається обмежувач (empty, '#').
        Повертає True при успіху, False при помилці.
        """
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
                # п.5.1: остача від ділення
                self.leks.append((self.modulo, '%'))
            elif ch == '*':
                if self.i + 1 < len(self.text) and self.text[self.i + 1] == '*':
                    # п.5.2: піднесення до степеня
                    self.leks.append((self.power, '**'))
                    self.i += 1
                else:
                    self.leks.append((self.multiply, '*'))
            elif ch == '/':
                if self.i + 1 < len(self.text) and self.text[self.i + 1] == '/':
                    # п.5.1: ділення на ціло
                    self.leks.append((self.floordiv, '//'))
                    self.i += 1
                else:
                    self.leks.append((self.divide, '/'))
            elif ch.isdigit():
                # п.5.5: число (ціле або дійсне)
                self.onenumber()
                self.i -= 1
            elif ch.isalpha():
                # п.5.3: ім'я функції (sin, cos)
                if not self.scan_funcname():
                    return False
            else:
                return False  # недопустимий символ

            self.i += 1

        self.leks.append((self.empty, '#'))
        return True

    def onenumber(self):
        """Прочитати числову константу і додати до списку лексем.

        Підтримує формати (п.5.5):
          - ціле:              123
          - фіксована крапка:  45.02
          - експоненціальна:   1.0e-5,  28e4,  3E+2
        """
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
        # конвертувати у числове значення
        value = float(num_str) if ('.' in num_str or 'e' in num_str or 'E' in num_str) \
                else int(num_str)
        self.leks.append((self.number, value))

    def scan_funcname(self):
        """Прочитати ім'я функції і додати до списку лексем.

        Підтримувані функції (п.5.3): sin, cos.
        Дужку '(' не поглинаємо -- вона буде прочитана основним циклом.
        Повертає True при успіху, False при невідомій функції.
        """
        name = ''
        while self.i < len(self.text) and self.text[self.i].isalpha():
            name += self.text[self.i]
            self.i += 1
        if name in ('sin', 'cos'):
            self.leks.append((self.funcname, name))
            self.i -= 1  # повернутися на '('
            return True
        else:
            return False  # невідома функція

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
        """term ::= factor ( ( "*" | "/" | "//" | "%" ) factor ) *

        Додано (п.5.1): операції // і %.
        """
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
            else:  # modulo
                if right == 0:
                    raise errorexpr('Остача від ділення на нуль')
                z = z % right
        return z

    def factor(self):
        """factor ::= ["+" | "-"] ( number | "(" arith_expr ")" | function )
                      [ "**" factor ]

        Зміни (п.5.2, п.5.3, п.5.4):
        - п.5.4: унарні + і - реалізовані рекурсивним викликом factor().
          Кілька підряд: --5 = +5, ---5 = -5 тощо.
        - п.5.2: ** має ВИЩИЙ пріоритет ніж унарний знак.
          Механізм: унарний знак застосовується через return -self.factor(),
          де self.factor() рекурсивно обробляє ** перед поверненням.
          Тому: -2**2 => -(factor(2**2)) = -(4) = -4.
        - п.5.3: виклик функцій sin(), cos()
        """
        # п.5.4: унарний + або -
        # Рекурсивний виклик factor() забезпечує правильний пріоритет **
        if self.leks[self.k][0] == self.add:
            self.GetNextToken()
            return +self.factor()
        elif self.leks[self.k][0] == self.subtract:
            self.GetNextToken()
            return -self.factor()

        # розпізнати основну частину (число, дужки або функція)
        if self.leks[self.k][0] == self.number:
            self.GetNextToken()
            val = self.leks[self.k - 1][1]

        elif self.leks[self.k][0] == self.openbracket:
            self.GetNextToken()
            val = self.arithexpr()
            if self.leks[self.k][0] == self.closebracket:
                self.GetNextToken()
            else:
                raise errorexpr("Очікується закриваюча дужка ')'")

        elif self.leks[self.k][0] == self.funcname:
            # п.5.3: funcname '(' arith_expr ')'
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
            raise errorexpr('Очікується число, дужка або функція')

        # п.5.2: піднесення до степеня -- правоасоціативне
        # Застосовується до val (числа/дужки/функції) ДО повернення до унарного знаку
        if self.leks[self.k][0] == self.power:
            self.GetNextToken()
            exponent = self.factor()  # рекурсія для правої асоціативності
            val = val ** exponent

        return val

    def GetNextToken(self):
        """Перейти до наступної лексеми."""
        if self.k < len(self.leks) - 1:
            self.k += 1
        else:
            raise errorexpr('Несподіваний кінець виразу')


# ==================== ТЕСТУВАННЯ ====================

def run_test(description, formula, expected=None):
    """Виконати один тест і показати результат."""
    print(f'\n{"─" * 55}')
    print(f'Тест: {description}')
    res = ExtArithexprInterpret(formula).calc()
    if res[0]:
        status = ''
        if expected is not None:
            try:
                if abs(res[1] - expected) < 1e-9:
                    status = '  OK (збігається з Python)'
                else:
                    status = f'  ПОМИЛКА (очікувалось {expected})'
            except TypeError:
                pass
        print(f'Результат: {res[1]}{status}')
    else:
        print(f'Помилка: {res[1]}')


if __name__ == '__main__':
    print('╔══════════════════════════════════════════════════════╗')
    print('║  Лабораторна робота 12 -- Частина 2                 ║')
    print('║  Розширений інтерпретатор алгебраїчних формул       ║')
    print('╚══════════════════════════════════════════════════════╝')

    # --- базовий тест з умови завдання ---
    print('\n=== Базовий тест з умови ===')
    run_test('49 - 108 / (6 + 11) * (100 - 94)',
             '49 - 108 / (6 + 11) * (100 - 94)',
             49 - 108 / (6 + 11) * (100 - 94))

    # --- п.5.1: // і % ---
    print('\n=== п.5.1: Бінарні операції // і % ===')
    run_test('Ціле ділення: 17 // 5',      '17 // 5',           17 // 5)
    run_test('Остача: 17 % 5',             '17 % 5',            17 % 5)
    run_test('Змішане: 17//5 + 17%5',      '17 // 5 + 17 % 5',  17 // 5 + 17 % 5)
    run_test('Ціле ділення з дужками',     '(10 + 7) // 3',     (10 + 7) // 3)

    # --- п.5.2: ** ---
    print('\n=== п.5.2: Операція ** (піднесення до степеня) ===')
    run_test('2 ** 10',                     '2 ** 10',            2 ** 10)
    run_test('Пріоритет: 2 * 3 ** 2',       '2 * 3 ** 2',        2 * 3 ** 2)
    run_test('Правоасоц.: 2 ** 3 ** 2',     '2 ** 3 ** 2',       2 ** 3 ** 2)
    run_test('Дробовий степінь: 8**(1/3)',   '8 ** (1 / 3)',      8 ** (1/3))

    # --- п.5.3: sin() і cos() ---
    print('\n=== п.5.3: Функції sin() і cos() ===')
    run_test('sin(0)',                      'sin(0)',             math.sin(0))
    run_test('cos(0)',                      'cos(0)',             math.cos(0))
    run_test('sin(pi/2) ~= 1',             'sin(3.14159265/2)',  math.sin(math.pi/2))
    run_test('cos(pi) ~= -1',              'cos(3.14159265)',    math.cos(math.pi))
    run_test('2*sin(1)+cos(0)',             '2*sin(1)+cos(0)',    2*math.sin(1)+math.cos(0))

    # --- п.5.4: унарні ---
    print('\n=== п.5.4: Унарні операції + і - ===')
    run_test('Унарний мінус: -2 + -6',     '-2 + -6',           -2 + -6)
    run_test('Унарний плюс: 4 * +8',       '4 * +8',             4 * +8)
    run_test('Подвійний унарний: --5',      '--5',                5)
    run_test('Потрійний унарний: ---5',     '---5',               -5)
    run_test('-2**2 = -(2**2) = -4',        '-2 ** 2',           -(2 ** 2))
    run_test('Унарний перед дужками',       '-(10 - 3)',          -(10 - 3))
    run_test('Унарний перед функцією',      '-sin(0)',            -math.sin(0))

    # --- п.5.5: дійсні числа ---
    print('\n=== п.5.5: Дійсні числа ===')
    run_test('Фіксована крапка: 45.02+0.98', '45.02 + 0.98',    45.02 + 0.98)
    run_test('Експон.: 1.0e-5 * 100000',     '1.0e-5 * 100000', 1.0e-5 * 100000)
    run_test('Скорочена: 28e4 / 2',          '28e4 / 2',         28e4 / 2)
    run_test("2.5E-2 + 0.1",                 '2.5E-2 + 0.1',     2.5e-2 + 0.1)

    # --- комплексні вирази ---
    print('\n=== Комплексні вирази ===')
    run_test('sin(2)**2 + cos(2)**2 ~= 1',
             'sin(2) ** 2 + cos(2) ** 2',
             math.sin(2)**2 + math.cos(2)**2)
    run_test('-(3**2) + 17//5 - 4%3',
             '-3 ** 2 + 17 // 5 - 4 % 3',
             -(3 ** 2) + 17 // 5 - 4 % 3)

    # --- помилки ---
    print('\n=== Тести помилок ===')
    run_test('Ділення на нуль',             '5 / 0')
    run_test('Ціле ділення на нуль',        '5 // 0')
    run_test('Синтаксична помилка',         '2 + * 3')
    run_test('Невідома функція',            'log(10)')
    run_test('Незакрита дужка',             '(2 + 3')

    print(f'\n{"=" * 55}')
    print('Тестування завершено.')

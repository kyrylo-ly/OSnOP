# Лабораторна робота 11 — інтерпретатор формул без рангів операцій
# Розширений інтерпретатор на основі базового simple.py
# Автор: Кирило Литвішко, ПМІ-43

import math

# ---------- синтаксичне визначення формули (розширене) ----------
"""
arith_expr    ::= [ base_prefix ]  number  unary_ops  ( operator  number  unary_ops ) *
base_prefix   ::= "0b" | "0x"
number        ::= [ num_prefix ]  digit  digit *
num_prefix    ::= "0b" | "0x"
digit         ::= dec_digit | bin_digit | hex_digit   (залежно від контексту)
dec_digit     ::= "0" | "1" | ... | "9"
bin_digit     ::= "0" | "1"
hex_digit     ::= "0" | ... | "9" | "a" | ... | "f" | "A" | ... | "F"
operator      ::= "+" | "-" | "*" | "/" | "%" | "^" | "&" | "|"
unary_ops     ::= ( unary_op ) *
unary_op      ::= "sqrt" | "sin" | "abs"
"""

# --- п.3: розширений набір бінарних операцій ---
# +  додавання
# -  віднімання
# *  множення
# /  ділення
# %  остача від ділення (mod)
# ^  піднесення до степеня (pow)
# &  менше з двох (min)
# |  більше з двох (max)

BINARY_OPS = ['+', '-', '*', '/', '%', '^', '&', '|']

# --- п.4: унарні постфіксні операції ---
# sqrt  квадратний корінь
# sin   синус (аргумент у радіанах)
# abs   модуль числа

UNARY_OPS = ['sqrt', 'sin', 'abs']


class SimpleInterpret:
    """Інтерпретатор формул без рангів операцій.

    Підтримує:
      - 8 бінарних операцій: + - * / % ^ & |
      - 3 унарні постфіксні операції: sqrt, sin, abs
      - системи числення: двійкова (0b), шістнадцяткова (0x), десяткова
      - контроль помилок запису формули
    """

    def __init__(self, text):  # конструктор
        self.original = text       # оригінальний текст (для повідомлень)
        self.text = text           # робоча копія тексту формули
        self.leks = []             # список лексем
        self.i = 0                 # поточна позиція сканування
        # --- п.5: система числення ---
        self.global_base = 10      # глобальна система числення (10 за замовчуванням)
        self.error_msg = ""        # повідомлення про помилку

    # ==================== ОСНОВНИЙ МЕТОД ====================

    def calc(self):
        """Виконати повну процедуру обчислення.

        Повертає кортеж (success: bool, result_or_error).
        """
        self.delblank()  # викреслити пропуски (збережемо пропуски навколо слів-операцій)

        # --- п.6: перевірка порожньої формули ---
        if len(self.text) == 0:
            return (False, "Помилка: формула порожня")

        # --- п.5: визначити глобальну систему числення ---
        self._detect_global_base()

        # перший перегляд — сканування формули
        if not self.scanner():
            return (False, self.error_msg)

        # --- п.6: додатковий структурний контроль після сканування ---
        err = self._validate_structure()
        if err:
            return (False, err)

        # другий перегляд — обчислення формули
        result = self._evaluate()
        if isinstance(result, str):  # повідомлення про помилку
            return (False, result)

        # --- п.5: форматування результату відповідно до системи числення ---
        formatted = self._format_result(result)
        return (True, formatted)

    # ==================== ПІДГОТОВКА ТЕКСТУ ====================

    def delblank(self):
        """Викреслити незначущі пропуски, зберігаючи один пропуск між словами.

        Потрібно для розпізнавання текстових унарних операцій (sqrt, sin, abs).
        """
        # замінити множинні пропуски на один
        while '  ' in self.text:
            self.text = self.text.replace('  ', ' ')
        self.text = self.text.strip()

    # --- п.5: визначення глобальної системи числення ---
    def _detect_global_base(self):
        """Визначити глобальну систему числення за префіксом формули.

        Префікси: '0b' — двійкова, '0x' — шістнадцяткова.
        Якщо формула починається з '0b ' або '0x ' (з пропуском),
        це глобальний префікс для всієї формули.
        """
        if self.text.startswith('0b ') or self.text == '0b':
            self.global_base = 2
            self.text = self.text[3:] if len(self.text) > 2 else ''
        elif self.text.startswith('0x ') or self.text == '0x':
            self.global_base = 16
            self.text = self.text[3:] if len(self.text) > 2 else ''

    # ==================== СКАНУВАННЯ (перший перегляд) ====================

    def scanner(self):
        """Сканувати формулу і поділити на лексеми.

        Повертає True якщо сканування успішне, None інакше.
        """
        # --- п.6: формула порожня після видалення префіксу ---
        if len(self.text) == 0:
            self.error_msg = "Помилка: формула порожня (лише префікс системи числення)"
            return None

        # --- п.6: формула починається з оператора ---
        if self.text[0] in BINARY_OPS:
            self.error_msg = (
                f"Помилка: формула не може починатись з оператора "
                f"'{self.text[0]}'"
            )
            return None

        # читати перше число
        n = self.onenumber()
        if n is not None:
            self.leks.append(n)  # правило formula ::= number
        else:
            return None  # помилка в найпершому числі

        # --- п.4: унарні операції після першого числа ---
        self._scan_unary_ops()

        while self.i < len(self.text):
            # пропустити пропуски
            self._skip_spaces()
            if self.i >= len(self.text):
                break

            # --- п.6: два числа підряд без оператора ---
            if self._is_digit_char(self.text[self.i]) or self._is_num_prefix():
                self.error_msg = (
                    "Помилка: очікувався оператор після числа, "
                    f"але знайдено '{self.text[self.i]}' на позиції {self.i + 1}"
                )
                return None

            # читати знак операції
            sign = self.onesign()
            if sign is not None:
                self.leks.append(sign)
            else:
                return None  # помилка знаку операції

            self._skip_spaces()

            # --- п.6: два оператори підряд ---
            if self.i < len(self.text) and self.text[self.i] in BINARY_OPS:
                self.error_msg = (
                    f"Помилка: два оператори підряд "
                    f"'{sign}{self.text[self.i]}' на позиції {self.i}"
                )
                return None

            # --- п.6: формула закінчується оператором ---
            if self.i >= len(self.text):
                self.error_msg = (
                    f"Помилка: формула не може закінчуватись оператором '{sign}'"
                )
                return None

            # наступна позиція — число
            n = self.onenumber()
            if n is not None:
                self.leks.append(n)
            else:
                return None  # помилка в числі

            # --- п.4: унарні операції після числа ---
            self._scan_unary_ops()

        return "OK"  # всі лексеми правильні

    def onenumber(self):
        """Читати літери числа.

        Підтримує числа з індивідуальним префіксом системи числення (0b, 0x).
        Повертає кортеж (string_value, base) або None при помилці.
        """
        self._skip_spaces()
        if self.i >= len(self.text):
            self.error_msg = "Помилка: очікувалось число, але формула закінчилась"
            return None

        num = ""
        base = self.global_base  # за замовчуванням — глобальна система

        # --- п.5: перевірити індивідуальний префікс числа ---
        if self._is_num_prefix():
            prefix = self.text[self.i:self.i + 2]
            if prefix == '0b':
                base = 2
            elif prefix == '0x':
                base = 16
            self.i += 2  # пропустити префікс

        # читати цифри відповідно до системи числення
        while self.i < len(self.text) and self._is_valid_digit(self.text[self.i], base):
            num += self.text[self.i]
            self.i += 1

        if len(num) > 0:
            # --- п.6: перевірка, чи наступний символ не є невідомою цифрою ---
            if self.i < len(self.text) and self.text[self.i].isalnum() \
               and self.text[self.i] not in BINARY_OPS \
               and not self._starts_unary():
                bad_char = self.text[self.i]
                if base == 2:
                    self.error_msg = (
                        f"Помилка: цифра '{bad_char}' недопустима "
                        f"у двійковій системі на позиції {self.i + 1}"
                    )
                elif base == 10:
                    self.error_msg = (
                        f"Помилка: невідомий символ '{bad_char}' "
                        f"на позиції {self.i + 1}"
                    )
                else:
                    self.error_msg = (
                        f"Помилка: невідомий символ '{bad_char}' "
                        f"на позиції {self.i + 1}"
                    )
                return None
            return (num, base)
        else:
            # --- п.6: невідомий символ замість числа ---
            if self.i < len(self.text):
                self.error_msg = (
                    f"Помилка: невідомий символ '{self.text[self.i]}' "
                    f"на позиції {self.i + 1}"
                )
            else:
                self.error_msg = "Помилка: очікувалось число"
            return None

    # --- п.3: розширений набір операцій ---
    def onesign(self):
        """Читати знак бінарної операції.

        Підтримує: + - * / % ^ & |
        """
        self._skip_spaces()
        if self.i < len(self.text) and self.text[self.i] in BINARY_OPS:
            self.i += 1
            return self.text[self.i - 1]
        else:
            if self.i < len(self.text):
                self.error_msg = (
                    f"Помилка: невідомий оператор '{self.text[self.i]}' "
                    f"на позиції {self.i + 1}"
                )
            else:
                self.error_msg = "Помилка: очікувався оператор"
            return None

    # --- п.4: сканування унарних операцій ---
    def _scan_unary_ops(self):
        """Сканувати послідовність унарних операцій після числа."""
        while True:
            self._skip_spaces()
            found = False
            for op in UNARY_OPS:
                if self.text[self.i:self.i + len(op)] == op:
                    # перевірити, що після слова немає літери (щоб 'sinus' не зчитувалось як 'sin')
                    end_pos = self.i + len(op)
                    if end_pos < len(self.text) and self.text[end_pos].isalpha():
                        continue
                    self.leks.append(op)
                    self.i += len(op)
                    found = True
                    break
            if not found:
                break

    # ==================== ДОПОМІЖНІ МЕТОДИ СКАНУВАННЯ ====================

    def _skip_spaces(self):
        """Пропустити пропуски."""
        while self.i < len(self.text) and self.text[self.i] == ' ':
            self.i += 1

    def _is_digit_char(self, ch):
        """Перевірити, чи символ є цифрою поточної системи числення."""
        return self._is_valid_digit(ch, self.global_base)

    def _is_valid_digit(self, ch, base):
        """Перевірити, чи символ є допустимою цифрою для системи числення."""
        if base == 2:
            return ch in '01'
        elif base == 16:
            return ch in '0123456789abcdefABCDEF'
        else:  # base == 10
            return ch.isdigit()

    def _is_num_prefix(self):
        """Перевірити, чи на поточній позиції є префікс системи числення (0b або 0x)."""
        if self.i + 1 < len(self.text):
            pair = self.text[self.i:self.i + 2]
            return pair in ('0b', '0x')
        return False

    def _starts_unary(self):
        """Перевірити, чи на поточній позиції починається унарна операція."""
        for op in UNARY_OPS:
            if self.text[self.i:self.i + len(op)] == op:
                end_pos = self.i + len(op)
                if end_pos >= len(self.text) or not self.text[end_pos].isalpha():
                    return True
        return False

    # ==================== ВАЛІДАЦІЯ СТРУКТУРИ (п.6) ====================

    def _validate_structure(self):
        """Перевірити структурну коректність списку лексем після сканування.

        Повертає повідомлення про помилку або None якщо все коректно.
        """
        if len(self.leks) == 0:
            return "Помилка: формула порожня"

        # перша лексема має бути числом (кортеж)
        if not isinstance(self.leks[0], tuple):
            return f"Помилка: формула має починатись з числа, а не '{self.leks[0]}'"

        return None

    # ==================== ОБЧИСЛЕННЯ (другий перегляд) ====================

    def _evaluate(self):
        """Обчислити формулу за списком лексем.

        Повертає числовий результат або рядок з повідомленням про помилку.
        """
        # додати на початок списку знак "+"
        self.leks.insert(0, '+')

        k = 0
        res = 0

        while k < len(self.leks):
            lex = self.leks[k]

            # --- п.4: перевірити, чи це унарна операція ---
            if isinstance(lex, str) and lex in UNARY_OPS:
                result = self._apply_unary(lex, res)
                if isinstance(result, str):  # помилка
                    return result
                res = result
                k += 1
                continue

            # бінарна операція: пара [знак, операнд]
            oper = self.leks[k]
            k += 1
            num_tuple = self.leks[k]
            k += 1

            # --- п.5: конвертація числа з відповідної системи числення ---
            n = int(num_tuple[0], num_tuple[1])

            # --- п.3: виконання бінарної операції ---
            result = self._apply_binary(oper, res, n)
            if isinstance(result, str):  # помилка
                return result
            res = result

        return res

    # --- п.3: виконання бінарної операції ---
    def _apply_binary(self, oper, left, right):
        """Виконати бінарну операцію.

        Повертає результат або рядок з повідомленням про помилку.
        """
        if oper == '+':
            return left + right
        elif oper == '-':
            return left - right
        elif oper == '*':
            return left * right
        elif oper == '/':
            # --- п.6: ділення на нуль ---
            if right == 0:
                return "Помилка: ділення на нуль"
            return left / right
        elif oper == '%':
            # --- п.6: остача від ділення на нуль ---
            if right == 0:
                return "Помилка: ділення на нуль при операції '%'"
            return left % right
        elif oper == '^':
            return left ** right
        elif oper == '&':
            return min(left, right)
        elif oper == '|':
            return max(left, right)
        else:
            return f"Помилка: невідома операція '{oper}'"

    # --- п.4: виконання унарної операції ---
    def _apply_unary(self, op, value):
        """Виконати унарну операцію над значенням.

        Повертає результат або рядок з повідомленням про помилку.
        """
        if op == 'sqrt':
            # --- п.6: квадратний корінь від від'ємного числа ---
            if value < 0:
                return (
                    f"Помилка: квадратний корінь від від'ємного числа ({value})"
                )
            return math.sqrt(value)
        elif op == 'sin':
            return math.sin(value)
        elif op == 'abs':
            return abs(value)
        else:
            return f"Помилка: невідома унарна операція '{op}'"

    # ==================== ФОРМАТУВАННЯ РЕЗУЛЬТАТУ (п.5) ====================

    def _format_result(self, result):
        """Форматувати результат відповідно до системи числення.

        Якщо глобальна система — десяткова, показати лише десятковий результат.
        Якщо двійкова або шістнадцяткова — показати у відповідній системі
        і додатково в десятковій.
        Якщо використовувались різні системи — показати в десятковій,
        двійковій і шістнадцятковій.
        """
        # визначити, чи були числа з різними системами числення
        bases_used = set()
        for lex in self.leks:
            if isinstance(lex, tuple):
                bases_used.add(lex[1])

        # якщо результат — ціле число, форматувати у різних системах
        is_int = isinstance(result, (int,)) or (isinstance(result, float) and result == int(result))

        if is_int:
            int_result = int(result)
            if self.global_base == 2:
                return f"{bin(int_result)} (десяткове: {int_result})"
            elif self.global_base == 16:
                return f"{hex(int_result)} (десяткове: {int_result})"
            elif len(bases_used) > 1:
                # різні системи — показати у всіх
                return (
                    f"{int_result}"
                    f" (двійкове: {bin(int_result)},"
                    f" шістнадцяткове: {hex(int_result)})"
                )
            else:
                return str(int_result)
        else:
            # дійсне число — показати лише десятковий запис
            if self.global_base == 2 or self.global_base == 16:
                return f"{result} (дійсне число, лише десятковий запис)"
            return str(round(result, 6))


# ==================== ІНТЕРАКТИВНЕ МЕНЮ ТЕСТУВАННЯ ====================

def run_test(description, formula):
    """Виконати один тест і показати результат."""
    print(f"\n  Формула: {formula}")
    print(f"  Опис:    {description}")
    res = SimpleInterpret(formula).calc()
    if res[0]:
        print(f"  Результат: {res[1]}")
    else:
        print(f"  {res[1]}")
    print()


def demo_tests():
    """Демонстрація всіх тестових прикладів."""

    print("=" * 60)
    print("  ТЕСТУВАННЯ ІНТЕРПРЕТАТОРА ФОРМУЛ")
    print("=" * 60)

    # --- п.3: бінарні операції ---
    print("\n--- п.3: Бінарні операції ---")
    run_test("Базовий тест (+ - * /)", "65 + 122 - 99 / 6 - 12 * 2 + 1")
    run_test("Остача від ділення (%)", "10 % 3")
    run_test("Піднесення до степеня (^)", "2 ^ 10")
    run_test("Менше з двох (&)", "5 & 3")
    run_test("Більше з двох (|)", "5 | 3")
    run_test("Змішані операції зліва направо", "10 + 5 % 3 ^ 2")
    run_test("Степінь та остача", "3 ^ 3 % 5")

    # --- п.4: унарні операції ---
    print("\n--- п.4: Унарні операції (постфіксні) ---")
    run_test("Квадратний корінь", "25 + 52 sqrt")
    run_test("Модуль числа", "0 - 5 abs")
    run_test("Синус", "3 sin")
    run_test("Кілька унарних: sqrt і sin", "25 + 52 sqrt - 120 sin * 2")
    run_test("Два унарних підряд", "100 sqrt sqrt")
    run_test("abs після від'ємного результату", "3 - 10 abs")

    # --- п.5.1: єдина система числення ---
    print("\n--- п.5.1: Єдина система числення ---")
    run_test("Двійкова формула", "0b 1010 + 110")
    run_test("Двійкове множення", "0b 1010 * 10")
    run_test("Шістнадцяткова формула", "0x FF + A0")
    run_test("Шістнадцяткове віднімання", "0x FF - 1B")

    # --- п.5.2: різні системи в одній формулі ---
    print("\n--- п.5.2: Різні системи числення в одній формулі ---")
    run_test("Двійкове + шістнадцяткове + десяткове", "0b1010 + 0xFF - 100")
    run_test("Змішана формула", "0xA + 0b1100 * 2")

    # --- п.6: помилки ---
    print("\n--- п.6: Контроль помилок ---")
    run_test("Порожня формула", "")
    run_test("Невідомий символ", "65 + A * 4")
    run_test("Два оператори підряд", "5 + * 3")
    run_test("Починається з оператора", "+ 5 - 3")
    run_test("Закінчується оператором", "5 + 3 -")
    run_test("Ділення на нуль", "10 / 0")
    run_test("Остача від ділення на нуль", "10 % 0")
    run_test("Корінь від від'ємного числа", "0 - 4 sqrt")
    run_test("Неправильна цифра для двійкової системи", "0b 125")
    run_test("Два числа підряд без оператора", "5 3 + 2")


if __name__ == "__main__":
    print("\n╔══════════════════════════════════════════════════╗")
    print("║  Інтерпретатор формул без рангів операцій       ║")
    print("║  Лабораторна робота №11                         ║")
    print("╚══════════════════════════════════════════════════╝\n")
    print("Оберіть режим:")
    print("  1 — Демонстрація тестів (всі приклади)")
    print("  2 — Ввести власну формулу")
    print("  3 — Вийти")
    print()

    while True:
        choice = input("Ваш вибір (1/2/3): ").strip()
        if choice == '1':
            demo_tests()
        elif choice == '2':
            print("\nДоступні операції:")
            print("  Бінарні: + - * / % ^ & |")
            print("  Унарні (постфіксні): sqrt sin abs")
            print("  Системи числення: 0b (двійкова), 0x (шістнадцяткова)")
            print("  Приклад: 25 + 52 sqrt - 120 sin * 2")
            print("  Приклад: 0b 1010 + 110")
            print("  Приклад: 0xFF + 0b1010 - 100")
            print()
            formula = input("  Введіть формулу: ")
            res = SimpleInterpret(formula).calc()
            if res[0]:
                print(f"  Результат: {res[1]}")
            else:
                print(f"  {res[1]}")
            print()
        elif choice == '3':
            print("До побачення!")
            break
        else:
            print("Невідомий вибір. Спробуйте ще раз.\n")

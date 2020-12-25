from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QTimer
from itertools import product
from threading import Thread
from timeit import timeit
import sqlite3
import random
import copy
import sys
import os
import datetime

hardcore = [[8, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 3, 6, 0, 0, 0, 0, 0],
            [0, 7, 0, 0, 9, 0, 2, 0, 0],
            [0, 5, 0, 0, 0, 7, 0, 0, 0],
            [0, 0, 0, 0, 4, 5, 7, 0, 0],
            [0, 0, 0, 1, 0, 0, 0, 3, 0],
            [0, 0, 1, 0, 0, 0, 0, 6, 8],
            [0, 0, 8, 5, 0, 0, 0, 1, 0],
            [0, 9, 0, 0, 0, 0, 4, 0, 0]]

PROGRAM_SECOND = 1000

EMPTY = 0
IN_GAME = 1
GAME_SOLVED = 2

LEVELS = {
    'EASY': (30, 35),
    'STANDARD': (25, 30),
    'HARD': (20, 25),
    'HARDCORE': (10, 20)
}

DB_NAME = 'sudoku.db'


def solve_sudoku(size, grid):
    """Интерпретация алгоритма X для решения судоку"""
    grid = copy.deepcopy(grid)
    rows_count, colums_count = size
    cells_count = rows_count * colums_count
    x_set = ([("rc", rc) for rc in product(range(cells_count), range(cells_count))] +
             [("rn", rn) for rn in product(range(cells_count), range(1, cells_count + 1))] +
             [("cn", cn) for cn in product(range(cells_count), range(1, cells_count + 1))] +
             [("bn", bn) for bn in product(range(cells_count), range(1, cells_count + 1))])
    y_set = dict()
    for r, c, n in product(range(cells_count), range(cells_count), range(1, cells_count + 1)):
        b = (r // rows_count) * rows_count + (c // colums_count)
        y_set[(r, c, n)] = [
            ("rc", (r, c)),
            ("rn", (r, n)),
            ("cn", (c, n)),
            ("bn", (b, n))]

    x_set, y_set = exact_cover(x_set, y_set)
    for i, row in enumerate(grid):
        for j, n in enumerate(row):
            if n:
                select(x_set, y_set, (i, j, n))

    count = 0
    for solution in solve(x_set, y_set, []):
        if not solution:
            return False
        for (row, col, number) in solution:
            grid[row][col] = number
        count += 1
        if count > 2:
            return False
        yield grid


def exact_cover(x_set, y_set):
    x_set = {j: set() for j in x_set}
    for i, row in y_set.items():
        for j in row:
            x_set[j].add(i)
    return x_set, y_set


def solve(x_set, y_set, solution):
    if not x_set:
        yield list(solution)
    else:
        c = min(x_set, key=lambda c: len(x_set[c]))
        for r in list(x_set[c]):
            solution.append(r)
            cols = select(x_set, y_set, r)
            count = 0
            for s in solve(x_set, y_set, solution):
                count += 1
                if count > 2:
                    yield False
                yield s
            deselect(x_set, y_set, r, cols)
            solution.pop()


def select(x_set, y_set, r):
    cols = []
    for j in y_set[r]:
        for i in x_set[j]:
            for k in y_set[i]:
                if k != j:
                    x_set[k].remove(i)
        cols.append(x_set.pop(j))
    return cols


def deselect(x_set, y_set, r, cols):
    for j in reversed(y_set[r]):
        x_set[j] = cols.pop()
        for i in x_set[j]:
            for k in y_set[i]:
                if k != j:
                    x_set[k].add(i)


class MyDataBaseCursor:
    def __init__(self, db_path: str):
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()

    def insert_sudoku_into_db(self, sudoku) -> None:
        problem_matrix = self._matrix_to_str(sudoku.get_problem_matrix())
        solved_matrix = self._matrix_to_str(sudoku.get_solved_matrix())
        sudoku_level = sudoku.get_difficult_level_name()
        timestamp = sudoku.get_timestamp()
        size = sudoku.get_size()

        data = {'problem_matrix': problem_matrix,
                'solved_matrix': solved_matrix,
                'sudoku_level': sudoku_level,
                'timestamp': timestamp,
                'size': size}

        self.cursor.execute(f"""INSERT INTO matrixes({', '.join([str(key) for key in data.keys()])})
         VALUES ({', '.join([str(data[key]) for key in data.keys()])}""")

    def get_sudoku_from_db(self, **kwargs):
        # TODO
        pass

    def _matrix_to_str(self, matrix: list) -> str:
        return str(matrix)

    def _str_to_matrix(self, s: str) -> list:
        return [row.strip()[1:-1].split(', ') for row in s.strip()[1:-1].split(', ')]


class Sudoku:
    """Класс матрицы для судоку"""

    def __init__(self, size=3, level=None, timestamp=None,
                 solved_sudoku=None, problem_sudoku=None):
        """Параметр size задает размер квадратов, на которые разбивается матрица,
        то есть конечная матрица будет иметь размер size ** 2 на size ** 2"""
        self.size = size
        self.solved_sudoku = solved_sudoku
        self.problem_sudoku = problem_sudoku
        self.timestamp = timestamp
        self.difficult_level_name = level
        self.constant = True if self.solved_sudoku else False

    def initialize_matrix(self):
        self.solved_sudoku = []
        self.problem_sudoku = []

    def generate_initial_district(self, shift):
        """Генерирует и возвращает начальный район из self.size квадратных блоков со сдвигом shift"""
        initial_row = [i + 1 for i in range(self.size ** 2)]
        district = [initial_row[i * self.size + shift:] +
                    initial_row[:i * self.size + shift] for i in range(self.size)]
        return district

    def generate_initial_matrix(self):
        """Генерирует заполненную матрицу судоку"""
        self.initialize_matrix()
        for i in range(self.size):
            self.solved_sudoku += self.generate_initial_district(i)

    def transpose_matrix(self):
        """Транспонирует матрицу"""

        self.solved_sudoku = list(map(list, zip(*copy.deepcopy(self.solved_sudoku))))

    def change_rows(self):
        """Обменивает две случайные строки внутри одного района"""
        start = random.choice(range(self.size))
        variants = list(range(start * self.size, start * self.size + self.size))
        random.shuffle(variants)
        first = variants.pop()
        second = variants.pop()
        self.solved_sudoku[first], self.solved_sudoku[second] = self.solved_sudoku[second], \
                                                                self.solved_sudoku[first]

    def change_cols(self):
        """Обменивает два случайных столбца внутри одного района"""
        self.transpose_matrix()
        self.change_rows()
        self.transpose_matrix()

    def change_row_districts(self):
        """Обменивает два случайных горизонтальных района"""
        variants = list(range(self.size))
        first = random.choice(variants)
        variants.remove(first)
        second = random.choice(variants)

        for i in range(self.size):
            self.solved_sudoku[first * self.size + i], \
            self.solved_sudoku[second * self.size + i] = self.solved_sudoku[
                                                             second * self.size + i], \
                                                         self.solved_sudoku[first * self.size + i]

    def change_col_districts(self):
        """Обменивает два случайных вертикальных района"""
        self.transpose_matrix()
        self.change_row_districts()
        self.transpose_matrix()

    def random_mix_matrix(self, k=10):
        """Совершает k случайных действий над матрицей,
         не приводящих к недопустимым позициям"""
        mix_functions = [self.transpose_matrix,
                         self.change_rows,
                         self.change_cols,
                         self.change_row_districts,
                         self.change_col_districts]

        for _ in range(k):
            mix_function = random.choice(mix_functions)
            mix_function()

    def _show_matrix_as_sudoku(self, showed_matrix):
        """Выводит матрицу в консоль в виде судоку"""
        showed_matrix = copy.deepcopy(showed_matrix)
        number_of_symbols = len(str(self.size ** 2))
        for i, row in enumerate(showed_matrix):
            for j, element in enumerate(row):
                cell_value = str(element) if element else ''
                cell_value = cell_value.rjust(number_of_symbols, ' ')
                print(' ' + cell_value + ' ', end='')
            print()
        print()

    def show_solved_matrix(self, as_matrix=False):
        """Выводит решенную матрицу в консоль"""
        if as_matrix:
            for row in self.solved_sudoku:
                print(row)
        else:
            self._show_matrix_as_sudoku(self.solved_sudoku)

    def show_problem_matrix(self, as_matrix=False):
        """Выводит нерешенную матрицу в консоль"""
        if as_matrix:
            for row in self.solved_sudoku:
                print(row)
        else:
            self._show_matrix_as_sudoku(self.problem_sudoku)

    def set_sudoku_size(self, size):
        """Устанавливает новый размер судоку матрицы,
         генерирует новую матрицу"""
        self.size = size

    def generate_sudoku(self, difficult_level_name):
        """Генерирует и возвращает судоку определенного уровня сложности difficult,
        представленным в виде кортежа наименьшего и наибольшего возможного
        количества оставшихся на поле клеток"""
        if not self.constant:
            self.difficult_level_name = difficult_level_name

            self.initialize_matrix()
            self.generate_initial_matrix()
            self.random_mix_matrix()

            problem_sudoku = self.get_solved_matrix()

            cells = self.size ** 4

            difficult_max, difficult_min = LEVELS[difficult_level_name]
            difficult_max = cells - difficult_max

            variants = [(row, col, problem_sudoku[row][col]) for row in range(self.size ** 2)
                        for col in range(self.size ** 2)]
            random.shuffle(variants)

            history = []

            maximum_difficult = 0
            maximum_sudoku = None

            attempts = 0
            max_attempts_count = 1000

            current_difficult = 0
            while current_difficult < difficult_max:
                row, col, value = variants.pop()
                problem_sudoku[row][col] = 0
                solutions = 0
                for _ in solve_sudoku((self.size, self.size), problem_sudoku):
                    solutions += 1
                if solutions == 1:
                    current_difficult += 1
                    if current_difficult > maximum_difficult:
                        maximum_difficult = current_difficult
                        # TODO
                        # print('NEW MAXIMUM DIFFICULT', maximum_difficult)
                        maximum_sudoku = copy.deepcopy(problem_sudoku)
                    if variants:
                        history.append(((row, col, value), copy.deepcopy(problem_sudoku),
                                        copy.deepcopy(variants), current_difficult))
                else:
                    problem_sudoku[row][col] = value

                if not variants:
                    deleted, problem_sudoku, variants, current_difficult = history.pop()
                    row, col, value = deleted
                    problem_sudoku[row][col] = value

                attempts += 1
                if attempts > max_attempts_count:
                    problem_sudoku = copy.deepcopy(maximum_sudoku)
                    current_difficult = maximum_difficult
                    break

            print('Max Target:', difficult_max, 'Max Founded:', maximum_difficult,
                  'Current:', current_difficult, 'Attempt', attempts)

            self.problem_sudoku = problem_sudoku
            self.timestamp = datetime.datetime.timestamp(datetime.datetime.now())
        else:
            problem_sudoku = copy.deepcopy(self.problem_sudoku)

        return problem_sudoku

    def get_solved_matrix(self):
        """Возвращает копию текущей заполненной матрицы"""
        return copy.deepcopy(self.solved_sudoku)

    def get_problem_matrix(self):
        """Возвращает копию текущей незаполненной матрицы"""
        return copy.deepcopy(self.problem_sudoku)

    def get_timestamp(self):
        return self.timestamp

    def get_difficult_level_name(self):
        return self.difficult_level_name

    def get_size(self):
        """Возвращает размер самого маленького квадрата судоку"""
        return self.size


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(501, 509)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 501, 21))
        self.menubar.setObjectName("menubar")
        self.menu = QtWidgets.QMenu(self.menubar)
        self.menu.setObjectName("menu")
        self.menu_2 = QtWidgets.QMenu(self.menu)
        self.menu_2.setObjectName("menu_2")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setAcceptDrops(False)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.action = QtWidgets.QAction(MainWindow)
        self.action.setObjectName("action")
        self.action_2 = QtWidgets.QAction(MainWindow)
        self.action_2.setObjectName("action_2")
        self.action_5 = QtWidgets.QAction(MainWindow)
        self.action_5.setObjectName("action_5")
        self.action_7 = QtWidgets.QAction(MainWindow)
        self.action_7.setObjectName("action_7")
        self.action_8 = QtWidgets.QAction(MainWindow)
        self.action_8.setObjectName("action_8")
        self.action_9 = QtWidgets.QAction(MainWindow)
        self.action_9.setObjectName("action_9")
        self.action_10 = QtWidgets.QAction(MainWindow)
        self.action_10.setObjectName("action_10")
        self.action_11 = QtWidgets.QAction(MainWindow)
        self.action_11.setObjectName("action_10")
        self.menu_2.addAction(self.action_7)
        self.menu_2.addAction(self.action_8)
        self.menu_2.addAction(self.action_9)
        self.menu_2.addAction(self.action_10)
        self.menu.addAction(self.menu_2.menuAction())
        self.menu.addSeparator()
        self.menu.addAction(self.action_5)
        self.menu.addAction(self.action_2)
        self.menu.addSeparator()
        self.menu.addAction(self.action_11)
        self.menu.addSeparator()
        self.menu.addAction(self.action)
        self.menubar.addAction(self.menu.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Судоку"))
        self.menu.setTitle(_translate("MainWindow", "Файл"))
        self.menu_2.setTitle(_translate("MainWindow", "Новая игра"))
        self.action.setText(_translate("MainWindow", "Выход"))
        self.action_2.setText(_translate("MainWindow", "Таблица рекордов"))
        self.action_5.setText(_translate("MainWindow", "Сохранить"))
        self.action_7.setText(_translate("MainWindow", "Легко 👶"))
        self.action_8.setText(_translate("MainWindow", "Средне 👦"))
        self.action_9.setText(_translate("MainWindow", "Сложно 🤓"))
        self.action_10.setText(_translate("MainWindow", "Адски сложно 🎓"))
        self.action_11.setText(_translate("MainWindow", "Спрятать таймер"))


class MainWindow(Ui_MainWindow, QMainWindow):
    def __init__(self, sudoku_size=3):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.sudoku_size = sudoku_size
        self.sudoku = Sudoku(self.sudoku_size)
        self.game_state = EMPTY

        self.action_11.triggered.connect(self.show_hide_timer)

        self.database_cursor = None
        self.connect_db()

        self.timer = QTimer(self)
        self.timer.start(PROGRAM_SECOND)
        self.timer.timeout.connect(self.showtime)
        self.game_seconds = 0
        self.is_show_timer = True
        self.showtime()

        for i in range(7, 11):
            getattr(self, 'action_%d' % i).triggered.connect(self.new_game_btn_clicked)

        self.main_layout = QtWidgets.QGridLayout(self.centralwidget)
        self.main_layout.setHorizontalSpacing(3)
        self.main_layout.setVerticalSpacing(3)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                           QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)

        for i in range(self.sudoku_size):
            for j in range(self.sudoku_size):
                name = 'layout%i%d' % (i, j)
                setattr(self, name, QtWidgets.QGridLayout())
                getattr(self, name).setHorizontalSpacing(1)
                getattr(self, name).setVerticalSpacing(1)
                self.main_layout.addLayout(getattr(self, name), i, j)

        for i in range(self.sudoku_size ** 2):
            for j in range(self.sudoku_size ** 2):
                name = f'layout{i // self.sudoku_size}{j // self.sudoku_size}'
                setattr(self, f'btn{i}{j}', QPushButton())
                getattr(self, name).addWidget(getattr(self, f'btn{i}{j}'), i % self.sudoku_size,
                                              j % self.sudoku_size, 1, 1)
                getattr(self, f'btn{i}{j}').setSizePolicy(sizePolicy)
                getattr(self, f'btn{i}{j}').setMinimumSize(QtCore.QSize(30, 30))
                my_font = QtGui.QFont()
                my_font.setPixelSize(20)
                getattr(self, f'btn{i}{j}').setFont(my_font)

    def load_matrix(self, matrix=None):
        if matrix is None:
            matrix = self.sudoku.get_problem_matrix()
        for i in range(len(matrix)):
            for j in range(len(matrix)):
                getattr(self, f'btn{i}{j}').setDisabled(False)
                getattr(self, f'btn{i}{j}').setText(str(matrix[i][j]) if matrix[i][j] else ' ')
                if getattr(self, f'btn{i}{j}').text() != ' ':
                    getattr(self, f'btn{i}{j}').setDisabled(True)

    def new_game_btn_clicked(self):
        self.check_save()
        btn = self.sender()
        levels = {
            "Легко 👶": 'EASY',
            "Средне 👦": 'STANDARD',
            "Сложно 🤓": 'HARD',
            "Адски сложно 🎓": 'HARDCORE'
        }
        level = levels[btn.text()]
        print(level)
        self.sudoku.generate_sudoku(level)
        self.load_matrix()
        self.reset_time()
        self.game_state = IN_GAME

    def save_game(self):
        try:
            self.database_cursor.insert_sudoku_into_db(self.sudoku)
        except Exception as e:
            print(e)

    def reset_time(self):
        self.game_seconds = 0

    def showtime(self):
        if self.game_state == IN_GAME:
            self.game_seconds += 1
        if self.is_show_timer:
            hours = self.game_seconds // 3600
            minutes = self.game_seconds // 60 % 60
            seconds = self.game_seconds % 60
            self.statusbar.showMessage((str(hours) + ':' if hours else '') + f'{minutes}' +
                                       ':' + f'{seconds}'.rjust(2, '0'))

    def show_hide_timer(self):
        self.is_show_timer = not self.is_show_timer
        if self.is_show_timer:
            self.action_11.setText('Спрятать таймер')
        else:
            self.action_11.setText('Показать таймер')

    def connect_db(self):
        try:
            self.database_cursor = MyDataBaseCursor(DB_NAME)
        except Exception as e:
            print(e)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.check_save()

    def check_save(self):
        if self.game_state != EMPTY:
            mb = QtWidgets.QMessageBox
            answer = mb.question(self, '',
                                 'Сохранить текущую игру?',
                                 mb.No | mb.Yes)

            if answer == mb.Yes:
                self.save_game()
            elif answer == mb.No:
                return False
            elif answer == 65536:
                return None


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec())


class MyThread(Thread):
    def __init__(self, sudoku_level_name, log, name):
        super().__init__()
        self.log = log
        self.sudoku_level_name = sudoku_level_name
        self.sudoku_level = LEVELS[sudoku_level_name]
        self.name = name

    def run(self):
        sudoku = Sudoku()
        now = datetime.datetime.now()
        sudoku.generate_sudoku(self.sudoku_level_name)
        t = datetime.datetime.now() - now
        temp = []
        temp.append('=' * 100)
        temp.append(' '.join(['Поток', self.name,
                              self.sudoku_level_name,
                              'завершил работу за', str(t.microseconds / 1000000), 'секунд']))
        temp.append(sudoku)
        self.log.append(temp)
        print(temp)

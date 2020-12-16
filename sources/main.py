from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QTimer
from itertools import product
from timeit import timeit
import random
import copy
import sys
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
    'HARDCORE': (15, 20)
}


def solve_sudoku(size, grid):
    """Интерпретация алгоритма X для решения судоку"""
    grid = copy.deepcopy(grid)
    R, C = size
    N = R * C
    X = ([("rc", rc) for rc in product(range(N), range(N))] +
         [("rn", rn) for rn in product(range(N), range(1, N + 1))] +
         [("cn", cn) for cn in product(range(N), range(1, N + 1))] +
         [("bn", bn) for bn in product(range(N), range(1, N + 1))])
    Y = dict()
    for r, c, n in product(range(N), range(N), range(1, N + 1)):
        b = (r // R) * R + (c // C)  # Box number
        Y[(r, c, n)] = [
            ("rc", (r, c)),
            ("rn", (r, n)),
            ("cn", (c, n)),
            ("bn", (b, n))]
    X, Y = exact_cover(X, Y)
    for i, row in enumerate(grid):
        for j, n in enumerate(row):
            if n:
                select(X, Y, (i, j, n))
    for solution in solve(X, Y, []):
        for (r, c, n) in solution:
            grid[r][c] = n
        yield grid


def exact_cover(X, Y):
    X = {j: set() for j in X}
    for i, row in Y.items():
        for j in row:
            X[j].add(i)
    return X, Y


def solve(X, Y, solution):
    if not X:
        yield list(solution)
    else:
        c = min(X, key=lambda c: len(X[c]))
        for r in list(X[c]):
            solution.append(r)
            cols = select(X, Y, r)
            for s in solve(X, Y, solution):
                yield s
            deselect(X, Y, r, cols)
            solution.pop()


def select(X, Y, r):
    cols = []
    for j in Y[r]:
        for i in X[j]:
            for k in Y[i]:
                if k != j:
                    X[k].remove(i)
        cols.append(X.pop(j))
    return cols


def deselect(X, Y, r, cols):
    for j in reversed(Y[r]):
        X[j] = cols.pop()
        for i in X[j]:
            for k in Y[i]:
                if k != j:
                    X[k].add(i)


class Sudoku:
    """Класс матрицы для судоку"""

    def __init__(self, size=3):
        """Параметр size задает размер квадратов, на которые разбивается матрица,
        то есть конечная матрица будет иметь размер size ** 2 на size ** 2"""
        self.size = size
        self.solved_sudoku = None
        self.problem_sudoku = None
        self.initialize_matrix()

    def initialize_matrix(self):
        """Записывает в self.matrix матрицу размером self.size * self.size заполненную None"""
        self.solved_sudoku = [[None for _ in range(self.size)] for _ in range(self.size)]

    def generate_initial_district(self, shift):
        """Генерирует и возвращает начальный район из self.size квадратных блоков со сдвигом shift"""
        initial_row = [i + 1 for i in range(self.size ** 2)]
        district = [initial_row[i * self.size + shift:] +
                    initial_row[:i * self.size + shift] for i in range(self.size)]
        return district

    def generate_initial_matrix(self):
        """Генерирует заполненную матрицу судоку"""
        for i in range(self.size):
            self.solved_sudoku += self.generate_initial_district(i)

    def transpose_matrix(self):
        """Транспонирует матрицу"""
        self.solved_sudoku = list(map(list, zip(*self.solved_sudoku)))

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
            self.solved_sudoku[second * self.size + i] = self.solved_sudoku[second * self.size + i], \
                                                         self.solved_sudoku[first * self.size + i]

    def change_col_districts(self):
        """Обменивает два случайных вертикальных района"""
        self.transpose_matrix()
        self.change_row_districts()
        self.transpose_matrix()

    def random_mix_matrix(self, k=5):
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
                print(cell_value, end='')
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

    def generate_sudoku(self, difficult: tuple):
        """Генерирует и возвращает судоку определенного уровня сложности difficult,
        представленным в виде кортежа наименьшего и наибольшего возможного
        количества оставшихся на поле клеток"""
        self.initialize_matrix()
        self.generate_initial_matrix()
        self.random_mix_matrix()

        problem_sudoku = self.get_solved_matrix()

        difficult_max, difficult_min = difficult

        variants = [(row, col) for row in range(self.size ** 4) for col in range(self.size ** 4)]
        print(*variants, sep='\n')
        random.shuffle(variants)

        attempts_max_count = 10
        attempts = 0
        current_difficult = 0
        while current_difficult < difficult_max:
            row, col = variants.pop()
            deleted_value = problem_sudoku[row][col]
            problem_sudoku[row][col] = 0

            solutions = 0
            for _ in solve_sudoku((self.size, self.size), problem_sudoku):
                solutions += 1
            if solutions == 1:
                current_difficult += 1
            else:
                problem_sudoku[row][col] = deleted_value

                if current_difficult >= difficult_min:
                    attempts += 1
                if attempts > attempts_max_count:
                    break

                variants = [(row, col)] + variants

        self.problem_sudoku = problem_sudoku

        return problem_sudoku

    def get_solved_matrix(self):
        """Возвращает копию текущей заполненной матрицы"""
        return copy.deepcopy(self.solved_sudoku)

    def get_problem_matrix(self):
        """Возвращает копию текущей незаполненной матрицы"""
        return copy.deepcopy(self.problem_sudoku)


s = Sudoku()
matrix = s.generate_sudoku(LEVELS['HARD'])
s.show_problem_matrix()


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

        self.database_connection = None
        self.database_cursor = None

        self.timer = QTimer(self)
        self.timer.start(PROGRAM_SECOND)
        self.timer.timeout.connect(self.showtime)
        self.game_seconds = 0
        self.is_show_timer = True
        self.showtime()

        for i in range(7, 10):
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
            matrix = self.sudoku.get_matrix()
        for i in range(len(matrix)):
            for j in range(len(matrix)):
                getattr(self, f'btn{i}{j}').setText(str(matrix[i][j]) if matrix[i][j] else ' ')

    def new_game_btn_clicked(self):
        if self.game_state != EMPTY:
            mb = QtWidgets.QMessageBox
            answer = mb.question(self, '',
                                 'Сохранить текущую игру?',
                                 mb.No | mb.Yes, mb.No)
            if answer == mb.Yes:
                self.save_game()
        btn = self.sender()
        levels = {
            "Легко 👶": 2,
            "Средне 👦": 5,
            "Сложно 🤓": 7,
            "Адски сложно 🎓": 9
        }
        level = levels[btn.text()]
        self.sudoku.generate_sudoku(level)
        self.load_matrix()
        self.reset_time()
        self.game_state = IN_GAME

    def save_game(self):
        pass

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

# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     ex = MainWindow()
#
#     pole = Sudoku()
#     pole.generate_sudoku()
#
#     ex.load_matrix(pole.get_matrix())
#
#     ex.show()
#     sys.exit(app.exec())

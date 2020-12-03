from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton
from PyQt5 import QtCore, QtGui, QtWidgets
import random
from time import time
import copy


def get_variants(sudoku):
    variants = []
    size = int(len(sudoku) ** 0.5)
    for i, row in enumerate(sudoku):
        for j, value in enumerate(row):
            if not value:
                row_values = set(row)
                col_values = set([sudoku[k][j] for k in range(size ** 2)])
                sq_y, sq_x = i // size, j // size
                square_values = set([sudoku[m][n]
                                     for m in range(sq_y * size, sq_y * size + size)
                                     for n in range(sq_x * size, sq_x * size + size)])
                exists = row_values | col_values | square_values
                values = set(range(1, size ** 2 + 1)) - exists
                variants.append((i, j, values))
    return variants


def solve_sudoku(sudoku):
    if all([all(row) for row in sudoku]):
        return sudoku
    variants = get_variants(sudoku)
    x, y, values = min(variants, key=lambda x: len(x[2]))
    for v in values:
        new_sudoku = copy.deepcopy(sudoku)
        new_sudoku[x][y] = v
        s = solve_sudoku(new_sudoku)
        if s:
            return s


class Sudoku:
    """Класс судоку матрицы"""

    def __init__(self, size=3):
        self.size = size
        self.matrix = []
        self.generate_initial_matrix()

    def show(self):
        """Выводит судоку в консоль"""
        for row in range(self.size ** 2):
            for col in range(self.size ** 2):
                if self.matrix[row][col] != 0:
                    print(f'{self.matrix[row][col]:3d}', end='')
                else:
                    print('   ', end='')
            print()
        print()

    def transpose(self):
        """Транспонирует матрицу"""
        self.matrix = list(map(list, zip(*self.matrix)))

    def change_rows(self):
        start = random.choice(range(self.size))
        variants = list(range(start * self.size, start * self.size + self.size))
        random.shuffle(variants)
        first = variants.pop()
        second = variants.pop()
        self.matrix[first], self.matrix[second] = self.matrix[second], self.matrix[first]

    def change_cols(self):
        self.transpose()
        self.change_rows()
        self.transpose()

    def change_row_districts(self):
        """Обменивает два случайных района по горизонтали"""
        variants = list(range(self.size))
        first = random.choice(variants)
        variants.remove(first)
        second = random.choice(variants)

        for i in range(self.size):
            self.matrix[first * self.size + i], \
            self.matrix[second * self.size + i] = self.matrix[second * self.size + i], \
                                                  self.matrix[first * self.size + i]

    def change_col_districts(self):
        """Обменивает два случайных района по вертикали"""
        self.transpose()
        self.change_row_districts()
        self.transpose()

    def random_mix_matrix(self, k=5):
        w = [self.transpose,
             self.change_rows,
             self.change_cols,
             self.change_row_districts,
             self.change_col_districts]
        for _ in range(k):
            mix_function = random.choice(w)
            mix_function()

    def generate_initial_matrix(self):
        """Генерирует начальную матрицу судоку"""
        self.matrix = []
        for i in range(self.size):
            self.matrix += self.generate_initial_district(i)

    def generate_initial_district(self, shift=0):
        """Генерирует и возвращает начальный район из self.size квадратных блоков со сдвигом shift"""
        initial_row = [i + 1 for i in range(self.size ** 2)]
        w = [initial_row[i * self.size + shift:] + initial_row[:i * self.size + shift] for i in
             range(self.size)]
        return w

    def generate_initial_mixed_matrix(self, k=5):
        """Генерирует готовую перемешанную k раз матрицу судоку"""
        self.generate_initial_matrix()
        self.random_mix_matrix(k)

    def delete_random_cells(self, k=25):
        """Удалить рандомные ячейки, оставив k ячеек"""
        variants = [(row, col) for row in range(self.size ** 2) for col in range(self.size ** 2)]
        random.shuffle(variants)
        for i in range(self.size ** 4 - k):
            row, col = variants.pop()
            self.matrix[row][col] = 0

    def get_matrix(self):
        return copy.deepcopy(self.matrix)

    def generate_sudoku(self):
        self.generate_initial_mixed_matrix()
        self.delete_random_cells()


pole = Sudoku()
pole.generate_sudoku()
pole.show()
for _ in range(10):
    print('-' * 50)
    pole.show()
    s = time()
    print(*solve_sudoku(pole.get_matrix()), sep='\n')
    print("%.03f" % (time() - s))


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
        self.menu_2.addAction(self.action_7)
        self.menu_2.addAction(self.action_8)
        self.menu_2.addAction(self.action_9)
        self.menu_2.addAction(self.action_10)
        self.menu.addAction(self.menu_2.menuAction())
        self.menu.addSeparator()
        self.menu.addAction(self.action_5)
        self.menu.addAction(self.action_2)
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


class MainWindow(Ui_MainWindow, QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)

        self.main_layout = QtWidgets.QGridLayout(self.centralwidget)
        self.main_layout.setHorizontalSpacing(3)
        self.main_layout.setVerticalSpacing(3)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                           QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)

        for i in range(3):
            for j in range(3):
                name = 'layout%i%d' % (i, j)
                setattr(self, name, QtWidgets.QGridLayout())
                getattr(self, name).setHorizontalSpacing(1)
                getattr(self, name).setVerticalSpacing(1)
                self.main_layout.addLayout(getattr(self, name), i, j)

        for i in range(9):
            for j in range(9):
                name = f'layout{i // 3}{j // 3}'
                setattr(self, f'btn{i}{j}', QPushButton())
                getattr(self, name).addWidget(getattr(self, f'btn{i}{j}'), i % 3, j % 3, 1, 1)
                getattr(self, f'btn{i}{j}').setSizePolicy(sizePolicy)
                getattr(self, f'btn{i}{j}').setMinimumSize(QtCore.QSize(30, 30))

# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     ex = MainWindow()
#     ex.show()
#     sys.exit(app.exec())

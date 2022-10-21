import sys
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import random
import math

#puzzle = [[6, 1, 4],[2, 8, 5],[7, 3, 0]]

form_class = uic.loadUiType("slidePuzzle.ui")[0]

class WindowClass(QMainWindow, form_class) :
    puzzle = [[0, 1, 2], [3, 4, 5], [6, 7, 8]]
    puzzle_origin = []
    answer = [[0, 1, 2], [3, 4, 5], [6, 7, 8]]
    way = []
    way_pos = 0
    move_count = 0
    move_temp = []
    can_move = 1
    assign_list = [0,0,0,0,0,0,1,0,0]

    def __init__(self) :
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(960, 540)

        # 이미지에 클릭 속성 넣기
        def clickable(widget):
            class Filter(QObject):
                clicked = pyqtSignal(QLabel) # 시그널 객체 생성
                def eventFilter(self, obj, event):
                    if obj == widget:
                        if event.type() == QEvent.MouseButtonRelease:
                            if obj.rect().contains(event.pos()):
                                self.clicked.emit(obj)
                                # The developer can opt for .emit(obj) to get the object within the slot.
                                return True
                    return False

            filter = Filter(widget)
            widget.installEventFilter(filter)
            return filter.clicked

        self.qPixmap = [] # 이미지 저장
        self.qPixmapVar = [] # 이미지 할당용 1
        self.qPixmapVar2 = [] # 이미지 할당용 2
        self.image = 0 # 현재 선택된 이미지 번호

        for i in range(6): # 이미지 6 * 8장 불러오기
            self.qPixmap.append([])
            for j in range(9):
                self.qPixmap[i].append(QPixmap())
                self.qPixmap[i][j].load("잠금일러스트/조각"+str(i+1)+"/퍼즐일러스트"+str(i+1)+"_"+str(j+1)+".png")
        Background = QImage("잠금일러스트/배경.png")
        Background_scaled = Background.scaled(QSize(960, 540))
        palette = QPalette()
        palette.setBrush(10, QBrush(Background_scaled))
        self.setPalette(palette)

        self.qPixmap2 = []
        for i in range(5):
            self.qPixmap2.append(QPixmap())
            self.qPixmap2[i].load("잠금일러스트/사각형"+str(i+1)+".png")
            #self.qPixmap2[i].load("잠금일러스트/선택.png")
        self.label4 = self.label4_1
        self.label4.move(509, 298)
        self.label4.resize(410, 150)
        self.label4.setPixmap(self.qPixmap2[0])

        self.temp_size1 = 125
        self.temp_size2 = 83

        self.qPixmap3 = QPixmap()
        self.qPixmap3.load("잠금일러스트/선택.png")
        self.qPixmapVar3 = (self.qPixmap3.scaledToHeight(self.temp_size2))
        self.alpha = self.label4_2
        self.alpha.move(-100, -100)
        self.alpha.resize(self.temp_size2, self.temp_size2)
        self.alpha.setPixmap(self.qPixmapVar3)


        for i in range(9):
            self.qPixmapVar.append(self.qPixmap[0][i].scaledToHeight(self.temp_size1))
            self.qPixmapVar2.append(self.qPixmap[0][i].scaledToHeight(self.temp_size2))

        self.label = [self.label_1, self.label_2, self.label_3, self.label_4, self.label_5, self.label_6, self.label_7, self.label_8, self.label_9]
        self.label2 = [self.label2_1, self.label2_2, self.label2_3, self.label2_4, self.label2_5, self.label2_6, self.label2_7, self.label2_8, self.label2_9]

        self.select = -1
        self.mode = 0 # 0 : 배치중 1 : 실행중

        for i in range(9):
            self.label[i].move(58 + (i%3) * self.temp_size1, 58 + int(i/3) * self.temp_size1)
            self.label[i].resize(self.temp_size1, self.temp_size1)
            clickable(self.label[i]).connect(self.imageMove) #pixmap.width(), pixmap.height()
            self.label2[i].move(589 + (i%3) * self.temp_size2, 39 + int(i/3) * self.temp_size2)
            self.label2[i].resize(self.temp_size2, self.temp_size2)
            self.label2[i].setPixmap(self.qPixmapVar2[i])
            clickable(self.label2[i]).connect(self.imageSelect)

        clickable(self.label3).connect(self.closeButton)

        self.pushButton_1.setEnabled(False)
        self.pushButton_2.setEnabled(False)
        self.pushButton_3.setEnabled(False)
        self.pushButton_4.setEnabled(False)
        self.pushButton_6.setEnabled(False)
        self.pushButton_7.setEnabled(False)
        self.pushButton_1.clicked.connect(self.stopButton)
        self.pushButton_2.clicked.connect(self.nextButton)
        self.pushButton_3.clicked.connect(self.previousButton)
        self.pushButton_4.clicked.connect(self.resumeButton)
        self.pushButton_5.clicked.connect(self.randomButton)
        self.pushButton_6.clicked.connect(self.compileButton)
        self.pushButton_7.clicked.connect(self.solveButton)

        self.comboBox.activated[str].connect(self.cbActivated)

        self.solvethread = None
        self.movethread = None
        self.movethread2 = None

    class imageMoveThread(QThread):
        timeout = pyqtSignal(list)
        timer = QTimer()

        def __init__(self, way, label):
            super().__init__()
            self.way = way
            self.label = label

            self.timer.setInterval(600)
            self.timer.timeout.connect(self.move)
            self.timer.start()

        def move(self):
            if len(self.way) > 0:
                temp = self.way.pop(0)
                self.timeout.emit(temp)

        def stop_working(self):
            self.timer.stop()
            self.quit()

    class imageMoveThread2(QThread): # 이미지를 부드럽게 이동
        timeout = pyqtSignal()

        def __init__(self, x, y, label, time, temp_size):
            super().__init__()
            self.label = label
            self.x = x
            self.y = y
            self.time = time # 0.5
            self.defaultV = 125 * 1000 / 0.5 / self.time # 500
            self.t = 20
            self.count = 1
            self.frame = self.time / self.t # 25
            self.q = self.defaultV / self.frame # 20
            self.dist = 0
            self.temp_size = temp_size
            self.originXY = [58 + self.x[0] * self.temp_size, 58 + self.x[1] * self.temp_size]

            self.timer = QTimer(self)
            self.timer.setInterval(20)
            self.timer.timeout.connect(self.move)
            self.timer.start()

        def move(self):
            if self.t * self.count <= self.time:
                self.dist = self.temp_size * (math.log2(self.count) / math.log2(self.time/self.t))
                 # 매트릭스와 ui 좌표는 서로 순서가 다름!!
                self.label.move(int(self.originXY[1] + ((self.y[1] - self.x[1]) * self.dist)), int(self.originXY[0] + ((self.y[0] - self.x[0]) * self.dist)))

                self.count += 1
            else:
                self.label.move(58 + self.y[1] * self.temp_size, 58 + self.y[0] * self.temp_size)
                self.timeout.emit()
                self.timer.stop()
                self.quit()

    @pyqtSlot(list)
    def thread_imageMove(self, temp):
        self.way_pos += 1
        num = self.puzzle[temp[0]][temp[1]]
        blank = self.findPiece(6, self.puzzle)

        if abs(blank[0] - temp[0]) + abs(blank[1] - temp[1]) != 1:
            return

        self.label[6].move(self.label[num].x(), self.label[num].y())
        self.can_move = 0
        timer = QTimer()
        timer.singleShot(70, self.nowCanMove)
        self.movethread2 = self.imageMoveThread2(temp, blank, self.label[num], 150, self.temp_size1)
        self.movethread2.timeout.connect(self.thread_imageMoveEnd)
        self.swap(blank, temp, self.puzzle)

    def nowCanMove(self):
        self.can_move = 1

    @pyqtSlot()
    def thread_imageMoveEnd(self):
        self.can_move = 1
        self.movethread2 = None
        if self.move_temp:
            self.thread_imageMove(self.move_temp)
            self.move_temp = []

    def allIsOn(self):
        for i in range(9):
            if not self.assign_list[i]:
                return False
        return True


    def imageMove(self, obj):
        if self.mode == 0 and self.select != -1: # 배치중
            for i in range(9):
                if self.label[i] == obj:
                    To = self.findPiece(self.select, self.puzzle)
                    My = self.findPiece(i, self.puzzle)
                    break
            Tox = self.label[self.select].x()
            Toy = self.label[self.select].y()
            Myx = obj.x()
            Myy = obj.y()
            self.label[self.select].move(Myx, Myy)
            obj.move(Tox, Toy)
            self.label[self.select].setPixmap(self.qPixmapVar[self.select])
            self.swap(To, My, self.puzzle)
            self.assign_list[self.select] = 1
            if self.allIsOn():
                self.label4.setPixmap(self.qPixmap2[1])
                self.pushButton_6.setEnabled(True)
        elif self.mode == 1 and self.can_move == 1: # 실행중
            for i in range(9):
                if self.label[i] == obj:
                    temp = self.findPiece(i, self.puzzle)
                    break
            if self.movethread2 is None:
                self.thread_imageMove(temp)
                self.way_pos -= 1
            else:
                self.move_temp = temp

    def imageSelect(self, obj):
        if self.mode == 0:
            for i in range(9):
                if self.label2[i] == obj:
                    self.select = i
                    self.alpha.move(obj.x(), obj.y())
                    break

    def closeButton(self, obj):
        QCoreApplication.instance().quit()

    def compileButton(self):
        if self.mode == 0: # 편집 -> 배치 완료
            self.pushButton_5.setEnabled(False)
            self.pushButton_7.setEnabled(True)
            self.pushButton_6.setText("편집")
            self.mode = 1
            #self.opacity_effect.setOpacity(0)
            self.alpha.move(-100, -100)
            self.select = -1
            self.puzzle_origin = self.solveThread.puzzleCopy(self, self.puzzle)
            self.label4.setPixmap(self.qPixmap2[2])
        elif self.mode == 1: # 배치완료 -> 편집
            self.pushButton_1.setEnabled(False)
            self.pushButton_2.setEnabled(False)
            self.pushButton_3.setEnabled(False)
            self.pushButton_4.setEnabled(False)
            self.pushButton_5.setEnabled(True)
            self.pushButton_7.setEnabled(False)
            self.pushButton_7.setText("풀이확인")
            self.pushButton_6.setText("배치완료")
            self.way = []
            self.way_pos = 0
            self.move_count = 0
            self.mode = 0
            self.label4.setPixmap(self.qPixmap2[1])
        elif self.can_move == 1: # 해답 -> 배치완료
            if self.solvethread is not None:
                self.solvethread.stop = 1
            self.pushButton_1.setEnabled(False)
            self.pushButton_2.setEnabled(False)
            self.pushButton_3.setEnabled(False)
            self.pushButton_4.setEnabled(False)
            self.pushButton_5.setEnabled(False)
            self.pushButton_7.setEnabled(True)
            self.pushButton_7.setText("풀이확인")
            self.pushButton_6.setText("편집")
            self.mode = 1
            #self.opacity_effect.setOpacity(0)
            self.alpha.move(-100, -100)
            self.select = -1
            self.puzzle = self.solveThread.puzzleCopy(self, self.puzzle_origin)
            for i in range(3):
                for j in range(3):
                    self.label[self.puzzle[i][j]].move(58 + j * self.temp_size1, 58 + i * self.temp_size1)
                    self.label[self.puzzle[i][j]].setPixmap(self.qPixmapVar[self.puzzle[i][j]])
            self.label4.setPixmap(self.qPixmap2[2])

    def cbActivated(self, text):
        num = int(text[1]) - 1
        for i in range(9):
            self.qPixmapVar[i] = self.qPixmap[num][i].scaledToHeight(self.temp_size1)
            if self.label[i].pixmap() is not None:
                self.label[i].setPixmap(self.qPixmapVar[i])
            self.qPixmapVar2[i] = self.qPixmap[num][i].scaledToHeight(self.temp_size2)
            self.label2[i].setPixmap(self.qPixmapVar2[i])

    def getH(self, puzzle): # h(n) 값을 반환
        count = 0
        for i in range(9):
            if i == 6:
                continue
            a = self.findPiece(i, puzzle)
            count += abs(a[0] - int(i/3)) + abs(a[1] - i%3)
        return count

    def swap(self, x, y, puzzle):  # x와 y의 위치를 서로 바꿈
        temp = puzzle[x[0]][x[1]]
        puzzle[x[0]][x[1]] = puzzle[y[0]][y[1]]
        puzzle[y[0]][y[1]] = temp

    def findPiece(self, x, puzzle):  # x번째 퍼즐의 위치를 반환
        for i in range(3):
            if x in puzzle[i]:
                return [i, puzzle[i].index(x)]
            else:
                continue
        return -1

    def puzzle_shuffle(self, puzzle):
        for i in range(3):
            for j in range(3):
                puzzle[i][j] = i * 3 + j
        blank = self.findPiece(6, puzzle)
        block = None
        #limit = random.randrange(16,20)
        limit = 21
        while True:
            h = self.getH(puzzle)
            if h >= limit:
                break
            temp_list = []
            if blank[0] < 2: # 아래로 이동
                temp = [blank[0] + 1, blank[1]]
                if not temp == block:
                    temp_list.append(temp)
            if blank[0] > 0:  # 위로 이동
                temp = [blank[0] - 1, blank[1]]
                if not temp == block:
                    temp_list.append(temp)
            if blank[1] < 2:  # 오른쪽으로 이동
                temp = [blank[0], blank[1] + 1]
                if not temp == block:
                    temp_list.append(temp)
            if blank[1] > 0:  # 왼쪽으로 이동
                temp = [blank[0], blank[1] - 1]
                if not temp == block:
                    temp_list.append(temp)

            select = temp_list[random.randrange(0,len(temp_list))]
            self.swap(blank, select, puzzle)
            block = select
            blank = select

    def resumeButton(self):
        if len(self.way) > 0 and self.way_pos < len(self.way) - 1:
            self.movethread = self.imageMoveThread(self.way[self.way_pos + 1:], self.label)
            self.movethread.timeout.connect(self.thread_imageMove)
            self.pushButton_2.setEnabled(False)
            self.pushButton_3.setEnabled(False)
            self.pushButton_6.setEnabled(False)

    def stopButton(self):
        if self.movethread is not None:
            self.movethread.stop_working()
            self.pushButton_2.setEnabled(True)
            self.pushButton_3.setEnabled(True)
            self.pushButton_6.setEnabled(True)

    def nextButton(self):
        if self.way_pos < len(self.way) - 1 and self.can_move == 1 and self.movethread2 is None:
            self.way_pos += 1
            temp = self.way[self.way_pos]
            num = self.puzzle[temp[0]][temp[1]]
            self.way_pos -= 1
            self.thread_imageMove(temp)

    def previousButton(self):
        if self.way_pos > 0 and self.can_move == 1 and self.movethread2 is None:
            self.way_pos -= 1
            temp = self.way[self.way_pos]
            num = self.puzzle[temp[0]][temp[1]]
            self.way_pos -= 1
            self.thread_imageMove(temp)

    def randomButton(self):
        self.puzzle = [[0, 1, 2], [3, 4, 5], [6, 7, 8]]
        self.puzzle_shuffle(self.puzzle)
        for i in range(3):
            for j in range(3):
                self.label[self.puzzle[i][j]].move(58 + j * self.temp_size1, 58 + i * self.temp_size1)
                self.label[self.puzzle[i][j]].setPixmap(self.qPixmapVar[self.puzzle[i][j]])
        self.assign_list = [1, 1, 1, 1, 1, 1, 1, 1, 1]
        self.label4.setPixmap(self.qPixmap2[1])
        self.pushButton_6.setEnabled(True)

    def solveButton(self):
        self.mode = 2
        self.solvethread = self.solveThread()
        self.solvethread.threadEvent.connect(self.solveThreadControl)
        self.solvethread.set(self.puzzle, self.answer)
        self.pushButton_7.setText("계산중...")
        self.solvethread.start()

    @pyqtSlot(list, int)
    def solveThreadControl(self, way, move_count):
        if move_count == -1:
            self.label4.setPixmap(self.qPixmap2[4])
            self.pushButton_7.setText("계산실패")
            self.pushButton_7.setEnabled(False)
            self.mode = 1
        else:
            self.way = way
            self.way_pos = 0
            self.move_count = move_count
            self.pushButton_7.setText("계산완료")
            self.pushButton_6.setText("원래대로")
            self.pushButton_1.setEnabled(True)
            self.pushButton_2.setEnabled(True)
            self.pushButton_3.setEnabled(True)
            self.pushButton_4.setEnabled(True)
            self.pushButton_7.setEnabled(False)
            self.label4.setPixmap(self.qPixmap2[3])
        self.solvethread.stop = 1
        self.solvethread = None

    class solveThread(QThread):
        threadEvent = pyqtSignal(list, int)
        stop = 0

        def swap(self, x, y, puzzle):  # x와 y의 위치를 서로 바꿈
            temp = puzzle[x[0]][x[1]]
            puzzle[x[0]][x[1]] = puzzle[y[0]][y[1]]
            puzzle[y[0]][y[1]] = temp
            puzzle = None
            answer = None

        def getH(self, puzzle):  # h(n) 값을 반환
            count = 0
            for i in range(9):
                if i == 6:
                    continue
                a = self.findPiece(i, puzzle)
                count += abs(a[0] - int(i / 3)) + abs(a[1] - i % 3)
            return count

        def findPiece(self, x, puzzle):  # x번째 퍼즐의 위치를 반환
            for i in range(3):
                if x in puzzle[i]:
                    return [i, puzzle[i].index(x)]
                else:
                    continue
            return -1

        def set(self, puzzle, answer):
            self.puzzle = puzzle
            self.answer = answer

        def puzzleCopy(self, puzzle):
            temp = []
            for i in range(3):
                temp.append(puzzle[i].copy())
            return temp

        def run(self):
            stack = [[self.puzzle, 0, [], [self.findPiece(6, self.puzzle)]]]  # 현재 퍼즐 상태, 이동 횟수, 이전 공백 위치
            closed = []
            h_stack = [self.getH(self.puzzle) + 0]
            while (self.stop == 0):
                minH = min(h_stack)
                for i in range(len(h_stack)):
                    if h_stack[i] == minH:
                        temp_puzzle, move_count, block, way = stack.pop(i)
                        h_stack.pop(i)
                        break

                if minH - move_count == 2 and temp_puzzle[2][0] == 6:
                    self.threadEvent.emit([], -1)
                    break

                if temp_puzzle == self.answer:
                    self.threadEvent.emit(way, move_count)
                    break

                closed.append(temp_puzzle)

                x = self.findPiece(6, temp_puzzle)
                if x[0] < 2:  # 밑으로 이동
                    temp = [x[0] + 1, x[1]]  # x가 이동할 목적지를 저장해두는 변수
                    if not temp in block:  # temp 위치에 걸림돌이 없다면
                        moved_puzzle = self.puzzleCopy(temp_puzzle)  # 원본 퍼즐을 복사
                        self.swap(x, temp, moved_puzzle)  # 복사된 퍼즐을 이동
                        if not moved_puzzle in closed or not moved_puzzle in stack:
                            h_stack.append(self.getH(moved_puzzle) + move_count + 1)
                            stack.append([moved_puzzle, move_count + 1, [x], way + [temp]])  # 결과를 임시 스택에 저장

                if x[0] > 0:  # 위로 이동
                    temp = [x[0] - 1, x[1]]
                    if not temp in block:
                        moved_puzzle = self.puzzleCopy(temp_puzzle)
                        self.swap(x, temp, moved_puzzle)
                        if not moved_puzzle in closed or not moved_puzzle in stack:
                            h_stack.append(self.getH(moved_puzzle) + move_count + 1)
                            stack.append([moved_puzzle, move_count + 1, [x], way + [temp]])

                if x[1] < 2:  # 오른쪽으로 이동
                    temp = [x[0], x[1] + 1]
                    if not temp in block:
                        moved_puzzle = self.puzzleCopy(temp_puzzle)
                        self.swap(x, temp, moved_puzzle)
                        if not moved_puzzle in closed or not moved_puzzle in stack:
                            h_stack.append(self.getH(moved_puzzle) + move_count + 1)
                            stack.append([moved_puzzle, move_count + 1, [x], way + [temp]])

                if x[1] > 0:  # 왼쪽으로 이동
                    temp = [x[0], x[1] - 1]
                    if not temp in block:
                        moved_puzzle = self.puzzleCopy(temp_puzzle)
                        self.swap(x, temp, moved_puzzle)
                        if not moved_puzzle in closed or not moved_puzzle in stack:
                            h_stack.append(self.getH(moved_puzzle) + move_count + 1)
                            stack.append([moved_puzzle, move_count + 1, [x], way + [temp]])
            self.quit()
            self.wait(5000)

if __name__ == "__main__" :
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    app.exec_()
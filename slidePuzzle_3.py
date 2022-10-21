import sys
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import random
import math
import os


class WindowClass(QMainWindow) :
    puzzle = [[0, 1, 2], [3, 4, 5], [6, 7, 8]] # 현재 퍼즐 상태
    puzzle_origin = [] # "원래대로" 버튼 눌렀을 때 puzzle에 할당할 퍼즐 기본 상태
    answer = [[0, 1, 2], [3, 4, 5], [6, 7, 8]] # 답지
    way = [] # 해답
    way_pos = 0 # 현재 이동할 조각이 way에서 몇번째인지
    move_count = 0 # 이동한 횟수
    move_temp = [] # 퍼즐이 움직이는 동안에 다른 퍼즐을 클릭한 경우 예약해둠
    can_move = 1 # 퍼즐을 직접 손으로 움직일 수 있는 상태인지
    assign_list = [0,0,0,0,0,0,1,0,0] # 배치된 퍼즐 여부
    puzzle_select = 0 # 현재 퍼즐 번호
    temp_size1 = 125 # 왼쪽 퍼즐 이미지 사이즈
    temp_size2 = 83 # 오른쪽 퍼즐 이미지 사이즈
    unlockImage = 0 # 잠금 상태인지 이미지 번호로 구별
    select = -1 # 현재 선택된 이미지 번호
    mode = 0  # 0 : 배치중 1 : 실행중 2 : 풀이중
    # 각 버튼이 사용가능한지 여부
    enabledButton = [False, False, False, False, False, False, True]  # 0시작, 1정지, 2이전, 3다음, 4풀이, 5배치완료, 6랜덤배치
    # 스레드 변수. 스레드 생상시 아래 변수에 할당됨
    solvethread = None # "풀이확인" 버튼 누르면 생성
    movethread = None # "시작" 버튼 누르면 생성
    movethread2 = None # movethread가 퍼즐 움직일 때마다 생성

    def __init__(self) :
        super().__init__()
        #self.setupUi(self)
        self.setWindowTitle("라스트오리진 퍼즐")
        self.setWindowIcon(QIcon("잠금일러스트/아이콘.ico"))
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

        # 기본배경화면 일러스트 설정
        Background = QImage("잠금일러스트/배경1.png")
        palette = QPalette()
        palette.setBrush(10, QBrush(Background))
        self.setPalette(palette)

        # 퍼즐 조각 로딩
        self.qPixmap = []  # 이미지 저장용 변수
        for i in range(6): # 이미지 6 * 8장 불러오기
            self.qPixmap.append([])
            for j in range(9):
                self.qPixmap[i].append(QPixmap())
                if j == 6: continue
                self.qPixmap[i][j].load("잠금일러스트/조각"+str(i+1)+"/퍼즐일러스트"+str(i+1)+"_"+str(j+1)+".png")

        # 원본에서 크기 변형한 조각을 저장할 변수
        self.qPixmapVar = []  # 이미지 할당용 1
        self.qPixmapVar2 = []  # 이미지 할당용 2
        for i in range(9):
            if i == 6:
                self.qPixmapVar.append(self.qPixmap[0][i])
                self.qPixmapVar2.append(self.qPixmap[0][i])
                continue
            self.qPixmapVar.append(self.qPixmap[0][i].scaledToHeight(self.temp_size1))
            self.qPixmapVar2.append(self.qPixmap[0][i].scaledToHeight(self.temp_size2))

        # 조각 이미지 표시할 라벨 로딩
        self.label = [] # 왼쪽 이미지 라벨
        self.label2 = [] # 오른쪽 이미지 라벨
        for i in range(9):
            self.label.append(QLabel("" + str(i + 1), self))
            self.label2.append(QLabel("" + str(i + 1), self))

        # 각 라벨을 배치하고 이미지 할당
        for i in range(9):
            self.label[i].move(58 + (i % 3) * self.temp_size1, 58 + int(i / 3) * self.temp_size1)
            self.label[i].resize(self.temp_size1, self.temp_size1)
            clickable(self.label[i]).connect(self.imageMove)
            self.label2[i].move(589 + (i % 3) * self.temp_size2, 39 + int(i / 3) * self.temp_size2)
            self.label2[i].resize(self.temp_size2, self.temp_size2)
            self.label2[i].setPixmap(self.qPixmapVar2[i])
            clickable(self.label2[i]).connect(self.imageSelect)

        # 잠금화면으로 나가는 버튼. 화면 중앙 하단에 있음
        self.label3 = QLabel("", self)
        clickable(self.label3).connect(self.closeButton)
        self.label3.move(454, 479)
        self.label3.resize(51, 51)
        self.label3.setText("")

        # 퍼즐 설명 이미지 로딩
        self.qPixmap2 = []
        for i in range(5):
            self.qPixmap2.append(QPixmap())
            self.qPixmap2[i].load("잠금일러스트/사각형"+str(i+1)+".png")
        self.label4 = QLabel("", self)
        self.label4.move(509, 298)
        self.label4.resize(410, 150)
        self.label4.setPixmap(self.qPixmap2[0])

        # 선택한 퍼즐을 나타내는 이미지 로딩
        self.qPixmap3 = QPixmap()
        self.qPixmap3.load("잠금일러스트/선택.png")
        self.qPixmapVar3 = self.qPixmap3.scaledToHeight(self.temp_size2)
        self.alpha = QLabel("", self)
        self.alpha.move(-100, -100)
        self.alpha.resize(self.temp_size2, self.temp_size2)
        self.alpha.setPixmap(self.qPixmapVar3)

        # 화면에 뜨는 버튼 이미지 로딩
        self.qPixmap4 = []
        for i in range(7):
            self.qPixmap4.append([])
            for j in range(2):
                self.qPixmap4[i].append(QPixmap())
                self.qPixmap4[i][j].load("잠금일러스트/버튼"+str(i+1)+"_"+str(j+1)+".png")
            if i == 4:
                for j in range(2,5):
                    self.qPixmap4[i].append(QPixmap())
                    self.qPixmap4[i][j].load("잠금일러스트/버튼" + str(i + 1) + "_" + str(j + 1) + ".png")
            if i == 5:
                for j in range(2,6):
                    self.qPixmap4[i].append(QPixmap())
                    self.qPixmap4[i][j].load("잠금일러스트/버튼" + str(i + 1) + "_" + str(j + 1) + ".png")

        # 버튼에 사용할 라벨 로딩
        self.label5 = []
        for i in range(0, 6):
            self.label5.append(QLabel(""+str(i+1), self))
            self.label5[i].setPixmap(self.qPixmap4[i][1])
        self.label5.append(QLabel("", self))
        self.label5[6].setPixmap(self.qPixmap4[6][0])
        self.label5[0].move(58, 470)
        self.label5[1].move(118, 470)
        self.label5[2].move(178, 470)
        self.label5[3].move(238, 470)
        self.label5[4].move(330, 470)
        self.label5[5].move(720, 470)
        self.label5[6].move(820, 470)
        self.label5[0].resize(51, 51)
        self.label5[1].resize(51, 51)
        self.label5[2].resize(51, 51)
        self.label5[3].resize(51, 51)
        self.label5[4].resize(91, 51)
        self.label5[5].resize(91, 51)
        self.label5[6].resize(91, 51)

        # 각 버튼과 함수 연결
        clickable(self.label5[0]).connect(self.resumeButton)
        clickable(self.label5[1]).connect(self.stopButton)
        clickable(self.label5[2]).connect(self.previousButton)
        clickable(self.label5[3]).connect(self.nextButton)
        clickable(self.label5[4]).connect(self.solveButton)
        clickable(self.label5[5]).connect(self.compileButton)
        clickable(self.label5[6]).connect(self.randomButton)

        # 오른쪽 퍼즐 양쪽에 붙은 화살표 로딩
        self.qPixmap5 = []
        for i in range(2):
            self.qPixmap5.append(QPixmap())
            self.qPixmap5[i].load("잠금일러스트/화살표" + str(i + 1) + ".png")

        # 화살표 라벨 로딩
        self.label6 = []
        self.label6.append(QLabel("", self))
        self.label6.append(QLabel("", self))
        self.label6[0].setPixmap(self.qPixmap5[0])
        self.label6[0].move(589-79 - 5, 39 + 92)
        self.label6[0].resize(79, 66)
        self.label6[1].setPixmap(self.qPixmap5[1])
        self.label6[1].move(589 + self.temp_size2 * 3 + 5, 39 + 92)
        self.label6[1].resize(79, 66)
        clickable(self.label6[0]).connect(self.puzzleSelect)
        clickable(self.label6[1]).connect(self.puzzleSelect)

        # 잠금화면, 잠금 푼 화면 로딩
        self.qPixmap6 = []
        for i in range(2):
            self.qPixmap6.append(QPixmap())
            self.qPixmap6[i].load("잠금일러스트/배경" + str(i+2) + ".png")
        self.label7_1 = QLabel('', self)
        self.label7_1.setPixmap(self.qPixmap6[0])
        self.label7_1.move(0, 541) # 0, 0
        self.label7_1.resize(960, 540)
        self.label7_1.setText("")
        clickable(self.label7_1).connect(self.unlockButton)

        # 퍼즐로 돌아가는 버튼
        self.label7_2 = QLabel('', self)
        self.label7_2.move(0, 541) # 455, 430
        self.label7_2.resize(50, 50)
        self.label7_2.setText("")
        clickable(self.label7_2).connect(self.getBackButton)

        # 잠금화면으로 돌아가는 버튼
        self.label7_3 = QLabel('', self)
        self.label7_3.move(0, 541) # 902, 54
        self.label7_3.resize(58, 32)
        self.label7_3.setText("")

    # 화살표 누르면 작동하는 함수
    def puzzleSelect(self, obj):
        if obj == self.label6[0]:
            self.puzzle_select -= 1
            if self.puzzle_select < 0:
                self.puzzle_select = 5
        else:
            self.puzzle_select += 1
            if self.puzzle_select > 5:
                self.puzzle_select = 0

        for i in range(9):
            if i == 6:
                continue
            self.qPixmapVar[i] = self.qPixmap[self.puzzle_select][i].scaledToHeight(self.temp_size1)
            if self.label[i].pixmap() is not None:
                self.label[i].setPixmap(self.qPixmapVar[i])
            self.qPixmapVar2[i] = self.qPixmap[self.puzzle_select][i].scaledToHeight(self.temp_size2)
            self.label2[i].setPixmap(self.qPixmapVar2[i])

    # "시작" 버튼 누르면 생성
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
                self.label5[5].setPixmap(self.qPixmap4[5][0])
                self.enabledButton[5] = True
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
        self.label7_1.move(0, 0)
        self.label7_2.move(455, 430)

    def unlockButton(self, obj):
        if self.unlockImage == 0:
            self.unlockImage = 1
            self.label7_1.setPixmap(self.qPixmap6[1])
            self.label7_2.move(0, 541)
        else:
            self.unlockImage = 0
            self.label7_1.setPixmap(self.qPixmap6[0])
            self.label7_2.move(455, 430)

    def getBackButton(self, obj):
        self.label7_1.move(0, 541)
        self.label7_2.move(0, 541)

    def compileButton(self):
        if self.enabledButton[5] is False:
            return
        if self.mode == 0: # 편집 -> 배치 완료
            self.label5[4].setPixmap(self.qPixmap4[4][0])
            self.enabledButton[4] = True
            self.label5[5].setPixmap(self.qPixmap4[5][2])
            self.enabledButton[4] = True
            self.label5[6].setPixmap(self.qPixmap4[6][1])
            self.enabledButton[6] = False
            self.mode = 1
            #self.opacity_effect.setOpacity(0)
            self.alpha.move(-100, -100)
            self.select = -1
            self.puzzle_origin = self.solveThread.puzzleCopy(self, self.puzzle)
            self.label4.setPixmap(self.qPixmap2[2])
        elif self.mode == 1: # 배치완료 -> 편집
            self.label5[0].setPixmap(self.qPixmap4[0][1])
            self.enabledButton[0] = False
            self.label5[1].setPixmap(self.qPixmap4[1][1])
            self.enabledButton[1] = False
            self.label5[2].setPixmap(self.qPixmap4[2][1])
            self.enabledButton[2] = False
            self.label5[3].setPixmap(self.qPixmap4[3][1])
            self.enabledButton[3] = False
            self.label5[4].setPixmap(self.qPixmap4[4][1])
            self.enabledButton[4] = False
            self.label5[5].setPixmap(self.qPixmap4[5][0])
            self.enabledButton[5] = True
            self.label5[6].setPixmap(self.qPixmap4[6][0])
            self.enabledButton[6] = True
            self.way = []
            self.way_pos = 0
            self.move_count = 0
            self.mode = 0
            self.label4.setPixmap(self.qPixmap2[1])
        elif self.can_move == 1: # 해답 -> 배치완료
            if self.solvethread is not None:
                self.solvethread.stop_working()
                self.solvethread = None
            self.label5[0].setPixmap(self.qPixmap4[0][1])
            self.enabledButton[0] = False
            self.label5[1].setPixmap(self.qPixmap4[1][1])
            self.enabledButton[1] = False
            self.label5[2].setPixmap(self.qPixmap4[2][1])
            self.enabledButton[2] = False
            self.label5[3].setPixmap(self.qPixmap4[3][1])
            self.enabledButton[3] = False
            self.label5[4].setPixmap(self.qPixmap4[4][0])
            self.enabledButton[4] = True
            self.label5[5].setPixmap(self.qPixmap4[5][2])
            self.enabledButton[5] = True
            self.label5[6].setPixmap(self.qPixmap4[6][1])
            self.enabledButton[6] = False
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
        limit = random.randrange(10,19)
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
        if self.enabledButton[0] is True and len(self.way) > 0 and self.way_pos < len(self.way) - 1:
            self.movethread = self.imageMoveThread(self.way[self.way_pos + 1:], self.label)
            self.movethread.timeout.connect(self.thread_imageMove)
            self.label5[0].setPixmap(self.qPixmap4[0][1])
            self.enabledButton[0] = False
            self.label5[1].setPixmap(self.qPixmap4[1][0])
            self.enabledButton[1] = True
            self.label5[2].setPixmap(self.qPixmap4[2][1])
            self.enabledButton[2] = False
            self.label5[3].setPixmap(self.qPixmap4[3][1])
            self.enabledButton[3] = False
            self.label5[5].setPixmap(self.qPixmap4[5][5])
            self.enabledButton[5] = False
            self.label5[1].setPixmap(self.qPixmap4[1][0])
            self.enabledButton[1] = True

    def stopButton(self):
        if self.enabledButton[1] is True and self.movethread is not None:
            self.movethread.stop_working()
            self.label5[0].setPixmap(self.qPixmap4[0][0])
            self.enabledButton[0] = True
            self.label5[1].setPixmap(self.qPixmap4[1][1])
            self.enabledButton[1] = False
            self.label5[2].setPixmap(self.qPixmap4[2][0])
            self.enabledButton[2] = True
            self.label5[3].setPixmap(self.qPixmap4[3][0])
            self.enabledButton[3] = True
            self.label5[5].setPixmap(self.qPixmap4[5][4])
            self.enabledButton[5] = True

    def previousButton(self):
        if self.enabledButton[2] is True and self.way_pos > 0 and self.can_move == 1 and self.movethread2 is None:
            self.way_pos -= 1
            temp = self.way[self.way_pos]
            num = self.puzzle[temp[0]][temp[1]]
            self.way_pos -= 1
            self.thread_imageMove(temp)

    def nextButton(self):
        if self.enabledButton[3] is True and self.way_pos < len(self.way) - 1 and self.can_move == 1 and self.movethread2 is None:
            self.way_pos += 1
            temp = self.way[self.way_pos]
            num = self.puzzle[temp[0]][temp[1]]
            self.way_pos -= 1
            self.thread_imageMove(temp)

    def randomButton(self):
        if self.enabledButton[6] is False:
            return
        self.puzzle = [[0, 1, 2], [3, 4, 5], [6, 7, 8]]
        self.puzzle_shuffle(self.puzzle)
        for i in range(3):
            for j in range(3):
                self.label[self.puzzle[i][j]].move(58 + j * self.temp_size1, 58 + i * self.temp_size1)
                self.label[self.puzzle[i][j]].setPixmap(self.qPixmapVar[self.puzzle[i][j]])
        self.assign_list = [1, 1, 1, 1, 1, 1, 1, 1, 1]
        self.label4.setPixmap(self.qPixmap2[1])
        self.label5[5].setPixmap(self.qPixmap4[5][0])
        self.enabledButton[5] = True

    def solveButton(self):
        if self.enabledButton[4] is False:
            return
        self.mode = 2
        self.solvethread = self.solveThread()
        self.solvethread.threadEvent.connect(self.solveThreadControl)
        self.solvethread.set(self.puzzle, self.answer)
        self.label5[4].setPixmap(self.qPixmap4[4][2])
        self.enabledButton[4] = False
        self.solvethread.start()

    @pyqtSlot(list, int)
    def solveThreadControl(self, way, move_count):
        if move_count == -1:
            self.label4.setPixmap(self.qPixmap2[4])
            self.label5[4].setPixmap(self.qPixmap4[4][4])
            self.enabledButton[4] = False
            self.mode = 1
        else:
            self.way = way
            self.way_pos = 0
            self.move_count = move_count
            self.label5[0].setPixmap(self.qPixmap4[0][0])
            self.enabledButton[0] = True
            self.label5[1].setPixmap(self.qPixmap4[1][1])
            self.enabledButton[1] = False
            self.label5[2].setPixmap(self.qPixmap4[2][0])
            self.enabledButton[2] = True
            self.label5[3].setPixmap(self.qPixmap4[3][0])
            self.enabledButton[3] = True
            self.label5[4].setPixmap(self.qPixmap4[4][3])
            self.enabledButton[4] = False
            self.label5[5].setPixmap(self.qPixmap4[5][4])
            self.enabledButton[5] = True
            self.label4.setPixmap(self.qPixmap2[3])
        self.solvethread.stop_working()
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

        def stop_working(self):
            self.stop = 1
            self.quit()
            self.wait(5000)

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

if __name__ == "__main__" :

    try:
        os.chdir(sys._MEIPASS)
    except:
        os.chdir(os.getcwd())

    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    app.exec_()
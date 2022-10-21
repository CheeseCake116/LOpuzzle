import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import random
import math
import os
from PIL import ImageGrab, Image, ImageQt
import cv2
from tempfile import TemporaryDirectory

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
    puzzle_select_limit = -1 # 퍼즐 번호 한계
    unlockImage = 0 # 잠금 상태인지 이미지 번호로 구별
    select = -1 # 현재 선택된 이미지 번호
    mode = 0  # 0 : 배치중 1 : 실행중 2 : 풀이중
    # 각 버튼이 사용가능한지 여부
    # 0시작, 1정지, 2이전, 3다음, 4풀이, 5배치완료, 6랜덤배치, 7불러오기, 8화살표, 9설정
    enabledButton = [False, False, False, False, False, False, True, True, True, True]
    # 스레드 변수. 스레드 생상시 아래 변수에 할당됨
    solvethread = None # "풀이확인" 버튼 누르면 생성
    movethread = None # "시작" 버튼 누르면 생성
    movethread2 = None # movethread가 퍼즐 움직일 때마다 생성
    resolution = {0 : [960, 540], 1 : [1280, 720], 2 : [1600, 900]} # 해상도 dictionary
    res_select = 0 # 현재 선택된 해상도 값
    puzzleSize = {0 : 3, 1 : 4, 2 : 5}
    size_select = 0 # 현재 선택된 퍼즐 크기. 3x3, 4x4, 5x5
    psize = puzzleSize[size_select]
    temp_size1 = int(624 / 3) # 왼쪽 퍼즐 크기
    temp_size2 = int(417 / 3) # 오른쪽 퍼즐 크기
    setting_on = 0 # 옵션창 꺼져있는지
    inst_num = 0 # 현재 Instruction 몇 번인지
    # 현재 실행파일 위치.
    # os.chdir로 위치 바뀌기 전에 미리 저장
    origin_addr = os.getcwd()

    def __init__(self) : # 이미지 및 라벨 생성
        super().__init__()

        try:
            os.chdir(sys._MEIPASS)
        except:
            os.chdir(os.getcwd())

        self.setWindowTitle("라스트오리진 퍼즐 시뮬레이터")
        self.setWindowIcon(QIcon("PuzzleImage/PuzzleIcon.ico"))

        # 기본배경화면 일러스트 로딩
        # __init__에서 PIL.image로 이미지 로딩 -> setting에서 Image.resize로 크기 조절 -> QLabel에 setPixmap으로 할당
        self.qPixmap_back = Image.open("PuzzleImage/Background1.png")
        self.qLabel_back = QLabel('', self)

        # 조각이 배치되지 않은 label에 사용
        self.emptyPixmap = QPixmap()

        # 조각 이미지
        self.qPixmap = []
        self.qPixmapVar = [[None] * (self.psize ** 2), [None] * (self.psize ** 2)]

        # 완성본 이미지
        self.qPixmap7 = []
        self.qPixmapVar7 = []

        # 'custom', 'Complete' 이미지 불러오기
        file_list = os.listdir(self.origin_addr + '\custom')
        self.puzzle_select_limit = -1
        i = 0
        for num in range(6 + len(file_list)):
            if num < 6:
                im = Image.open('PuzzleImage/Complete/Comp' + str(num + 1) + '.png')
            else:
                try:
                    im = Image.open(self.origin_addr + '\custom\\' + file_list[num - 6])
                except:
                    continue
            width, height = im.size
            if width < height:
                size = width # 정사각형 한 변 길이
                pos = [0, int((height - size) / 2)] # 이미지에서 정사각형 왼쪽 위 좌표
            else:
                size = height
                pos = [int((width - size) / 2), 0]

            croppedSize = int(size / self.psize) # 조각 한 개 크기
            bbox = (pos[0], pos[1], pos[0] + croppedSize * self.psize, pos[1] + croppedSize * self.psize)
            croppedImage = im.crop(bbox)
            self.qPixmap7.append(croppedImage)
            self.qPixmapVar7.append(None)

            self.qPixmap.append([])
            for j in range(self.psize ** 2):
                if j == self.psize ** 2 - self.psize:
                    self.qPixmap[i].append(QPixmap())
                    continue
                left = pos[0] + (j % self.psize) * croppedSize
                top = pos[1] + int(j / self.psize) * croppedSize
                bbox = (left, top, left + croppedSize, top + croppedSize)
                croppedImage = im.crop(bbox)
                self.qPixmap[i].append(croppedImage)
            self.puzzle_select_limit += 1
            i += 1

        # 조각 이미지 표시할 라벨 로딩
        self.label = []  # 왼쪽 이미지 라벨
        self.label2 = []  # 오른쪽 이미지 라벨
        for i in range(25):
            self.label.append(QLabel("", self))
            self.label[i].move(0, 901)
            self.clickable(self.label[i]).connect(self.imageMove)
            self.label2.append(QLabel("", self))
            self.label2[i].move(0, 901)
            self.clickable(self.label2[i]).connect(self.imageSelect)

        # 잠금화면으로 나가는 버튼. 화면 중앙 하단에 있음
        self.label3 = QLabel("", self)
        self.clickable(self.label3).connect(self.closeButton)

        # 퍼즐 설명 이미지 로딩
        self.qPixmap2 = []
        self.qPixmapVar2 = []
        for i in range(7):
            self.qPixmap2.append(Image.open("PuzzleImage/Instruction"+str(i+1)+".png"))
            self.qPixmapVar2.append(None)
        self.label4 = QLabel("", self)

        self.label8 = QLabel("", self)
        self.clickable(self.label8).connect(self.unComplete)

        # 선택한 퍼즐을 나타내는 이미지 로딩
        self.qPixmap3 = Image.open("PuzzleImage/Select.png")
        self.alpha = QLabel("", self)

        # 화면에 뜨는 버튼 이미지 로딩
        self.qPixmap4 = []
        self.qPixmapVar4 = []
        for i in range(8):
            self.qPixmap4.append([])
            self.qPixmapVar4.append([])
            for j in range(2):
                self.qPixmap4[i].append(Image.open("PuzzleImage/Btn" + str(i + 1) + "_" + str(j + 1) + ".png"))
                self.qPixmapVar4[i].append(None)
            if i == 4:
                for j in range(2, 5):
                    self.qPixmap4[i].append(Image.open("PuzzleImage/Btn" + str(i + 1) + "_" + str(j + 1) + ".png"))
                    self.qPixmapVar4[i].append(None)
            if i == 5:
                for j in range(2, 6):
                    self.qPixmap4[i].append(Image.open("PuzzleImage/Btn" + str(i + 1) + "_" + str(j + 1) + ".png"))
                    self.qPixmapVar4[i].append(None)

        # 버튼에 사용할 라벨 로딩
        self.label5 = []
        for i in range(8):
            self.label5.append(QLabel("", self))

        # 각 버튼과 함수 연결
        self.clickable(self.label5[0]).connect(self.resumeButton)
        self.clickable(self.label5[1]).connect(self.stopButton)
        self.clickable(self.label5[2]).connect(self.previousButton)
        self.clickable(self.label5[3]).connect(self.nextButton)
        self.clickable(self.label5[4]).connect(self.solveButton)
        self.clickable(self.label5[5]).connect(self.compileButton)
        self.clickable(self.label5[6]).connect(self.randomButton)
        self.clickable(self.label5[7]).connect(self.clipboardButton)

        # 오른쪽 퍼즐 양쪽에 붙은 화살표 로딩
        self.qPixmap5 = []
        self.qPixmapVar5 = []
        for i in range(2):
            self.qPixmap5.append([])
            self.qPixmapVar5.append([])
            for j in range(2):
                self.qPixmap5[i].append(Image.open("PuzzleImage/Arrow" + str(i + 1) + "_" + str(j + 1) + ".png"))
                self.qPixmapVar5[i].append(None)

        # 화살표 라벨 로딩
        self.label6 = []
        self.label6.append(QLabel("", self))
        self.label6.append(QLabel("", self))
        self.clickable(self.label6[0]).connect(self.puzzleSelect)
        self.clickable(self.label6[1]).connect(self.puzzleSelect)

        # 옵션창 이미지 로딩
        self.qPixmap8 = []
        self.qPixmapVar8 = []
        self.qPixmap8.append([])
        self.qPixmapVar8.append([])

        for i in range(2):  # 톱니바퀴 버튼. qPixmap8[0][0~1]
            self.qPixmap8[0].append(Image.open("PuzzleImage/Setting_" + str(i + 1) + ".png"))
            self.qPixmapVar8[0].append(None)

        self.qPixmap8.append(Image.open("PuzzleImage/Option.png"))  # 옵션창. qPixmap8[1]
        self.qPixmapVar8.append(None)

        for i in range(2, 4):  # 옵션 버튼.
            self.qPixmap8.append([])
            self.qPixmapVar8.append([])
            for j in range(6):
                self.qPixmap8[i].append(Image.open("PuzzleImage/optBtn" + str(i - 1) + "_" + str(j + 1) + ".png"))
                self.qPixmapVar8[i].append(None)

        # 옵션 라벨 로딩
        self.label9 = []

        self.label9.append(QLabel("", self))  # 톱니바퀴 버튼
        self.clickable(self.label9[0]).connect(self.settingButton)

        self.label9.append(QLabel("", self))  # 옵션창. 클릭하면 꺼짐
        self.clickable(self.label9[1]).connect(self.settingButton)

        for i in range(2, 4):  # 옵션창 버튼들
            self.label9.append([])
            for j in range(3):
                self.label9[i].append(QLabel("", self))
                self.clickable(self.label9[i][j]).connect(self.settingButton)

        # 잠금화면, 잠금 푼 화면 로딩
        self.qPixmap6 = []
        self.qPixmapVar6 = []
        for i in range(2):
            self.qPixmap6.append(Image.open("PuzzleImage/Background" + str(i + 2) + ".png"))
            self.qPixmapVar6.append(None)
        self.label7_1 = QLabel('', self)
        self.clickable(self.label7_1).connect(self.unlockButton)

        # 퍼즐로 돌아가는 버튼
        self.label7_2 = QLabel('', self)
        self.clickable(self.label7_2).connect(self.getBackButton)

        self.setting()

    # 이미지에 클릭 속성 넣기
    def clickable(self, widget):
        class Filter(QObject):
            clicked = pyqtSignal(QLabel)  # 시그널 객체 생성

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

    def setting(self):
        # 기본배경화면 일러스트 설정
        self.qLabel_back.move(0, 0)
        self.qLabel_back.resize(self.adjustResolution(1600), self.adjustResolution(900))
        Background_resize = self.qPixmap_back.resize((self.adjustResolution(1600), self.adjustResolution(900)),
                                                     Image.ANTIALIAS)
        self.qLabel_back.setPixmap(ImageQt.toqpixmap(Background_resize))

        self.psize = self.puzzleSize[self.size_select]
        self.temp_size1 = int(624 / self.psize)
        self.temp_size2 = int(417 / self.psize)

        # 원본에서 크기 변형한 조각을 저장할 변수
        for i in range(self.psize ** 2):
            if i == self.psize ** 2 - self.psize:
                self.qPixmapVar[0][i] = self.qPixmap[self.puzzle_select][i]
                self.qPixmapVar[1][i] = self.qPixmap[self.puzzle_select][i]
                continue

            img1 = self.qPixmap[self.puzzle_select][i].resize(
                (self.adjustResolution(self.temp_size1), self.adjustResolution(self.temp_size1)), Image.ANTIALIAS)
            img2 = self.qPixmap[self.puzzle_select][i].resize(
                (self.adjustResolution(self.temp_size2), self.adjustResolution(self.temp_size2)), Image.ANTIALIAS)
            self.qPixmapVar[0][i] = ImageQt.toqpixmap(img1)
            self.qPixmapVar[1][i] = ImageQt.toqpixmap(img2)

        # 완성샷 이미지 로딩
        for i in range(self.puzzle_select_limit + 1):
            croppedImage = self.qPixmap7[i].resize(
                (self.adjustResolution(self.temp_size1) * self.psize, self.adjustResolution(self.temp_size1) * self.psize),
                Image.ANTIALIAS)
            self.qPixmapVar7[i] = ImageQt.toqpixmap(croppedImage)

        # 각 라벨을 배치하고 이미지 할당
        for i in range(self.psize):
            for j in range(self.psize):
                self.label[self.puzzle[i][j]].move(
                    self.adjustResolution(96) + j * self.adjustResolution(self.temp_size1),
                    self.adjustResolution(96) + i * self.adjustResolution(self.temp_size1))
                if self.assign_list[self.puzzle[i][j]]:
                    self.label[self.puzzle[i][j]].setPixmap(self.qPixmapVar[0][self.puzzle[i][j]])
                else:
                    self.label[self.puzzle[i][j]].setPixmap(self.emptyPixmap)

        for i in range(self.psize ** 2):
            self.label[i].resize(self.adjustResolution(self.temp_size1), self.adjustResolution(self.temp_size1))
            self.label2[i].move(
                self.adjustResolution(982) + (i % self.psize) * self.adjustResolution(self.temp_size2),
                self.adjustResolution(65) + int(i / self.psize) * self.adjustResolution(self.temp_size2))
            self.label2[i].resize(self.adjustResolution(self.temp_size2), self.adjustResolution(self.temp_size2))
            self.label2[i].setPixmap(self.qPixmapVar[1][i])

        # 잠금화면으로 나가는 버튼. 화면 중앙 하단에 있음
        self.label3.move(self.adjustResolution(757), self.adjustResolution(798))
        self.label3.resize(self.adjustResolution(85), self.adjustResolution(85))

        # 퍼즐 설명 이미지 로딩
        for i in range(7):
            img = self.qPixmap2[i].resize((self.adjustResolution(683), self.adjustResolution(250)), Image.ANTIALIAS)
            self.qPixmapVar2[i] = ImageQt.toqpixmap(img)
        self.label4.move(self.adjustResolution(848), self.adjustResolution(497))
        self.label4.resize(self.adjustResolution(683), self.adjustResolution(250))
        self.label4.setPixmap(self.qPixmapVar2[self.inst_num])

        self.label8.move(0, 901)
        self.label8.resize(
            self.adjustResolution(self.temp_size1) * self.psize, self.adjustResolution(self.temp_size1) * self.psize)

        # 선택한 퍼즐을 나타내는 이미지 로딩
        img = self.qPixmap3.resize(
            (self.adjustResolution(self.temp_size2), self.adjustResolution(self.temp_size2)), Image.ANTIALIAS)
        self.qPixmapVar3 = ImageQt.toqpixmap(img)
        if self.select == -1:
            self.alpha.move(0, 901)
        else:
            self.alpha.move(
                self.adjustResolution(982) + (self.select % self.psize) * self.adjustResolution(self.temp_size2),
                self.adjustResolution(65) + int(self.select / self.psize) * self.adjustResolution(self.temp_size2))
        self.alpha.resize(self.adjustResolution(self.temp_size2), self.adjustResolution(self.temp_size2))
        self.alpha.setPixmap(self.qPixmapVar3)

        # 화면에 뜨는 버튼 이미지 로딩
        for i in range(8):
            for j in range(2):
                if i < 4:
                    img = self.qPixmap4[i][j].resize(
                        (self.adjustResolution(85), self.adjustResolution(85)), Image.ANTIALIAS)
                else:
                    img = self.qPixmap4[i][j].resize(
                        (self.adjustResolution(152), self.adjustResolution(85)), Image.ANTIALIAS)
                self.qPixmapVar4[i][j] = ImageQt.toqpixmap(img)
            if i == 4:
                for j in range(2,5):
                    img = self.qPixmap4[i][j].resize((self.adjustResolution(152), self.adjustResolution(85)), Image.ANTIALIAS)
                    self.qPixmapVar4[i][j] = ImageQt.toqpixmap(img)
            if i == 5:
                for j in range(2,6):
                    img = self.qPixmap4[i][j].resize((self.adjustResolution(152), self.adjustResolution(85)), Image.ANTIALIAS)
                    self.qPixmapVar4[i][j] = ImageQt.toqpixmap(img)

        # 버튼에 사용할 라벨 로딩
        for i in range(8):
            self.label5[i].setPixmap(self.qPixmapVar4[i][1])
        if self.enabledButton[5]:
            self.label5[5].setPixmap(self.qPixmapVar4[5][0])
        self.label5[6].setPixmap(self.qPixmapVar4[6][0])
        self.label5[7].setPixmap(self.qPixmapVar4[7][0])
        if self.size_select != 0:
            self.label5[7].setPixmap(self.qPixmapVar4[7][1])
            self.enabledButton[7] = False
        self.label5[0].move(self.adjustResolution(97), self.adjustResolution(783))
        self.label5[1].move(self.adjustResolution(197), self.adjustResolution(783))
        self.label5[2].move(self.adjustResolution(297), self.adjustResolution(783))
        self.label5[3].move(self.adjustResolution(397), self.adjustResolution(783))
        self.label5[4].move(self.adjustResolution(550), self.adjustResolution(783))
        self.label5[5].move(self.adjustResolution(1033), self.adjustResolution(783))
        self.label5[6].move(self.adjustResolution(1367), self.adjustResolution(783))
        self.label5[7].move(self.adjustResolution(1200), self.adjustResolution(783))
        self.label5[0].resize(self.adjustResolution(85), self.adjustResolution(85))
        self.label5[1].resize(self.adjustResolution(85), self.adjustResolution(85))
        self.label5[2].resize(self.adjustResolution(85), self.adjustResolution(85))
        self.label5[3].resize(self.adjustResolution(85), self.adjustResolution(85))
        self.label5[4].resize(self.adjustResolution(152), self.adjustResolution(85))
        self.label5[5].resize(self.adjustResolution(152), self.adjustResolution(85))
        self.label5[6].resize(self.adjustResolution(152), self.adjustResolution(85))
        self.label5[7].resize(self.adjustResolution(152), self.adjustResolution(85))

        # 오른쪽 퍼즐 양쪽에 붙은 화살표 로딩
        for i in range(2):
            for j in range(2):
                img = self.qPixmap5[i][j].resize((self.adjustResolution(132), self.adjustResolution(110)), Image.ANTIALIAS)
                self.qPixmapVar5[i][j] = ImageQt.toqpixmap(img)

        # 화살표 라벨 로딩
        self.label6[0].setPixmap(self.qPixmapVar5[0][0])
        self.label6[0].move(self.adjustResolution(982 - 132 - 5), self.adjustResolution(65 + 154))
        self.label6[0].resize(self.adjustResolution(132), self.adjustResolution(110))
        self.label6[1].setPixmap(self.qPixmapVar5[1][0])
        self.label6[1].move(self.adjustResolution(982 + 5) + self.adjustResolution(self.temp_size2) * self.psize, self.adjustResolution(65 + 154))
        self.label6[1].resize(self.adjustResolution(132), self.adjustResolution(110))

        # 옵션창 이미지 로딩
        for i in range(2): # 톱니바퀴 버튼. qPixmap8[0][0~1]
            img = self.qPixmap8[0][i].resize((self.adjustResolution(63), self.adjustResolution(63)), Image.ANTIALIAS)
            self.qPixmapVar8[0][i] = ImageQt.toqpixmap(img)

        img = self.qPixmap8[1].resize((self.adjustResolution(672), self.adjustResolution(421)), Image.ANTIALIAS)
        self.qPixmapVar8[1] = ImageQt.toqpixmap(img)

        for i in range(2, 4): # 옵션 버튼.
            for j in range(6):
                img = self.qPixmap8[i][j].resize((self.adjustResolution(117), self.adjustResolution(48)), Image.ANTIALIAS)
                self.qPixmapVar8[i][j] = ImageQt.toqpixmap(img)

        # 옵션 라벨 로딩
        self.label9[0].setPixmap(self.qPixmapVar8[0][0])
        self.label9[0].move(self.adjustResolution(1600 - 63), self.adjustResolution(0))
        self.label9[0].resize(self.adjustResolution(63), self.adjustResolution(63))

        self.label9[1].setPixmap(self.qPixmapVar8[1])
        self.label9[1].move(0, 901)
        self.label9[1].resize(self.adjustResolution(672), self.adjustResolution(421))

        for i in range(2, 4): # 옵션창 버튼들
            for j in range(3):
                self.label9[i][j].setPixmap(self.qPixmapVar8[i][j * 2 + 1])
                self.label9[i][j].move(0, 901)
                self.label9[i][j].resize(self.adjustResolution(117), self.adjustResolution(48))

        if self.setting_on: # 옵션창 커져있으면
            self.label9[1].move(self.adjustResolution(464), self.adjustResolution(240))
            for i in range(2, 4):
                for j in range(3):
                    self.label9[i][j].move(self.adjustResolution(464 + 161 + 149 * j),
                                           self.adjustResolution(240 + 100 + 79 * (i - 2)))

        # 현재 선택된 버튼들 불 켜기
        self.label9[2][self.res_select].setPixmap(self.qPixmapVar8[2][self.res_select * 2])
        self.label9[3][self.size_select].setPixmap(self.qPixmapVar8[3][self.size_select * 2])

        # 잠금화면, 잠금 푼 화면 로딩
        for i in range(2):
            img = self.qPixmap6[i].resize((self.adjustResolution(1600), self.adjustResolution(900)), Image.ANTIALIAS)
            self.qPixmapVar6[i] = ImageQt.toqpixmap(img)
        self.label7_1.setPixmap(self.qPixmapVar6[0])
        self.label7_1.move(0, 901) # 0, 0
        self.label7_1.resize(self.adjustResolution(1600), self.adjustResolution(900))

        # 퍼즐로 돌아가는 버튼
        self.label7_2.move(0, 901) # 455, 430
        self.label7_2.resize(self.adjustResolution(83), self.adjustResolution(83))

        # 마지막으로 해상도 설정
        self.setFixedSize(self.resolution[self.res_select][0], self.resolution[self.res_select][1])

    # 해상도에 맞게 값을 변환시켜줌
    def adjustResolution(self, value):
        if self.res_select == 0:
            return int(math.ceil(value * (3 / 5)))
        elif self.res_select == 1:
            return int(math.ceil(value * (4 / 5)))
        elif self.res_select == 2:
            return value

    # 세팅 버튼 누르면 작동하는 함수
    def settingButton(self, obj):
        if self.enabledButton[9] is False:
            return

        if obj == self.label9[0]:
            self.setting_on = 1
            self.label9[1].move(self.adjustResolution(464), self.adjustResolution(240))
            for i in range(2, 4):
                for j in range(3):
                    self.label9[i][j].move(self.adjustResolution(464 + 161 + 149 * j), self.adjustResolution(240 + 100 + 79 * (i-2)))
        elif obj == self.label9[1] or obj == 0:
            self.closeSetting()
        else:
            for j in range(3):
                if obj == self.label9[2][j]:
                    if self.res_select != j:
                        self.resolutionChange(j)
                elif obj == self.label9[3][j]:
                    if self.size_select != j:
                        self.sizeChange(j)

    # 세팅창 종료 함수
    def closeSetting(self):
        self.setting_on = 0
        self.label9[1].move(0, 901)
        for i in range(2, 4):
            for j in range(3):
                self.label9[i][j].move(0, 901)

    # 설정창에서 해상도 변경하면 작동하는 함수
    def resolutionChange(self, num):
        for j in range(3):
            self.label9[2][j].setPixmap(self.qPixmapVar8[2][j * 2 + 1])
        self.label9[2][num].setPixmap(self.qPixmapVar8[2][num * 2])
        self.res_select = num
        self.setting()

    # 설정창에서 퍼즐 크기 변경하면 작동하는 함수
    def sizeChange(self, num):
        for j in range(3):
            self.label9[3][j].setPixmap(self.qPixmapVar8[3][j * 2 + 1])
        self.label9[3][num].setPixmap(self.qPixmapVar8[3][num * 2])
        self.size_select = num

        self.psize = self.puzzleSize[num] # 3, 4, 5
        self.temp_size1 = int(624 / self.psize)
        self.temp_size2 = int(417 / self.psize)

        self.puzzle = []
        self.answer = []
        for i in range(self.psize):
            self.puzzle.append([])
            self.answer.append([])
            for j in range(self.psize):
                self.puzzle[i].append(i * self.psize + j)
                self.answer[i].append(i * self.psize + j)

        self.qPixmap = []
        self.qPixmapVar = [[None] * (self.psize ** 2), [None] * (self.psize ** 2)]
        self.qPixmap7 = []
        self.qPixmapVar7 = []

        # 'custom' 이미지 불러오기
        file_list = os.listdir(self.origin_addr + '\custom')
        self.puzzle_select_limit = -1
        i = 0
        for num in range(6 + len(file_list)):
            if num < 6:
                im = Image.open('PuzzleImage/Complete/Comp' + str(num + 1) + '.png')
            else:
                try:
                    im = Image.open(self.origin_addr + '\custom\\' + file_list[num - 6])
                except:
                    continue
            width, height = im.size
            if width < height:
                size = width
                pos = [0, int((height - size) / 2)]
            else:
                size = height
                pos = [int((width - size) / 2), 0]

            croppedSize = int(size / self.psize)
            bbox = (pos[0], pos[1], pos[0] + croppedSize * self.psize, pos[1] + croppedSize * self.psize)
            croppedImage = im.crop(bbox)
            self.qPixmap7.append(croppedImage)
            self.qPixmapVar7.append(None)

            self.qPixmap.append([])
            for j in range(self.psize ** 2):
                if j == self.psize ** 2 - self.psize:
                    self.qPixmap[i].append(QPixmap())
                    continue
                left = pos[0] + (j % self.psize) * croppedSize
                top = pos[1] + int(j / self.psize) * croppedSize
                bbox = (left, top, left + croppedSize, top + croppedSize)
                croppedImage = im.crop(bbox)
                self.qPixmap[i].append(croppedImage)
            self.puzzle_select_limit += 1
            i += 1

        # 조각 이미지 표시할 라벨 로딩
        for i in range(self.psize ** 2):
            self.label[i].setPixmap(self.emptyPixmap)

        self.assign_list = [0] * (self.psize ** 2)
        self.assign_list[self.psize ** 2 - self.psize] = 1

        # 원본에서 크기 변형한 조각을 저장할 변수
        for i in range(self.psize ** 2):
            if i == self.psize ** 2 - self.psize:
                self.qPixmapVar[0][i] = self.emptyPixmap
                self.qPixmapVar[1][i] = self.emptyPixmap
                continue

            img1 = self.qPixmap[self.puzzle_select][i].resize(
                (self.adjustResolution(self.temp_size1), self.adjustResolution(self.temp_size1)), Image.ANTIALIAS)
            img2 = self.qPixmap[self.puzzle_select][i].resize(
                (self.adjustResolution(self.temp_size2), self.adjustResolution(self.temp_size2)), Image.ANTIALIAS)
            self.qPixmapVar[0][i] = ImageQt.toqpixmap(img1)
            self.qPixmapVar[1][i] = ImageQt.toqpixmap(img2)

        # 완성샷 이미지 로딩
        for i in range(self.puzzle_select_limit + 1):
            croppedImage = self.qPixmap7[i].resize(
                (self.adjustResolution(self.temp_size1) * self.psize,
                 self.adjustResolution(self.temp_size1) * self.psize),
                Image.ANTIALIAS)
            self.qPixmapVar7[i] = ImageQt.toqpixmap(croppedImage)

        # 각 라벨을 배치하고 이미지 할당
        for i in range(self.psize):
            for j in range(self.psize):
                self.label[i * self.psize + j].move(
                    self.adjustResolution(96) + j * self.adjustResolution(self.temp_size1),
                    self.adjustResolution(96) + i * self.adjustResolution(self.temp_size1))

        for i in range(self.psize ** 2):
            self.label[i].resize(self.adjustResolution(self.temp_size1), self.adjustResolution(self.temp_size1))
            self.label2[i].move(self.adjustResolution(982) + (i % self.psize) * self.adjustResolution(self.temp_size2),
                                self.adjustResolution(65) + int(i / self.psize) * self.adjustResolution(
                                    self.temp_size2))
            self.label2[i].resize(self.adjustResolution(self.temp_size2), self.adjustResolution(self.temp_size2))
            self.label2[i].setPixmap(self.qPixmapVar[1][i])

        for i in range(self.psize ** 2, 25):
            self.label[i].move(0, 901)
            self.label2[i].move(0, 901)

        # 완성샷 이미지 조절, 라벨 이동
        self.label8.move(0, 901)
        self.label8.resize(
            self.adjustResolution(self.temp_size1) * self.psize, self.adjustResolution(self.temp_size1) * self.psize)

        # 선택한 퍼즐을 나타내는 이미지 로딩
        img = self.qPixmap3.resize(
            (self.adjustResolution(self.temp_size2), self.adjustResolution(self.temp_size2)), Image.ANTIALIAS)
        self.qPixmapVar3 = ImageQt.toqpixmap(img)

        self.select = -1
        self.alpha.move(0, 901)
        self.alpha.resize(self.adjustResolution(self.temp_size2), self.adjustResolution(self.temp_size2))
        self.alpha.setPixmap(self.qPixmapVar3)

        # 배치완료 버튼 끄기
        self.label5[5].setPixmap(self.qPixmapVar4[5][1])
        self.enabledButton[5] = False

        # 불러오기 버튼 끄기
        if self.size_select == 0:
            self.label5[7].setPixmap(self.qPixmapVar4[7][0])
            self.enabledButton[7] = True
        else:
            self.label5[7].setPixmap(self.qPixmapVar4[7][1])
            self.enabledButton[7] = False

        # 설명 초기화
        self.inst_num = 0
        self.label4.setPixmap(self.qPixmapVar2[self.inst_num])

    # 화살표 누르면 작동하는 함수
    def puzzleSelect(self, obj):
        if self.enabledButton[8] == False:
            return
        if obj == self.label6[0]:
            self.puzzle_select -= 1
            if self.puzzle_select < 0:
                self.puzzle_select = self.puzzle_select_limit
        else:
            self.puzzle_select += 1
            if self.puzzle_select > self.puzzle_select_limit:
                self.puzzle_select = 0

        for i in range(self.psize ** 2):
            if i == self.psize ** 2 - self.psize:
                continue
            img1 = self.qPixmap[self.puzzle_select][i].resize(
                (self.adjustResolution(self.temp_size1), self.adjustResolution(self.temp_size1)), Image.ANTIALIAS)
            img2 = self.qPixmap[self.puzzle_select][i].resize(
                (self.adjustResolution(self.temp_size2), self.adjustResolution(self.temp_size2)), Image.ANTIALIAS)
            self.qPixmapVar[0][i] = ImageQt.toqpixmap(img1)
            self.qPixmapVar[1][i] = ImageQt.toqpixmap(img2)

            if self.assign_list[i]:
                self.label[i].setPixmap(self.qPixmapVar[0][i])
            self.label2[i].setPixmap(self.qPixmapVar[1][i])

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

        def __init__(self, x, y, label, timedata, obj):
            super().__init__()
            self.main = obj
            self.label = label
            self.x = x
            self.y = y
            self.time = timedata # 0.5
            self.defaultV = 125 * 1000 / 0.5 / self.time # 500
            self.t = 20
            self.count = 1
            self.frame = self.time / self.t # 25
            self.q = self.defaultV / self.frame # 20
            self.dist = 0
            self.temp_size = self.main.adjustResolution(self.main.temp_size1)
            self.originXY = [self.main.adjustResolution(96) + self.x[0] * self.temp_size,
                             self.main.adjustResolution(96) + self.x[1] * self.temp_size]
            self.timer = QTimer(self)
            self.timer.setInterval(20)
            self.timer.timeout.connect(self.move)
            self.timer.start()
            self.res_select = self.main.res_select

        def move(self):
            self.originXY = [self.main.adjustResolution(96) + self.x[0] * self.temp_size,
                             self.main.adjustResolution(96) + self.x[1] * self.temp_size]
            if self.t * self.count <= self.time:
                self.dist = self.temp_size * (math.log2(self.count) / math.log2(self.time/self.t))
                 # 매트릭스와 ui 좌표는 서로 순서가 다름!!
                self.label.move(int(self.originXY[1] + ((self.y[1] - self.x[1]) * self.dist)), int(self.originXY[0] + ((self.y[0] - self.x[0]) * self.dist)))

                self.count += 1
            else:
                self.label.move(self.main.adjustResolution(96) + self.y[1] * self.temp_size, self.main.adjustResolution(96) + self.y[0] * self.temp_size)
                self.timeout.emit()
                self.timer.stop()
                self.quit()

    @pyqtSlot(list)
    def thread_imageMove(self, temp):
        self.way_pos += 1
        num = self.puzzle[temp[0]][temp[1]]
        blank = self.findPiece(self.psize ** 2 - self.psize, self.puzzle)

        if abs(blank[0] - temp[0]) + abs(blank[1] - temp[1]) != 1:
            return

        self.label[self.psize ** 2 - self.psize].move(self.label[num].x(), self.label[num].y())
        self.can_move = 0
        timer = QTimer()
        timer.singleShot(70, self.nowCanMove)
        self.movethread2 = self.imageMoveThread2(temp, blank, self.label[num], 150, self)
        self.movethread2.timeout.connect(self.thread_imageMoveEnd)
        self.swap(blank, temp, self.puzzle)

    def nowCanMove(self):
        self.can_move = 1

    @pyqtSlot()
    def thread_imageMoveEnd(self):
        self.can_move = 1
        self.movethread2 = None
        if self.puzzle == self.answer:
            self.label8.move(self.adjustResolution(96), self.adjustResolution(96))
            self.label8.setPixmap(self.qPixmapVar7[self.puzzle_select])
            if self.mode == 2:
                self.label5[0].setPixmap(self.qPixmapVar4[0][0])
                self.enabledButton[0] = True
                self.label5[1].setPixmap(self.qPixmapVar4[1][1])
                self.enabledButton[1] = False
                self.label5[2].setPixmap(self.qPixmapVar4[2][0])
                self.enabledButton[2] = True
                self.label5[3].setPixmap(self.qPixmapVar4[3][0])
                self.enabledButton[3] = True
                self.label5[5].setPixmap(self.qPixmapVar4[5][4])
                self.enabledButton[5] = True

        if self.move_temp:
            self.thread_imageMove(self.move_temp)
            self.move_temp = []

    def unComplete(self):
        self.label8.move(0,901)

    def allIsOn(self):
        for i in range(self.psize ** 2):
            if not self.assign_list[i]:
                return False
        return True

    def imageMove(self, obj):
        if self.mode == 0 and self.select != -1: # 배치중
            for i in range(self.psize ** 2):
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
            self.label[self.select].setPixmap(self.qPixmapVar[0][self.select])
            self.swap(To, My, self.puzzle)
            self.assign_list[self.select] = 1
            if self.allIsOn():
                self.label4.setPixmap(self.qPixmapVar2[1])
                self.inst_num = 1
                self.label5[5].setPixmap(self.qPixmapVar4[5][0])
                self.enabledButton[5] = True
        elif self.mode == 1 and self.can_move == 1: # 실행중
            for i in range(self.psize ** 2):
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
            for i in range(self.psize ** 2):
                if self.label2[i] == obj:
                    self.select = i
                    self.alpha.move(obj.x(), obj.y())
                    break

    def closeButton(self, obj):
        self.label7_1.move(0, 0)
        self.label7_2.move(self.adjustResolution(758), self.adjustResolution(717))

    def unlockButton(self, obj):
        if self.unlockImage == 0:
            self.unlockImage = 1
            self.label7_1.setPixmap(self.qPixmapVar6[1])
            self.label7_2.move(0, 901)
        else:
            self.unlockImage = 0
            self.label7_1.setPixmap(self.qPixmapVar6[0])
            self.label7_2.move(self.adjustResolution(758), self.adjustResolution(717))

    def getBackButton(self, obj):
        self.label7_1.move(0, 901)
        self.label7_2.move(0, 901)

    def compileButton(self):
        if self.enabledButton[5] is False:
            return
        if self.mode == 0: # 편집 -> 배치 완료
            if self.size_select == 0: # 3x3 배치에서만 풀이 가능
                self.label5[4].setPixmap(self.qPixmapVar4[4][0])
                self.enabledButton[4] = True
            else:
                self.label5[4].setPixmap(self.qPixmapVar4[4][1])
                self.enabledButton[4] = False
            self.label5[5].setPixmap(self.qPixmapVar4[5][2])
            self.enabledButton[5] = True
            self.label5[6].setPixmap(self.qPixmapVar4[6][1])
            self.enabledButton[6] = False
            self.label5[7].setPixmap(self.qPixmapVar4[7][1])
            self.enabledButton[7] = False
            self.label6[0].setPixmap(self.qPixmapVar5[0][1])
            self.label6[1].setPixmap(self.qPixmapVar5[1][1])
            self.enabledButton[8] = False
            self.label9[0].setPixmap(self.qPixmapVar8[0][1])
            self.enabledButton[9] = False
            self.closeSetting()
            self.mode = 1
            #self.opacity_effect.setOpacity(0)
            self.alpha.move(0, 901)
            self.select = -1
            self.puzzle_origin = self.solveThread.puzzleCopy(self, self.puzzle)
            if self.size_select == 0:
                self.label4.setPixmap(self.qPixmapVar2[2])
                self.inst_num = 2
            else:
                self.label4.setPixmap(self.qPixmapVar2[6])
                self.inst_num = 6

            self.inst_num = 2
        elif self.mode == 1: # 배치완료 -> 편집
            self.unComplete()
            self.label5[0].setPixmap(self.qPixmapVar4[0][1])
            self.enabledButton[0] = False
            self.label5[1].setPixmap(self.qPixmapVar4[1][1])
            self.enabledButton[1] = False
            self.label5[2].setPixmap(self.qPixmapVar4[2][1])
            self.enabledButton[2] = False
            self.label5[3].setPixmap(self.qPixmapVar4[3][1])
            self.enabledButton[3] = False
            self.label5[4].setPixmap(self.qPixmapVar4[4][1])
            self.enabledButton[4] = False
            self.label5[5].setPixmap(self.qPixmapVar4[5][0])
            self.enabledButton[5] = True
            self.label5[6].setPixmap(self.qPixmapVar4[6][0])
            self.enabledButton[6] = True
            if self.size_select != 0:
                self.label5[7].setPixmap(self.qPixmapVar4[7][1])
                self.enabledButton[7] = False
            else:
                self.label5[7].setPixmap(self.qPixmapVar4[7][0])
                self.enabledButton[7] = True
            self.label6[0].setPixmap(self.qPixmapVar5[0][0])
            self.label6[1].setPixmap(self.qPixmapVar5[1][0])
            self.enabledButton[8] = True
            self.label9[0].setPixmap(self.qPixmapVar8[0][0])
            self.enabledButton[9] = True
            self.way = []
            self.way_pos = 0
            self.move_count = 0
            self.mode = 0
            self.label4.setPixmap(self.qPixmapVar2[1])
            self.inst_num = 1
        elif self.can_move == 1: # 해답 -> 배치완료
            if self.solvethread is not None:
                self.solvethread.stop_working()
                self.solvethread = None
            self.unComplete()
            self.label5[0].setPixmap(self.qPixmapVar4[0][1])
            self.enabledButton[0] = False
            self.label5[1].setPixmap(self.qPixmapVar4[1][1])
            self.enabledButton[1] = False
            self.label5[2].setPixmap(self.qPixmapVar4[2][1])
            self.enabledButton[2] = False
            self.label5[3].setPixmap(self.qPixmapVar4[3][1])
            self.enabledButton[3] = False
            self.label5[4].setPixmap(self.qPixmapVar4[4][0])
            self.enabledButton[4] = True
            self.label5[5].setPixmap(self.qPixmapVar4[5][2])
            self.enabledButton[5] = True
            self.label5[6].setPixmap(self.qPixmapVar4[6][1])
            self.enabledButton[6] = False
            self.label5[7].setPixmap(self.qPixmapVar4[7][1])
            self.enabledButton[7] = False
            self.mode = 1
            #self.opacity_effect.setOpacity(0)
            self.alpha.move(0, 901)
            self.select = -1
            self.puzzle = self.solveThread.puzzleCopy(self, self.puzzle_origin)
            for i in range(self.psize):
                for j in range(self.psize):
                    self.label[self.puzzle[i][j]].move(self.adjustResolution(96) + j * self.adjustResolution(self.temp_size1), self.adjustResolution(96) + i * self.adjustResolution(self.temp_size1))
                    self.label[self.puzzle[i][j]].setPixmap(self.qPixmapVar[0][self.puzzle[i][j]])
            if self.size_select == 0:
                self.label4.setPixmap(self.qPixmapVar2[2])
                self.inst_num = 2
            else:
                self.label4.setPixmap(self.qPixmapVar2[6])
                self.inst_num = 6

    def getH(self, puzzle): # h(n) 값을 반환
        count = 0
        for i in range(self.psize ** 2):
            if i == self.psize ** 2 - self.psize:
                continue
            a = self.findPiece(i, puzzle)
            count += abs(a[0] - int(i/self.psize)) + abs(a[1] - i%self.psize)
        return count

    def swap(self, x, y, puzzle):  # x와 y의 위치를 서로 바꿈
        temp = puzzle[x[0]][x[1]]
        puzzle[x[0]][x[1]] = puzzle[y[0]][y[1]]
        puzzle[y[0]][y[1]] = temp

    def findPiece(self, x, puzzle):  # x번째 퍼즐의 위치를 반환
        for i in range(self.psize):
            if x in puzzle[i]:
                return [i, puzzle[i].index(x)]
            else:
                continue
        return -1

    def puzzle_shuffle(self, puzzle):
        for i in range(self.psize):
            for j in range(self.psize):
                puzzle[i][j] = i * self.psize + j
        blank = self.findPiece(self.psize ** 2 - self.psize, puzzle)
        block = None
        if self.psize == 3:
            limit = random.randrange(10,20)
        elif self.psize == 4:
            limit = random.randrange(30,40)
        elif self.psize == 5:
            limit = random.randrange(70,80)
        while True:
            h = self.getH(puzzle)
            if h >= limit:
                break
            temp_list = []
            if blank[0] < self.psize - 1: # 아래로 이동
                temp = [blank[0] + 1, blank[1]]
                if not temp == block:
                    temp_list.append(temp)
            if blank[0] > 0:  # 위로 이동
                temp = [blank[0] - 1, blank[1]]
                if not temp == block:
                    temp_list.append(temp)
            if blank[1] < self.psize - 1:  # 오른쪽으로 이동
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
            self.unComplete()
            self.movethread = self.imageMoveThread(self.way[self.way_pos + 1:], self.label)
            self.movethread.timeout.connect(self.thread_imageMove)
            self.label5[0].setPixmap(self.qPixmapVar4[0][1])
            self.enabledButton[0] = False
            self.label5[1].setPixmap(self.qPixmapVar4[1][0])
            self.enabledButton[1] = True
            self.label5[2].setPixmap(self.qPixmapVar4[2][1])
            self.enabledButton[2] = False
            self.label5[3].setPixmap(self.qPixmapVar4[3][1])
            self.enabledButton[3] = False
            self.label5[5].setPixmap(self.qPixmapVar4[5][5])
            self.enabledButton[5] = False
            self.label5[1].setPixmap(self.qPixmapVar4[1][0])
            self.enabledButton[1] = True

    def stopButton(self):
        if self.enabledButton[1] is True and self.movethread is not None:
            self.movethread.stop_working()
            self.label5[0].setPixmap(self.qPixmapVar4[0][0])
            self.enabledButton[0] = True
            self.label5[1].setPixmap(self.qPixmapVar4[1][1])
            self.enabledButton[1] = False
            self.label5[2].setPixmap(self.qPixmapVar4[2][0])
            self.enabledButton[2] = True
            self.label5[3].setPixmap(self.qPixmapVar4[3][0])
            self.enabledButton[3] = True
            self.label5[5].setPixmap(self.qPixmapVar4[5][4])
            self.enabledButton[5] = True

    def previousButton(self):
        if self.enabledButton[2] is True and self.way_pos > 0 and self.can_move == 1 and self.movethread2 is None:
            self.unComplete()
            self.way_pos -= 1
            temp = self.way[self.way_pos]
            self.way_pos -= 1
            self.thread_imageMove(temp)

    def nextButton(self):
        if self.enabledButton[3] is True and self.way_pos < len(self.way) - 1 and self.can_move == 1 and self.movethread2 is None:
            self.unComplete()
            self.way_pos += 1
            temp = self.way[self.way_pos]
            self.way_pos -= 1
            self.thread_imageMove(temp)

    def randomButton(self):
        if self.enabledButton[6] is False:
            return

        self.puzzle = []
        for i in range(self.psize):
            self.puzzle.append([])
            for j in range(self.psize):
                self.puzzle[i].append(i * self.psize + j)

        self.puzzle_shuffle(self.puzzle)
        for i in range(self.psize):
            for j in range(self.psize):
                self.label[self.puzzle[i][j]].move(self.adjustResolution(96) + j * self.adjustResolution(self.temp_size1), self.adjustResolution(96) + i * self.adjustResolution(self.temp_size1))
                self.label[self.puzzle[i][j]].setPixmap(self.qPixmapVar[0][self.puzzle[i][j]])
        self.assign_list = [1] * (self.psize ** 2)
        self.label4.setPixmap(self.qPixmapVar2[1])
        self.inst_num = 1
        self.label5[5].setPixmap(self.qPixmapVar4[5][0])
        self.enabledButton[5] = True

    def solveButton(self):
        if self.enabledButton[4] is False:
            return
        self.unComplete()
        self.mode = 2
        self.solvethread = self.solveThread()
        self.solvethread.threadEvent.connect(self.solveThreadControl)
        self.solvethread.set(self.puzzle, self.answer)
        self.label5[4].setPixmap(self.qPixmapVar4[4][2])
        self.enabledButton[4] = False
        self.solvethread.start()

    @pyqtSlot(list, int)
    def solveThreadControl(self, way, move_count):
        if move_count == -1:
            self.label4.setPixmap(self.qPixmapVar2[4])
            self.inst_num = 4
            self.label5[4].setPixmap(self.qPixmapVar4[4][4])
            self.enabledButton[4] = False
            self.mode = 1
        else:
            self.way = way
            self.way_pos = 0
            self.move_count = move_count
            self.label5[0].setPixmap(self.qPixmapVar4[0][0])
            self.enabledButton[0] = True
            self.label5[1].setPixmap(self.qPixmapVar4[1][1])
            self.enabledButton[1] = False
            self.label5[2].setPixmap(self.qPixmapVar4[2][0])
            self.enabledButton[2] = True
            self.label5[3].setPixmap(self.qPixmapVar4[3][0])
            self.enabledButton[3] = True
            self.label5[4].setPixmap(self.qPixmapVar4[4][3])
            self.enabledButton[4] = False
            self.label5[5].setPixmap(self.qPixmapVar4[5][4])
            self.enabledButton[5] = True
            self.label4.setPixmap(self.qPixmapVar2[3])
            self.inst_num = 3
        self.solvethread.stop_working()
        self.solvethread = None

    class solveThread(QThread):
        threadEvent = pyqtSignal(list, int)
        stop = 0

        def swap(self, x, y, puzzle):  # x와 y의 위치를 서로 바꿈
            temp = puzzle[x[0]][x[1]]
            puzzle[x[0]][x[1]] = puzzle[y[0]][y[1]]
            puzzle[y[0]][y[1]] = temp

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

    def diffImage(self, img1, img2):
        image1 = img1
        image2 = img2

        data = image2.shape
        width = int(data[1] / 3)
        height = int(data[0] / 3)

        croppedImage = []
        for row in range(3):
            croppedImage.append([])
            for col in range(3):
                croppedImage[row].append(
                    image2.copy()[0 + row * height: 0 + (row + 1) * height, 0 + col * width: 0 + (col + 1) * width])

        # 히스토그램 비교 (histo_compare.py)

        imgs = [image1] + croppedImage[0] + croppedImage[1] + croppedImage[2]
        hists = []
        for i, img in enumerate(imgs):
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            hist = cv2.calcHist([hsv], [0, 1], None, [180, 256], [0, 180, 0, 256])
            cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
            hists.append(hist)

        query = hists[0]
        flag = cv2.HISTCMP_CORREL

        ret_list = []
        for i, (hist, img) in enumerate(zip(hists[1:], imgs[1:])):
            ret_list.append(cv2.compareHist(query, hist, flag))

        return ret_list

    def maxIndex(self, temp_list):
        maxindex = 0
        for i in range(len(temp_list)):
            if temp_list[i] > temp_list[maxindex]:
                maxindex = i
        return maxindex

    def clipboardButton(self, obj):
        if self.enabledButton[7] is False:
            return
        try:
            with TemporaryDirectory() as tmpdirname:
                temp = ImageGrab.grabclipboard()
                temp.save(tmpdirname + 'testImageFile.png', 'PNG')
                image2 = cv2.imread(tmpdirname + 'testImageFile.png', cv2.IMREAD_UNCHANGED)
        except:
            self.label4.setPixmap(self.qPixmapVar2[5])
            self.inst_num = 5
            return

        data = []
        max_ret_list = []
        for puzzleNum in range(6):
            ret_list = []
            max_ret = 0
            for i in range(9):
                if i == 6:
                    ret_list.extend([0, 0, 0, 0, 0, 0, 0, 0, 0])
                    continue
                image1 = cv2.imread(
                    "PuzzleImage/Img" + str(puzzleNum + 1) + "/Piece" + str(puzzleNum + 1) + "_" + str(i + 1) + ".png",
                    cv2.IMREAD_UNCHANGED)
                temp = self.diffImage(image1, image2)
                ret_list.extend(temp)
                if max_ret < max(ret_list):
                    max_ret = max(ret_list)
            data.append(ret_list)
            max_ret_list.append(max_ret)

        puzzleNum = self.maxIndex(max_ret_list)
        ret_list = data[puzzleNum]

        self.assign_list = [0, 0, 0, 0, 0, 0, 1, 0, 0]
        puzzle_list = [6, 6, 6, 6, 6, 6, 6, 6, 6]
        for i in range(len(ret_list)) :
            retIndex = self.maxIndex(ret_list)
            num = int(retIndex / 9)
            pos = retIndex % 9
            if puzzle_list[pos] == 6 and not num in puzzle_list:
                puzzle_list[pos] = num
                self.assign_list[num] = 1
            ret_list[retIndex] = -100
            if sum(self.assign_list) > 8:
                break

        # 퍼즐 선택
        self.puzzle_select = puzzleNum + 1
        self.puzzleSelect(self.label6[0])

        self.puzzle = [[0, 1, 2], [3, 4, 5], [6, 7, 8]]

        for i in range(9):
            num = puzzle_list[i]
            if num == 6:
                continue
            pos_x = self.findPiece(num, self.puzzle)
            pos_y = [int(i/3), i%3]
            self.swap(pos_x, pos_y, self.puzzle)
            self.assign_list[i] = 1

        for i in range(3):
            for j in range(3):
                if self.assign_list[i*3+j]:
                    self.label[self.puzzle[i][j]].move(self.adjustResolution(96) + j * self.adjustResolution(self.temp_size1), self.adjustResolution(96) + i * self.adjustResolution(self.temp_size1))
                    self.label[self.puzzle[i][j]].setPixmap(self.qPixmapVar[0][self.puzzle[i][j]])
                else:
                    self.label[self.puzzle[i][j]].setPixmap(self.emptyPixmap)

        if self.allIsOn():
            self.label4.setPixmap(self.qPixmapVar2[1])
            self.inst_num = 1
            self.label5[5].setPixmap(self.qPixmapVar4[5][0])
            self.enabledButton[5] = True
        else:
            self.label4.setPixmap(self.qPixmapVar2[0])
            self.inst_num = 0
            self.label5[5].setPixmap(self.qPixmapVar4[5][1])
            self.enabledButton[5] = False

if __name__ == "__main__" :

    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    app.exec_()
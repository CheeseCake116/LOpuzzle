#puzzle = [[2, 8, 1], [6, 5, 4], [3, 7, 0]] #6은 공백조각
puzzle = [[6, 1, 4],[2, 8, 5],[7, 3, 0]]
answer = [[0, 1, 2], [3, 4, 5], [6, 7, 8]]
#puzzle = []
confirmed = [] # 확정된 조각

def init(): # 데이터 입력
    data = input("퍼즐 순서 : ").split()
    for row in range(3):
        temp = []
        for piece in range(3):
            temp.append(int(data[row * 3 + piece]))
        puzzle.append(temp)

def findPiece(x, puzzle): #x번째 퍼즐의 위치를 반환
    for i in range(3):
        if x in puzzle[i]:
            return [i, puzzle[i].index(x)]
        else:
            continue
    return -1

def posInfo(*args, puzzle): #pos 위치에 있는 퍼즐 번호를 반환
    if len(args) > 1:
        return puzzle[args[0]][args[1]]
    else:
        return puzzle[int(args[0] / 3)][args[0] % 3]

def swap(x, y, puzzle): # x와 y의 위치를 서로 바꿈
    temp = puzzle[x[0]][x[1]]
    puzzle[x[0]][x[1]] = puzzle[y[0]][y[1]]
    puzzle[y[0]][y[1]] = temp

#최단거리 리스트
def OLD_getWayTo(x, dest, block=[]): #x가 현재 위치에서 dest까지 가는 경우의 수를 도출하는 함수. block은 걸림돌 위치의 리스트
    stack = [[x]]
    confirmed_way = []
    while(True):
        if len(stack) == 0: # 모든 경우의 수를 테스트한 경우
            return confirmed_way # 결과를 반환하고 탈출

        way = stack.pop(0) # 아니라면 스택에서 길을 하나 뽑아옴
        x = way[-1] # x의 현재 위치는 스택의 마지막 요소
        if x == dest: # 현재 x 위치가 목적지라면
            confirmed_way.append(way) # confirmed_way에 현재 길을 추가. pop했으므로 이 길은 다시 검사하지 않음
            continue # 다음 길을 검사

        if x[0] < dest[0]: # x가 목적지보다 위에 있는 경우
            temp = [x[0] + 1, x[1]] # x가 이동할 목적지를 저장해두는 변수
            if not temp in block: # temp 위치에 걸림돌이 없다면
                stack.append(way + [temp]) # way + temp를 다시 stack에 추가

        elif x[0] > dest[0]:  # x가 목적지보다 아래에 있는 경우
            temp = [x[0] - 1, x[1]]
            if not temp in block:
                stack.append(way + [temp])

        if x[1] < dest[1]:  # x가 목적지보다 왼쪽에 있는 경우
            temp = [x[0], x[1] + 1]
            if not temp in block:
                stack.append(way + [temp])

        elif x[1] > dest[1]:  # x가 목적지보다 아래에 있는 경우
            temp = [x[0], x[1] - 1]
            if not temp in block:
                stack.append(way + [temp])

#최단거리 리스트
def getWayTo(x, dest, block=[]): #x가 현재 위치에서 dest까지 가는 경우의 수를 도출하는 함수. block은 걸림돌 위치의 리스트
    shortest = 10 # 최소 이동 횟수
    stack = [[x]]
    confirmed_way = []
    while(True):
        if len(stack) == 0: # 모든 경우의 수를 테스트한 경우
            return confirmed_way # 결과를 반환하고 탈출

        way = stack.pop(0) # 아니라면 스택에서 길을 하나 뽑아옴
        x = way[-1] # x의 현재 위치는 스택의 마지막 요소
        if x == dest: # 현재 x 위치가 목적지라면
            confirmed_way.append(way) # confirmed_way에 현재 길을 추가. pop했으므로 이 길은 다시 검사하지 않음
            if shortest > len(way): # 이동 횟수가 shortest보다 작으면
                shortest = len(way) # shortest 갱신
            continue # 다음 길을 검사
        elif shortest <= len(way): # 도착을 못했는데 shortest보다 이동횟수가 같거나 크면
            continue # 포기

        if x[0] < 2: # 밑으로 이동
            temp = [x[0] + 1, x[1]] # x가 이동할 목적지를 저장해두는 변수
            if not temp in block and not temp in way: # temp 위치에 걸림돌이 없다면, 이미 지나간 길이 아니라면
                stack.append(way + [temp]) # way + temp를 다시 stack에 추가

        if x[0] > 0: # 위로 이동
            temp = [x[0] - 1, x[1]]
            if not temp in block and not temp in way:
                stack.append(way + [temp])

        if x[1] < 2:  # 오른쪽으로 이동
            temp = [x[0], x[1] + 1]
            if not temp in block and not temp in way:
                stack.append(way + [temp])

        if x[1] > 0:  # 왼쪽으로 이동
            temp = [x[0], x[1] - 1]
            if not temp in block and not temp in way:
                stack.append(way + [temp])

def puzzleCopy(puzzle):
    temp = []
    for i in range(3):
        temp.append(puzzle[i].copy())
    return temp

def moveBlankTo(dest, puzzle, block=[]):
    blank = findPiece(6, puzzle)
    way_list = getWayTo(blank, dest, block=block)  # 가짓수를 받아옴
    confirmed_puzzle = []
    move_count = []
    for way in way_list:
        move_count.append(len(way) - 1)
        temp_puzzle = puzzleCopy(puzzle)
        while(len(way) > 1):  # 목적지에 도착할 때까지
            From = way.pop(0)
            To = way[0]
            swap(From, To, temp_puzzle)
        confirmed_puzzle.append(temp_puzzle)  # 결과를 추가하고 종료
    return [confirmed_puzzle, move_count]

def movePieceTo(x, dest, puzzle, block=[]):
    way_list = getWayTo(x, dest, block=block)  # 가짓수를 받아옴
    confirmed_puzzle = []
    confirmed_move = []
    for way in way_list:
        stack_puzzle = [puzzleCopy(puzzle)] # moveBlankTo 함수로 나오는 퍼즐 가짓수가 여러가지기 때문에 스택으로 관리
        move_count = [0]
        while (len(way) > 1):  # 목적지에 도착할 때까지
            From = way.pop(0) # [row, col]
            To = way[0] # [row, col]
            moveBlankCases = []
            moveBlankCounts = []

            for i in range(len(stack_puzzle)):
                moveBlankDatas = moveBlankTo(To, stack_puzzle[i], [From]+block)
                moveBlankCases.extend(moveBlankDatas[0])
                for j in range(len(moveBlankDatas[1])):
                    moveBlankDatas[1][j] += move_count[i]
                moveBlankCounts.extend(moveBlankDatas[1])

            for i in range(len(moveBlankCases)):
                swap(From, To, moveBlankCases[i])
                moveBlankCounts[i] += 1

            stack_puzzle = moveBlankCases
            move_count = moveBlankCounts
        confirmed_puzzle.extend(stack_puzzle)  # 결과를 추가하고 종료
        confirmed_move.extend(move_count)
    return [confirmed_puzzle, confirmed_move]

def getH(puzzle, answer):
    count = 0
    for i in range(9):
        a = findPiece(i, puzzle)
        b = findPiece(i, answer)
        count += abs(a[0] - b[0]) + abs(a[1] - b[1])
    return count

def OLD_solve(puzzle, answer):
    stack = [[puzzle, 0, []]] # 현재 퍼즐 상태, 이동 횟수, 이전 공백 위치
    h_stack = [getH(puzzle, answer)]
    for case in range(10):
        temp_stack = []
        h_list = []
        minH = min(h_stack)

        while len(stack) > 0:
            temp_puzzle, move_count, block = stack.pop(0)
            x = findPiece(6, temp_puzzle)
            if x[0] < 2:  # 밑으로 이동
                temp = [x[0] + 1, x[1]]  # x가 이동할 목적지를 저장해두는 변수
                if not temp in block:  # temp 위치에 걸림돌이 없다면
                    moved_puzzle = puzzleCopy(temp_puzzle)  # 원본 퍼즐을 복사
                    swap(x, temp, moved_puzzle)  # 복사된 퍼즐을 이동
                    h_list.append(getH(moved_puzzle, answer))
                    temp_stack.append([moved_puzzle, move_count + 1, [x]])  # 결과를 임시 스택에 저장

            if x[0] > 0:  # 위로 이동
                temp = [x[0] - 1, x[1]]
                if not temp in block:
                    moved_puzzle = puzzleCopy(temp_puzzle)
                    swap(x, temp, moved_puzzle)
                    h_list.append(getH(moved_puzzle, answer))
                    temp_stack.append([moved_puzzle, move_count + 1, [x]])

            if x[1] < 2:  # 오른쪽으로 이동
                temp = [x[0], x[1] + 1]
                if not temp in block:
                    moved_puzzle = puzzleCopy(temp_puzzle)
                    swap(x, temp, moved_puzzle)
                    h_list.append(getH(moved_puzzle, answer))
                    temp_stack.append([moved_puzzle, move_count + 1, [x]])

            if x[1] > 0:  # 왼쪽으로 이동
                temp = [x[0], x[1] - 1]
                if not temp in block:
                    moved_puzzle = puzzleCopy(temp_puzzle)
                    swap(x, temp, moved_puzzle)
                    h_list.append(getH(moved_puzzle, answer))
                    temp_stack.append([moved_puzzle, move_count + 1, [x]])

        minH = min(h_list)
        for i in range(len(h_list)):
            if h_list[i] == minH:
                stack.append(temp_stack[i])
        print(stack, minH)
        if minH == 0:
            break


def solve(puzzle, answer):
    stack = [[puzzle, 0, [], [findPiece(6, puzzle)]]]  # 현재 퍼즐 상태, 이동 횟수, 이전 공백 위치
    closed = []
    h_stack = [getH(puzzle, answer) + 0]
    while True:
        #temp_stack = []
        #h_list = []

        minH = min(h_stack)
        for i in range(len(h_stack)):
            if h_stack[i] == minH:
                temp_puzzle, move_count, block, way = stack.pop(i)
                h_stack.pop(i)
                break

        if temp_puzzle == answer:
            print(way)
            print(move_count)
            return temp_puzzle

        closed.append(temp_puzzle)

        x = findPiece(6, temp_puzzle)
        if x[0] < 2:  # 밑으로 이동
            temp = [x[0] + 1, x[1]]  # x가 이동할 목적지를 저장해두는 변수
            if not temp in block:  # temp 위치에 걸림돌이 없다면
                moved_puzzle = puzzleCopy(temp_puzzle)  # 원본 퍼즐을 복사
                swap(x, temp, moved_puzzle)  # 복사된 퍼즐을 이동
                if not moved_puzzle in closed or not moved_puzzle in stack:
                    h_stack.append(getH(moved_puzzle, answer) + move_count + 1)
                    stack.append([moved_puzzle, move_count + 1, [x], way+[temp]])  # 결과를 임시 스택에 저장

        if x[0] > 0:  # 위로 이동
            temp = [x[0] - 1, x[1]]
            if not temp in block:
                moved_puzzle = puzzleCopy(temp_puzzle)
                swap(x, temp, moved_puzzle)
                if not moved_puzzle in closed or not moved_puzzle in stack:
                    h_stack.append(getH(moved_puzzle, answer) + move_count + 1)
                    stack.append([moved_puzzle, move_count + 1, [x], way+[temp]])

        if x[1] < 2:  # 오른쪽으로 이동
            temp = [x[0], x[1] + 1]
            if not temp in block:
                moved_puzzle = puzzleCopy(temp_puzzle)
                swap(x, temp, moved_puzzle)
                if not moved_puzzle in closed or not moved_puzzle in stack:
                    h_stack.append(getH(moved_puzzle, answer) + move_count + 1)
                    stack.append([moved_puzzle, move_count + 1, [x], way+[temp]])

        if x[1] > 0:  # 왼쪽으로 이동
            temp = [x[0], x[1] - 1]
            if not temp in block:
                moved_puzzle = puzzleCopy(temp_puzzle)
                swap(x, temp, moved_puzzle)
                if not moved_puzzle in closed or not moved_puzzle in stack:
                    h_stack.append(getH(moved_puzzle, answer) + move_count + 1)
                    stack.append([moved_puzzle, move_count + 1, [x], way+[temp]])

solve(puzzle, answer)

'''
puzzles = movePieceTo([0,0], [2,2], puzzle)
resultSet = [[], []]
for i in range(len(puzzles[0])):
    print(puzzles[0][i], puzzles[1][i])
    if puzzles[1][i] == min(puzzles[1]):
        resultSet[0].append(puzzles[0][i])
        resultSet[1].append(puzzles[1][i])

print(resultSet)
'''

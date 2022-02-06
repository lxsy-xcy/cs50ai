"""
Tic Tac Toe Player
"""

from logging import exception
import copy
import math

X = "X"
O = "O"
EMPTY = None
INF = 9999


def initial_state():
    """
    Returns starting state of the board.
    """
    return [[EMPTY, EMPTY, EMPTY],
            [EMPTY, EMPTY, EMPTY],
            [EMPTY, EMPTY, EMPTY]]


def player(board):
    """
    Returns player who has the next turn on a board.
    """
    cntx=0
    cnto=0
    for i in board:
        for j in i:
            if j == X:
                cntx+=1
            elif j ==O:
                cnto+=1
    if cntx==cnto:
        return X
    else:
        return O


def actions(board):
    """
    Returns set of all possible actions (i, j) available on the board.
    """
    action=set()
    for i in range(3):
        for j in range(3):
            if board[i][j]==EMPTY:
                action.add((i,j))
    return action

def result(board, action):
    """
    Returns the board that results from making move (i, j) on the board.
    """
    x = action[0]
    y = action[1]
    if board[x][y] != EMPTY:
        raise Exception("action error!")

    ans = copy.deepcopy(board)
    ans[x][y]=player(board)
    return ans

def winner(board):
    # row
    for i in range(3):
        if board[i][0]==board[i][1] and board[i][1]==board[i][2]:
            return board[i][0]

    # col
    for j in range(3):
        if board[0][j]==board[1][j] and board[1][j]==board[2][j]:
            return board[0][j]

    # dia
    if board[0][0]==board[1][1] and board[1][1]==board[2][2]:
        return board[0][0]

    if board[2][0]==board[1][1] and board[1][1]==board[0][2]:
        return board[2][0]

    return None


def terminal(board):
    """
    Returns True if game is over, False otherwise.
    """
    if winner(board):
        return True
    for row in board:
        for cube in row:
            if cube == EMPTY:
                return False
    return True


def utility(board):
    if winner(board) == X:
        return 1
    elif winner(board)==O:
        return -1
    elif winner(board)==EMPTY:
        return 0

def getmaxscore(board):
    if terminal(board):
        return (utility(board),None)
    else:
        maxvalue = -INF
        maxaction = None
        Actions = actions(board)
        for action in Actions:
            Result = result(board,action)
            if getminscore(Result)[0] > maxvalue:
                maxvalue = getminscore(Result)[0]
                maxaction = action
        return (maxvalue,maxaction)

def getminscore(board):
    if terminal(board):
        return (utility(board),None)
    else:
        minvalue = INF
        minaction = None
        Actions = actions(board)
        for action in Actions:
            Result = result(board,action)
            if getmaxscore(Result)[0] < minvalue:
                minvalue = getmaxscore(Result)[0]
                minaction = action
        return (minvalue,minaction)


def minimax(board):
    if(terminal(board)):
        return None
    
    # want max(now we are x)
    if player(board) == X:
        return getmaxscore(board)[1]

    # want min
    if player(board) == O:
        return getminscore(board)[1]


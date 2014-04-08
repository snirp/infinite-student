"""<
# This code file follows the SLiP (Semi-Literate Programming) annotation convention.
# specification at: ...
title:      "AI for playing Tic-Tac-Toe"
author:     Roy Prins
published:  17-04-2014
status:     project
progress:   90
summary: >
    An exploration of several algorithms to play a game of Tic-Tac-Toe against
    a human opponent. Notably the Negamax algorithm is used.
>"""

"""<
#Tic-Tac-Toe

In the game of tic-tac-toe two players take turns to occupy a cell of a 3x3 grid with
their marks (O's or X's). The player who manages to place three marks in a row, wins
the game. If both players play a perfect game, the result will always be a draw.
More on [wikipedia](http://en.wikipedia.org/wiki/Tic-tac-toe).

##The goal

The goal is to create a program that enables a user to compete against an artificial
intelligence. Additionally we could input any given position and receive the best move
in return. The program should be able to achieve this in a number of different ways:

1. AI_random: Random move: not the best, but useful for testing and for letting your kids play.
2. AI_search: Search the game tree for the optimal solution.
3. AI_rules: Follow a set of strategic rules to arrive at a move.


##The grid

The positions will be internally handled as list of 9 items of different types:

+ `0` for a blank cell;
+ `1` for a human player occupied cell;
+ `-1` for acomputer occupied cell.

The position can be initiated as a simple string.
The `parse_grid()` function makes sure that it is parsed into a list with the correct values.
It will soon be explained why it is preferred to use `1` rather than `"X"` internally.

The user will be presented with the current board and a grid of possible moves, numbered
1 to 9. The `ask_input()` function will call `print_grid()` twice to pretty-print the
respective grids.

>"""

# Handle the markings as integers internally
blank = 0
human = 1
computer = -1


def parse_grid(position):
    """Parse the position-iterable into a list of length 9"""
    # Mapping of possible marks:
    markmap = {'X': 1,  'x': 1,     # accepted human marks
               'O': -1, 'o': -1,    # accepted computer marks
               ' ': 0,  '.': 0}     # accpeted blanks
    grid = [markmap[c] for c in position if c in markmap]
    return grid

"""
For the grid [ 1, 0, 1, 0, -1, 0, 0, -1, 1 ]
the printed playboard should resemble:

X | . | X
- + - + -
. | O | .
- + - + -
. | O | X

And the legal moves are presented as:

  | 2 |
- + - + -
4 |   | 6
- + - + -
7 |   |

"""


def print_grid(grid, boardprint=True):
    # Transform the grid into a 3x3 board:
    board = ([grid[i*3:i*3+3] for i in range(3)])
    divider = '- + - + -'
    # Reversed mapping for markings:
    printmap = {1: 'X', -1: 'O', 0: '.'}
    for i in range(len(board)):
        if boardprint:
            # we are printing a playboard.
            print(' | '.join(printmap[c] for c in board[i]))
        else:
            # we are printing legal moves or value analysis
            print(' | '.join(str(c) for c in board[i]))
        if i < 2:
            print(divider)


def ask_input(grid):
    """print current grid and legal moves"""
    print_grid(grid)
    print("\nPossible moves:")
    options = list(grid)  # create a grid of legal moves
    for n in range(9):
        if options[n] == blank:
            options[n] = str(n+1)
        else:
            options[n] = " "
    # print legal moves
    print_grid(options, boardprint=False)


"""<
##Winning at Tic-Tac-Toe

The tic-tac-toe grid has 8 'winlines': the horizontals, the diagonals and the verticals.
If a player occupies all three cells on any winline, he is the winner.

Some of the AI algorithms rely heavily on frequently trying to determine
the winner. This means that writing an effective `winner()` algorithm really pays off.
To speed up our algorithm we make the following choices:

+ We only determine whether the current players is a winner. Since you can
only win by making a move, there is no need to check for a win by the opponent.
+ We handle the player markings internally as -1 and +1 instead of "X" and "O".
This allows for faster comparisons. As an added benefit, it allows for easier
switching between the players.
+ If a player has less than 3 markings on the board, there is no need to
further check whether he is a winner.
+ When checking the lines, we `break` when we first encouter a marking that
does not equal the player's. This eliminates the need to check the remaining
cells on that line.

Further optimizations are conceivable, but not (yet) implemented:

+ Consider the most recent move: determining the winner will only be relevant
for the lines on which the most recent move took place. We now evaluate all 8
lines, but that can be reduced to an avarage of 2.8 lines per move.
+ Define the winlines as slices rather than tuples of indices.

>"""

# tuples of grid-indices that define the winning lines
winlines = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # horizontals
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # verticals
    (0, 4, 8), (2, 4, 6), )           # diagonals


def winner(grid, player):
    """Verify whether the player is a winner"""
    if grid.count(player) < 3:
        return False  # no winner with less than 3 moves
    # Check all winlines.
    for line in winlines:
        for c in line:
            # Break at the first incorrect occurence
            if grid[c] != player:
                break
        else:
            return True
    return False

"""<
##Initialize play

The player can be either human: ( `'X'` or `-1` ), or computer ( `'O'` or `-1` ). We
can start from a blank grid or we can initiate a custom position. This
is handled in the `play()` function, which will also check for a premature
win by either side.

##Taking turns

The `player_move()` function is a recursive function that lets the human
and the computer player alternate turns. After each turn, we evaluate
if it was the winning move or whether a draw is reached. Since we check
for a win first, it is safe to assume that any full board equates a draw.

The human player's move is found by asking for user input as decribed earlier
under 'The grid'. The computer move can be found by calling one of the `ai_...()`
functions, which we will describe in more detail.
>"""


def play(human_first=True, position="."*9):
    """
    Initialize play
      - human_first: this is used to determine the first move;
      - position: by default a blank grid is initiated.
    """
    grid = parse_grid(position)
    # Check for unplayable grids
    if winner(grid, human):
        print("You won without playing.")
    if winner(grid, computer):
        print("The computer won without playing.")
    if human_first:
        player = human
    else:
        player = computer
    player_move(grid, player)


def player_move(grid, player):
    """Recursive function to handle player moves"""
    if grid.count(blank) == 0:
        print("It is a draw.")
    if player == human:
        # Print the current board and legl moves:
        ask_input(grid)
        while True:
            move = input("Your move: ")
            try:
                move = int(move)
            except ValueError:
                print('Choose a number.')
                continue
            if grid[move-1] == blank:
                break
            else:
                print('That square is taken.')
        grid[move-1] = player
        if winner(grid, player):
            print("winning move!")
        return player_move(grid, computer)
    else:
        # change to a different "ai_" function if needed.
        move = ai_search(grid, computer)
        print("Computer plays: "+str(move+1))
        grid[move] = computer
        if winner(grid, computer):
            print("Oops, the computer won")
        return player_move(grid, human)



"""<

##Artificial intelligence

All the artificial intelligence algorithms take a grid and
return the optimal move. We have three different algorithms:

+ Random `ai_random()`: this returns a random rather than optimal move. Usually
easy to beat and useful to check the other algorithms.
+ Negamax `ai_search()` and `move_value()`: follows a simplified Minimax algorithm.
+ Rule-based `ai_rules()`: follows simple strategy rules.

>"""


def ai_random(grid):
    """Simple AI that plays a random move"""
    import random
    moves = []
    for i in range(len(grid)):
        if grid[i] == blank:
            moves.append(i)
    move = random.choice(moves)
    return move

"""<

##Negamax algorithm

Negamax is a special case of the so called Minimax algorithms. They all rely on
building a "game tree" of every possible move. For any position that is on the
end of the tree, a "value" is calculated. A good position (for the active player)
is indicated by a high value; a bad position by a low value.

When we assume that both the player and his opponent play a perfect game, we can
propagate these values up the tree. In a perfect game, the opponent makes the move
that minimizes the outcome for the player. The player will choose the move that
maximizes the outcome. Hence Mini-Max.

![Minimax tree]({{ url_for('static', filename='images/minimax-tree.png') }})

The image above is an example that calculates a fixed number of moves. The various
node values are calculated by evaluating the strength, using heuristics. This is
more typical for games of higher complexity, such as chess, go or reversi.

Because tic-tac-toe is much less complex than aformentioned games, we can calculate
all possible positions. That means our tree will end in a win or a draw every time.

##Implement the Negamax

Wikipedia has the [following](http://en.wikipedia.org/wiki/Negamax) to say about implementing
a negamax algorithm:

> [...] The value of a position to player A in such a game is the negation of the value
to player B. Thus, the player on move looks for a move that maximizes the negation
of the value of the position resulting from the move: this successor position must
by definition have been valued by the opponent. The reasoning of the previous sentence
works regardless of whether A or B is on move. This means that a single procedure
can be used to value both positions.

We can implement this with a simple recursive function `value()`. For a given move, it
calculates the values of all the opponents moves. From this, it takes the best one (max).
We can then negate the value to arrive at the player's value.

This is calculated recursively until the return values are reached:

+ `2` for the winnning move
+ `1` for a draw.

A player cannot make a move that directly causes a loss, so we can safely disregard that option.

The function `ai_search()` simply calls the `value()` function for all possible moves and
returns the (first) move of highest value.

There is room for optimization: when one of the opponent moves results in a win, there
is no point in calculating the remaining moves since we found the max-value already.
This is what so-called 'pruning' is for and it is easy enough to
[implement](http://en.wikipedia.org/wiki/Negamax#NegaMax_with_Alpha_Beta_Pruning).

>"""


def value(grid, player, move):
    """A negamax-style recursive depth first search."""
    grid = grid[:]
    grid[move] = player
    if winner(grid, player):
        return 2
    if grid.count(blank) == 0:
        return 1
    values = []
    for i in range(9):
        if grid[i] == blank:
            values.append(value(grid, -player, i))
    # assume the opponent's best move (max) and reverse it.
    return 2-max(values)


def ai_search(grid, player):
    """Brute force AI that picks the first optimal move"""
    movevalues = []
    for i in range(9):
        if grid[i] != blank:
            movevalues.append(-1)
        else:
            movevalues.append(value(grid, player, i))
    # the highest valued move
    return movevalues.index(max(movevalues))


"""<
##Rule-based strategy

Try and find the best move, using heuristics. We will follow the
 [tic-tac-toe strategy guide](http://en.wikipedia.org/wiki/Tic-tac-toe#Strategy) from wikipedia:

1. Win: If the player has two in a row, they can place a third to get three in a row.
2. Block: If the opponent has two in a row, the player must play the third themself to block the opponent.
3. Fork: Create an opportunity where the player has two threats to win (two non-blocked lines of 2).
4. Blocking an opponent's fork:
    1. Option 1: The player should create two in a row to force the opponent into defending, as long as it doesn't result in them creating a fork. For example, if "X" has a corner, "O" has the center, and "X" has the opposite corner as well, "O" must not play a corner in order to win. (Playing a corner in this scenario creates a fork for "X" to win.)
    2. Option 2: If there is a configuration where the opponent can fork, the player should block that fork.
5. Center: A player marks the center. (If it is the first move of the game, playing on a corner gives "O" more opportunities to make a mistake and may therefore be the better choice; however, it makes no difference between perfect players.)
6. Opposite corner: If the opponent is in the corner, the player plays the opposite corner.
7. Empty corner: The player plays in a corner square.
8. Empty side: The player plays in a middle square on any of the 4 sides.

The algorithm below does a naive implementation of this strategy guide. It suffers
from some mistakes and sections of code that repeat each other. That makes it easy
to beat, so have a go.

To do a proper implementation, you would have to look two steps ahead and the
algorithm becomes rather complex. More complex than I am willing to pursue at
this moment.
>"""


def ai_rules(grid, player):
    # 1: make a winning move
    for line in winlines:
        gridline = [grid[x] for x in line]
        if gridline.count(player) == 2 \
                and gridline.count(blank) == 1:
            return line[gridline.index(blank)]
    # 2: prevent winning move
    for line in winlines:
        gridline = [grid[x] for x in line]
        if gridline.count(-player) == 2 \
                and gridline.count(blank) == 1:
            return line[gridline.index(blank)]
    # 3: create fork
    # This is not testing for 'pure' forks: they can overlap!
    for i in range(len(grid)):
        if grid[i] == blank:
            grid = grid[:]  # copy grid
            grid[i] = player
            forkcount = 0
            for line in winlines:
                gridline = [grid[x] for x in line]

                if gridline.count(player) == 2 \
                        and gridline.count(blank) == 1:
                    forkcount += 1
                    if forkcount == 2:
                        print(forkcount)
                        return i
    # 4: block a fork
    for i in range(len(grid)):
        if grid[i] == blank:
            grid = grid[:]  # copy grid
            grid[i] = -player
            forkcount = 0
            for line in winlines:
                gridline = [grid[x] for x in line]
                if gridline.count(-player) == 2 \
                        and gridline.count(blank) == 1:
                    print("fork")
                    forkcount += 1
                    if forkcount == 2:
                        return i
    # 5: play center
    if grid[4] == blank:
        return 4
    # 6: play opposite corner
    opposite_corners = ((0, 8), (8, 0), (2, 6), (6, 2))
    for p in opposite_corners:
        if grid[p[0]] == -player and grid[p[1]] == blank:
            return p[1]
    # 7: play corner
    corners = (0, 2, 6, 8)
    for c in corners:
        if grid[c] == blank:
            return c
    # 8: return random move (officially middle sides)
    return ai_random(grid)



"""<
##Testing the game

Let's pit our artificial intelligence against 100 monkies. Every
monkey gets to start and will make random moves. As we stated, a
perfect player will never lose a game. Not even against 100 consecutive
monkies.

In the `monkeytest()` function, the monkies make use of `ai_random()`
for their moves. The function returns the number of times that our
algortihm wins and draws against the monkeys. It has yet to fail the
monkeytest :)
>"""


def monkeytest(ai=ai_search, monkies=10):
    """Test the ai against random opponents"""
    wins = 0
    draws = 0

    for _ in range(monkies):
        grid = [0]*9
        while True:
            grid[ai_random(grid)] = 1
            if winner(grid, 1):
                print("Oops, the monkies won.")
            grid[ai(grid, -1)] = -1
            if winner(grid, -1):
                wins += 1
                break
            elif grid.count(0) == 0:
                draws += 1
                break
    print('wins: %d' % wins)
    print('draws: %d' % draws)


"""<
##Run the game

You can start the game from any position. Uncomment the `monkeytest`
line to start the testing.


>"""

pos1 =  '...' \
        '...' \
        '...'

pos2 =  '.OX' \
        '.X.' \
        'O..'

if __name__ == "__main__":

    # uncomment the next line to run the tests:
    #monkeytest(monkies=20)

    play(position=pos1)


"""<
#References

The following resources have been helpful in creating this code:

+ [Creating a chess engine, by Martin Knudsen](http://www.chess.com/blog/zaifrun/creating-a-chess-engine-part-2)
+ [Stackoverflow discussion on tac-tac-toe](http://stackoverflow.com/questions/125557/what-algorithm-for-a-tic-tac-toe-game-can-i-use-to-determine-the-best-move-for_)
+ [General algorithm for tic-tac-toe by Aaron Gordon](http://rowdy.msudenver.edu/~gordona/cs1050/progs/tictactoermccsc.pdf)
+ [Sudoku solver, by Peter Norvig](http://norvig.com/sudoku.html)
+ [Wikipedia article on Tic-Tac-Toe](http://en.wikipedia.org/wiki/Tic-tac-toe)
+ [Wikipedia article on Game Theory](http://en.wikipedia.org/wiki/Game_theory)
+ [An Introduction to Game Tree Algorithms, by Hamed Ahmadi](http://www.hamedahmadi.com/gametree/)
>"""


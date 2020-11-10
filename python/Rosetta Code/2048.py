#!/usr/bin/env python3

import curses
from random import randrange, choice  # generate and place new tile
from collections import defaultdict

keys = '˄˂˅˃re'
actions = ['Up', 'Left', 'Down', 'Right', 'Restart', 'Exit']
letter_codes = [curses.KEY_UP, curses.KEY_LEFT, curses.KEY_DOWN, curses.KEY_RIGHT] + [ord(ch) for ch in keys[-2:]]
actions_dict = dict(zip(letter_codes, actions))



def transpose(field):
    return [list(row) for row in zip(*field)]


def invert(field):
    return [row[::-1] for row in field]


class GameField(object):
    def __init__(self, stdscr, height=4, width=4, win=2048):
        self.stdscr = stdscr
        self.height = height
        self.width = width
        self.win_value = win
        self.score = 0
        self.high_score = 0
        self.reset()

    def reset(self):
        if self.score > self.high_score:
            self.high_score = self.score
        self.score = 0
        self.field = [[0 for i in range(self.width)] for j in range(self.height)]
        self.spawn()
        self.spawn()

    def move(self, direction):
        def move_row_left(row):
            def tighten(row):  # squeese non-zero elements together
                new_row = [i for i in row if i != 0]
                new_row += [0 for i in range(len(row) - len(new_row))]
                return new_row

            def merge(row):
                pair = False
                new_row = []
                for i in range(len(row)):
                    if pair:
                        new_row.append(2 * row[i])
                        self.score += 2 * row[i]
                        pair = False
                    else:
                        if i + 1 < len(row) and row[i] == row[i + 1]:
                            pair = True
                            new_row.append(0)
                        else:
                            new_row.append(row[i])
                assert len(new_row) == len(row)
                return new_row

            return tighten(merge(tighten(row)))

        moves = {}
        moves['Left'] = lambda field: \
            [move_row_left(row) for row in field]
        moves['Right'] = lambda field: \
            invert(moves['Left'](invert(field)))
        moves['Up'] = lambda field: \
            transpose(moves['Left'](transpose(field)))
        moves['Down'] = lambda field: \
            transpose(moves['Right'](transpose(field)))

        if direction in moves:
            if self.move_is_possible(direction):
                self.field = moves[direction](self.field)
                self.spawn()
                return True
            else:
                return False

    def is_win(self):
        return any(any(i >= self.win_value for i in row) for row in self.field)

    def is_gameover(self):
        return not any(self.move_is_possible(move) for move in actions)

    def draw(self):
        help_string = " ".join([f"({key}){action}" for key, action in zip(keys, actions)])
        gameover_string = '          GAME OVER'
        win_string      = '          YOU WIN!'

        def cast(string):
            self.stdscr.addstr(string + '\n')

        def draw_hor_separator():
            top = '┌' + ('┬──────' * self.width + '┐')[1:]
            mid = '├' + ('┼──────' * self.width + '┤')[1:]
            bot = '└' + ('┴──────' * self.width + '┘')[1:]
            separator = defaultdict(lambda: mid)
            separator[0], separator[self.height] = top, bot
            if not hasattr(draw_hor_separator, "counter"):
                draw_hor_separator.counter = 0
            cast(separator[draw_hor_separator.counter])
            draw_hor_separator.counter += 1

        def draw_row(row):
            cast(''.join('|{: ^5} '.format(num) if num > 0 else '|      ' for num in row) + '|')

        self.stdscr.clear()
        cast('SCORE: ' + str(self.score))
        if 0 != self.high_score:
            cast('HIGH SCORE: ' + str(self.high_score))
        for row in self.field:
            draw_hor_separator()
            draw_row(row)
        draw_hor_separator()
        if self.is_win():
            cast(win_string)
        else:
            if self.is_gameover():
                cast(gameover_string)
            else:
                cast(help_string)

    def spawn(self):
        new_element = 4 if randrange(100) > 89 else 2
        (i, j) = choice([(i, j) for i in range(self.width) for j in range(self.height) if self.field[i][j] == 0])
        self.field[i][j] = new_element

    def move_is_possible(self, direction):
        def row_is_left_movable(row):
            def change(i):  # true if there'll be change in i-th tile
                if row[i] == 0 and row[i + 1] != 0:  # Move
                    return True
                if row[i] != 0 and row[i + 1] == row[i]:  # Merge
                    return True
                return False

            return any(change(i) for i in range(len(row) - 1))

        check = {}
        check['Left'] = lambda field: \
            any(row_is_left_movable(row) for row in field)

        check['Right'] = lambda field: \
            check['Left'](invert(field))

        check['Up'] = lambda field: \
            check['Left'](transpose(field))

        check['Down'] = lambda field: \
            check['Right'](transpose(field))

        if direction in check:
            return check[direction](self.field)
        else:
            return False

    def get_user_action(self):
        char = "N"
        while char not in actions_dict:
            char = self.stdscr.getch()
        return actions_dict[char]

def main(stdscr):
    curses.use_default_colors()
    game_field = GameField(stdscr)
    state_actions = {}  # Init, Game, Win, Gameover, Exit

    def init():
        game_field.reset()
        return 'Game'

    state_actions['Init'] = init

    def not_game(state):
        game_field.draw()
        action = game_field.get_user_action()
        responses = defaultdict(lambda: state)
        responses['Restart'], responses['Exit'] = 'Init', 'Exit'
        return responses[action]

    state_actions['Win'] = lambda: not_game('Win')
    state_actions['Gameover'] = lambda: not_game('Gameover')

    def game():
        game_field.draw()
        action = game_field.get_user_action()
        if action == 'Restart':
            return 'Init'
        if action == 'Exit':
            return 'Exit'
        if game_field.move(action):  # move successful
            if game_field.is_win():
                return 'Win'
            if game_field.is_gameover():
                return 'Gameover'
        return 'Game'

    state_actions['Game'] = game

    state = 'Init'
    while state != 'Exit':
        state = state_actions[state]()


curses.wrapper(main)

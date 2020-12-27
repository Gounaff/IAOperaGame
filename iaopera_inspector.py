import json
import logging
import os
import random
import socket
from logging.handlers import RotatingFileHandler
import math
import copy

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import protocol

host = "localhost"
port = 12000
# HEADERSIZE = 10

"""
set up fantom logging
"""
fantom_logger = logging.getLogger()
fantom_logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s :: %(levelname)s :: %(message)s", "%H:%M:%S")
# file
if os.path.exists("./logs/fantom.log"):
    os.remove("./logs/fantom.log")
file_handler = RotatingFileHandler('./logs/fantom.log', 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
fantom_logger.addHandler(file_handler)
# stream
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.WARNING)
fantom_logger.addHandler(stream_handler)

passages = [{1, 4}, {0, 2}, {1, 3}, {2, 7}, {0, 5, 8},
            {4, 6}, {5, 7}, {3, 6, 9}, {4, 9}, {7, 8}]
# ways for the pink character
pink_passages = [{1, 4}, {0, 2, 5, 7}, {1, 3, 6}, {2, 7}, {0, 5, 8, 9},
                 {4, 6, 1, 8}, {5, 7, 2, 9}, {3, 6, 9, 1}, {4, 9, 5},
                 {7, 8, 4, 6}]

def isalone(fantom_pos, game_state):
    count = 0
    for character in game_state['characters']:
        if character['position'] == fantom_pos:
            count += 1
    if count == 1:
        return True
    return False

def evalMove(game_state):
    score = 10
    for character in game_state['characters']:
    	if character['suspect'] == True:
    		score -= 1
    score += game_state['position_carlotta']
    if score >= 22:
    	score -= 10
    return score

def maxminminmax(colors, game_state, depth, alpha, beta):
    bestmove = 0
    bestcolor = ''
    analyzedCharacter = {}

    if depth == 0:
        score = evalMove(copy.deepcopy(game_state))
        #print(pad + str(score))
        return score, 0, ''
  
    if depth == 4 or depth == 1:
        maxEval = -math.inf
        for selectedColor in colors:
            newColors = colors[:]
            newColors.remove(selectedColor)
        
            possiblePath = update_possible_path(selectedColor, game_state)
            for path in possiblePath:
                for character in game_state['characters']:
                    if character['color'] == selectedColor:
                        character['position'] = path
                        break;

                eval_, move, nextcolor = maxminminmax(newColors, copy.deepcopy(game_state), depth-1, alpha, beta)

                if eval_ > maxEval:
                    maxEval = eval_
                    bestmove = path
                    bestcolor = selectedColor
                alpha = max(alpha, eval_)
                if beta <= alpha:
                    return maxEval, bestmove, bestcolor
        return maxEval, bestmove, bestcolor
    else:
        minEval = math.inf
        for selectedColor in colors:
            newColors = colors[:]
            newColors.remove(selectedColor)
        
        possiblePath = update_possible_path(selectedColor, game_state)
        for path in possiblePath:
            for character in game_state['characters']:
                if character['color'] == selectedColor:
                    character['position'] = path
                    break;

            eval_, move, nextcolor = maxminminmax(newColors, copy.deepcopy(game_state), depth-1, alpha, beta)

            if eval_ < minEval:
                minEval = eval_
                bestmove = path
                bestcolor = selectedColor
            beta = min(beta, eval_)
            if beta <= alpha:
                return minEval, bestmove, bestcolor
        return minEval, bestmove, bestcolor

def maxmaxmin(colors, game_state, depth, alpha, beta):
    bestmove = 0
    bestcolor = ''

    if depth == 0:
        return evalMove(copy.deepcopy(game_state)), 0, ''
  
    if depth != 1:
        maxEval = -math.inf
        for selectedColor in colors:
            newColors = colors[:]
            newColors.remove(selectedColor)
        
            possiblePath = update_possible_path(selectedColor, game_state)
            for path in possiblePath:
                for character in game_state['characters']:
                    if character['color'] == selectedColor:
                        character['position'] = path
                        break;

                eval, move, nextcolor = maxmaxmin(newColors, copy.deepcopy(game_state), depth-1, alpha, beta)
        
                if eval > maxEval:
                    maxEval = eval
                    bestmove = path
                    bestcolor = selectedColor
                alpha = max(alpha, eval)
                if beta <= alpha:
                    return maxEval, bestmove, bestcolor
        return maxEval, bestmove, bestcolor
    else:
        minEval = math.inf
        for selectedColor in colors:
            newColors = colors[:]
            newColors.remove(selectedColor)
        
            possiblePath = update_possible_path(selectedColor, game_state)
            for path in possiblePath:
                for character in game_state['characters']:
                    if character['color'] == selectedColor:
                        character['position'] = path
                        break;

                eval, move, nextcolor = maxmaxmin(newColors, copy.deepcopy(game_state), depth-1, alpha, beta)

                if eval < minEval:
                    minEval = eval
                    bestmove = path
                    bestcolor = selectedColor
                beta = min(beta, eval)
                if beta <= alpha:
                    return minEval, bestmove, bestcolor
        return minEval, bestmove, bestcolor

def selectNextMove(colors, game_state):
    chosenColor = ""

    if game_state['num_tour'] % 2 == 0:
        eval_, bestmove, chosenColor = maxminminmax(colors[:], game_state.copy(), len(colors), -math.inf, math.inf)
    else:
        eval_, bestmove, chosenColor = maxmaxmin(colors[:], game_state.copy(), len(colors), -math.inf, math.inf)
    return chosenColor, bestmove

def update_possible_path(charact, game_state):
    characters_in_room = [
        q for q in game_state['characters'] if q['position'] == charact['position']]
    number_of_characters_in_room = len(characters_in_room)
    available_rooms = list()
    available_rooms.append(get_adjacent_positions(charact, game_state))
    for step in range(1, number_of_characters_in_room):
        next_rooms = list()
        for room in available_rooms[step-1]:
            next_rooms += get_adjacent_positions_from_position(room, charact, game_state)
        available_rooms.append(next_rooms)
    final_rooms = []
    for rooms in available_rooms:
        final_rooms = final_rooms + list(set(rooms))
    final_rooms = list(set(final_rooms))
    return final_rooms
    
def get_adjacent_positions(charact, game):
    if charact['color'] == "pink":
        active_passages = pink_passages
    else:
        active_passages = passages
    return [room for room in active_passages[charact['position']] if set([room, charact['position']]) != set(game['blocked'])]


def get_adjacent_positions_from_position(position, charact, game):
    if charact['color'] == "pink":
        active_passages = pink_passages
    else:
        active_passages = passages
    return [room for room in active_passages[position] if set([room, position]) != set(game['blocked'])]



class Player():

    def __init__(self):
        self.end = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def connect(self):
        self.socket.connect((host, port))

    def reset(self):
        self.socket.close()

    def answer(self, question):
        # work
        data = question["data"]
        game_state = question["game state"]
        quest = question['question type']

        fantom_logger.debug("|\n|")
        fantom_logger.debug("fantom answers")
        fantom_logger.debug(f"question type ----- {question['question type']}")
        fantom_logger.debug(f"data -------------- {data}")

        if "power" in quest:
            if "grey" in quest and "move" not in quest:
                roomnb = 0
                maxroom = 10
                newmax = 0
                for i in range(0, 10):
                    newmax = 0
                    for character in game_state['characters']:
                        if character['position'] == i:
                            newmax += 1
                    if newmax < maxroom:
                        maxroom = newmax
                        roomnb = i
                response_index = data.index(roomnb)
            else:
                response_index = random.randint(0, len(data)-1)
        elif "character" in quest:
            self.answers = selectNextMove(data[:], game_state)
            response_index = 0
            for answer in data:
              if answer['color'] == self.answers[0]['color']:
                break
              response_index += 1
        elif "position" in quest:
            response_index = data.index(self.answers[1])

        # log
        
        fantom_logger.debug(f"response index ---- {response_index}")
        fantom_logger.debug(f"response ---------- {data[response_index]}")
        fantom_logger.debug(f" ----------- {game_state}")
        return response_index

    def handle_json(self, data):
        data = json.loads(data)
        response = self.answer(data)
        # send back to server
        bytes_data = json.dumps(response).encode("utf-8")
        protocol.send_json(self.socket, bytes_data)

    def run(self):

        self.connect()

        while self.end is not True:
            received_message = protocol.receive_json(self.socket)
            if received_message:
                self.handle_json(received_message)
            else:
                print("no message, finished learning")
                self.end = True


p = Player()

p.run()

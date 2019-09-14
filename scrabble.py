"""
implementation of solution research is from the below article:

@article{Appel1988TheWF,
  title={The World's Fastest Scrabble Program},
  author={Andrew W. Appel and Guy J. Jacobson},
  journal={Commun. ACM},
  year={1988},
  volume={31},
  pages={572-578}
}

doi 10.1145/42411.42420

https://sci-hub.tw/10.1145/42411.42420

"""
import itertools
import json
import os.path
import random
import time
import logging
from collections import OrderedDict
from copy import deepcopy
from datetime import datetime
from typing import Generator, Iterator, List, Dict, Set, Optional, Union, NamedTuple, Tuple

import hug
# import line_profiler
import zmq
from hug import interface
from marshmallow import fields, Schema, ValidationError, validates, validates_schema, \
    post_load, pre_dump, post_dump
from marshmallow.validate import OneOf, Range, Length

from dictionary import Trie, Mask, MaskItem, WordCouple

# required since hug deals with http status as string and not as integer
HTTP_STATUS_CODES = {
    100: "100 Continue",
    101: "101 Switching Protocols",
    102: "102 Processing",

    200: "200 OK",
    201: "201 Created",
    202: "202 Accepted",
    203: "203 Non-authoritative Information",
    204: "204 No Content",
    205: "205 Reset Content",
    206: "206 Partial Content",
    207: "207 Multi-Status",
    208: "208 Already Reported",
    226: "226 IM Used",

    300: "300 Multiple Choices",
    301: "301 Moved Permanently",
    302: "302 Found",
    303: "303 See Other",
    304: "304 Not Modified",
    305: "305 Use Proxy",
    307: "307 Temporary Redirect",
    308: "308 Permanent Redirect",

    400: "400 Bad Request",
    401: "401 Unauthorized",
    402: "402 Payment Required",
    403: "403 Forbidden",
    404: "404 Not Found",
    405: "405 Method Not Allowed",
    406: "406 Not Acceptable",
    407: "407 Proxy Authentication Required",
    408: "408 Request Timeout",
    409: "409 Conflict",
    410: "410 Gone",
    411: "411 Length Required",
    412: "412 Precondition Failed",
    413: "413 Payload Too Large",
    414: "414 Request-URI Too Long",
    415: "415 Unsupported Media Type",
    416: "416 Requested Range Not Satisfiable",
    417: "417 Expectation Failed",
    418: "418 I'm a teapot",
    421: "421 Misdirected Request",
    422: "422 Unprocessable Entity",
    423: "423 Locked",
    424: "424 Failed Dependency",
    426: "426 Upgrade Required",
    428: "428 Precondition Required",
    429: "429 Too Many Requests",
    431: "431 Request Header Fields Too Large",
    444: "444 Connection Closed Without Response",
    451: "451 Unavailable For Legal Reasons",
    499: "499 Client Closed Request",

    500: "500 Internal Server Error",
    501: "501 Not Implemented",
    502: "502 Bad Gateway",
    503: "503 Service Unavailable",
    504: "504 Gateway Timeout",
    505: "505 HTTP Version Not Supported",
    506: "506 Variant Also Negotiates",
    507: "507 Insufficient Storage",
    508: "508 Loop Detected",
    510: "510 Not Extended",
    511: "511 Network Authentication Required",
    599: "599 Network Connect Timeout Error",
}

JSON_INDENT = 4

LETTER_MULTIPLIER_SET = [
    1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1,
    1, 1, 1, 1, 1, 3, 1, 1, 1, 3, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 2, 1, 2, 1, 1, 1, 1, 1, 1,
    2, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 2,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 3, 1, 1, 1, 3, 1, 1, 1, 3, 1, 1, 1, 3, 1,
    1, 1, 2, 1, 1, 1, 2, 1, 2, 1, 1, 1, 2, 1, 1,
    1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1,
    1, 1, 2, 1, 1, 1, 2, 1, 2, 1, 1, 1, 2, 1, 1,
    1, 3, 1, 1, 1, 3, 1, 1, 1, 3, 1, 1, 1, 3, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    2, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 2,
    1, 1, 1, 1, 1, 1, 2, 1, 2, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 3, 1, 1, 1, 3, 1, 1, 1, 1, 1,
    1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1,
]

WORD_MULTIPLIER_SET = [
    3, 1, 1, 1, 1, 1, 1, 3, 1, 1, 1, 1, 1, 1, 3,
    1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1,
    1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1,
    1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1,
    1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    3, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 3,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1,
    1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1,
    1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1,
    1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1,
    3, 1, 1, 1, 1, 1, 1, 3, 1, 1, 1, 1, 1, 1, 3,
]

SUPPORTED_LANGUAGES = {"FR", "EN"}

PLAY_MODE_SET = {"auto", "manual"}  # different possible mode selectable for a player

# possible return code from Game.play_xxx methods
PLAY_RC_SET = {"played",  # regular play was performed
               "skip",  # skip this play no tile change requested
               "change"}  # skip this play - request change of all letters

PLAY, SKIP, CHANGE = "1", "2", "3"

DICT_SERVER_IP_ADDRESS = "127.0.0.1"

DICT_SERVER_TCP_PORT = "5555"

# profile = line_profiler.LineProfiler()

dict_object = None  # provision for global variable hosting either a Trie object or a DictionaryServer object

# -------------------------------------------------------
#                       SET LOGGING
# -------------------------------------------------------

# set-up logger before anything - two  handlers : one on console, the other one on file
formatter = logging.Formatter("%(asctime)s :: %(funcName)s :: %(levelname)s :: %(message)s")

handler_file = logging.FileHandler("scrabble.log", mode="a", encoding="utf-8")  # TODO implement name and rotation
handler_console = logging.StreamHandler()

handler_file.setFormatter(formatter)
handler_console.setFormatter(formatter)

handler_file.setLevel(logging.DEBUG)
handler_console.setLevel(logging.DEBUG)

logger = logging.getLogger("dictionary")
logger.setLevel(logging.DEBUG)
logger.addHandler(handler_file)
logger.addHandler(handler_console)

# -------------------------------------------------------
#                      END SET LOGGING
# -------------------------------------------------------

# LANGUAGE CLOSURE
"""
En français, il y a 102 jetons (dans la première édition du jeu, il n'y avait pas de jokers, et le jeu ne contenait 
donc que 100 jetons). Les diacritiques ne sont pas pris en compte :

0 point : Joker ×2 (appelés en français jokers ou lettres blanches)
1 point : E ×15, A ×9, I ×8, N ×6, O ×6, R ×6, S ×6, T ×6, U ×6, L ×5
2 points : D ×3, M ×3, G ×2
3 points : B ×2, C ×2, P ×2
4 points : F ×2, H ×2, V ×2
8 points : J ×1, Q ×1
10 points : K ×1, W ×1, X ×1, Y ×1, Z ×1

ENGLISH
2 blank tiles (scoring 0 points)
1 point: E ×12, A ×9, I ×9, O ×8, N ×6, R ×6, T ×6, L ×4, S ×4, U ×4
2 points: D ×4, G ×3
3 points: B ×2, C ×2, M ×2, P ×2
4 points: F ×2, H ×2, V ×2, W ×2, Y ×2
5 points: K ×1
8 points: J ×1, X ×1
10 points: Q ×1, Z ×1
"""


def character_value_closure(lang):
    # TODO add parameter checks

    character_value_dict = {
        'EN': {
            'E': 1,
            'A': 1,
            'I': 1,
            'O': 1,
            'N': 1,
            'R': 1,
            'T': 1,
            'L': 1,
            'S': 1,
            'U': 1,
            'D': 2,
            'G': 2,
            'B': 3,
            'C': 3,
            'M': 3,
            'P': 3,
            'F': 4,
            'H': 4,
            'V': 4,
            'W': 4,
            'Y': 4,
            'K': 5,
            'J': 8,
            'X': 8,
            'Q': 10,
            'Z': 10,
            ' ': 0},
        'FR': {
            'E': 1,
            'A': 1,
            'I': 1,
            'N': 1,
            'O': 1,
            'R': 1,
            'S': 1,
            'T': 1,
            'U': 1,
            'L': 1,
            'D': 2,
            'M': 2,
            'G': 2,
            'B': 3,
            'C': 3,
            'P': 3,
            'F': 4,
            'H': 4,
            'V': 4,
            'J': 8,
            'Q': 8,
            'K': 10,
            'W': 10,
            'X': 10,
            'Y': 10,
            'Z': 10,
            ' ': 0},
    }
    language = lang  # TODO is it really needed

    def character_value(letter):
        # TODO add parameter checks
        return character_value_dict[language][letter]

    return character_value


def character_set_closure(lang):
    # TODO add parameter checks

    character_set_dict = {
        'FR': ['E', 'E', 'E', 'E', 'E', 'E', 'E', 'E', 'E', 'E', 'E', 'E', 'E', 'E', 'E',
               'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A',
               'I', 'I', 'I', 'I', 'I', 'I', 'I', 'I',
               'N', 'N', 'N', 'N', 'N', 'N',
               'O', 'O', 'O', 'O', 'O', 'O',
               'R', 'R', 'R', 'R', 'R', 'R',
               'S', 'S', 'S', 'S', 'S', 'S',
               'T', 'T', 'T', 'T', 'T', 'T',
               'U', 'U', 'U', 'U', 'U', 'U',
               'L', 'L', 'L', 'L', 'L',
               'D', 'D', 'D',
               'M', 'M', 'M',
               'G', 'G',
               'B', 'B',
               'C', 'C',
               'P', 'P',
               'F', 'F',
               'H', 'H',
               'V', 'V',
               'J', 'Q', 'K', 'W', 'X', 'Y', 'Z',
               ' ', ' '
               ],
        'EN': ['E', 'E', 'E', 'E', 'E', 'E', 'E', 'E', 'E', 'E', 'E', 'E',
               'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A',
               'I', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'I',
               'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O',
               'N', 'N', 'N', 'N', 'N', 'N',
               'R', 'R', 'R', 'R', 'R', 'R',
               'T', 'T', 'T', 'T', 'T', 'T',
               'L', 'L', 'L', 'L',
               'S', 'S', 'S', 'S',
               'U', 'U', 'U', 'U',
               'D', 'D', 'D', 'D',
               'G', 'G', 'G',
               'B', 'B',
               'C', 'C',
               'M', 'M',
               'P', 'P',
               'F', 'F',
               'H', 'H',
               'V', 'V',
               'W', 'W',
               'Y', 'Y',
               'K', 'J', 'Q', 'X', 'Z',
               ' ', ' '
               ],
    }
    language = lang  # TODO is it really needed

    def character_set():
        # TODO add parameter checks
        return character_set_dict[language]

    return character_set


character_value = character_value_closure('FR')
character_set = character_set_closure('FR')


class TestHugException(Exception):  # TODO TEST TO BE REMOVE / IMPLEMENTED
    pass


class BoardCoordinateAlreadyOccupied(Exception):
    pass


class RequestedRackTilesChangeNotAllowed(Exception):
    pass


class DictionaryServerInternalError(Exception):
    pass


class DictionaryServerNotResponding(Exception):
    pass


class FirstPlayNotCoveringBoardCenter(Exception):
    pass


class CellUsedOrCrossWordInvalid(Exception):
    pass


class WordNotInDictionary(Exception):
    pass


class CrossWordNotInDictionary(Exception):
    pass


class ChangeRackLettersNotAllowed(Exception):
    pass


class AnchorTuple(NamedTuple):
    """Stored where to start mask scanning for an anchor position  - left_index is the index where to start scanning"""
    pos: 'Position'
    left_index: int


class CrossWord(NamedTuple):
    """Cross word tuple - index is the offset of the letter that is part of main word """
    word: 'Word'
    index_of_main_word_line: int


class JokerTuple(NamedTuple):
    """Store location and letter of the blank joker in a word that is built using it"""
    index: int
    letter: str


class PlayReturnTuple(NamedTuple):
    """Tuple returned by the play_auto and play_manual_old methods in Board()"""
    rc: str  # from PLAY_RC_SET
    letter_from_rack_list: List[str] = ""
    solution: Optional['Solution'] = None


class PlayItem(NamedTuple):
    """Store a play item by recording the tile-list and the solution chosen"""
    tile_list: List[str]
    solution: 'Solution'


class GameSummary(NamedTuple):
    """Store game summary metrics"""
    total_score: int
    nb_play: int
    word_list: List['Word']
    left_in_bag: List[str]
    player_score: Dict[str, int]


# -------------------------------------------------------
#
#               MARSHMALLOW SCHEMA CLASSES
#
# -------------------------------------------------------


class JokerTupleSchema(Schema):
    index = fields.Integer(validate=Range(0, 14))
    letter = fields.String(validate=Length(1))

    @post_dump
    def postdump_joker_tuple(self, data, **kwargs):
        return data

    @post_load
    def postload_joker_tuple(self, data, **kwargs):
        return JokerTuple(**data)


class DirectionSchema(Schema):
    down = fields.Boolean()

    @post_load
    def postload_direction(self, data, **kwargs):
        return Direction(orientation='Down' if data['down'] else 'Accross')


class PositionSchema(Schema):
    row = fields.Integer(validate=Range(0, 14))
    col = fields.Integer(validate=Range(0, 14))

    @post_load
    def make_pos(self, data, **kwargs):
        return Position(**data)


class WordSchema(Schema):
    text = fields.String()
    direction = fields.Nested(DirectionSchema())
    origin = fields.Nested(PositionSchema())

    @validates('text')
    def validate_text(self, value, **kwargs):
        if not value.isalpha():
            raise ValidationError("word must be composed of alphabetic letters only", 'word')
        if not value.isupper():
            raise ValidationError("word must be in upper case")
        if not (1 < len(value) < 16):
            raise ValidationError("word must have at least 2 letters and at max 15 letters ", 'word')

    @validates_schema
    def validate_word(self, data, **kwargs):
        if data['direction'].is_accross:
            if (data['origin'].col + len(data['text']) > 15):
                raise ValidationError("word out of board limits ", 'word')
        else:
            if (data['origin'].row + len(data['text']) > 15):
                raise ValidationError("word ou t of board limits ", 'word')

    @post_load
    def make_word(self, data, **kwargs):
        return Word(**data)


class ProposedWordSchema(Schema):
    word = fields.Nested(WordSchema(), required=True)
    word_mask = fields.String(required=True, allow_none=True)

    @validates_schema
    def validate_word_mask(self, data, **kwargs):
        if not data['word_mask']:
            return
        if not data['word_mask'].replace(" ", "").isalpha():
            raise ValidationError("word_mask must be alpha - enter a valid character string", 'word_mask')
        if not data['word_mask'].replace(" ", "").isupper():
            raise ValidationError("word_mask must be upper case", 'word_mask')
        if data['word_mask'].count(" ") > 2:
            raise ValidationError("Can't use more than two jokers - enter a valid character string", 'word_mask')
        if len(data['word_mask']) != len(data['word']):
            raise ValidationError("word and mask must be same length - enter a valid character string")
        if ["_" for a, b in zip(data['word'].text.upper(), data['word_mask'].upper()) if a != b and b != " "]:
            raise ValidationError("word and mask letters not matching - enter a valid character string", 'word_mask')

    @post_load
    def make_proposed_word(self, data, **kwargs):
        return ProposedWord(**data)


class CrossWordSchema(Schema):
    word = fields.Nested(WordSchema())
    index_of_main_word_line = fields.Integer(validate=Range(0, 14))

    @post_load
    def make_cross_word(self, data, **kwargs):
        return CrossWord(**data)


class BagOfTileSchema(Schema):
    bag = fields.List(fields.String(validate=Length(min=1, max=1)))
    is_full = fields.Boolean()
    is_empty = fields.Boolean()

    @post_load
    def make_bag(self, data, **kwargs):
        return BagOfTile(**data)


class RackSchema(Schema):
    tile_list = fields.List(fields.String())
    n = fields.Integer()

    @post_load
    def make_rack(self, data, **kwargs):
        return Rack(**data)


class BoardSchema(Schema):
    """marshmallow class for Board class"""
    board = fields.List(fields.String())
    board_values = fields.List(fields.Integer())
    word_set = fields.List(fields.Nested(WordSchema()))
    position_to_words = fields.Dict(keys=fields.Str(),
                                    values=fields.List(fields.Str()))
    nb_moves = fields.Integer()

    @pre_dump
    def pre_board(self, board_object, **kwargs):
        """make board instance json ready by remove sets and making dict key and values as strings"""
        board_new = Board()
        board_new.board = board_object.board.copy()
        board_new.board_values = board_object.board_values.copy()
        board_new.nb_moves = board_object.nb_moves
        board_new.word_set = list(board_object.word_set)  # set not jsonable
        # in order to be jsonable key and value of dict must be str or int - not functional objects
        board_new.position_to_words = {
            PositionSchema().dumps(position): [WordSchema().dumps(w) for w in word_list]
            for position, word_list in board_object.position_to_words.items()}

        return board_new

    @post_load
    def make_board(self, data, **kwargs):
        """Restore sets and dict to their internal types - see @pre-dump"""
        pos_2_words = {PositionSchema().loads(k): [WordSchema().loads(w_json) for w_json in v]
                       for k, v in data['position_to_words'].items()}

        return Board(data['board'],
                     data['board_values'],
                     set(data['word_set']),
                     pos_2_words,
                     data['nb_moves'])

    @validates('board')
    def validate_board(self, value, **kwargs):
        if any(not (
                (
                        (cell.isalpha() and cell.isupper())
                        or cell == " "
                )
                and len(cell) == 1
        )
               for cell in value
               ):
            raise ValidationError("Board must contain single letter in uppercase of blank")


class SolutionSchema(Schema):
    board = fields.Nested(BoardSchema())
    main_word = fields.Nested(WordSchema())
    cross_word_list = fields.List(fields.Nested(CrossWordSchema()))
    joker_set = fields.List(fields.Nested(JokerTupleSchema()))
    from_record = fields.Boolean()
    value = fields.Integer(required=False)
    score = fields.Integer(required=False)

    @pre_dump
    def pre_solution(self, solution_object, **kwargs):
        solution_new = deepcopy(solution_object)
        if not solution_object.from_record:
            solution_new.board = deepcopy(solution_object.board)
        solution_new.joker_set = list(solution_object.joker_set)
        return solution_new

    @post_load
    def make_solution(self, data, **kwargs):
        if not data['from_record']:
            sol = Solution(data['board'],
                           data['main_word'],
                           data['cross_word_list'],
                           set(data['joker_set']))
        else:
            sol = Solution(None,
                           data['main_word'],
                           data['cross_word_list'],
                           set(data['joker_set']),
                           True,
                           data['value'],
                           data['score']
                           )

        return sol


class PlayItemSchema(Schema):
    tile_list = fields.List(fields.String(validate=Length(1)))
    solution = fields.Nested(SolutionSchema(), required=False, allow_none=True)

    @post_load
    def make_play_item(self, data, **kwargs):
        return PlayItem(**data)


class TypeOfPlaySchema(Schema):
    type_of_play = fields.String(validate=OneOf([PLAY, SKIP, CHANGE]), required=True)


class ProposedPlaySchema(Schema):
    """Validate a proposed play and return a play instruction if no error is detected"""
    type_of_play = fields.Nested(TypeOfPlaySchema(), required=True)
    proposed_word = fields.Nested(ProposedWordSchema(), missing=None)

    @validates_schema
    def valid_proposed_play(self, data, **kwargs):
        # logger.debug("DATA FROM ProposedPlaySchema ==>", str(data))  # TODO DEBUG
        if data['type_of_play']['type_of_play'] == PLAY and data['proposed_word'] is None:
            raise ValidationError("Need to propose a word when instruction is to play")
        if data['type_of_play']['type_of_play'] == SKIP and data['proposed_word'] is not None:
            raise ValidationError("No word can be propose when instruction is to skip")
        if data['type_of_play']['type_of_play'] == CHANGE and data['proposed_word'] is not None:
            raise ValidationError("No word can be propose when instruction is to change letters")

    @post_load
    def postload_proposed_play_schema(self, pplay, **kwargs):
        """Validate the proposed play and return a play instruction if validated or return a ValidationError if not"""

        type_of_play = pplay['type_of_play']['type_of_play']

        if type_of_play == PLAY:
            raw_play_instruction = (type_of_play, pplay['proposed_word'])

        elif type_of_play == SKIP:
            raw_play_instruction = (type_of_play, None)

        elif type_of_play == CHANGE:
            raw_play_instruction = (type_of_play, None)

        else:
            raise ValidationError('type_of_play must be PLAY, SKIP or CHANGE')

        return raw_play_instruction


class GameSummarySchema(Schema):
    total_score = fields.Integer()
    nb_play = fields.Integer()
    word_list = fields.List(fields.Nested(WordSchema()))
    left_in_bag = fields.List(fields.Str())
    player_score = fields.Dict(keys=fields.Str(), values=fields.Integer())

    @post_load
    def make_game_summary(self, data, **kwargs):
        return GameSummary(**data)


class GameRecordSchema(Schema):
    play_list = fields.List(fields.Nested(PlayItemSchema()))
    game_summary = fields.Nested(GameSummarySchema(), allow_none=True)

    @post_load
    def make_game_record(self, data, **kwargs):
        return GameRecord(**data)


class GameSchema(Schema):
    bag = fields.Nested(BagOfTileSchema())
    board = fields.Nested(BoardSchema())
    game_record = fields.Nested(GameRecordSchema())
    player_dict = fields.Dict(keys=fields.String(), values=fields.Dict(keys=fields.String()))
    players_name_list = fields.List(fields.String())
    # play_list_history = fields.List(fields.String())
    play_list_history = fields.List(fields.Dict(keys=fields.String(), values=fields.String()))

    @pre_dump
    def pre_dump_game_schema(self, game_object, **kwargs):
        for player, dict_2nd_level in game_object.player_dict.items():
            dict_2nd_level['rack'] = RackSchema().dumps(dict_2nd_level['rack'])
        return game_object

    @post_load
    def make_game(self, data, **kwargs):
        for player, dict_2nd_level in data['player_dict'].items():
            dict_2nd_level['rack'] = RackSchema().loads(dict_2nd_level['rack'])

        return Game(**data)


# -------------------------------------------------------
#
#           END OF MARSHMALLOW SCHEMA CLASSES
#
# -------------------------------------------------------

class Direction():
    """
    Provide support for abstracting from directions on the board, so that across and down words can be treated same
    """

    def __init__(self, orientation: str):
        """Initialize a direction to DOWN or ACCROSS"""
        assert isinstance(orientation, str)
        assert orientation.isalpha()
        assert orientation.upper() in ["DOWN", "ACCROSS"]
        if orientation.upper() == "DOWN":
            self.down = True
        else:
            self.down = False

    @property
    def is_down(self) -> bool:
        """Return True if direction is Down - False otherwise"""
        if self.down:
            return True
        else:
            return False

    @property
    def is_accross(self) -> bool:
        """Return True if direction is Accross - False otherwise"""
        if self.down:
            return False
        else:
            return True

    def ortho(self) -> 'Direction':
        """Return the orthogonal direction to the object one Down if Accross and vice versa"""
        if self.down:
            return Direction("accross")
        else:
            return Direction("down")

    def __eq__(self, other: 'Direction') -> bool:
        return self.down == other.down

    def __ne__(self, other: "Direction") -> bool:
        return not (self == other)

    def __hash__(self) -> int:
        return hash(self.down)

    def __repr__(self) -> str:
        if self.down:
            return "Down"
        else:
            return "Accross"


class Position():
    """Support for storing and manipulating positions of letters on the board"""

    def __init__(self, row: int, col: int):
        """Initialize a position from its row and col - first position is zero"""
        assert type(row) == int
        assert type(col) == int
        assert 0 <= row <= 14
        assert 0 <= col <= 14
        self.row = row
        self.col = col

    @property
    def coordinate(self) -> tuple:
        """Return the (row, col) tuple for the object"""
        return (self.row, self.col)

    def __eq__(self, other) -> bool:
        return self.coordinate == other.coordinate

    def __ne__(self, other) -> bool:
        return not (self == other)

    def __hash__(self) -> int:
        return hash(self.coordinate)

    def next_accross(self) -> Generator['Position', None, None]:
        """Generator for next position to the object in accross direction"""
        if self.col == 14:
            raise StopIteration
        else:
            i = 1
            while self.col + i <= 14:
                yield Position(self.row, self.col + i)
                i += 1

    def prev_accross(self):
        """Generator for previous position to the object in accross direction"""

        if self.col == 0:
            raise StopIteration
        else:
            i = 1
            while self.col - i >= 0:
                yield Position(self.row, self.col - i)
                i += 1

    def next(self, direction: Direction):
        """Return next position in direction passed as parameter"""
        assert isinstance(direction, Direction)
        if direction.is_down:
            return self.next_down()
        else:
            return self.next_accross()

    def prev_down(self):
        """Generator for previous position to the object in down direction"""
        if self.row == 0:
            raise StopIteration
        else:
            i = 1
            while self.row - i >= 0:
                yield Position(self.row - i, self.col)
                i += 1

    def next_down(self):
        """Generator for next position to the object in down direction"""
        if self.row == 14:
            raise StopIteration
        else:
            i = 1
            while self.row + i <= 14:
                yield Position(self.row + i, self.col)
                i += 1

    def prev(self, direction: Direction):
        """Return previous position in direction passed as parameter"""
        assert isinstance(direction, Direction)
        if direction.is_down:
            return self.prev_down()
        else:
            return self.prev_accross()

    def is_filled(self, board: 'Board') -> bool:
        """Returns True if object position is empty on board object passed as parameter - False otherwise"""
        assert type(board) == Board

        try:
            board.position_to_words[self]
            return True
        except KeyError:
            return False

    def is_empty(self, board: 'Board') -> bool:
        """Returns True if object position is empty on board object passed as parameter - False otherwise"""
        return not self.is_filled(board)

    def __repr__(self) -> str:
        return str("(" + str(self.row) + ", " + str(self.col) + str(")"))


class Line():
    """
    Provide support for working seamlessly on line whether they are row or columns

    a Line instance is either a row or column.
    a Line object is made of the 15 positions of the line it does NOT contain tiles
    tiles/letters are stored in the Board class instances - not in Line
    """

    def __init__(self, direction: Direction, line_index: int):
        """Initialize a line object from its direction and index"""
        assert isinstance(direction, Direction)
        assert isinstance(line_index, int)
        assert 0 <= line_index <= 14
        self.direction = direction
        self.line_index = line_index

    def __getitem__(self, item: int) -> Position:
        """Return the position on board of the line index - position as a Position class instance """
        if item > 14 or item < 0:
            raise IndexError
        if self.direction.is_down:
            return Position(item, self.line_index)
        else:
            return Position(self.line_index, item)

    def __contains__(self, position: Position) -> bool:
        """Return True if position provided as parameter belongs to the line object - False Otherwise"""
        if not isinstance(position, Position):
            raise TypeError("in parameter must be of type Position")

        row, col = position.coordinate

        if self.direction.is_down:
            if col == self.line_index:
                return True
            else:
                return False
        else:
            if row == self.line_index:
                return True
            else:
                return False

    def __iter__(self) -> Iterator:
        """default iterator of the class returns positions in sequence - position as Position class instance"""
        self.n = 0
        return self

    def __next__(self) -> Position:
        """default iterator of the class returns next  positions in sequence - position as Position class instance"""
        if self.n <= 14:
            if self.direction.is_down:
                p = Position(self.n, self.line_index)
            else:
                p = Position(self.line_index, self.n)
            self.n += 1
            return p
        else:
            raise StopIteration

    def __eq__(self, other: 'Line') -> bool:
        return self.direction == other.direction and self.line_index == other.line_index

    def __ne__(self, other: 'Line') -> bool:
        return not (self == other)

    def __hash__(self) -> int:
        return hash((self.direction, self.line_index))

    def index_2_pos(self, index: int) -> Position:
        """Return position on board for the cell at index offset on the line"""
        assert isinstance(index, int)
        assert 0 <= index <= 14

        if self.direction.is_accross:
            return Position(self.line_index, index)
        else:
            return Position(index, self.line_index)

    def pos_2_index(self, pos: Position) -> int:
        """Return index on the line of the position provided as inputs"""
        assert isinstance(pos, Position)
        if self.direction.is_accross:
            assert pos.row == self.line_index
            return pos.col
        else:
            assert pos.col == self.line_index
            return pos.row

    def __repr__(self) -> str:
        if self.direction.is_down:
            string = "col="
        else:
            string = "row="
        string += str(self.line_index).zfill(2)

        return string


class Word():
    """
    Provide support for words on the board. Word object is made of a string, a direction and an origin position

    No link with a Board instance is provided even though a position is stored
    This is because this class is heavily used before choosing to actually put a word on the board and storing the
    board reference would have increase complexity and impacted performances with no added value
    """

    def __init__(self,
                 text: str,
                 direction: Direction,
                 origin: Position):
        """Initialise a word from string, direction and position of first letter on board"""
        assert text.isalpha()
        assert isinstance(direction, Direction)
        assert isinstance(origin, Position)
        self.text = text.upper()  # Trie is in upper
        self.direction = direction
        self.origin = origin  # Position(row, col)
        row, col = self.origin.coordinate
        try:
            if self.direction.is_accross:
                assert 0 < col + len(self.text) - 1 <= 14  # word are 2 letter min
            else:
                assert 0 < row + len(self.text) - 1 <= 14
        except AssertionError:
            logger.critical("word out of board edges: %s" % self.text + str(self.direction) + str(self.origin))
            raise AssertionError

    def positions(self) -> Generator[Position, None, None]:
        """
        Returns a generator providing the positions of the letters composing the word from start to end
        """
        if len(self.text) == 0:
            # yield None
            raise StopIteration
        else:
            if self.direction.is_accross:
                row_step, col_step = (0, 1)
            elif self.direction.is_down:
                row_step, col_step = (1, 0)
            else:
                raise ValueError
            for i in range(len(self.text)):
                yield Position(self.origin.row + row_step * i, self.origin.col + col_step * i)

    def is_subset(self, word: 'Word') -> bool:
        """
        Return True if word is contained within self - False if not

        contained means all positions of word are part of self
        in case word and self are equal True is returned
        """
        try:
            assert type(word) == Word
        except AssertionError as e:
            logger.critical(str(self) + str(word) + str(e))
            raise AssertionError

        pos_list = [p for p in self.positions()]
        for position in word.positions():
            if position not in pos_list:
                return False
        return True

    def intersection_index(self, other: 'Word') -> int:
        """Return index of letter that is at crossing with other - raise AssertionError if words are not crossing"""
        assert isinstance(other, __class__)
        assert self.direction == other.direction.ortho()

        if self.direction.is_accross:
            # ensure words are actually crossing
            assert self.origin.col <= other.origin.col < self.origin.col + len(self)
            assert other.origin.row + len(other) > self.origin.row
            return other.origin.col - self.origin.col
        else:
            assert self.origin.row <= other.origin.row < self.origin.row + len(self)
            assert other.origin.col + len(other) > self.origin.col
            return other.origin.row - self.origin.row

    def __eq__(self, other: 'Word') -> bool:
        return (self.text == other.text and
                self.direction == other.direction and
                self.origin == other.origin)

    def __ne__(self, other: 'Word') -> bool:
        return not (self == other)

    def __hash__(self) -> int:
        return hash(self.text + str(self.direction) + str(self.origin))

    def __len__(self) -> int:
        return len(self.text)

    def __iter__(self) -> Iterator:
        """Default iterator of the class returns letters of teh word in sequence"""
        self.n = 0
        return self

    def __next__(self) -> 'Word':
        """Return next letter in the word"""
        try:
            self.text[0]
        except LookupError:  # in case word is empty
            raise StopIteration
        else:
            if self.n <= len(self.text) - 1:
                ret = self.text[self.n]
                self.n += 1
                return ret
            else:
                raise StopIteration

    def __repr__(self) -> str:
        value = self.text
        value += " | " + str(self.direction)
        value += " | " + str(self.origin)
        return value


class ProposedWord:
    """Support proposal for a word in a play in manual mode - word and mask with jokers position if applicable"""

    def __init__(self, word: fields.Nested(WordSchema()), word_mask: Optional[str] = None):
        self.word = word
        self.word_mask = word_mask

    def __repr__(self):
        return str(self.word) + self.word_mask


class ProposedPlay:
    """Support proposal for a play in manual mode - ProposedWord and type of play => PLAY, SKIP, CHANGE"""

    def __init__(self, type_of_play: fields.Nested(TypeOfPlaySchema(), required=True),
                 proposed_word: fields.Nested(ProposedWordSchema(), required=True, allow_none=True) = None,
                 board: fields.Nested(BoardSchema(), required=True, allow_none=True) = None
                 ):
        self.type_of_play = type_of_play
        self.proposed_word = proposed_word
        self.board = board  # a proposed play is mandatorily with reference to a given board


@hug.local()
def proposed_word(word_struct: fields.Nested(ProposedWordSchema())):
    # TODO THIS IS FOR TESTING PURPOSE ONLY - TO BE REMOVED ?
    return str(ProposedWord(word=word_struct.word, word_mask=word_struct.word_mask))


class BagOfTile():
    """Provide support for the bag content and method to randomly pick tile and put them back in the bag"""

    def __init__(self, bag: Optional[List[str]] = None,
                 is_full: Optional[bool] = None,
                 is_empty: Optional[bool] = None):
        """Initialize a bag with full tile set"""

        if all(p is not None for p in (bag, is_full, is_empty)):
            self.bag = bag.copy()
            # assert all(c.isupper() for c in CHARACTER_SET if c != ' ')
            assert all(c.isupper() for c in character_set() if c != ' ')
            self.is_full = is_full
            self.is_empty = is_empty
        else:
            self.bag = character_set().copy()  # TODO copy is probably no longer necesary
            assert all(c.isupper() for c in character_set() if c != ' ')
            self.is_full = True
            self.is_empty = False

    def get_tile(self) -> str:
        """Provide a tile randomly chosen and remove it from the bag"""
        if self.is_full:
            self.is_full = False
        if len(self.bag) == 0:
            return ""  # bool("") == False
        else:
            char = random.choice(self.bag)
            self.bag.remove(char)
            if len(self.bag) == 0:
                self.is_empty = True
            return char

    def put_tile_back(self, char: str):
        """Put back a tile in the bag"""
        assert (type(char) == str) and (len(char) == 1)
        self.bag.append(char)
        if len(self.bag) == len(character_set()):
            self.is_full = True

    def __len__(self) -> int:
        """Returns the number of tile currently in the bag"""
        return len(self.bag)

    def __eq__(self, other):
        return True if (self.bag == other.bag
                        and self.is_full == other.is_full
                        and self.is_empty == other.is_empty) else False

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return "".join(self.bag) + "\n" + str(self.is_empty) + "\n" + str(self.is_full)


class Rack():
    """Provide support for handling rack of tiles

       Dependency on BagOfTile class
    """

    def __init__(self, tile_list: List[str] = None):
        """Initialize a rack - including filling it with tile from the bag passed as parameter"""
        self.tile_list = []
        if tile_list is None:
            self.tile_list = []
        else:
            assert isinstance(tile_list, list)
            assert all(isinstance(l, str) and len(l) == 1 for l in tile_list)
            assert len(tile_list) <= 7
            self.tile_list = tile_list

    def fill_rack(self, bag: BagOfTile):
        """Fill the rack with up to 7 tiles with tiles from the bag as much as bag content allows"""
        for _ in range(7 - len(self.tile_list)):
            ret = bag.get_tile()
            if ret:
                self.tile_list.append(ret)
            else:
                # TODO do something to state that bag is empty
                logger.warning('trying to fill rack from an empty bag')
                break

    def fill_rack_for_testing_purpose(self, string: str):
        """fill the rack with the string provided as parameter - bag content is ignored - this for testing purpose"""
        assert type(string) == str
        assert len(string) == 7
        assert type(string.replace(" ", "A").isalpha())
        assert type(string.replace(" ", "A").isupper())

        self.tile_list = []
        for c in string:
            self.tile_list.append(c)

    def remove_list_of_letters(self, letters_list: list) -> List[str]:
        """Remove letters from the rack - needed when a word is played on the board"""
        assert type(letters_list) == list
        assert all(l in self.tile_list for l in letters_list)

        for l in letters_list:
            self.tile_list.remove(l)

        return self.tile_list

    def change_all_letters(self, bag: BagOfTile):
        """Change all letters of the rack for new ones randomly picked from the bag - useful when no word can be found
        """
        # TODO SECURE CASE OF CHANGING LETTERS WHEN RACK HAS LESS THAN 7 LETTERS
        # put letters back in the bag
        if not bag.is_empty:
            for i in range(len(self.tile_list)):
                bag.put_tile_back(self.tile_list.pop())
            # and fill it with new set
            self.fill_rack(bag)

    def get_letters(self) -> str:
        """
        Return letters in the rack sorted by alphabetical order as a string

        :return: letters of the rack as a string
        """
        return "".join(sorted(self.tile_list))

    def __eq__(self, other):
        return self.tile_list == other.tile_list  # TODO THIS MIGTH NOT BE CORRECT ?

    def __ne__(self, other):
        return not (self == other)

    def __len__(self) -> int:
        return len(self.tile_list)

    def __iter__(self) -> Iterator:
        # defaullt iterator of the class returns letters in sequence
        self.n = 0
        return self

    def __next__(self) -> str:
        try:
            self.tile_list[0]
        except LookupError:  # in case word is empty
            raise StopIteration
        else:
            if self.n <= len(self.tile_list) - 1:
                ret = self.tile_list[self.n]
                self.n += 1
                return ret
            else:
                raise StopIteration

    def __repr__(self) -> str:
        return str(''.join(self.tile_list))


class Solution():
    """
    Store and manage an identified solution for the board - word, cross words, jokers and computation of value and score
    """

    def __init__(self,
                 board: Optional['Board'] = None,
                 main_word: Word = None,
                 cross_word_list: Optional[List[CrossWord]] = None,
                 joker_set: Optional[Set[JokerTuple]] = None,
                 from_record: bool = False,
                 value: Optional[int] = None,
                 score: Optional[int] = None):
        """Initialize Solution object either from record or normal mode with value computed from word position on board

        if the from_record param is True then no board reference must be provided and value and score must be provided.
        This option is needed for testing purpose - it is not used in real game playing
        """
        assert board is None and value and score if from_record else True
        assert isinstance(board, Board) if not from_record else True
        assert isinstance(main_word, Word)
        if cross_word_list is not None:
            assert isinstance(cross_word_list, list)
            for item in cross_word_list:
                assert isinstance(item, CrossWord)
                assert isinstance(item.word, Word)
                assert item.index_of_main_word_line < len(item.word)
        if joker_set is not None:
            assert isinstance(joker_set, set)
            for item in joker_set:
                assert isinstance(item, JokerTuple)
                assert isinstance(item.index, int)
                assert isinstance(item.letter, str)
                assert len(item.letter) == 1

        self.from_record = from_record

        self.main_word = main_word

        self.cross_word_list = [] if cross_word_list is None else cross_word_list

        self.joker_set = set() if joker_set is None else joker_set

        # compute value if not from_record
        if not self.from_record:
            self.board = board
            self.value = board.compute_word_value(self.main_word, joker_set)
            joker_index_list = {joker_tuple.index for joker_tuple in self.joker_set}
            for cross_word in self.cross_word_list:
                joker_at_crossing = True if self.main_word.intersection_index(cross_word.word) in joker_index_list \
                    else False
                self.value += board.compute_cross_word_value(cross_word, joker_at_crossing)
            self.score = self.value  # TODO score is a provision for future heuristics implemntation
        else:
            self.value = value
            self.score = score

    def __eq__(self, other: 'Solution') -> bool:
        return self.score == other.score

    def __gt__(self, other: 'Solution') -> bool:
        if self.score > other.score:
            return True
        else:
            return False

    def __repr__(self) -> str:
        s = "\n"
        s += "Main word=" + str(self.main_word) + "\n"
        for btuple in self.joker_set:
            s += "   Joker at offset=" + str(btuple.index) + " with letter: " + str(btuple.letter) + "\n"
        for ow in self.cross_word_list:
            s += "    cross word=" + str(ow.word) + "\n"
        s += "Value=" + str(self.value) + "\n"
        s += "Score=" + str(self.score) + "\n"

        return s


class Board():
    """Provide support for a scrabble board - letter and word multipliers value - words played on the board"""

    def __init__(self,
                 board: List[str] = None,
                 board_values: List[int] = None,
                 word_set: Set[Word] = None,
                 position_to_words: Dict[Position, List[Word]] = None,
                 nb_moves: int = None):
        """Initialize an empty board ready for a new game"""

        if all(p is not None for p in (board, board_values, word_set, position_to_words)):
            self.board = board
            self.board_values = board_values
            self.word_set = word_set
            self.position_to_words = position_to_words
            self.nb_moves = nb_moves
        elif all(p is None for p in (board, board_values, word_set, position_to_words)):
            # self.letter_multiplier = LETTER_MULTIPLIER_SET.copy()
            # self.word_multiplier = WORD_MULTIPLIER_SET.copy()
            # board storing letters at their location coordinate (0,0) at nw
            self.board = [" " for _ in range(15 * 15)]  # flat list access is twice faster as 2D list

            # board_value storing value of letters once put on board
            # this is needed because of the joker tile that once played has a letter assigned but still keeps
            # a value of zero. Therefore we can't rely on the reference value to compute cross-words values
            self.board_values = [0 for _ in range(15 * 15)]  # flat list access is twice faster as 2D list

            # keep a list of words existing on the board in their Word() class format
            # when word crosses on the board a given letter can belong to several board
            self.word_set = set()
            # build an index of words per position
            # this is a dicionnary of list - dictionnary key are positions and list are populated with words utilizing
            # the position - can be two words when words are crossing
            self.position_to_words = {}
            self.nb_moves = 0  # number of moves already played in the game
        else:
            raise ValueError("Board() called with invalid parameter combination - should be all parameters "
                             "or one of them but not a subset")

    def _assign_letter(self, letter: str, position: "Position", is_not_joker: bool = True) -> int:
        """
        Assign letter at position on the board

        :param letter:
        :param position:
        :return: 1 if position was empty 0 if word uses an already existing letter
        raise exception if cell already occupied by another letter
        """
        assert type(letter) == str and len(letter) == 1
        assert type(position) == Position
        # row, col = position.coordinate

        # this latter case catters for when a word is re-using a letter that is already on the
        # board from an existing word
        if self.board[position.row * 15 + position.col] == letter:
            nb_letter_from_rack = 0
        # assign letter only if cell
        elif self.board[position.row * 15 + position.col] == ' ':
            self.board[position.row * 15 + position.col] = letter
            # self.board_values[position.row * 15 + position.col] = CHARACTER_VALUE[letter] if is_not_joker else 0
            self.board_values[position.row * 15 + position.col] = character_value(letter) if is_not_joker else 0

            nb_letter_from_rack = 1
        else:
            logger.critical("trying to replace an existing letter on the board at position %s" % str(position))
            raise BoardCoordinateAlreadyOccupied

        return nb_letter_from_rack

    def get_position_content(self, position: 'Position') -> str:
        """Return the letter or blank stored at position on the board"""
        assert isinstance(position, Position)

        return self.board[position.row * 15 + position.col]

    @staticmethod
    def line_positions(direction: Direction, line: 'Line') -> Generator[Position, None, None]:
        """Return a generator of all positions in the line starting at 0 index"""
        assert isinstance(direction, Direction)
        assert isinstance(line, int)
        assert 0 <= line <= 14

        if direction.is_accross:
            row_start, col_start = (line, 0)
            row_step, col_step = (0, 1)
        elif direction.is_down:
            row_start, col_start = (0, line)
            row_step, col_step = (1, 0)
        else:
            raise ValueError
        for i in range(15):
            yield Position(row_start + row_step * i, col_start + col_step * i)

    def adjacent_letters_2_line(self, line: Line) -> Dict[str, List[Position]]:
        # noinspection PyUnresolvedReferences
        """
                Identify adjacent non empty cells to the line

                :param line: row or col number to be treated (depends on direction)
                :return: False if no adjacent cells - a list of Position
                         in below dictionary format
                         {
                           'side_lower: [Position(x, y), Position(x, y),..],
                           'side_higher: [Position(x, y), Position(x, y),..]
                         }
                """
        assert isinstance(line, Line)

        side_to_be_checked = ["side_lower", "side_higher"]

        #  select sides of the word to be checked - if the line is located on the edge of the board some side are not
        # possible
        if line.line_index == 0:
            side_to_be_checked.remove("side_lower")
        elif line.line_index == 14:
            side_to_be_checked.remove("side_higher")

        # initialize row and col increments depending on direction
        if line.direction.is_accross:
            row_lower, col_lower = (-1, 0)
            row_higher, col_higher = (1, 0)
        elif line.direction.is_down:
            row_lower, col_lower = (0, -1)
            row_higher, col_higher = (0, 1)

        adjacent = {"side_lower": [],
                    "side_higher": []}

        for side in side_to_be_checked:

            if side == "side_lower":
                for position in line:
                    row, col = position.coordinate
                    row_tested = row + row_lower
                    col_tested = col + col_lower
                    if self.board[row_tested * 15 + col_tested] != ' ':
                        adjacent["side_lower"].append(Position(row_tested, col_tested))

            elif side == "side_higher":
                for position in line:
                    row, col = position.coordinate
                    row_tested = row + row_higher
                    col_tested = col + col_higher
                    if self.board[row_tested * 15 + col_tested] != ' ':
                        adjacent["side_higher"].append(Position(row_tested, col_tested))

        return adjacent

    def build_mask_for_line(self, line: Line) -> Mask:
        """
        Return mask for the line that states if positions on the line are empty, empty potential cross-words or occupied

        It represents the possible utilisation of the cell in a line (row or column).
        list length is 15 and items 0 to 14 represents the line position in Down(row) or Accross(Column) direction

        item values can be:
         - "L" a letter already placed on the board
         - {} ==> empty dict stands for an empty position with no adjacent tile
         - {"letter": word_couple,
            "letter": word_couple,
            ...}                    ==> stands for an empty position WITH ADJACENT letters.
                                     letter value used as key can form a valid word that is provided in word_couple

                                     word_couple is a namedtuple of the below form:
                                     word_couple = namedtuple("word_couple", ["index", "word_str"])
                                     - index is the position of the letter key in the word
                                     - word_str is the full cross word that can be built with the letter

         - None ==> stands for an empty position WITH ADJACENT letters and for which NO cross-words can be build.
                    Which means that this position can't be utilized at all

        :param dict: is the dict word to be used to identify words
        :param line: is a Line instance
        :return: mask as described above
        """
        global dict_object
        assert isinstance(dict_object, Trie) or isinstance(dict_object,
                                                           DictionaryServer)  # TODO BUG dict_object not initialize when first play is manual
        assert isinstance(line, Line)

        # initialise mask with set() when blank and letter from board when position is already filled
        # replace blank by empty list that will receive possible letters for cross-words whenever applicable
        mask = Mask([])
        for item in [self.get_position_content(position) for position in line]:
            if item == " ":
                mask.append(MaskItem({}))
            else:
                mask.append(MaskItem(item))

        mask_positions = [position for position in line]

        # then build possible cross words on empty position
        # first step is to gather adjacent tiles on sides of the line
        adjacent_positions = self.adjacent_letters_2_line(line)
        flatten_adjacent_positions = adjacent_positions["side_lower"] + adjacent_positions["side_higher"]

        # build a list of filled positions contiguous to the adjacent positions that includes the line
        # position adjacent to the adjacent_position so that potential words can be detected and mask can
        # be populated only with letters that can form valid cross-words - this will reduce the nb of solutions
        # explored later when looking at potential solution on the board for a given rack
        for adjacent_position in flatten_adjacent_positions:
            position_list = [adjacent_position]
            # scan backwards
            for position in adjacent_position.prev(line.direction.ortho()):
                if self.get_position_content(position) != " " or position in mask_positions:
                    position_list.insert(0, position)
                else:
                    break
            # scan forwards
            for position in adjacent_position.next(line.direction.ortho()):
                if self.get_position_content(position) != " " or position in mask_positions:
                    position_list.append(position)
                else:
                    break

            string = "".join([self.get_position_content(c) for c in position_list])
            if " " in string:  # if no blank in string this is an already existing word on the board that is ignored
                # get all possible words from string - string contains exactly one blank
                word_dict = dict_object.possible_word_set_from_string(string)
                if line.direction.is_accross:
                    mask_index = adjacent_position.col
                else:
                    mask_index = adjacent_position.row
                if word_dict:
                    mask[mask_index] = MaskItem(word_dict)
                else:  # there's no solution to build a cross-word with adjacent positions
                    mask[mask_index] = MaskItem(None)

        return mask

    @staticmethod
    def get_anchor_positions_from_line(line: Line, mask: Mask) -> List[Position]:
        """Determine anchor position on the line: anchor is the 1st empty position at the left of a occupied position"""
        assert isinstance(line, Line)
        assert isinstance(mask, list)
        for item in mask:
            assert isinstance(item, MaskItem)

        return [position for i, position in enumerate(line)
                if i != 14
                and mask[i].has_no_letter
                and mask[i + 1].has_letter]

    def build_left_masks_list(self, line: Line, mask: Mask) -> List[AnchorTuple]:
        """
        Identify anchor position and build left masks for each of them

        anchor positions are defined as the first empty position at the left of a tile on the board

        left mask is the mask for the positions at the left of the anchor that can be used  to build a word.
        A left mask is made either of letters already on board or of empty positions: BUT NOT OF A MIX OF BOTH.
        For the latter case it is provided as many left masks per anchor position as len(left_mask). This is to
        ensure that in later stages word starting from any blank position will be searched and not only the ones
        staring at the left of the mask


        :param line:
        :param mask:
        :return: [namedtuple("AnchorTuple", ["pos", "left_index"]),...]
                 - pos is the anchor position of type Position
                 - left_index is the index for the starting position of the left mask in the 15 indices full mask
                   for the line
        """
        # TODO  consider case of anchor being None
        assert isinstance(mask, list)
        for item in mask:
            assert isinstance(item, MaskItem)

        anchor_position_list = self.get_anchor_positions_from_line(line, mask)

        anchor_tuple_list = []  # contains all tuples (anchor_position, left_position)

        # if first position of the line is a letter we need to scan from position zero
        # as no anchor pos will be identified for this case
        if mask[0].has_letter:
            anchor_tuple_list.append(AnchorTuple(line.index_2_pos(0), 0))

        for anchor_position in anchor_position_list:
            anchor_index = line.pos_2_index(anchor_position)

            # if anchor position is None then only one scan starting on first position of the word on the right
            if mask[anchor_index].is_not_usable:
                anchor_tuple_list.append(AnchorTuple(anchor_position, anchor_index + 1))
                continue
            # identify left mask for current anchor position
            # left mask is made either of letters already on board or of empty position but NOT OF BOTH
            sub_mask = mask[:anchor_index]  # sub_mask contains all position before anchor excluding it
            if sub_mask:

                if sub_mask[-1].has_letter:  # single blank between two words
                    # mask starting at the letter on the right of the anchor
                    anchor_tuple_list.append(AnchorTuple(anchor_position, anchor_index + 1))

                elif sub_mask[-1].is_usable:  # at least two blank at left of word
                    for i, item in enumerate(reversed(sub_mask)):
                        if i == 5 and item.is_usable:
                            # no need to have left mask longer than 7  as rack contains only 7 letters
                            # here we stop at 6 because the anchor position will be added later
                            start_left_mask_index = len(sub_mask) - 6
                            break
                        elif item.has_letter or item.is_not_usable:
                            # empty pos before letter is not taken so that words for left_mask are preceded
                            # by a blank...else not a separated word ==> hence the - i + 1
                            start_left_mask_index = len(sub_mask) - i + 1
                            break
                        elif i == len(sub_mask) - 1:  # first position of mask is set()
                            start_left_mask_index = 0
                    # left_mask is made of empty position only - need to create mask of every length including the
                    # mask starting from the anchor position itself hence "anchor_index + 1..." below
                    for i in range(anchor_index + 2 - start_left_mask_index):
                        anchor_tuple_list.append(AnchorTuple(anchor_position,
                                                             start_left_mask_index + i))

        return anchor_tuple_list

    def get_potential_solutions_for_first_play(self, rack: Rack) -> List['Solution']:
        """
        Return all potential solutions for first play with rack from the dict
        """
        global dict_object
        assert isinstance(dict_object, Trie) or isinstance(dict_object, DictionaryServer)
        assert isinstance(rack, Rack)
        assert len(rack) == 7

        mask = Mask([MaskItem({}) for _ in range(7)])
        potential_words = dict_object.possible_words_for_mask_with_rack(mask,
                                                                        rack.tile_list,
                                                                        1)
        solution_list = []
        for w in potential_words:
            joker_set = set()
            w_pattern = [" " for _ in range(len(w))]
            for i, item in enumerate(mask[:len(w)]):
                if isinstance(item, str):
                    w_pattern[i] = "board"
            tile_list_copy = rack.tile_list.copy()
            for i, (l_pattern, l_w) in enumerate(zip(w_pattern, w)):
                if l_pattern == "board":
                    continue
                if l_w in tile_list_copy:
                    tile_list_copy.remove(l_w)
                    w_pattern[i] = "rack"
            for i, (l_w, pattern_item) in enumerate(zip(w, w_pattern)):
                if pattern_item == " ":
                    joker_set.add(JokerTuple(i, l_w))

            # TODO improve determination of Position for first word - randomized ? centered ?
            solution_list.append(Solution(self, Word(w, Direction("Accross"), Position(7, 7)), [], joker_set))

        return solution_list

    def get_potential_solutions_for_line(self, line: Line, rack: Rack) -> List[Solution]:
        """
        Return all potential solutions for the line and rack from the dict.

        It includes the cross-words if relevant

        :param dict:
        :param line:
        :param rack:
        :return: list of Solution
        """
        global dict_object
        assert isinstance(dict_object, Trie) or isinstance(dict_object, DictionaryServer)
        assert isinstance(line, Line)
        assert isinstance(rack, Rack)

        # build mask which adds to the mask letter already on board and letters for potential cross-words when
        # line has adjacent letters
        mask = self.build_mask_for_line(line)
        # print(mask)

        # (1) Identify anchor positions that are defined as the left most empty position to a word on the line
        # (2) build the left masks for every anchor position -
        #          - left masks do not contain the anchor_position that is by definition empty
        #          - they start at the left most position of the anchor position and they can be empty
        #          - what is returned is anchor position together with the index of the left most cell to
        #            be included in the mask for word search later on
        # AnchorTuple = namedtuple("AnchorTuple",["pos", "left_index"])
        anchor_tuple_list_to_be_treated = self.build_left_masks_list(line, mask)
        # print("anchor_tuple_list_to_be_treated=", anchor_tuple_list_to_be_treated)

        # @ this stage mask_list contains all masks to be scanned for solution. There could be several mask
        # for a given anchor position

        # for every mask look for solutions
        solution_list = []
        # AnchorTuple = namedtuple("AnchorTuple",["pos", "left_index"])
        for anchor_item in anchor_tuple_list_to_be_treated:
            mask_2_scan = mask[anchor_item.left_index:]
            # compute minimal length of the words to be selected so that they contain at minimum all existing
            # letters on the board at the right of the anchor position
            min_length = line.pos_2_index(anchor_item.pos) - anchor_item.left_index + 1
            while mask_2_scan[min_length].has_letter and min_length < len(mask_2_scan) - 1:
                min_length += 1

            potential_words = dict_object.possible_words_for_mask_with_rack(mask_2_scan,
                                                                            rack.tile_list,
                                                                            min_length)

            # detect if cross words can be identified from the mask
            cross_word = False
            if potential_words and any(m for m in mask_2_scan if m.is_cross_word):  # non empty dict in mask
                cross_word = True

            for word in potential_words:
                # keep only words which are followed by a blank position or ending at edge of board
                if anchor_item.left_index + len(word) == 15:
                    main_word = Word(word, line.direction, line.index_2_pos(anchor_item.left_index))
                elif mask[anchor_item.left_index + len(word)].is_usable:
                    main_word = Word(word, line.direction, line.index_2_pos(anchor_item.left_index))
                else:
                    break

                # add cross words if any
                cross_word_list = []  # [ (Word, index), ...] where index is the position of the line in the cross-word
                if cross_word:
                    for i, (letter, mask_item) in enumerate(zip(word, mask_2_scan)):
                        if mask_item.is_cross_word:
                            try:
                                index_of_main_word_line, word_str = mask_item.data[letter]  # KeyError if no word
                                if line.direction.is_accross:
                                    row = line.line_index - index_of_main_word_line
                                    col = anchor_item.left_index + i
                                else:
                                    row = anchor_item.left_index + i
                                    col = line.line_index - index_of_main_word_line
                                cross_word_list.append(
                                    CrossWord(
                                        Word(word_str,
                                             line.direction.ortho(),
                                             Position(row, col)
                                             ),
                                        index_of_main_word_line
                                    )
                                )
                            except KeyError:
                                pass

                # detect location of blank whenever applicable
                joker_set = set()
                word_pattern = [" " for _ in range(len(word))]
                for i, item in enumerate(mask_2_scan[:len(word)]):
                    if item.has_letter:
                        word_pattern[i] = "board"
                tile_list_copy = rack.tile_list.copy()
                for i, (letter_pattern, letter_word) in enumerate(zip(word_pattern, word)):
                    if letter_pattern == "board":
                        continue
                    if letter_word in tile_list_copy:
                        tile_list_copy.remove(letter_word)
                        word_pattern[i] = "rack"
                for i, (letter_word, pattern_item) in enumerate(zip(word, word_pattern)):
                    if pattern_item == " ":
                        joker_set.add(JokerTuple(i, letter_word))
                if not joker_set:
                    joker_set = None

                # retain only words that are not yet on board
                if not ({main_word} & self.word_set):
                    solution_list.append(Solution(self, main_word, cross_word_list, joker_set))

        return solution_list

    def put_on_board(self, word: Word, is_main_word=True, joker_set: Optional[Set[JokerTuple]] = None) -> List[str]:
        """Put a word on the board as part of a play action"""
        assert type(word) == Word

        # if an existing word on board is subset of word this existing word must be removed from index and list
        # before the new word is actually put on board
        # example   LE is a subset of LES
        # and therefore the word LE is replaced on board by LES if a player adds an S to lE
        for w in [wsub for wsub in self.word_set if word.is_subset(wsub)]:
            self.word_set.discard(w)
            for position in w.positions():
                self.position_to_words[position].remove(w)

        joker_index_set = {joker_tuple.index for joker_tuple in joker_set} if joker_set else {}
        letter_from_rack_list = []
        for i, (letter, position) in enumerate(zip(word, word.positions())):
            is_not_joker = False if i in joker_index_set else True
            if self._assign_letter(letter, position, is_not_joker):
                letter_from_rack_list.append(letter)
            # fill position to words index
            try:
                self.position_to_words[position]
            except KeyError:
                self.position_to_words[position] = []
            finally:
                self.position_to_words[position].append(word)

        self.word_set.add(word)

        if is_main_word:  # cross words do not count as a move
            self.nb_moves += 1

        return letter_from_rack_list

    def compute_word_value(self, word: Word, joker_set: Optional[JokerTuple] = None) -> int:
        """
        Compute value of a word at a given position on the board

        this function is there for evaluating values during the research of the best solution
        or to compute score when a word is selected and put on the board

        Cross words are not considered and have to be computed separately

        this function must be called BEFORE word is put on board else it is not possible to distinguish letters
        that were already on board from the new ones that are the only ones to which multipliers applies

        :param word:
        :return:
        """
        assert type(word) == Word
        # TODO can the assert below be removed for good - hit when PlayItem list is loaded with marshmallow
        # assert word not in self.word_set  # compute must be called before word is put on board
        if joker_set is not None:
            assert isinstance(joker_set, set)
            for item in joker_set:
                assert isinstance(item, JokerTuple)
                assert isinstance(item.index, int)
                assert isinstance(item.letter, str)
                assert len(item.letter) == 1

        value = 0
        word_coeff = 1
        nb_letter_not_yet_on_board = len(word)

        joker_index_set = {joker_tuple.index for joker_tuple in joker_set} if joker_set else {}

        for i, (letter, pos) in enumerate(zip(word, word.positions())):
            if self.get_position_content(pos) != " ":  # letter provided by an existing word on the board
                nb_letter_not_yet_on_board -= 1  # not considered for scrabble count
                value += self.board_values[pos.row * 15 + pos.col]  # no letter multipliers applied for existing letters
            else:
                if i not in joker_index_set:
                    value += character_value(letter) * LETTER_MULTIPLIER_SET[pos.row * 15 + pos.col]
                # detect word multipliers only for new letters
                if WORD_MULTIPLIER_SET[pos.row * 15 + pos.col] > 1:
                    word_coeff *= WORD_MULTIPLIER_SET[pos.row * 15 + pos.col]

        # apply word multipliers
        value *= word_coeff

        # apply scrabble bonus
        if nb_letter_not_yet_on_board >= 7:  # scrabble provides 50 points bonus
            value += 50

        return value

    def compute_cross_word_value(self, cross_word: 'CrossWord', joker_at_crossing: bool) -> int:
        """
        Compute value of a cross word at a given position on the board

        this function is there for evaluating values during the research of the best solution
        or to compute score when a word is selected and put on the board

        Cross words are not considered and have to be computed separately

        this function must be called BEFORE word is put on board else it is not possible to distinguish letters
        that were already on board from the new ones to which only multipliers applies

        :param cross_word:
        :return:
        """
        assert type(cross_word) == CrossWord
        # TODO can the assert below be removed for good - hit when PlayItem list is loaded with marshmallow
        # assert cross_word.word not in self.word_set  # compute must be called before word is put on board

        value = 0
        word_coeff = 1

        for i, (letter, pos) in enumerate(zip(cross_word.word, cross_word.word.positions())):
            if i == cross_word.index_of_main_word_line:  # intersection: letter belonging to main word as well
                # letter and word multiplier do apply only at intersection
                # value += CHARACTER_VALUE[letter] * self.letter_multiplier[pos.row * 15 + pos.col]
                if not joker_at_crossing:
                    value += character_value(letter) * LETTER_MULTIPLIER_SET[pos.row * 15 + pos.col]
                # detect word multipliers only for new letters
                if WORD_MULTIPLIER_SET[pos.row * 15 + pos.col] > word_coeff:
                    word_coeff *= WORD_MULTIPLIER_SET[pos.row * 15 + pos.col]
            else:  # else only letter value is considered with no multiplier
                # and we use value from board_values, not from CHARACTER_VALUE, because in some case a letter can be
                # a joker and in this case its value will be zero, not the actual letter value
                value += self.board_values[pos.row * 15 + pos.col]  # no letter multipliers applied for existing letters

        # apply word multipliers
        value *= word_coeff

        return value

    def get_sorted_list_of_solutions_for_rack(self,
                                              rack: Rack) -> Union[List[Solution], bool]:
        """Identify the best solution possible with tiles available from the rack"""

        global dict_object
        assert isinstance(dict_object, Trie) or isinstance(dict_object, DictionaryServer)
        assert isinstance(rack, Rack)
        assert len(rack) != 0

        if self.nb_moves == 0:  # first move of the game must cover center of the board (7,7)
            solution_list = self.get_potential_solutions_for_first_play(rack)
        else:
            solution_list = list(
                itertools.chain.from_iterable(
                    (
                        self.get_potential_solutions_for_line(Line(direction, i), rack)
                        for i in range(15)
                        for direction in [Direction("Accross"), Direction("Down")]
                    )
                )
            )

        # Sort solutions identified, if any, by increasing score as primary key
        # and secondary sort with hash on main_word.text
        # secondary sort ensures that in case of solution with same score, sorting several time wil returns the same
        # order. Else it is not the case when several words exists for a given
        # tile_list. This is needed for the record / play list feature used for debugging and performance mngt
        if solution_list:
            solution_list.sort(key=lambda s: (s, s.main_word.text))
        else:
            return False  # no word found

        return solution_list

    def get_best_solution_for_rack(self,
                                   rack: Rack) -> Union[Solution, bool]:
        """Identify the best solution possible with tiles available from the rack"""

        global dict_object
        assert isinstance(dict_object, Trie) or isinstance(dict_object, DictionaryServer)
        assert isinstance(rack, Rack)
        assert len(rack) != 0

        solution_list = self.get_sorted_list_of_solutions_for_rack(rack)

        if solution_list:
            return solution_list[-1]
        else:
            return False  # no word found

    def print_board(self):
        # TODO MAKE IT A __repr__ or __str__ or at least a function returning a string that can be used in logger
        print("")
        print("   [" + "".join(map(lambda x: x + " ", [str(j).zfill(2) for j in range(15)])) + "]")
        for i in range(15):
            print(str(i).zfill(2) + " [" + "".join(
                map(lambda x: "_" + x + "_",
                    [self.board[i * 15 + j] for j in range(15)]))
                  + "]"
                  )
        print("")

    def __eq__(self, other):
        return (self.board == other.board
                and self.board_values == other.board_values
                and self.nb_moves == other.nb_moves
                and self.position_to_words == other.position_to_words
                and self.word_set == other.word_set)

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return json.dumps(json.loads(BoardSchema().dumps(self)), indent=JSON_INDENT)

    # def to_json_mm(self) -> str:
    #     return BoardSchema().dumps(self)


class Game():
    """Implement all logic required to play a scrabble game instance

       It depends on the below external classes:
        - BagOfTile
        - Rack
        - Board
        - GameRecord
        - Trie


    """

    def __init__(self,
                 bag: BagOfTile = None,
                 players_name_list: List[str] = None,
                 player_dict: dict_object = None,
                 board: Board = None,
                 game_record: 'GameRecord' = None,
                 players_dict: OrderedDict = None,
                 play_list_history: OrderedDict = None):
        """
        Initialize an instance of Game class
        """
        # global dict
        # self.dict = dict  # local copy of global variable for performance TODO is it worth doing ?

        if all(p is None for p in (bag, players_name_list, player_dict, board, game_record, play_list_history)) \
                and players_dict is not None:
            # assert isinstance(dict, Trie)
            assert type(players_dict) == OrderedDict
            assert 1 < len(players_dict) <= 5
            for player, mode in players_dict.items():
                assert player.isalnum()
                assert mode in PLAY_MODE_SET

            self.bag = BagOfTile()
            self.players_name_list = [player for player in players_dict]  # Used to know in which order players play
            self.player_dict = {}  # TODO not an OrderedDict as in typing ?
            for player, mode in players_dict.items():
                self.player_dict[player] = {}
                self.player_dict[player]['mode'] = mode
                # self.player_dict[player]['play_func'] = self.play_auto if mode == "auto" else self.play_manual_old
                self.player_dict[player]['score'] = 0
                self.player_dict[player]['rack'] = Rack()
                self.player_dict[player]['rack'].fill_rack(self.bag)
                self.player_dict[player]['nb_skip_in_sequence'] = 0
                self.player_dict[player]['tile_changed'] = False
                self.player_dict[player]['play_list'] = []
            self.board = Board()
            self.game_record = GameRecord()  # Provision for recording game for debugging and perf analysis
            # list of string - every string is a play of below structure
            #  - word text capital letter
            #  - position (row,col)
            #  - direction H or V
            #  - value
            self.play_list_history = []
        elif (all(p is not None for p in (bag, players_name_list, player_dict, board, game_record, play_list_history))
              and players_dict is None):
            self.bag = bag
            self.players_name_list = players_name_list
            self.player_dict = player_dict
            self.board = board
            self.game_record = game_record
            self.play_list_history = play_list_history
        else:
            raise ValueError("parameters are not provided properly")

    def _play(self, solution: Solution, player_dict_ref: Dict[str, str],
              player: Optional[str] = None) -> PlayReturnTuple:
        """Play a solution on the board - solution is assumed as correct: no  checks are performed"""
        player_dict_ref['nb_skip_in_sequence'] = 0
        letter_from_rack_list = self.board.put_on_board(solution.main_word, True, solution.joker_set)

        # treat case of joker used for the word - replace letter used as joker by actual blank so that removal
        # in tile-list works
        for joker_tuple in solution.joker_set:
            letter_from_rack_list.remove(joker_tuple.letter)
            letter_from_rack_list.append(" ")

        for cross_word in solution.cross_word_list:
            self.board.put_on_board(cross_word.word, False)

        player_dict_ref['score'] += solution.value

        # TODO add solution to player_dict_ref so that it can be sent to web client and displayed

        direction_code = "H" if solution.main_word.direction.is_accross else "V"
        # self.play_list_history.append(player + " - "
        #                               + solution.main_word.text + " - ("
        #                               + str(solution.main_word.origin.row + 1) + ","
        #                               + chr(solution.main_word.origin.col + 65) + ") - "
        #                               + direction_code + " - "
        #                               + str(solution.value))

        # row coordinate is translated to capital letter and col origin set to 1 instead of 0 so that display on board
        # is correct TODO BETTER TO HAVE THIS POSITION FORMATING DONE CLIENT SIDE IN FINAL VERSION
        self.play_list_history.append(
            {
                "player": player,
                "word_text": solution.main_word.text,
                "row": str(solution.main_word.origin.row + 1),
                "col": chr(solution.main_word.origin.col + 65),
                "direction": direction_code,
                "value": str(solution.value)
            }
        )

        return PlayReturnTuple(rc="played",
                               letter_from_rack_list=letter_from_rack_list,
                               solution=solution)

    def play_manual(self, play_instruction: Tuple[str, Optional[Solution]],
                    player_dict_ref: Dict[str, str],
                    player_name: Optional[str] = None) -> PlayReturnTuple:
        """play a manual instruction: word on board, skip or change letters"""
        assert isinstance(play_instruction, Tuple)
        type_of_play, solution = play_instruction
        assert type_of_play in (PLAY, SKIP, CHANGE)
        assert isinstance(solution, Solution) if type_of_play == PLAY else solution is None

        if type_of_play == PLAY:
            return self._play(solution, player_dict_ref, player_name)

        elif type_of_play == SKIP:
            player_dict_ref['nb_skip_in_sequence'] += 1
            return PlayReturnTuple(rc="skip")

        elif type_of_play == CHANGE:
            if len(player_dict_ref['rack']) == 7 and len(self.bag) >= 7:
                return PlayReturnTuple(rc="change")
            else:
                logger.critical("Can't change letters if rack not full or less that 7 letters left in bag")
                raise ChangeRackLettersNotAllowed("Can't change letters if rack not full or "
                                                  "less that 7 letters left in bag")

    def play_auto(self, player_dict_ref: Dict[str, str], player_name: Optional[str] = None) -> PlayReturnTuple:
        """Compute a solution (either a new word of skip or change letters) and play it

        :return: a PlayResultTuple stating
                    rc  play, skip, change
                    letters from rack put on the board or None
                    solution played if any or
        """

        solution = self.board.get_best_solution_for_rack(player_dict_ref['rack'])
        if solution:
            return self._play(solution, player_dict_ref, player_name)
        else:
            if len(player_dict_ref['rack']) == 7 and len(self.bag) >= 7:
                logger.info("No word found for rack= %s - changing tiles" % player_dict_ref['rack'])
                return PlayReturnTuple(rc="change")
            else:
                logger.info("No word found for rack= %s - skipping this play" % player_dict_ref['rack'])
                player_dict_ref['nb_skip_in_sequence'] += 1
                return PlayReturnTuple(rc="skip")

    def manual_play(self, player_name: str,
                    play_instruction: Tuple[str, Optional[Solution]],
                    record: bool = False,
                    play_list_filename: Optional[str] = None) -> bool:
        """Play a manual play for player and play auto for next players that are in auto mode """
        assert isinstance(player_name, str)
        assert player_name in self.players_name_list
        assert isinstance(record, bool)
        assert not (record and play_list_filename)  # record and play from record are mutually exclusive

        player_list_starting_with_current_player = self.players_name_list[self.players_name_list.index(player_name):] \
                                                   + self.players_name_list[:self.players_name_list.index(player_name)]

        # select all player in mode auto following current manual player
        looping_on_player_list = player_list_starting_with_current_player[0:1] \
                                 + [p for p in player_list_starting_with_current_player[1:] if
                                    self.player_dict[p]['mode'] == 'auto']

        game_over = False
        for i, player in enumerate(looping_on_player_list):

            player_dict_ref = self.player_dict[player]  # for the sake of performance and readability

            if i == 0:  # this is a manual play
                play_return = self.play_manual(play_instruction, player_dict_ref, player)
            else:  # this is an automatic play
                play_return = self.play_auto(player_dict_ref, player)

            if play_return.rc == "played":
                if record:
                    self.game_record.record_this_play(
                        PlayItem(
                            player_dict_ref['rack'].tile_list.copy(), play_return.solution
                        )
                    )
                player_dict_ref['rack'].remove_list_of_letters(play_return.letter_from_rack_list)
                if self.bag.is_empty:
                    if not player_dict_ref['rack'].tile_list:  # no tile left on rack - game ended
                        logger.info('{} has used all tile from rack and bag is empty - END OF GAME'.format(player))
                        game_over = True
                        break
                else:
                    player_dict_ref['rack'].fill_rack(self.bag)

            elif play_return.rc == "skip":
                if all(self.player_dict[player]['nb_skip_in_sequence'] >= 3 for player in self.player_dict):
                    logger.info("No solution possible for any player after 3 attempts per player - END OF GAME")
                    game_over = True
                    break

            elif play_return.rc == "change":
                if len(player_dict_ref['rack']) == 7 and len(self.bag) >= 7:
                    player_dict_ref['rack'].change_all_letters(self.bag)
                else:
                    logger.critical("Can't change tiles if less than 7 tiles in rack or less than 7 tiles left in bag")
                    raise RequestedRackTilesChangeNotAllowed("Can't change tiles if less than 7 tiles in rack"
                                                             "or less than 7 tiles left in bag")

        if game_over:
            if record:
                filename = "scrabble_play_list-" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".json"
                self.game_record.save_json_play_list(filename)
                logger.info("play list saved as: %s" % filename)

            # player on exit of main loop is finisher - compute final scoring
            if not self.player_dict[player_name]['rack'].tile_list:  # last player exhausted his rack
                other_players = [p for p in self.player_dict if p != player_name]
                for op in other_players:
                    unused_letters_value = sum(map(lambda x: character_value(x), self.player_dict[op]['rack']))
                    self.player_dict[op]['score'] -= unused_letters_value
                    self.player_dict[player_name]['score'] += unused_letters_value
            else:
                pass  # game ended with no possibility to put remaining letters so in this case remaining letters
                # yields no value to the game score

            game_summary = GameSummary(total_score=sum([self.player_dict[p]['score'] for p in self.player_dict]),
                                       nb_play=self.board.nb_moves,
                                       word_list=list(self.board.word_set),
                                       left_in_bag=self.bag.bag.copy(),
                                       player_score={player: self.player_dict[player]['score']
                                                     for player in self.player_dict}
                                       )

            self.game_record.store_game_summary(game_summary)

        return True if game_over else False

    def automatic_play(self, record: bool = False, play_list_filename: Optional[str] = None) -> GameSummary:
        """
        Play game for players in automatic mode or from recorded play-list - returns score

        record and play_list_filename are mutually exclusive

        :param record: if True records the game in the self.game_record object
        :param play_list_filename: if True plays the game using the pickled play_list passed as parameter
        :return: game_summary dictionary
        """
        assert isinstance(record, bool)
        assert not (record and play_list_filename)  # record and play from record are mutually exclusive
        # No manual player possible in this mode
        assert all(self.player_dict[player]["mode"] == "auto" for player in self.player_dict)

        if play_list_filename:
            assert os.path.exists(play_list_filename) and os.path.isfile(play_list_filename)
            tile_list_list_from_record = self.game_record.load_tile_list(play_list_filename)

        for player in itertools.cycle(self.players_name_list):  # main loop on players

            player_dict_ref = self.player_dict[player]  # for the sake of performance and readability

            play_return = self.play_auto(player_dict_ref, player)

            assert play_return.rc in PLAY_RC_SET

            # TODO DEBUG TO BE REMOVED
            print("========", player, "==== PLAY NB :", str(self.board.nb_moves).zfill(2), " =================")
            print("rack=", player_dict_ref['rack'])
            print(play_return.rc)
            print(play_return.solution)
            print("score is %s" % str(player_dict_ref['score']))
            self.board.print_board()

            if play_return.rc == "played":

                if play_list_filename:  # play from recorded game for performance or strategy analysis
                    try:
                        player_dict_ref['rack'].tile_list = tile_list_list_from_record.pop(0)
                    except IndexError:  # list is empty - end of game
                        logger.info("recorded list exhausted - END OF GAME")
                        break
                else:  # regular case played from bag
                    if record:
                        # copy board so that when recorded and serialized current state of board is kept - If reference
                        #  to board is kept rather than copy of values then when serializing at end of game each
                        # solution will have very same footprint of board object after last play
                        play_return.solution.board = deepcopy(play_return.solution.board)
                        self.game_record.record_this_play(
                            PlayItem(
                                player_dict_ref['rack'].tile_list.copy(), play_return.solution
                            )
                        )

                    player_dict_ref['rack'].remove_list_of_letters(play_return.letter_from_rack_list)
                    if self.bag.is_empty:
                        if not player_dict_ref['rack'].tile_list:  # no tile left on rack - game ended
                            logger.info('%s has used all tile from rack and bag is empty - END OF GAME' % player)
                            break
                    else:
                        player_dict_ref['rack'].fill_rack(self.bag)

            elif play_return.rc == "skip":
                if all(self.player_dict[player]['nb_skip_in_sequence'] >= 3 for player in self.player_dict):
                    logger.info("No solution possible for any player after 3 attempts per player - END OF GAME")
                    break

            elif play_return.rc == "change":
                if len(player_dict_ref['rack']) == 7 and len(self.bag) >= 7:
                    player_dict_ref['rack'].change_all_letters(self.bag)
                else:
                    raise RequestedRackTilesChangeNotAllowed("Can't change tiles if less than 7 tiles in rack"
                                                             "or less than 7 tiles left in bag")

        # player on exit of main loop is finisher - compute final scoring
        if not self.player_dict[player]['rack'].tile_list:  # last player exhausted his rack
            other_players = [p for p in self.player_dict if p != player]
            for op in other_players:
                unused_letters_value = sum(map(lambda x: character_value(x), self.player_dict[op]['rack']))
                self.player_dict[op]['score'] -= unused_letters_value
                self.player_dict[player]['score'] += unused_letters_value
        else:
            pass  # game ended with no possibility to put remaining letters so in this case remaining letters
            # yields no value to the game score

        game_summary = GameSummary(total_score=sum([self.player_dict[p]['score'] for p in self.player_dict]),
                                   nb_play=self.board.nb_moves,
                                   word_list=list(self.board.word_set),
                                   left_in_bag=self.bag.bag.copy(),
                                   player_score={player: self.player_dict[player]['score']
                                                 for player in self.player_dict}
                                   )

        self.game_record.store_game_summary(game_summary)

        if record:
            filename = "scrabble_play_list-" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".json"
            self.game_record.save_json_play_list(filename)
            logger.info("play list saved as: %s" % filename)

        return game_summary

    def __eq__(self, other: 'Game') -> bool:
        return (self.bag == other.bag
                and self.players_name_list == other.players_name_list
                and self.player_dict == other.player_dict
                and self.board == other.board
                and self.game_record == other.game_record)

    def __ne__(self, other: 'Game') -> bool:
        return not (self == other)

    def __repr__(self):
        return pretty_print_json(GameSchema().dumps(self))


class GameRecord():
    """Record inputs of a completed or interrupted Game so as to display it or replay it for debugging  or analysis

       play sequences are recorded in named tuple format : PlayItem that is made of the rack tile list and the solution
       object identified

    """

    def __init__(self, play_list: List[PlayItem] = None, game_summary: Optional[GameSummary] = None):
        """Initialize a game record object """
        if play_list is not None:
            assert all(isinstance(p, PlayItem) for p in play_list)
        assert isinstance(game_summary, GameSummary) or game_summary is None
        self.play_list = play_list if play_list is not None else []  # store PlayItem objects
        self.game_summary = game_summary  # Summary data for the game

    def __eq__(self, other):
        return self.play_list == other.play_list and self.game_summary == other.game_summary

    def __ne__(self, other):
        return not (self == other)

    def record_this_play(self, play_item: PlayItem):
        """Record a play item made of tile_list and solution"""
        assert isinstance(play_item, PlayItem)
        assert isinstance(play_item.tile_list, list)
        for item in play_item.tile_list:
            assert item.replace(" ", "A").isalpha()
            assert item.replace(" ", "A").isupper()
        assert isinstance(play_item.solution, Solution)

        self.play_list.append(play_item)

    def save_json_play_list(self, file_path=None):
        """Save recorded play list to file with json format"""
        with open(file_path, 'w') as fp:
            fp.write(PlayItemSchema(many=True).dumps(self.play_list))

    def load_tile_list(self, file_path: str):
        """Return a list with the successive tile_list recorded in the json file - solution are ignored"""
        assert os.path.exists(file_path)

        with open(file_path, 'r') as f:
            json_dict = json.load(f)

        play_item_list = PlayItemSchema(many=True).loads(json_dict)

        return [play_item.tile_list for play_item in play_item_list]

    def store_game_summary(self, game_summary: GameSummary):
        """Store gamme_summary metrics"""
        assert isinstance(game_summary, GameSummary)

        self.game_summary = game_summary

    def get_formated_game_summary(self) -> str:
        """Return a formatted str summarizing game results for display at end of game"""
        res = ["================ GAME SUMMARY ======================\n",
               "Total score=%s\n" % str(self.game_summary.total_score).zfill(3),
               "Nb of play =%s\n" % str(self.game_summary.nb_play).zfill(2)]
        for i, (player, score) in enumerate(sorted(
                [(player, score) for player, score in self.game_summary.player_score.items()],
                key=lambda x: x[1],
                reverse=True)
        ):
            if i == 0:
                res.append("%s score= %s ==> WINNER\n" % (player, str(score).zfill(3)))
            else:
                res.append("%s score= %s\n" % (player, str(score).zfill(3)))
        res.append("===================================================\n")

        return "".join(res)

    def __iter__(self) -> Iterator:
        """Default iterator that returns the PlayItems of the instance"""
        self.n = 0
        return self

    def __next__(self) -> PlayItem:
        """Return next PlayItem"""
        if self.n == len(self.play_list):
            raise StopIteration
        else:
            value = self.play_list[self.n]
            self.n += 1
            return value

    def __repr__(self):
        return pretty_print_json(GameRecordSchema().dumps(self))


#
# @hug.exception(TestHugException)  # TODO IMPLEMENTATION ON-GOING NOT WORKING SO FAR
# def value_error_handler(exception, response=None):
#     logger.error("%s" % str(exception))
#     logger.debug("DictionaryServerInternalError raised")
#     response.status = HTTP_STATUS_CODES[500]
#     # return 'this is a test of returning a string'
#     return {'errorServer': 'dictionaryServerInternalError'}


@hug.exception(DictionaryServerInternalError)
def dictionary_server_internal_error_handler(exception, response=None):
    """
    Return a string that is used in localisedMessage function of scrabble.js on client side
    """
    logger.error("%s" % str(exception))
    logger.debug("DictionaryServerInternalError raised")
    response.status = HTTP_STATUS_CODES[500]
    return 'dictionaryServerInternalError'


@hug.exception(DictionaryServerNotResponding)
def dictionary_server_not_responding_handler(exception, response=None):
    """
        Return a string that is used in localisedMessage function of scrabble.js on client side
    """
    logger.error("%s" % str(exception))
    logger.debug("DictionaryServerNotResponding raised")
    response.status = HTTP_STATUS_CODES[500]
    return 'dictionaryServerNotResponding'


@hug.exception(FirstPlayNotCoveringBoardCenter)
def first_play_not_covering_center_of_board_handler(exception, response=None):
    """
        Return a string that is used in localisedMessage function of scrabble.js on client side
    """
    logger.error("%s" % str(exception))
    logger.debug("FirstPlayNotCoveringBoardCenter raised")
    response.status = HTTP_STATUS_CODES[500]
    return 'firstPlayNotCoveringBoardCenter'


@hug.exception(CellUsedOrCrossWordInvalid)
def cell_already_used_or_crossword_not_valid_handler(exception, response=None):
    """
        Return a string that is used in localisedMessage function of scrabble.js on client side
    """
    logger.error("%s" % str(exception))
    logger.debug("CellUsedOrCrossWordInvalid raised")
    response.status = HTTP_STATUS_CODES[500]
    return 'cellUsedOrCrossWordInvalid'  # TODO retrieve the word in exception and pass it to js client


@hug.exception(WordNotInDictionary)
def word_not_in_dictionary_handler(exception, response=None):
    """
        Return a string that is used in localisedMessage function of scrabble.js on client side
    """
    logger.error("%s" % str(exception))
    logger.debug("WordNotInDictionary raised")
    response.status = HTTP_STATUS_CODES[500]
    return 'wordNotInDictionary'  # TODO retrieve the word in exception and pass it to js client


@hug.exception(CrossWordNotInDictionary)
def crossword_not_in_dictionary_handler(exception, response=None):
    """
        Return a string that is used in localisedMessage function of scrabble.js on client side
    """
    logger.error("%s" % str(exception))
    logger.debug("CrossWordNotInDictionary raised")
    response.status = HTTP_STATUS_CODES[500]
    return 'crossWordNotInDictionary'  # TODO retrieve the word in exception and pass it to js client


@hug.exception(ChangeRackLettersNotAllowed)
def change_letters_not_allowed_handler(exception, response=None):
    """
        Return a string that is used in localisedMessage function of scrabble.js on client side
    """
    logger.error("%s" % str(exception))
    logger.debug("ChangeRackLettersNotAllowed raised")
    response.status = HTTP_STATUS_CODES[500]
    return 'changeRackLettersNotAllowed'  # TODO retrieve the word in exception and pass it to js client


@hug.request_middleware()
def log_request(request, response):
    logger.debug(request)


@hug.response_middleware()
def log_response(request, response, resource):
    logger.debug(response)


@hug.directive()
def current_interface(default=None, interface=None, api=None, **kwargs):
    """Detect which hug interface between HTTP and local has been used"""
    if isinstance(interface, hug.interface.CLI):
        return "CLI"
    elif isinstance(interface, hug.interface.HTTP):
        return "HTTP"
    else:
        return "Local"


@hug.get("/ping_hug")
@hug.local()
def ping_hug(test: str) -> str:
    """return the string passed as parameter - for web interface testing"""
    logger.debug(" %s string received and returned" % str(test))
    return test


@hug.post("/start_game")
@hug.local()
def start_game(lang: fields.String(validate=OneOf(['Francais',
                                                   'french',
                                                   'Français',
                                                   'FRANCAIS',
                                                   'FRENCH'])),
               player_name: fields.String(),
               hug_current_interface) -> str:
    """start a game against program in specified language

       In current version the game is limited to a single manual player against the program
    """

    logger.info("game started in %s language for player %s against program" % (lang, player_name))

    players_ordered_dict = OrderedDict({player_name: "manual",
                                        "Server": "auto"})

    # create game instance that will be returned
    game = Game(players_dict=players_ordered_dict)

    # logger.debug("RESPONSE game=%s" % str(game))

    # return GameSchema().dumps(game)
    # TODO adapt test scenario to change of returning game_over in addition to game
    return json.dumps({"game_over": False,
                       "game": GameSchema().dumps(game)})


@hug.post("/play_4_player")
@hug.local()
def play_4_player(player_name: fields.String(required=True),
                  raw_proposed_play: fields.Nested(ProposedPlaySchema(), required=True),
                  game: fields.Nested(GameSchema(), required=True),
                  lang: fields.String(validate=OneOf(['FR', 'EN'])),
                  check_against_dictionary: fields.Boolean(required=True),
                  hug_current_interface,
                  response=None) -> str:
    """Play """

    # Initialize dictionary depending hug interface being used. Interface is provided by the
    # hug directive current_interface
    global dict_object

    logger.debug("check_against_directory = %s" % check_against_dictionary)  # TODO DEBUG TBREMOVED
    logger.debug("hug interface is %s" % hug_current_interface)
    # logger.debug("RECEIVED game=%s" % str(game))

    if hug_current_interface == "HTTP":
        # initiate a dictionary server object (zmq connect session)
        dict_object = DictionaryServer(lang)
    elif hug_current_interface == "Local":
        # load dictionary in global variable if not yet done
        if (dict_object is None) or (dict_object.lang != lang):
            dict_object = Trie(lang)
            logger.info("loading dictionary...")
            dict_object.load_from_json_word_list("word_list_15.json")  # TODO make file part of Trie Class
            logger.info("dictionary loaded")
    else:
        logger.critical("hug interface %s not implemented" % str(hug_current_interface))
        raise NotImplementedError("hug interface %s not implemented" % str(hug_current_interface))

    logger.debug("proposed_play is %s" % str(raw_proposed_play))

    type_of_play, proposed_word = raw_proposed_play

    # Build Solution object from the raw_proposed_play in case action is PLAY
    # for PLAY from Marshmallow we get only the Word Object and we must build crossword and jokerset
    # so as to build a full solution object
    if type_of_play == PLAY:
        word_proposed = proposed_word.word

        # Check that first play covers Position(7, 7) - center of board
        if game.board.nb_moves == 0 and Position(7, 7) not in word_proposed.positions():
            raise FirstPlayNotCoveringBoardCenter("First play must cover the center of the board")

        word_mask = proposed_word.word_mask
        joker_set = set()
        for i, (word_proposed_letter, word_mask_letter) in enumerate(zip(word_proposed, word_mask)):
            if word_mask_letter == " ":
                joker_set.add(JokerTuple(i, word_proposed_letter))

        line = Line(word_proposed.direction,
                    word_proposed.origin.row if word_proposed.direction.is_accross
                    else word_proposed.origin.col
                    )
        mask = game.board.build_mask_for_line(line)

        word_proposed_left_index = line.pos_2_index(word_proposed.origin)
        mask_2_be_scanned = mask[word_proposed_left_index:]

        word_is_correct = True
        for mask_item, letter in zip(mask_2_be_scanned, word_proposed):

            if mask_item.is_not_usable:
                word_is_correct = False
                break

            elif mask_item.has_letter:
                if letter != mask_item.data:
                    word_is_correct = False
                    break

            elif mask_item.is_cross_word:
                if letter not in mask_item:
                    word_is_correct = False
                    break

        if word_is_correct:  # build solution and play it

            # Build CrossWord list if needed
            cross_word_list = []
            for i, (mask_item, letter) in enumerate(zip(mask_2_be_scanned, word_proposed)):
                if mask_item.is_cross_word:
                    try:
                        index_of_main_word_line, word_str = mask_item.data[letter]  # KeyError if no word
                        if line.direction.is_accross:
                            row = line.line_index - index_of_main_word_line
                            col = word_proposed_left_index + i
                        else:
                            row = word_proposed_left_index + i
                            col = line.line_index - index_of_main_word_line
                        cross_word_list.append(
                            CrossWord(
                                Word(word_str,
                                     line.direction.ortho(),
                                     Position(row, col)
                                     ),
                                index_of_main_word_line
                            )
                        )
                    except KeyError:
                        pass

            proposed_play = (type_of_play,
                             Solution(board=game.board,
                                      main_word=word_proposed,
                                      cross_word_list=cross_word_list,
                                      joker_set=joker_set)
                             )

        else:
            raise CellUsedOrCrossWordInvalid(proposed_word)

        # Check for word and crosswords existence in dictionary if required
        if check_against_dictionary:
            if not dict_object.this_is_a_valid_word(word_proposed.text):
                raise WordNotInDictionary(word_proposed.text)
            for cw in cross_word_list:
                if not dict_object.this_is_a_valid_word(cw.word.text):
                    raise CrossWordNotInDictionary(cw.word.text)

    else:  # SKIP or CHANGE
        proposed_play = raw_proposed_play

    # let's play
    game_over = game.manual_play(player_name, proposed_play)

    return json.dumps({"game_over": game_over,
                       "game": GameSchema().dumps(game)})


@hug.post("/hint_4_player")
@hug.local()
def hint_4_player(player_name: fields.String(required=True),
                  game: fields.Nested(GameSchema(), required=True),
                  lang: fields.String(validate=OneOf(['FR', 'EN'])),
                  hug_current_interface,
                  response=None) -> str:
    """Return list of possible solution for player_name - sorted by descending value """

    # Initialize dictionary depending hug interface being used. Interface is provided by the
    # hug directive current_interface
    global dict_object

    logger.debug("hug interface is %s" % hug_current_interface)
    # logger.debug("RECEIVED game=%s" % str(game))

    if hug_current_interface == "HTTP":
        # initiate a dictionary server object (zmq connect session)
        dict_object = DictionaryServer(lang)
    elif hug_current_interface == "Local":
        # load dictionary in global variable if not yet done
        if (dict_object is None) or (dict_object.lang != lang):
            dict_object = Trie(lang)
            logger.info("loading dictionary...")
            dict_object.load_from_json_word_list("word_list_15.json")  # TODO make file a parameter
            logger.info("dictionary loaded")
    else:
        logger.critical("hug interface %s not implemented" % str(hug_current_interface))
        raise NotImplementedError("hug interface %s not implemented" % str(hug_current_interface))

    # let's get list of possible solution
    solution_list = game.board.get_sorted_list_of_solutions_for_rack(game.player_dict[player_name]['rack'])

    if solution_list:
        # return 4 best solutions
        return SolutionSchema(many=True, only=('main_word', 'value')).dumps(solution_list[-4:])
    else:
        return json.dumps([])


def print_exec_time(tps_avant: time, label_to_be_printed: str):
    tps_apres = time.time()
    tps_execution = tps_apres - tps_avant
    print("La fonction %s a mis %s pour s'exécuter" % (str(label_to_be_printed), str(tps_execution)))
    return


def pretty_print_json(json_raw_as_str: str) -> str:
    """Print a raw json in readable format with line breaks, indent and key sorted"""
    return json.dumps(json.loads(json_raw_as_str), sort_keys=True, indent=JSON_INDENT)


def load_trie():
    """load dictionary in memory"""
    global dict_object
    dict_object = Trie()
    logger.info("loading dictionary...")
    dict_object.load_from_json_word_list("word_list_15.json")
    logger.info("dictionary  loaded")


class DictionaryServer():
    """Implement access to dictionary server thru zmq sockets

     All Trie object methods that are for external usage must be implemented in DictionaryServer

     Depending on which hug interface is used (Local or HTTP) a local Trie object or an zmq DictionaryServer is
     used to access Dictionary resource. Assumption is that both object must provide the very same methods.
    """

    dictionary_server_dict = {  # TODO TO BE MOVED TO SOME EXTERNAL PARAMETER FILE
        "FR": ("127.0.0.1", "5555"),
        "EN": ("127.0.0.1", "5556")
    }

    def __init__(self, lang):
        """Initialize a zmq connection with dictionary server"""
        self.request_time_out = 2500
        self.request_retries = 3
        server_ip_address, server_tcp_port = __class__.dictionary_server_dict[lang]
        self.server_endpoint = "tcp://" + server_ip_address + ":" + server_tcp_port

    def _call_dictionary_server_method(self, method_str: str, kwargs: Dict):
        """Process method calls to Dictionary server"""

        context = zmq.Context()
        client = context.socket(zmq.REQ)
        client.connect(self.server_endpoint)
        poll = zmq.Poller()
        poll.register(client, zmq.POLLIN)

        sequence = 0
        retries_left = self.request_retries
        while retries_left:

            client.send_pyobj([method_str, kwargs])

            expect_reply = True
            while expect_reply:
                sequence += 1
                socks = dict(poll.poll(self.request_time_out))
                if socks.get(client) == zmq.POLLIN:

                    success, message_reply = client.recv_pyobj()
                    if success:
                        # logger.debug("success")  TODO UN-COMMENT
                        retries_left = 0
                        break
                    else:
                        logger.error("Internal Dictionary server error %s ", str(message_reply))
                        client.close()
                        raise DictionaryServerInternalError("Dictionary Server Internal error:%s" % str(
                            message_reply))  # catch in play_4_player to return HTTP 500
                else:
                    logger.warning("no response from server, retrying... - attempt %s" % str(sequence))
                    # socket migth be confused - close and remove
                    client.setsockopt(zmq.LINGER, 0)
                    client.close()
                    poll.unregister(client)
                    retries_left -= 1
                    if retries_left == 0:
                        logger.error("Dictionary Server seems to be offline, abandoning after %s attempt"
                                     % str(self.request_retries))
                        raise DictionaryServerNotResponding("Dictionary Server not responding")
                    logger.warning("Reconnecting and resending - attempt number %s " %
                                   str(sequence))
                    # create new connection
                    client = context.socket(zmq.REQ)
                    client.connect(self.server_endpoint)
                    poll.register(client, zmq.POLLIN)
                    client.send_pyobj([method_str, kwargs])

        context.destroy()

        return message_reply

    def this_is_a_valid_word(self, string: str) -> bool:
        """call this_is_a_valid_word method against Dictionary server"""
        return self._call_dictionary_server_method("this_is_a_valid_word",
                                                   {"string": string})

    def possible_word_set_from_string(self, string: str) -> Dict[str, WordCouple]:
        """call possible_word_set_from_string method against Dictionary server"""
        return self._call_dictionary_server_method("possible_word_set_from_string",
                                                   {"string": string})

    def possible_words_for_mask_with_rack(self,
                                          mask: 'Mask',
                                          tile_list: List[str],
                                          min_length: int) -> Set[str]:
        """call possible_words_for_mask_with_rack method against Dictionary server"""
        return self._call_dictionary_server_method("possible_words_for_mask_with_rack",
                                                   {"mask": mask,
                                                    "tile_list": tile_list,
                                                    "min_length": min_length})


if __name__ == "__main__":
    logger.info("scrabble.py loaded...")

# TODO implement hug customized exception so that javascript client can decode them
# @hug.exception(Exception):
# def my_handler(exception):
#      return {'my_exception': 'format'}
# from https://github.com/timothycrosley/hug/issues/227
#
# print(start_game("french", "thib"))
#
# sys.exit(234)

# atexit.register(profile.print_stats)
#
# players_ordered_dict = OrderedDict({"Thibault": "auto",
#                                     # "Valérie": "auto",
#                                     # "Gaïa": "auto",
#                                     # "Valentin": "auto",
#                                     "Unbeatable": "auto"})
#
# load_trie()
#
# game_duration = []
# for i in range(19):
#     t = time.time()
#     game = Game(players_dict=players_ordered_dict)
#     while not game.manual_play(player_name='Thibault', play_instruction=(SKIP, None)):
#         pass
#     game_duration.append(time.time() - t)
#     print(game.game_record.get_formated_game_summary())
#
# print(game_duration)
# print("max=", max(game_duration))
# print("min=", min(game_duration))
# print("avg=", sum(game_duration) / len(game_duration))
# players_ordered_dict = OrderedDict({"Thibault": "manual",
#                                     "Valérie": "auto",
#                                     "Gaïa": "auto",
#                                     "Valentin": "auto",
#                                     "Unbeatable": "auto"})
#
# dict = Trie()
# print("loading dict")
# dict.load_from_json_word_list("word_list_15.json")
# print("dict loaded")
#
# for _ in range(50):
#     # game = Game(players_ordered_dict, dict)
#     game = Game(players_dict=players_ordered_dict)
#
#     while not game.manual_play("Thibault", (SKIP, None)):
#         print("PLAY")
#         # game = Game(players_list, dict)
#         # game(play_list_filename="test.json")
#
#     print(game.game_record.get_formated_game_summary())
#     board_schema = BoardSchema()
#     # res = board_schema.dump(game.board)
#     # pprint(res)
#     res = GameSchema().dumps(game)
#     # pprint(res)
#     print(json.dumps(res.data, indent=JSON_INDENT))
#     loaded = GameSchema().load(res.data)
#     print(loaded.data)
#     assert game == loaded.data

# print(game_duration)
# print("max=", max(game_duration))
# print("min=", min(game_duration))
# print("avg=", sum(game_duration) / len(game_duration))

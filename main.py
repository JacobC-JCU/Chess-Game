import pygame as p
from abc import ABC, abstractmethod
import time
import re
import os
import json

# Konstanty pro velikost okna a šachovnice
width = 800
height = 800
board_size = 8
square_size = height // board_size
max_fps = 60

# Vynulování hodnot
eliminate_pieces = []
eliminate_pieces_white = []
eliminate_pieces_black = []
black_check = False
white_check = False

# Základní nastavení šachovnice a fontu
color_1 = p.Color((174, 40, 47))
color_2 = p.Color((214, 166, 62))
primary_font = "fonts/harry.TTF"

# Slovník pro uložení obrázků
images = {}

def load_images():
    # Funkce na load obrázku (mimo hlavní smyčku kvůli lepší zátěži)
    pieces = ["wp", "wR", "wN", "wB", "wK", "wQ", "bp", "bR", "bN", "bB", "bK", "bQ"]
    for piece in pieces:
        try:
            images[piece] = p.transform.scale(p.image.load(f"images/{piece}.png"), (square_size, square_size))
        except FileNotFoundError:
            print(f"Chyba: Obrázek {piece}.png nebyl nalezen!")

class GameState:
    def __init__(self):
        # Základní nastavení herních stavů a logiky šachovnice
        global black_check, white_check
        black_check = False
        white_check = False
        self.whiteToMove = True

        # Schéma šachovnice a rozvržení figurek
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["xx", "xx", "xx", "xx", "xx", "xx", "xx", "xx"],
            ["xx", "xx", "xx", "xx", "xx", "xx", "xx", "xx"],
            ["xx", "xx", "xx", "xx", "xx", "xx", "xx", "xx"],
            ["xx", "xx", "xx", "xx", "xx", "xx", "xx", "xx"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]
        ]   
        self.moveLog = []

        # Inicializace seznamů pro pozice bílých a černých figur
        self.obsazene_pozice_white = []
        self.obsazene_pozice_black = []
        self.possible_moves_white = []
        self.possible_moves_black = []                        
        self.possible_moves_black_king_check = []
        self.possible_moves_white_king_check = []

        self.position_bk = []
        self.position_wk = []
        self.attack_to_bk = []
        self.attack_to_wk = []

        self.safe_B = []
        self.safe_W = []
        
        # Nastavení časů hráčů a nulováný error message
        self.error_message = None
        self.error_message_time = 0 

        self.white_time = 15 * 60
        self.black_time = 15 * 60  
        self.last_time = time.time() 

        self.update_occupied_positions()
    def reset(self):
        # Funkce pro reset hry
        global black_check, white_check
        black_check = False
        white_check = False

        # Schéma šachovnice a rozvržení figurek
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["xx", "xx", "xx", "xx", "xx", "xx", "xx", "xx"],
            ["xx", "xx", "xx", "xx", "xx", "xx", "xx", "xx"],
            ["xx", "xx", "xx", "xx", "xx", "xx", "xx", "xx"],
            ["xx", "xx", "xx", "xx", "xx", "xx", "xx", "xx"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]
        ]   
        self.moveLog = []

        # Inicializace seznamů pro pozice bílých a černých figur
        self.obsazene_pozice_white = []
        self.obsazene_pozice_black = []
        self.possible_moves_white = []
        self.possible_moves_black = []                        
        self.possible_moves_black_king_check = []
        self.possible_moves_white_king_check = []

        self.position_bk = []
        self.position_wk = []
        self.attack_to_bk = []
        self.attack_to_wk = []

        self.safe_B = []
        self.safe_W = []

        self.error_message = None
        self.error_message_time = 0 

        self.white_time = 15 * 60
        self.black_time = 15 * 60  
        self.last_time = time.time() 

        self.update_occupied_positions()    

    def draw_error_message(self, message, screen):
        current_time = time.time()  # Získání aktuálního času
        
        # Skytí error message po 1 sekundě
        if self.error_message and current_time - self.error_message_time > 1:
            self.error_message = None
            return False
        
        # Vykreslení error message
        if self.error_message:
            font_error = p.font.Font(primary_font, 30)
            error_text = font_error.render(self.error_message, True, p.Color("red"))
            error_text_rect = error_text.get_rect()
            error_text_rect.center = (1100, 115)
            screen.blit(error_text, error_text_rect)
        else:
            # Pokud je nová zpráva, nastaví se
            if message:
                self.error_message = message
                self.error_message_time = current_time

    def save_move_log(self, gs, filename="game_log.json"):
        # Pokud není v moveLog žádný tah, soubor se neuloží
        if not self.moveLog:
            return
        
        # Vytvoření složky logs, pokud neexistuje
        if not os.path.exists("logs"):
            os.makedirs("logs")

        # Přidání údajů o hře do moveLog       
        game_stats = {
        "whiteToMove": gs.whiteToMove,
        "white_time": gs.white_time,
        "black_time": gs.black_time,
        "eliminated": eliminate_pieces
        }

        # Funkce pro získání pozic všech figurek na šachovnici 
        positions = []
        self.update_occupied_positions()
        for row in range(board_size):
            for col in range(board_size):
                piece = gs.board[row][col]
                if piece!= "xx":  # 
                    positions.append((row, col, piece))

        # Uložení všech dat do dílčích JSON 
        with open(os.path.join("logs", filename), "w") as file:
            json.dump(self.moveLog, file, indent=4)

        with open(os.path.join("logs", "positions.json"), "w") as file_xy:
            json.dump(positions, file_xy, indent=4)

        with open(os.path.join("logs", "game_stats.json"), "w") as file_stats:
            json.dump(game_stats, file_stats, indent=4)
    def update_occupied_positions(self):
        # Roztřídení figurek podle barvy a uložení jejich aktuálních pozic
        self.obsazene_pozice_white = []
        self.obsazene_pozice_black = []


        for row in range(board_size):
            for col in range(board_size):
                piece = self.board[row][col]
                if piece != "xx":  # Pokud není pole prázdné
                    if piece[0] == 'w':  # Bílé figury
                        if piece == "wK":
                            continue
                        self.obsazene_pozice_white.append((row, col))
                    elif piece[0] == 'b':  # Černé figury
                        if piece == "bK":
                            continue
                        self.obsazene_pozice_black.append((row, col))
    def undo_last_move(self, gs):
        """
        ************************************
        * Aktuálně běz využití,            *
        * možná implementace do budoucna   *
        * pro vrácení tahů..               *
        ************************************
        """

        global black_check, white_check

        # Pojistka pro případ absence tahu k vrácení 
        if not self.moveLog:
            return False  

        last_move = self.moveLog[-1]

        # Regulární výraz pro extrahování informací o tahu
        pattern = r'([wb][pRNBQK])\s*-\s*\((\d+),\s*(\d+)\)\s*-\s*\((\d+),\s*(\d+)\)'
        match = re.search(pattern, last_move)

        # Pokud je nalezena schoda..
        if match:
            # Uložení typu a souřadnic figurky do proměných
            piece = match.group(1)
            start_row = int(match.group(2))
            start_col = int(match.group(3))
            end_row = int(match.group(4))
            end_col = int(match.group(5))

            # Nulování šachu
            black_check = False
            white_check = False

            # Vrácení tahu
            self.whiteToMove = not self.whiteToMove
            removed_piece = None
            self.board[start_row][start_col] = piece

            # Kontrola pro případ, že daným tahem byla vyřazená figurka
            if eliminate_pieces:
                color_piece = eliminate_pieces[-1]
                if (piece[0] == "w" and color_piece[0] == "b"):
                    removed_piece = color_piece

                     # Odstraníme ji ze seznamu vyřazených
                    eliminate_pieces.remove(color_piece)

                if (piece[0] == "b" and color_piece[0] == "w"):
                    removed_piece = color_piece
                    # Odstraníme ji ze seznamu vyřazených
                    eliminate_pieces.remove(color_piece)
                    

            # Pokud byla figurka odstraněna, vrátíme ji na původní místo
            if removed_piece:
                self.board[end_row][end_col] = removed_piece 
            else:
                self.board[end_row][end_col] = "xx"
            
            # Aktualizace pozic a odstranění tahu z logu
            self.update_occupied_positions()
            self.moveLog.pop()

            return True
    def check(self, gs):
        global black_check, white_check
        # Vynulování seznamu s pozicemi figurek
        self.possible_moves_white = []
        self.possible_moves_black = []                        
        self.possible_moves_black_king_check = []
        self.possible_moves_white_king_check = [] 
        self.position_bk = ""
        self.position_wk = ""
        self.attack_to_bk = []
        self.attack_to_wk = []
        self.safe_B = []
        self.safe_W = []

        # Zjištění pozic králůs
        for row in range(board_size):
            for col in range(board_size):
                piece = self.board[row][col]
                if piece == "bK":
                    self.position_bk = (row, col)
                elif piece == "wK":
                    self.position_wk = (row, col)

        # Zjištění všech možných tahů všech figurek
        for row in range(board_size):
            for col in range(board_size):
                piece = self.board[row][col]

                if piece == "wp":
                    for x in range(board_size):
                        for y in range(board_size):
                            # Kontrola diagonálního útoku
                            if abs(y - col) == 1 and (x - row) == -1:
                                if x == row and y == col:
                                    continue
                                if (x, y) == self.position_bk:
                                    self.attack_to_bk.append(f"wp - ({row}, {col})")
                                self.possible_moves_white.append((x, y))
                                self.safe_W.append((x, y))
 
                elif piece == "bp":
                    for x in range(board_size):
                        for y in range(board_size):
                            # Kontrola diagonálního útoku
                            if abs(y - col) == 1 and (x - row) == 1:
                                if x == row and y == col:
                                    continue
                                if (x, y) == self.position_wk:
                                    self.attack_to_wk.append(f"bp - ({row}, {col})")

                                self.possible_moves_black.append((x, y))
                                self.safe_B.append((x, y))

                elif piece == "wR":
                    # Všechny 4 možné tahy pro věž
                    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)] 
                    for dx, dy in directions:
                        x, y = row, col
                        while 0 <= x < board_size and 0 <= y < board_size:
                            x += dx
                            y += dy
                            if not (0 <= x < board_size and 0 <= y < board_size):
                                break
                            if Rook.legal_movement(Rook("w"), row, col, x, y, self.board, self.obsazene_pozice_black, self.obsazene_pozice_white, gs):
                                if (x, y) in self.obsazene_pozice_white:
                                    self.safe_W.append((x, y))
                                    break 
                                if (x, y) == self.position_bk:
                                    self.attack_to_bk.append(f"wR - ({row}, {col})")
                                if (x, y) == self.position_wk:
                                    break
                                self.possible_moves_white.append((x, y))

                elif piece == "bR":
                    # Všechny 4 možné směry pro věž
                    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                    for dx, dy in directions:
                        x, y = row, col
                        while 0 <= x < board_size and 0 <= y < board_size:
                            x += dx
                            y += dy
                            if not (0 <= x < board_size and 0 <= y < board_size):
                                break
                            if Rook.legal_movement(Rook("b"), row, col, x, y, self.board, self.obsazene_pozice_black, self.obsazene_pozice_white, gs):
                                if (x, y) in self.obsazene_pozice_black:
                                    self.safe_B.append((x, y))
                                    
                                if (x, y) == self.position_wk:
                                    self.attack_to_wk.append(f"wR - ({row}, {col})")
                                if (x, y) == self.position_bk:
                                    break
                                self.possible_moves_black.append((x, y))

                elif piece == "wN":
                    for x in range(board_size):
                        for y in range(board_size):
                            osa1 = abs(row - x)
                            osa2 = abs(col - y)
                            if osa1 == 2 and osa2 == 1 or osa1 == 1 and osa2 == 2:
                                if x == row and y == col:
                                    continue
                                if (x, y) in self.obsazene_pozice_white:
                                    self.safe_W.append((x, y))
                                    break

                                if (x, y) == self.position_bk:
                                    self.attack_to_bk.append(f"wN - ({row}, {col})")
                                
                                if (x, y) == self.position_wk:
                                    break

                                self.possible_moves_white.append((x, y))

                elif piece == "bN":
                    for x in range(board_size):
                        for y in range(board_size):
                            osa1 = abs(row - x)
                            osa2 = abs(col - y)
                            if osa1 == 2 and osa2 == 1 or osa1 == 1 and osa2 == 2:
                                if x == row and y == col:
                                    continue
                                if (x, y) in self.obsazene_pozice_black:
                                    break
                                if (x, y) == self.position_wk:
                                    self.attack_to_wk.append(f"bN - ({row}, {col})")

                                if (x, y) == self.position_bk:
                                    break
                                    
                                
                                self.possible_moves_black.append((x, y))

                elif piece == "wB":
                    # Všechny 4 směry pro střelce
                    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
                    for dx, dy in directions:
                        x, y = row, col
                        while 0 <= x < board_size and 0 <= y < board_size:
                            x += dx
                            y += dy
                            if not (0 <= x < board_size and 0 <= y < board_size):
                                break
                            if Strelec.legal_movement(Strelec("w"), row, col, x, y, self.board, self.obsazene_pozice_black, self.obsazene_pozice_white, gs):
                                if (x, y) in self.obsazene_pozice_white:
                                    self.safe_W.append((x, y))
                                    break 
                                if (x, y) == self.position_bk:
                                    self.attack_to_bk.append(f"wB - ({row}, {col})")
                                if (x, y) == self.position_wk:
                                    break
                                self.possible_moves_white.append((x, y))

                elif piece == "bB":
                    # Všechny 4 směry pro střelce
                    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
                    for dx, dy in directions:
                        x, y = row, col
                        while 0 <= x < board_size and 0 <= y < board_size:
                            x += dx
                            y += dy
                            if not (0 <= x < board_size and 0 <= y < board_size):
                                break
                            if Strelec.legal_movement(Strelec("b"), row, col, x, y, self.board, self.obsazene_pozice_black, self.obsazene_pozice_white, gs):
                                if (x, y) in self.obsazene_pozice_black:
                                    self.safe_B.append((x, y))
                                    break 
                                if (x, y) == self.position_wk:
                                    self.attack_to_wk.append(f"wB - ({row}, {col})")
                                if (x, y) == self.position_bk:
                                    break 
                                self.possible_moves_black.append((x, y))

                elif piece == "wQ":
                    # Všech 8 směrů pro královnů
                    directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
                    for dx, dy in directions:
                        x, y = row, col
                        while 0 <= x < board_size and 0 <= y < board_size:
                            x += dx
                            y += dy
                            if not (0 <= x < board_size and 0 <= y < board_size):
                                break
                            if Quuen.legal_movement(Quuen("w"), row, col, x, y, self.board, self.obsazene_pozice_black, self.obsazene_pozice_white, gs):
                                if (x, y) in self.obsazene_pozice_white:
                                    self.safe_W.append((x, y))
                                    break 
                                if (x, y) == self.position_bk:
                                    self.attack_to_bk.append(f"wQ - ({row}, {col})")
                                if (x, y) == self.position_wk:
                                    break 
                                self.possible_moves_white.append((x, y))
 
                elif piece == "bQ":
                    # Všech 8 směrů pro královnů
                    directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)] 
                    for dx, dy in directions:
                        x, y = row, col
                        while 0 <= x < board_size and 0 <= y < board_size:
                            x += dx
                            y += dy
                            if not (0 <= x < board_size and 0 <= y < board_size):
                                break
                            if Quuen.legal_movement(Quuen("b"), row, col, x, y, self.board, self.obsazene_pozice_black, self.obsazene_pozice_white, gs):
                                if (x, y) in self.obsazene_pozice_black:
                                    self.safe_B.append((x, y))
                                    break 
                                if (x, y) == self.position_wk:
                                    self.attack_to_wk.append(f"wQ - ({row}, {col})")
                                if (x, y) == self.position_bk:
                                    break 
                                self.possible_moves_black.append((x, y))
 
                elif piece == "wK":
                    for x in range(board_size):
                        for y in range(board_size):
                            if King.legal_movement(King("w"), row, col, x, y, self.board, self.obsazene_pozice_black, self.obsazene_pozice_white, gs):
                                if x == row and y == col:
                                    continue
                                if (x, y) in self.obsazene_pozice_white:
                                    self.safe_W.append((x, y))


                                if (x, y) == self.position_bk:
                                    self.attack_to_bk.append(f"wK" - ({row}, {col}))


                                self.possible_moves_white_king_check.append((x, y))
                    
                elif piece == "bK":
                    for x in range(board_size):
                        for y in range(board_size):
                            if King.legal_movement(King("b"), row, col, x, y, self.board, self.obsazene_pozice_black, self.obsazene_pozice_white, gs):
                                if x == row and y == col:
                                    continue
                                if (x, y) in self.obsazene_pozice_black:
                                    self.safe_B.append((x, y))

                                if (x, y) == self.position_wk:
                                    self.attack_to_wk.append(f"bK - ({row}, {col})")
                              
                                
                                self.possible_moves_black_king_check.append((x, y))

        # Smazání duplicitních záznamů
        self.possible_moves_white = list(set(self.possible_moves_white))
        self.possible_moves_black = list(set(self.possible_moves_black))
        self.possible_moves_black_king_check = list(set(self.possible_moves_black_king_check))
        self.possible_moves_white_king_check = list(set(self.possible_moves_white_king_check))
        self.safe_B = list(set(self.safe_B))
        self.safe_W = list(set(self.safe_W))
                    
        # Kontola, zda je král v šachu
        if self.position_bk in self.possible_moves_white:
                # Kontrola, zda není mat
                self.check_mate(gs)
                # Nastavení šachu
                draw_right_menu(gs, "The black king's check")
                black_check = True
                
        elif piece == "wK":
            if self.attack_to_wk in self.possible_moves_black:
                # Kontrola, zda není mat
                self.check_mate(gs)
                # Nastavení šachu
                draw_right_menu(gs, "The white king's check")
                white_check = True
    def get_path_to_king(self, piece_pos, king_pos):
        # Funkce, co počítá cestu mezi dvěmi figurky
        path = []
        row1, col1 = piece_pos
        row2, col2 = king_pos
        
        row_step = col_step = 0 

        if row1 == row2:  # Horizontální pohyb (věž/dáma)
            col_step = 1 if col2 > col1 else -1
        elif col1 == col2:  # Vertikální pohyb (věž/dáma)
            row_step = 1 if row2 > row1 else -1
        elif abs(row2 - row1) == abs(col2 - col1):  # Diagonální pohyb (střelec/dáma)
            row_step = 1 if row2 > row1 else -1
            col_step = 1 if col2 > col1 else -1
        else:
            # Cesta neexistuje
            return [] 

        # Generování cesty mezi figurkami
        r, c = row1 + row_step, col1 + col_step
        while (r, c) != (row2, col2):
            path.append((r, c))
            r += row_step
            c += col_step

        return path
    def check_mate(self, gs):
        # Ověřování šach matu
        global play_option
        seznam = []
        # Pokud je černý král v šachu
        if black_check:
            #Kontroluje možné tahy černého krále
            for move in self.possible_moves_black_king_check:
                if move in self.obsazene_pozice_black:
                    continue
                if move in self.possible_moves_white:
                    continue
                if move in self.obsazene_pozice_white and move in self.safe_W:
                    continue
                seznam.append(move)
            # Pokud žádné tahy nejsou
            if not seznam:
                if self.attack_to_bk:
                    match = re.search(r'\((\d+), (\d+)\)', self.attack_to_bk[-1])
                    # Zjistí, která figurka na krále útočí
                    if match:
                        coordinates = (int(match.group(1)), int(match.group(2)))
                        # Pokud může být figurka vyřazená černou figurkou, vrátí False
                        if coordinates in self.possible_moves_black:
                                return False  
                        # Spočítá se cesta ke králi
                        path = self.get_path_to_king(coordinates, self.position_bk)
                        for move in path:
                            if move in self.possible_moves_black:
                                # Existuje tah na obranu, tedy není mat
                                return False

                        # Šach mat nastal -  Provedení příslušných kroků
                        draw_right_menu(gs, "Šach Mat - Bílý vyhráli")
                        play_option = "end_game"
                        check_mate_sound = p.mixer.Sound("sounds/Checkmate.mp3")
                        check_mate_sound.set_volume(0.4)

                        check_mate_sound_2 = p.mixer.Sound("sounds/Win.mp3")
                        check_mate_sound_2.set_volume(0.4)

                        channel = p.mixer.Channel(0) 
                        channel.play(check_mate_sound)

                        while channel.get_busy():
                            pass 

                        channel.play(check_mate_sound_2, -1)


        if white_check:
            # Kontroluje možné tahy bílého krále
            for move in self.possible_moves_white_king_check:
                if move in self.obsazene_pozice_white:
                    continue
                if move in self.possible_moves_black:
                    continue
                if move in self.obsazene_pozice_black and move in self.safe_B:
                    continue
                seznam.append(move)

            # Pokud žádné tahy nejsou
            if not seznam:
                if self.attack_to_wk:
                    # Zjistí, která figurka na krále útočí
                    match = re.search(r'\((\d+), (\d+)\)', self.attack_to_wk[-1])
                    if match:
                        coordinates = (int(match.group(1)), int(match.group(2)))
                        # Pokud může být figurka vyřazená bílou figurkou, vrátí False
                        if coordinates in self.possible_moves_white:
                            return False
                        # Spočítá cestu ke králi
                        path = self.get_path_to_king(coordinates, self.position_wk)
                        for move in path:
                            if move in self.possible_moves_white:
                                # Existuje tah na obranu, tedy není mat
                                return False  

                        
                        # Šach mat nastal - Provedení příslušných kroků
                        draw_right_menu(gs, "Šach Mat - Černí vyhráli")
                        play_option = "end_game"
                        check_mate_sound = p.mixer.Sound("sounds/Checkmate.mp3")
                        check_mate_sound.set_volume(0.4)

                        check_mate_sound_2 = p.mixer.Sound("sounds/Win.mp3")
                        check_mate_sound_2.set_volume(0.4)

                        channel = p.mixer.Channel(0) 
                        channel.play(check_mate_sound)

                        while channel.get_busy():
                            pass

                        channel.play(check_mate_sound_2, -1)


class LoadGame:
    def __init__(self, screen, gs):
        self.gs = gs
        self.test = "XXX"
        self.screen = screen
        self.loadgame_rect = p.Rect(100, 200, 600, 400)
        self.buttons = {
            "New Game": (400, 500, "game_player_vs_player"),
            "Load Game": (700, 500, "log_upload")}

    def load_log(self):
        # Nahrává uloženou hru z JSON dat uložené v logs
        global eliminate_pieces
        # Zkusí otevřít logy
        try:
            # Načte se soubor s pozicemi figurek
            with open("logs/positions.json", "r", encoding="utf-8") as file:
                # Vše se uloží do game_data
                game_data = json.load(file)
                # Vynuluje všechny pozice na šachovnici - V důsledku gs.__init__ se při load_game načtou základní pozice figurek, což je nežádoucí pro náhrávání dat z nějaké minulé hry
                for row in range(board_size):
                    for col in range(board_size):
                        self.gs.board[row][col] = "xx"
                # Vezme každou figurku a umístí ji na šachovnici
                for zaznam in game_data:
                    piece = zaznam[2]
                    start_row = zaznam[0]
                    start_col = zaznam[1]
                    self.gs.board[start_row][start_col] = piece

                    # Uložení hodnot do proměnných
                    self.piece = piece
                    self.start_row = start_row
                    self.start_col = start_col

                
                self.gs.update_occupied_positions()
            # Načte se soubor se stavem hry
            with open("logs/game_stats.json", "r", encoding="utf-8") as file:
                # vše se uloží do game_stats
                game_stats = json.load(file)
                # Nastaví parametry hry
                self.gs.whiteToMove = game_stats.get("whiteToMove", None)
                self.gs.white_time = game_stats.get("white_time", 0)
                self.gs.black_time = game_stats.get("black_time", 0)
                eliminate_pieces = game_stats.get("eliminated",0)
            # Našte se soubor s moveLogem
            with open("logs/game_log.json", "r", encoding="utf-8") as file:
                # Vše se uloží do game_log
                game_log = json.load(file)
                # Nastaví log, aby odpovídal odehrátím tahů
                self.gs.moveLog = game_log
 
        except Exception as e:
            # Pojistka pro případ absence souborů
            print(f"Error loading log: {e}")

    def draw_menu(self, screen):
        p.display.flip()
        background = p.image.load("images/wallpaper.jpg").convert_alpha()
        background = p.transform.scale(background, (1200, 800))
        background.set_alpha(255)  # Nastavení průhlednosti

        for event in p.event.get():
            if event.type == p.QUIT:
                return "exit"
            elif event.type == p.MOUSEBUTTONDOWN:
                x, y = event.pos
                for text, (bx, by, action) in self.buttons.items():
                    if bx <= x <= bx + 100 and by <= y <= by + 40:
                        if action == "log_upload":
                            self.load_log()
                            action = "game_player_vs_player"
                        return action  

        # Vykreslení pozadí
        screen.blit(background, (0, 0))

        # Černé průhledné menu
        menu_surface = p.Surface((1200, 800), p.SRCALPHA)
        menu_surface.fill((0, 0, 0, 80))
        screen.blit(menu_surface, (0, 0))

        primary_font  # Zadejte správný font
        font = p.font.Font(primary_font, 60)
        font_wizzard = p.font.Font(primary_font, 120)
        main_font = p.font.Font(primary_font, 150)

        main_text = main_font.render("Chess Game", True, p.Color("orange"))
        main_text_rect = main_text.get_rect(center=(600, 350))
        wizard_text = font_wizzard.render("Wizard's", True, p.Color("purple"))
        wizard_text_rect = wizard_text.get_rect(center=(600, 200))

        screen.blit(main_text, main_text_rect)
        screen.blit(wizard_text, wizard_text_rect)

        # Vykreslení tlačítek
        for text, (x, y, action) in self.buttons.items():
            btn_text = font.render(text, True, p.Color("white"))
            btn_text_rect = btn_text.get_rect(center=(x + 50, y + 20))

            border_rect = btn_text_rect.inflate(20, 20)
            p.draw.rect(screen, p.Color("red"), border_rect, border_radius=10)

            screen.blit(btn_text, btn_text_rect)

        # Logo
        logo = p.image.load("images/logo.png")
        logo = p.transform.scale(logo, (100, 100))
        logo_rect = logo.get_rect(center=(600, 700))
        screen.blit(logo, logo_rect)

        p.display.flip()

class Menu:
    # Úvodní menu
    def __init__(self):
        self.menu_rect = p.Rect(100, 200, 600, 400)
    @staticmethod
    def draw_menu(screen):
        # Vykreslí pozadí menu
        background = p.image.load("images/wallpaper.jpg").convert_alpha()
        background = p.transform.scale(background, (1200, 800))
        background.set_alpha(255)
        
        # Definujeme slovník s tlačítky
        buttons = {
            "Play game": (400, 500, "load_game"),
            "The end": (700, 500, "exit"),
        }
        
        # Kontrolujeme souřadnice kliknutí, zda jsou v oblasti tlačítek
        for event in p.event.get():
            if event.type == p.QUIT:
                return "exit"
            elif event.type == p.MOUSEBUTTONDOWN:
                x, y = event.pos
                for text, (bx, by, action) in buttons.items():
                    if bx <= x <= bx + 100 and by <= y <= by + 40:
                        # Vrátí "game_player_vs_player" nebo "exit"
                        return action 

        screen.blit(background, (0, 0))

        # Ztmavení pozadí
        menu_surface = p.Surface((1200, 800), p.SRCALPHA)
        menu_surface.fill((0, 0, 0, 80))
        screen.blit(menu_surface, (0, 0)) 

        # Nastavení fontů
        font = p.font.Font(primary_font, 60)
        font_wizzard = p.font.Font(primary_font, 120)
        main_font = p.font.Font(primary_font, 150)

        # Vykreslení textů
        main_text = main_font.render("Chess Game", True, p.Color("orange"))
        main_text_rect = main_text.get_rect(center=(600, 350))
        wizard_text = font_wizzard.render("Wizard's", True, p.Color("purple"))
        wizard_text_rect = wizard_text.get_rect(center=(600, 200))
        screen.blit(main_text, main_text_rect)
        screen.blit(wizard_text, wizard_text_rect)

        for text, (x, y, action) in buttons.items():
            btn_text = font.render(text, True, p.Color("white"))
            btn_text_rect = btn_text.get_rect(center=(x + 50, y + 20))

            # Vykreslení kulatého rámečku
            border_rect = btn_text_rect.inflate(20, 20)  # Zvýšení velikosti rámečku
            p.draw.rect(screen, p.Color("red"), border_rect, border_radius=10)
            screen.blit(btn_text, btn_text_rect.topleft)

        # Vykreslení loga
        logo = p.image.load("images/logo.png")
        logo = p.transform.scale(logo, (100, 100))
        logo_rect = logo.get_rect()
        logo_rect.center = (600, height - 100)
        screen.blit(logo, logo_rect)

        # Aktualizace obrazu
        p.display.flip()
        return None

class Piece(ABC):
    def __init__(self, color):
        self.color = color

    # Zajištujeme povinnost přítomnosti legal_moovment pro každou classu, která dědí z Piece
    @abstractmethod
    def legal_movement(self, start_row, start_col, end_row, end_col, board, obsazene_pozice_black, obsazene_pozice_white, gs):
        pass
    
    # Zajištujeme zavolání sprívné classy, konkrétně její metody legal_moovment
    def choose_piece(self, start_row, start_col, end_row, end_col, piece, board, obsazene_pozice_black, obsazene_pozice_white):
        piece_classes = {
            'p': Pawn,
            'R': Rook,
            'N': Jezdec,
            'B': Strelec,
            'K': King,
            'Q': Quuen  
        }

        piece_type = piece[1]

        if piece_type in piece_classes:
            piece_object = piece_classes[piece_type](piece[0])
            return piece_object.legal_movement(start_row, start_col, end_row, end_col, board, obsazene_pozice_black, obsazene_pozice_white, gs = None)
        
        return False


    def eliminate(self, board, end_row, end_col):
        global eliminate_pieces
        # Přidá vyřazenou figurku do seznamu eliminated_pieces
        if board[end_row][end_col] != "xx":
            eliminate_pieces.append(board[end_row][end_col])

class Pawn(Piece):
    # Pěšec
    def __init__(self, color):
        # Sdědí barvu z Piece
        super().__init__(color)

    def legal_movement(self, start_row, start_col, end_row, end_col, board, obsazene_pozice_black, obsazene_pozice_white, gs):
        # Výchozí řádek pěšce
        if self.color == "w":
            enemy_positions = obsazene_pozice_black
            direction = -1
            start_row_initial = 6
        else:
            enemy_positions = obsazene_pozice_white
            direction = 1
            start_row_initial = 1

        # Diagonální útok
        if abs(end_col - start_col) == 1 and (end_row - start_row) == direction:
            if (end_row, end_col) in enemy_positions:
                return True

        # Pohyb vpřed o jedno políčko
        if end_col == start_col and (end_row - start_row) == direction:
            if (end_row, end_col) not in obsazene_pozice_black and (end_row, end_col) not in obsazene_pozice_white:
                return True

        # Pohyb o 2 pole z počáteční pozice
        if end_col == start_col and (end_row - start_row) == 2 * direction and start_row == start_row_initial:
            if (start_row + direction, start_col) not in obsazene_pozice_black and (start_row + direction, start_col) not in obsazene_pozice_white:
                if (end_row, end_col) not in obsazene_pozice_black and (end_row, end_col) not in obsazene_pozice_white:
                    return True

        return False

class Rook(Piece):
    # Věž
    def __init__(self, color):
        # Zdědí barvu z Piece
        super().__init__(color)

    def legal_movement(self, start_row, start_col, end_row, end_col, board, obsazene_pozice_black, obsazene_pozice_white, gs):
        # Vertikální pohyb
        if start_col == end_col:
            step = 1 if end_row > start_row else -1
            for i in range(start_row + step, end_row, step):
                if (i, start_col) == gs.position_bk or (i, start_col) == gs.position_wk:
                    return False
                if (i, start_col) in obsazene_pozice_black or (i, start_col) in obsazene_pozice_white:
                    return False
            return True
        
        # Horizontální pohyb
        if start_row == end_row:
            step = 1 if end_col > start_col else -1
            for i in range(start_col + step, end_col, step):
                if (start_row, i) == gs.position_bk or (start_row, i) == gs.position_wk:
                    return False
                elif (start_row, i) in obsazene_pozice_black or (start_row, i) in obsazene_pozice_white:
                    return False
            return True
        
        return False

class Jezdec(Piece):
    # Jezdec
    def __init__(self, color):
        # Zdědí barvu z Piece
        super().__init__(color)

    def legal_movement(self, start_row, start_col, end_row, end_col, board, obsazene_pozice_black, obsazene_pozice_white, gs):
        # Ověření pohybu pomocí os
        osa1 = abs(end_row - start_row)
        osa2 = abs(end_col - start_col)
        if osa1 == 2 and osa2 == 1 or osa1 == 1 and osa2 == 2:
            return True
        return False

class Strelec(Piece):
    # Střelec
    def __init__(self, color):
        # Zdědí batvu z Piece
        super().__init__(color)

    def legal_movement(self, start_row, start_col, end_row, end_col, board, obsazene_pozice_black, obsazene_pozice_white, gs):
        # Kontrola diagonální pohybu
        if abs(end_row - start_row) == abs(end_col - start_col):
            row_step = 1 if end_row > start_row else -1
            col_step = 1 if end_col > start_col else -1
            # Kontroluje, zda je cesta volná
            for i, j in zip(range(start_row + row_step, end_row, row_step), range(start_col + col_step, end_col, col_step)):
                if (i, j) == gs.position_bk or (i, j) == gs.position_wk:
                    return False
                elif (i, j) in obsazene_pozice_white or (i, j) in obsazene_pozice_black:
                    return False

            return True 

        return False 

class Quuen(Piece):
    def __init__(self, color):
        # Zdědí barvu z Piece a nastaví se, aby se dědilo z Rook či Střelec
        super().__init__(color)
        self.rook = Rook(color)
        self.strelec = Strelec(color)

    def legal_movement(self, start_row, start_col, end_row, end_col, board, obsazene_pozice_black, obsazene_pozice_white, gs):
        # Kontola pohybu na základě legal_moovment Střelce nebo Věže
        return (self.rook.legal_movement(start_row, start_col, end_row, end_col, board, obsazene_pozice_black, obsazene_pozice_white, gs) or
                self.strelec.legal_movement(start_row, start_col, end_row, end_col, board, obsazene_pozice_black, obsazene_pozice_white, gs))

class King(Piece):
    # Král
    def __init__(self, color):
        # Zdědí barvu z Piece
        super().__init__(color)

    def legal_movement(self, start_row, start_col, end_row, end_col, board, obsazene_pozice_black, obsazene_pozice_white, gs):
        # Diagonální pohyb
        if abs(end_row - start_row) == 1 and abs(end_col - start_col) == 1:
            return True

        # Vertikální pohyb
        if start_col == end_col:
            if abs(start_row - end_row) == 1:
                return True
            return False
        
        # Horizontální pohyb
        if start_row == end_row:
            if abs(start_col - end_col) == 1:
                return True
            return False
    
        return False
    
def draw_board(screen, selected_square, gs, color_1=p.Color((174, 40, 47)), color_2=p.Color((214, 166, 62))):
    # Vykreslí šachovnici
    colors = [color_1, color_2]
    for row in range(board_size):
        for col in range(board_size):
            # Vytváří střídající se barvy pro šachovnici
            color = colors[(row + col) % 2]
            rect = p.Rect(200 + col * square_size, row * square_size, square_size, square_size)
            p.draw.rect(screen, color, rect)
            gs.update_occupied_positions()

            # Zvýraznění vybrané figurky
            if selected_square == (row, col):
                figurka = gs.board[row][col]
                p.draw.rect(screen, p.Color("green"), rect, 5) 
                
                # Aktuálně bez využití - Připraveno do budoucna
                """
                piece_class = None
                piece_classes = {
                            'p': Pawn,
                            'R': Rook,
                            'N': Jezdec,
                            'B': Strelec,
                            'K': King,
                            'Q': Quuen
                        }

                piece_class = piece_classes.get(figurka[1], None)  # Získáme třídu figurky
                piece_color = figurka[0]  # Získáme barvu figurky ('w' nebo 'b')
                
                if piece_class is not None:
                    piece_instance = piece_class(piece_color)
                    for x in range(board_size):
                        for y in range(board_size):
                            if piece_instance.legal_movement(selected_square[0], selected_square[1], x, y, gs.board, gs.obsazene_pozice_black, gs.obsazene_pozice_white, gs):
                                if figurka[0] == "b":
                                    gs.update_occupied_positions()
                                    if (x, y) == gs.position_wk or (x, y) == gs.position_bk:
                                        continue
                                    if (x, y) in gs.obsazene_pozice_black:
                                        continue
                                    elif (x, y) in gs.obsazene_pozice_white:
                                        color = "red"
                                    else:
                                        color = "green"
                                    p.draw.rect(screen, p.Color(color), p.Rect(200 + y * square_size, x * square_size, square_size, square_size), 5)
                                    
                                    
                                if figurka[0] == "w":
                                    gs.update_occupied_positions()
                                    if (x, y) == gs.position_wk or (x, y) == gs.position_bk:
                                        continue
                                    elif (x, y) in gs.obsazene_pozice_white:
                                        continue
                                    elif (x, y) in gs.obsazene_pozice_black:
                                        color = "red"
                                    else:
                                        color = "green"
                                    p.draw.rect(screen, p.Color(color), p.Rect(200 + y * square_size, x * square_size, square_size, square_size), 5)
                                    
        """                               
def update_time(gs):
    # Zajištění, aby se čas neodečítal, dokud nebude táhnuto
    if not gs.moveLog: 
        gs.last_time = time.time() 
        return  
    
    current_time = time.time()
    elapsed_time = current_time - gs.last_time
    # Střídání odečítání času podle toho, kdo je na tahu
    if gs.whiteToMove:
        gs.white_time -= elapsed_time
    else: 
        gs.black_time -= elapsed_time
    gs.last_time = current_time
def draw_right_menu(gs, message, images = images):
    # Vykreslení pravého menu
    menu = p.Rect(1000, 0, 200, 800)
    p.draw.rect(screen, "black", menu)
    font = p.font.Font(primary_font, 30)
    font2 = p.font.Font(primary_font, 26)
    font_small = p.font.Font(primary_font, 23)
    # Zajišťuje aktualizaci času
    update_time(gs)
    # Vykreslí chybovou hlášku
    gs.draw_error_message(message, screen)
    
    # Převod času na minuty a sekundy
    black_minutes = int(gs.black_time // 60)
    black_seconds = int(gs.black_time % 60)
    white_minutes = int(gs.white_time // 60)
    white_seconds = int(gs.white_time % 60)

    # Vykreslení odpočtu času
    white_text = font.render(f"White -- {white_minutes}:{white_seconds}", True, p.Color("white"))
    white_text_rect = white_text.get_rect()
    white_text_rect.center = (1100, 20)
    black_text = font.render(f"Black -- {black_minutes}:{black_seconds}", True, p.Color("white"))
    black_text_rect = black_text.get_rect()
    black_text_rect.center = (1100, 50)

    # Nastavení barev
    if gs.whiteToMove:
        worb = "white"
        color = "orange"
    else:
        worb = "black"
        color = "red"

    # Vykreslení zprávy, kdo je na tahu
    who_play = font2.render(f"It's {worb} player's turns", True, p.Color(color))
    who_play_rect = who_play.get_rect()
    who_play_rect.center = (1100, 80)

    # Vykreslení textu pro odstraněné figurky
    eliminate_white = font_small.render(f"White's eliminated pieces", True, p.Color("white"))
    eliminate_white_rect = eliminate_white.get_rect()
    eliminate_white_rect.center = (1100, 170)
    
    eliminate_black = font_small.render(f"Black's eliminated pieces", True, p.Color("white"))
    eliminate_black_rect = eliminate_black.get_rect()
    eliminate_black_rect.center = (1100, 470)

    screen.blit(white_text, white_text_rect)
    screen.blit(black_text, black_text_rect)
    screen.blit(who_play, who_play_rect)
    p.draw.line(screen, p.Color("white"), (1000,140), (1200, 140))
    screen.blit(eliminate_white, eliminate_white_rect)


    # Rozdělení odstraněných figur na bílé a černé
    eliminate_pieces_white = []
    eliminate_pieces_black = []
    for one_piece in eliminate_pieces:
        if one_piece[0] == "w":
            eliminate_pieces_white.append(one_piece)
        else:
            eliminate_pieces_black.append(one_piece)

    # Vykreslení odstraněných bílých figur
    for row in range(4):
        for col in range(4):
            index_white = row * 4 + col
            if index_white < len(eliminate_pieces_white):
                piece = eliminate_pieces_white[index_white]
                background_rect = p.Rect(1010 + col * 45, 190 + row * 60, 40, 40)
                p.draw.rect(screen, p.Color("red"), background_rect)
                
                # Vykreslení figurky
                scaled_image = p.transform.scale(images[piece], (40, 40))
                screen.blit(scaled_image, (1010 + col * 45, 190 + row * 60))

    p.draw.line(screen, p.Color("white"), (1000,440), (1200, 440))
    screen.blit(eliminate_black, eliminate_black_rect)


    # Vykreslení odstraněných černých figur
    for row in range(4):
        for col in range(4):
            index_black = row * 4 + col
            if index_black < len(eliminate_pieces_black):
                piece = eliminate_pieces_black[index_black]
                background_rect = p.Rect(1010 + col * 45, 490 + row * 60, 40, 40)
                p.draw.rect(screen, p.Color("red"), background_rect)
                
                # Vykreslení figurky
                scaled_image = p.transform.scale(images[piece], (40, 40))
                screen.blit(scaled_image, (1010 + col * 45, 490 + row * 60))

    p.draw.line(screen, p.Color("white"), (1000,740), (1200, 740))
    screen.blit(eliminate_white, eliminate_white_rect)

    # Vykreslení ikonek kolejí - Pro změnu barev
    logo = ["H", "M", "N", "Z"]
    images = []
    for row in range(4):
        img = p.transform.scale(p.image.load(f"images/{logo[row]}.png"), (40, 40))
        images.append(img)
    for i, img in enumerate(images):
        screen.blit(img, (1000 + i * 50, 750))
    # Aktualziace obrazovy
    p.display.flip()    

def draw_moveLog(gs):
    # Vykreslení moveLogu

    # Fonty
    font_small = p.font.Font(primary_font, 20)
    font_small_italic = p.font.Font(primary_font, 30)

    # Vykreslení černého pozadí
    background_rect = p.Rect(0, 0, 200, 1000)
    p.draw.rect(screen, p.Color("black"), background_rect)

    # Vykreslení textu pro moveLogu
    move_log_text = font_small_italic.render("Move's log", True, p.Color("white"))
    move_log_text_rect = move_log_text.get_rect()
    move_log_text_rect.center = (100, 30)

    screen.fill((0, 0, 0), background_rect)
    screen.blit(move_log_text, move_log_text_rect)

    # Vykreslení jednotlivých logu + Aut. měnění barev
    for i, move in enumerate(reversed(gs.moveLog)):
        if move[0] == "w":
            color = p.Color("orange")
        elif move[0] == "b":
            color = p.Color("red")
        else:
            color = p.Color("white")

        text = font_small.render(f"{len(gs.moveLog) - i}. {move}", True, color)
        text_rect = text.get_rect()
        text_rect.center = (100, 60 + i * 30)
        screen.blit(text, text_rect)
def draw_pieces(screen, board):
    # Vykreslení figurek na šachovnice
    for row in range(board_size):
        for col in range(board_size):
            piece = board[row][col]
            if piece != "xx":  
                screen.blit(images[piece], p.Rect(200 + col * square_size, row * square_size, square_size, square_size))
def render_board(screen, gs, selected_square, color_1, color_2):
    # Zajišťuje vykreslení všech částí šachovnice
    draw_board(screen, selected_square, gs, color_1, color_2)
    draw_pieces(screen, gs.board)
    draw_moveLog(gs)
    draw_right_menu(gs, gs.error_message, images)
def animation_move(start_row, start_col, end_row, end_col, Clock, gs, start_row_R=None, start_col_R=None, end_row_R=None, end_col_R=None, rook=None):
    # Získání hodnot
    start_x = 200 + start_col * 100 
    start_y = start_row * 100 
    end_x = 200 + end_col * 100 
    end_y = end_row * 100 

    # Doba animace
    duration = 0.1 

    # Změna animace
    delta_x = (end_x - start_x) / (duration * 120)
    delta_y = (end_y - start_y) / (duration * 120)    

    # Získání figurky
    piece = gs.board[start_row][start_col]

    for t in range(int(duration * 120)):
        # Animace pohybu
        x = start_x + t * delta_x
        y = start_y + t * delta_y

        # Smazání minule pozice
        screen.fill((0, 0, 0))
        # Vykreslení všech prvků na obrazovce
        draw_board(screen, None, gs, color_1, color_2)
        draw_pieces(screen, gs.board)
        draw_moveLog(gs)
        draw_right_menu(gs, gs.error_message, images)
        # Vykreslení pohybující se figurky
        screen.blit(images[piece], p.Rect(x, y, square_size, square_size))
        p.display.flip()
        Clock.tick(120)
    
    # Aktualizace pozice figurky na konci animace
    gs.board[end_row][end_col] = piece
    gs.board[start_row][start_col] = 'xx'

    # Animace pro věž v případě rošády
    if rook:
        start_x_R = 200 + start_col_R * 100
        start_y_R = start_row_R * 100
        end_x_R = 200 + end_col_R * 100
        end_y_R = end_row_R * 100

        delta_x_R = (end_x_R - start_x_R) / (duration * 120)
        delta_y_R = (end_y_R - start_y_R) / (duration * 120)

        for t in range(int(duration * 120)):
            x_R = start_x_R + t * delta_x_R
            y_R = start_y_R + t * delta_y_R

            screen.fill((0, 0, 0))
            draw_board(screen, None, gs, color_1, color_2)
            draw_pieces(screen, gs.board)
            draw_moveLog(gs)
            draw_right_menu(gs, gs.error_message, images)
            # Vykreslení pohybující se věže
            screen.blit(images[rook], p.Rect(x_R, y_R, square_size, square_size))
            p.display.flip()
            Clock.tick(120)


def main():
    global white_check, black_check, screen, play_option, figurka, color_1, color_2
    # Nastavení hodnoty na menu, aby se vykreslilo při spuštění
    play_option = "menu"
    # Inicializace pygame a nastavení základních parametrů
    p.init()
    screen = p.display.set_mode((1200, 800), p.DOUBLEBUF)
    p.display.set_caption("Wizard's Chess Game")
    clock = p.time.Clock()
    gs = GameState()  
    load_images()  
    selected_square = None  

    # Spuštění hudby
    try:
        p.mixer.music.load("sounds/HP_main.mp3")
        p.mixer.music.set_volume(0.3)
        p.mixer.music.play()
    except Exception as e:
        print(e)

    run = True
    
    while run:
        if play_option == "menu":
            # Vykreslení menu při spuštění
            action = Menu.draw_menu(screen)
            if action:
                play_option = action

        if play_option == "load_game":
            # Načtení hry z logu
            load_game = LoadGame(screen, gs)
            action = load_game.draw_menu(screen)
            if action:
                play_option = action
        
        if play_option == "exit":
            # Pro ukončení programu
            run = False

        if play_option == "reset_game":
            # Reset hry

            # Z nějakého důvodu aktuálně nefunguje...
            black_check = False
            white_check = False
            gs.reset()
            play_option = "game_player_vs_player"

        if play_option == "end_game":
            # Vykreslení menu pro ukončení hry

            #Zjištění, kdo vyhrál
            if white_check:
                gs.error_message = "Checkmate - Black's won"
            else:
                gs.error_message = "Checkmate - White's won"

            # Zachycení kliknutí
            for event in p.event.get():
                if event.type == p.QUIT:
                    return "exit"
                elif event.type == p.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    for text, (bx, by, action) in buttons.items():
                        if bx <= x <= bx + 100 and by <= y <= by + 40:
                            return action

            # Vykreslení menu
            end_game_menu = p.Rect(300, 200, 600, 400)
            p.draw.rect(screen, (0, 0, 0), end_game_menu)
            # Fonty
            font = p.font.Font(primary_font, 70)
            font_button = p.font.Font(primary_font, 36)

            # Vykreslení textu a loga
            text = font.render(gs.error_message, True, p.Color("green"))
            text_rect = text.get_rect(center=(600, 300))
            screen.blit(text, text_rect)
            logo = p.image.load("images/logo.png")
            logo = p.transform.scale(logo, (80, 80))
            logo_rect = logo.get_rect()
            logo_rect.center = (600, 530)
            screen.blit(logo, logo_rect)

            buttons = {
            "Play again": (450, 400, "game_player_vs_player"),
            "The end": (650, 400, "reset_game"),
            }

            
            for text, (x, y, action) in buttons.items():
                btn_text = font_button.render(text, True, p.Color("white"))
                btn_text_rect = btn_text.get_rect(center=(x + 50, y + 20))

                # Vykreslení kulatého rámečku
                border_rect = btn_text_rect.inflate(20, 20)  # Zvýšení velikosti rámečku
                p.draw.rect(screen, p.Color("red"), border_rect, border_radius=10)

                screen.blit(btn_text, btn_text_rect.topleft)

            p.display.flip()

        if play_option == "change_piece":
            # Definování možných figurek pro výměnu
            pieces_white = ["wR", "wQ", "wB", "wN"]
            pieces_black = ["bR", "bQ", "bB", "bN"]

            # Zajištění, aby se zobrazili správné figurky
            if figurka[0] == "w":
                pieces = pieces_white
            else:
                pieces = pieces_black
            
            # Vykreslení pozadí menu
            change_menu = p.Rect(400, 300, 400, 200)
            p.draw.rect(screen, (0, 0, 0), change_menu)
            
            # Zobrazení figurek vedle sebe
            for row in range(4): 
                background_rect = p.Rect(420 + row * 95, 360, 80, 80)
                p.draw.rect(screen, p.Color("green"), background_rect)

                # Vykreslení figurky
                scaled_image = p.transform.scale(images[pieces[row]], (80, 80))
                screen.blit(scaled_image, (420 + row *95, 360)) 
            # Aktualizace obrazovky
            p.display.flip()

            # Čekáme, než si hráč vybere
            waiting_for_selection = True
            while waiting_for_selection:
                # Zachycení kliknutí
                for event in p.event.get():
                    if event.type == p.QUIT:
                        run = False
                        waiting_for_selection = False
                    elif event.type == p.MOUSEBUTTONDOWN:
                        x, y = event.pos
                        for row in range(4):
                            if 420 + row * 95 <= x <= 420 + row * 95 + 80 and 350 <= y <= 350 + 80:
                                # Zjištění, na kterou figurku bylo kliknuto a její nastavení na danou pozici
                                selected_piece = pieces[row]
                                gs.board[row2][col2] = selected_piece
                                gs.update_occupied_positions()
                                # Vypnutí cyklu a návrat zpět do hry
                                waiting_for_selection = False
                                play_option = "game_player_vs_player"
                                gs.check(gs)
                                

        if play_option == "game_player_vs_player":
            # Kontrola šachu
            gs.check(gs)
            # Vykreslení pravého menu
            draw_right_menu(gs, gs.error_message, images)

            for event in p.event.get():
                if event.type == p.QUIT:
                    run = False

                elif event.type == p.MOUSEBUTTONDOWN:  
                    x, y = event.pos
                    col = (x - 200) // square_size  
                    row = y // square_size 

                    # Funkce pro změnu barev šachovnice
                    for z in range(4):
                        x_start = 1000 + z * 50
                        x_end = x_start + 50
                        y_start = 700
                        y_end = 800

                        if x_start <= x <= x_end and y_start <= y <= y_end:
                            znak = z

                            # Nastavení barev podle výběru
                            if znak == 0:
                                color_1 = p.Color((59, 133, 184))
                                color_2 = p.Color((233, 235, 237))
                            elif znak == 1:
                                color_1 = p.Color((208, 159, 74))
                                color_2 = p.Color((227, 227, 227))
                            elif znak == 2:
                                color_1 = p.Color((174, 40, 47))
                                color_2 = p.Color((214, 166, 62))
                            elif znak == 3:
                                color_1 = p.Color((58, 115, 85))
                                color_2 = p.Color((180, 182, 184))

                            # Vykreslení šachovnice s novými barvami
                            draw_board(screen, selected_square, gs, color_1, color_2)
                            p.display.flip()


                    # Zajistíme pouze validní kliknutí na šachovnici
                    if col >= board_size or row >= board_size:
                        continue 

                    # První kliknutí - výběr figurky
                    if selected_square is None:
                        # Zkontroluje, jestli na poli je figura
                        if gs.board[row][col] != "xx":
                            # Kontrola, zda je hráč na tahu - Umožňuje kliknout pouze na figurky hráče, který hraje
                            if gs.whiteToMove and (gs.board[row][col])[0] == "w" or not gs.whiteToMove and (gs.board[row][col])[0] == "b":
                                draw_board(screen, selected_square, gs, color_1, color_2)
                                # Uložíme
                                selected_square = (row, col)
                                

                    # Druhý kliknutí - pokus o přesun figurky
                    else:   
                        # Kontrola, zda nebylo kliknuto na stejnou figurku
                        if selected_square == (row, col):
                            selected_square = None
                            break
                        
                        row2, col2 = row, col
                        piece = gs.board[selected_square[0]][selected_square[1]]
                        piece_object = None
                        piece_classes = {
                            'p': Pawn,
                            'R': Rook,
                            'N': Jezdec,
                            'B': Strelec,
                            'K': King,
                            'Q': Quuen
                        }

                        piece_object = piece_classes.get(piece[1], None)

                        if piece_object:
                            piece_object = piece_object(piece[0]) 
                    
                      
                        def move(): 
                            global black_check, white_check, play_option, figurka

                            # Rošáda
                            rosada_done = False
                            # Počítání cest pro všechny typy rošád
                            moves1 = gs.get_path_to_king((7, 4), (7, 7))
                            moves2 = gs.get_path_to_king((0, 4), (0, 7))
                            moves3 = gs.get_path_to_king((7, 4), (7, 0))
                            moves4 = gs.get_path_to_king((0, 4), (0, 0))

                            # Seznamy, kam se ukládají součadnice, pokud je v cestě překážka
                            moves1_clear = [pohyb for pohyb in moves1 if gs.board[pohyb[0]][pohyb[1]] != "xx"]
                            moves2_clear = [pohyb for pohyb in moves2 if gs.board[pohyb[0]][pohyb[1]] != "xx"]
                            moves3_clear = [pohyb for pohyb in moves3 if gs.board[pohyb[0]][pohyb[1]] != "xx"]
                            moves4_clear = [pohyb for pohyb in moves4 if gs.board[pohyb[0]][pohyb[1]] != "xx"]

                            try:
                                # Pokud je cesta volná..
                                if not moves1_clear:
                                    # Zkontrolujeme pozice krále a věže
                                    if gs.board[7][4] == "wK" and gs.board[7][7] == "wR" and piece == "wK":
                                        # Pokud bylo kliknuto na správné pole
                                        if (row2, col2) == (7, 6):
                                            # Prověříme log pro prípad, že již bylo táhnuto s věží či králem
                                            for log in gs.moveLog:
                                                if isinstance(log, str):
                                                    pattern = r'([wb][pRNBQK])\s*-\s*\((\d+),\s*(\d+)\)\s*-\s*\((\d+),\s*(\d+)\)'
                                                    match = re.search(pattern, log)
                                                    if match:
                                                        figurka_moveLog = match.group(1)
                                                        start_row = int(match.group(2))
                                                        start_col = int(match.group(3))
                                                        if ("wK" == figurka_moveLog and (start_row, start_col) == (7, 4)) or \
                                                        ("wR" == figurka_moveLog and (start_row, start_col) == (7, 7)):
                                                            return False
                                            # Zavoláme animaci
                                            animation_move(selected_square[0], selected_square[1], row2, col2, clock, gs, 7, 7, 7, 5, "wR")
                                            # Nastavíme správné pozice na šachovnici 
                                            gs.board[7][7] = "xx"
                                            gs.board[7][4] = "xx"
                                            gs.board[7][6] = "wK"
                                            gs.board[7][5] = "wR"
                                            # Aktualizujeme pozice
                                            gs.update_occupied_positions()
                                            # Zajistíme popis do logu
                                            rosada_done = True
                                            popis = "Castling White - Kingside"
                                # Pokud je cesta volná..
                                if not moves2_clear:
                                    # Zkontrolujeme pozice krále a věže
                                    if gs.board[0][4] == "bK" and gs.board[0][7] == "bR" and piece == "bK":
                                        # Pokud bylo kliknuto na správné pole
                                        if (row2, col2) == (0, 6):
                                            # Prověříme log pro prípad, že již bylo táhnuto s věží či králem
                                            for log in gs.moveLog:
                                                if isinstance(log, str):
                                                    pattern = r'([wb][pRNBQK])\s*-\s*\((\d+),\s*(\d+)\)\s*-\s*\((\d+),\s*(\d+)\)'
                                                    match = re.search(pattern, log)
                                                    if match:
                                                        figurka_moveLog = match.group(1)
                                                        start_row = int(match.group(2))
                                                        start_col = int(match.group(3))
                                                        if ("bK" == figurka_moveLog and (start_row, start_col) == (0, 4)) or \
                                                        ("bR" == figurka_moveLog and (start_row, start_col) == (0, 7)):
                                                            return False
                                            # Zavoláme animaci
                                            animation_move(selected_square[0], selected_square[1], row2, col2, clock, gs, 0, 7, 0, 5, "bR")
                                            # Nastavíme správné pozice na šachovnici
                                            gs.board[0][7] = "xx"
                                            gs.board[0][4] = "xx"
                                            gs.board[0][6] = "bK"
                                            gs.board[0][5] = "bR"
                                            # Aktualizujeme pozice
                                            gs.update_occupied_positions()
                                            # Zajistíme popis do logu
                                            rosada_done = True
                                            popis = "Castlink Black - Kingside"
                                # Pokud je cesta volná..
                                if not moves3_clear:
                                    # Zkontrolujeme pozice krále a věže
                                    if gs.board[7][4] == "wK" and gs.board[7][0] == "wR" and piece == "wK":
                                        # Pokud bylo kliknuto na správné pole
                                        if (row2, col2) == (7, 2):
                                            # Prověříme log pro prípad, že již bylo táhnuto s věží či králem
                                            for log in gs.moveLog:
                                                if isinstance(log, str):
                                                    pattern = r'([wb][pRNBQK])\s*-\s*\((\d+),\s*(\d+)\)\s*-\s*\((\d+),\s*(\d+)\)'
                                                    match = re.search(pattern, log)
                                                    if match:
                                                        figurka_moveLog = match.group(1)
                                                        start_row = int(match.group(2))
                                                        start_col = int(match.group(3))
                                                        if ("wK" == figurka_moveLog and (start_row, start_col) == (7, 4)) or \
                                                        ("wR" == figurka_moveLog and (start_row, start_col) == (7, 0)):

                                                            return False
                                            # Zavoláme animaci
                                            animation_move(selected_square[0], selected_square[1], row2, col2, clock, gs, 7, 0, 7, 3, "wR")
                                            # Nastavíme správné pozice na šachovnici
                                            gs.board[7][0] = "xx"
                                            gs.board[7][4] = "xx"
                                            gs.board[7][2] = "wK"
                                            gs.board[7][3] = "wR"
                                            # Aktualizujeme pozice
                                            gs.update_occupied_positions()
                                            # Zajistíme popis do logu
                                            rosada_done = True
                                            popis = "Castling White - Queenside"
                                # Pokud je cesta volná..
                                if not moves4_clear:
                                    # Zkontrolujeme pozice krále a věže
                                    if gs.board[0][4] == "bK" and gs.board[0][0] == "bR" and piece == "bK":
                                        # Pokud bylo kliknuto na správné pole
                                        if (row2, col2) == (0, 2):
                                            # Prověříme log pro prípad, že již bylo táhnuto s věží či králem
                                            for log in gs.moveLog:
                                                if isinstance(log, str):
                                                    pattern = r'([wb][pRNBQK])\s*-\s*\((\d+),\s*(\d+)\)\s*-\s*\((\d+),\s*(\d+)\)'
                                                    match = re.search(pattern, log)
                                                    if match:
                                                        figurka_moveLog = match.group(1)
                                                        start_row = int(match.group(2))
                                                        start_col = int(match.group(3))
                                                        if ("bK" == figurka_moveLog and (start_row, start_col) == (0, 4)) or \
                                                        ("bR" == figurka_moveLog and (start_row, start_col) == (0, 0)):
                                                            return False
                                            # Zavoláme animaci
                                            animation_move(selected_square[0], selected_square[1], row2, col2, clock, gs, 0, 0, 0, 3, "bR")
                                            # Nastavíme správné pozice na šachovnici
                                            gs.board[0][0] = "xx"
                                            gs.board[0][4] = "xx"
                                            gs.board[0][2] = "bK"
                                            gs.board[0][3] = "bR"
                                            # Aktualizujeme pozice
                                            gs.update_occupied_positions()
                                            # Zajistíme popis do logu
                                            rosada_done = True
                                            popis = "Castling Black - Queenside" 
                                # Pokud se rošáda provedla
                                if rosada_done:
                                    # Přidáme záznam do logu
                                    gs.moveLog.append(f"{piece} - {selected_square} - ({row2}, {col2})")
                                    gs.moveLog.append(popis)
                                    # Hraje druhý hráč
                                    gs.whiteToMove = not gs.whiteToMove
                                    return False
                            
                            except Exception as e:
                                print(f"Error: {e}")
                                pass
                            
                            finally:
                                # Vyresetujeme rošádu
                                rosada_done = False

                            # Pokud je pohyb legální a není šach ani na jedné straně
                            if piece_object and piece_object.legal_movement(selected_square[0], selected_square[1], row2, col2, gs.board, gs.obsazene_pozice_black, gs.obsazene_pozice_white, gs) and not black_check and not white_check:
                                local_piece = gs.board[row2][col2]
                                figurka = gs.board[selected_square[0]][selected_square[1]]
                                path = gs.get_path_to_king((selected_square[0], selected_square[1]), (row2, col2))
                                # Kontrola, zda v cestě není král - Kvůli absenci krále v obsazene_pozice_white or obsazene_pozice_black
                                for step in path:
                                    if step == gs.position_bk or step == gs.position_wk:
                                        draw_right_menu(gs, "The wrong move")
                                        return False
                                # Kotrola, zda na cílových souřadnicích není král - Kvůli absenci krále v obsazene_pozice_white or obsazene_pozice_black
                                if (row2, col2) == gs.position_bk or (row2, col2) == gs.position_wk:
                                    draw_right_menu(gs, "The wrong move")
                                    return False
                                # Simulace tahu
                                original_occupied_positions_black = gs.obsazene_pozice_black.copy()
                                original_occupied_positions_white = gs.obsazene_pozice_white.copy()
                                gs.board[row2][col2] = figurka
                                gs.board[selected_square[0]][selected_square[1]] = "xx"
                                gs.update_occupied_positions()
                                gs.check(gs)  # Aktualizace po tahu
                                
                                # Kontrola, zda v důsledku pohybu vlastní figurky nenastal šach
                                if black_check and figurka[0] == "b" or white_check and figurka[0] == "w":
                                    # Pokud ano, vše se vrátí a funkce vyhodí False
                                    gs.board[selected_square[0]][selected_square[1]] = figurka
                                    gs.board[row2][col2] = local_piece
                                    
                                    # Obnovení obsazených pozic
                                    gs.obsazene_pozice_black = original_occupied_positions_black.copy()
                                    gs.obsazene_pozice_white = original_occupied_positions_white.copy()
                                    
                                    gs.update_occupied_positions()
                                    black_check = False
                                    white_check = False
                                    return False

                                else:
                                    # Pokud ne, vše se vrátí a pokračuje se v dalších podmínkách
                                    gs.board[selected_square[0]][selected_square[1]] = figurka
                                    gs.board[row2][col2] = local_piece
                                    
                                    # Obnovení obsazených pozic
                                    gs.obsazene_pozice_black = original_occupied_positions_black.copy()
                                    gs.obsazene_pozice_white = original_occupied_positions_white.copy()
                                    
                                    gs.update_occupied_positions()

                                # Kontrola, zda pěšec nedosáhl druhé strany pro případnou změnu figurky
                                if row == 7 and piece == "bp" or row == 0 and piece == "wp":
                                    play_option = "change_piece"

                                # Zamezení pohybu krále na pozici, která by ho dostala do šachu a zabránění braní vlastních figurek
                                elif gs.board[selected_square[0]][selected_square[1]] == "bK":
                                    if (row2, col) in gs.possible_moves_white or (row2, col2) in gs.obsazene_pozice_black:
                                        draw_right_menu(gs, "The wrong move")
                                        return False
                                    
                                elif gs.board[selected_square[0]][selected_square[1]] == "wK":
                                    if (row2, col) in gs.possible_moves_black or (row2, col2) in gs.obsazene_pozice_white:
                                        draw_right_menu(gs, "The wrong move")
                                        return False

                                # Pokud je na cílové pozici figurka
                                elif gs.board[row2][col2] != "xx":
                                    # A není vlastní
                                    if local_piece[0] == piece_object.color:
                                        draw_right_menu(gs, "The wrong move")
                                        return
                                    # Elimace figurky + zvukový efekt
                                    kill = p.mixer.Sound("sounds/HP_kill.mp3")
                                    kill.set_volume(0.1)
                                    kill.play(0)
                                    piece_object.eliminate(gs.board, row2, col2)

                                # Zvuk pro pohyb figurky
                                move_sound = p.mixer.Sound("sounds/move.mp3")
                                move_sound.set_volume(0.07)
                                move_sound.play()

                                # Animace figurky
                                animation_move(selected_square[0], selected_square[1], row2, col2, clock, gs)
                                
                                # Přidání záznamu do logu
                                gs.moveLog.append(f"{piece} - {selected_square} - ({row2}, {col2})")

                                # Nastavíme nové pozice figurek
                                gs.board[row2][col2] = piece
                                gs.board[selected_square[0]][selected_square[1]] = "xx"

                                # Hraje druhý hráč
                                gs.whiteToMove = not gs.whiteToMove

                                # Pokud nastal šach, přehraje zvuk
                                if black_check or white_check:
                                    check_sound = p.mixer.Sound("sounds/Check.mp3")
                                    check_sound.set_volume(0.4)
                                    check_sound.play()
                                
                                # Aktualizace pozic
                                gs.update_occupied_positions()

                            # Pokud není pohyb legální
                            elif not piece_object.legal_movement(selected_square[0], selected_square[1], row2, col2, gs.board, gs.obsazene_pozice_black, gs.obsazene_pozice_white, gs):
                                draw_right_menu(gs, "The wrong move")
                            
                            # Pokud je král v šachu
                            else:
                                # Kontroluje pohyb krále
                                # possible_moves_black_king_check - Tahy, kam král může (de facto legal_moovment)
                                # possible_moves_white - Možné tahy všech bílých figurek
                                # safe_W = Chráněné pozice bílých (pro případ, že by král vzal figurku, od které má šach, ale ta je krytá jinou figurkou)
                                if piece == "bK":
                                    if (row2, col2) in gs.possible_moves_black_king_check and (row2, col2) not in gs.possible_moves_white and (row2, col2) not in gs.safe_W:
                                        # Pokud je tah možný, zruší se šah a zavolá se znovu funkce move() - Tentokrát to projde přes hlavní podmínku
                                        black_check = False
                                        move()
                                    else:
                                        # Tah není možný - Nestane se nic
                                        draw_right_menu(gs, "The wrong move")

                                # Kontroluje pohyb krále
                                # possible_moves_white_king_check - Tahy, kam král může (de facto legal_moovment)
                                # possible_moves_black - Možné tahy všech černých figurek
                                # safe_B = Chráněné pozice černých (pro případ, že by král vzal figurku, od které má šach, ale ta je krytá jinou figurkou)                                                      
                                elif piece == "wK":
                                    if (row2, col2) in gs.possible_moves_white_king_check and (row2, col2) not in gs.possible_moves_black and (row2, col2) not in gs.safe_B:
                                        # Pokud je tah možný, zruší se šah a zavolá se znovu funkce move() - Tentokrát to projde přes hlavní podmínku
                                        white_check = False
                                        move()
                                    else:
                                        # Tah není možný - Nestane se nic
                                        draw_right_menu(gs, "The wrong move")
                                    
                                
                                # Kontrola, zda nějaká figurka může zabránit šachu        
                                elif piece[0] == "b":
                                    if (row2, col2) in gs.possible_moves_white or (row2, col2) in gs.obsazene_pozice_white:
                                        black_check = False
                                        move()
                                    else:
                                        draw_right_menu(gs, "The wrong move")
                                
                                elif piece[0] == "w":
                                    if (row2, col2) in gs.possible_moves_black or (row2, col2) in gs.obsazene_pozice_black:
                                        white_check = False
                                        move()
                                    else:
                                        draw_right_menu(gs, "The wrong move")

                        move()
                        selected_square = None  
            render_board(screen, gs, selected_square, color_1, color_2) 
        p.display.flip()
        clock.tick(max_fps)
    # Uloží se data do moveLogu
    gs.save_move_log(gs)
    # Ukončení pygame
    p.quit()

if __name__ == "__main__":
    # Spustí hru
    main()
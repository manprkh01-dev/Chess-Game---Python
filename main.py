import pygame
import sys
import copy
import random
import time
from typing import Optional

# ── Constants ────────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 900, 700
BOARD_SIZE = 560
SQUARE = BOARD_SIZE // 8
BOARD_X = (WIDTH - BOARD_SIZE) // 2 - 40
BOARD_Y = (HEIGHT - BOARD_SIZE) // 2

FPS = 60

# Colours (rich dark theme)
C_BG          = (18, 18, 24)
C_PANEL       = (28, 28, 36)
C_BORDER      = (60, 60, 80)
C_LIGHT       = (235, 215, 185)
C_DARK        = (175, 135,  95)
C_HIGHLIGHT   = (100, 200, 120, 160)
C_SELECTED    = ( 80, 160, 240, 180)
C_MOVE_DOT    = ( 80, 200, 120, 140)
C_LAST_MOVE   = (200, 200,  80,  80)
C_CHECK       = (220,  60,  60, 180)
C_TEXT_MAIN   = (220, 220, 230)
C_TEXT_DIM    = (130, 130, 150)
C_ACCENT      = (100, 180, 255)
C_BTN         = ( 45,  45,  60)
C_BTN_HOVER   = ( 65,  65,  85)
C_BTN_ACTIVE  = ( 80, 140, 220)
C_WHITE_PIECE = (240, 235, 220)
C_BLACK_PIECE = ( 30,  28,  35)

# Piece symbols (Unicode chess glyphs)
UNICODE_PIECES = {
    ('w', 'K'): '♔', ('w', 'Q'): '♕', ('w', 'R'): '♖',
    ('w', 'B'): '♗', ('w', 'N'): '♘', ('w', 'P'): '♙',
    ('b', 'K'): '♚', ('b', 'Q'): '♛', ('b', 'R'): '♜',
    ('b', 'B'): '♝', ('b', 'N'): '♞', ('b', 'P'): '♟',
}

# Piece values for evaluation
PIECE_VALUE = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}

# Positional tables (from white's perspective, row 0 = rank 8)
PST = {
    'P': [
         0,  0,  0,  0,  0,  0,  0,  0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
         5,  5, 10, 25, 25, 10,  5,  5,
         0,  0,  0, 20, 20,  0,  0,  0,
         5, -5,-10,  0,  0,-10, -5,  5,
         5, 10, 10,-20,-20, 10, 10,  5,
         0,  0,  0,  0,  0,  0,  0,  0,
    ],
    'N': [
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  0,  0,  0,-20,-40,
        -30,  0, 10, 15, 15, 10,  0,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  0, 15, 20, 20, 15,  0,-30,
        -30,  5, 10, 15, 15, 10,  5,-30,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50,
    ],
    'B': [
        -20,-10,-10,-10,-10,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5, 10, 10,  5,  0,-10,
        -10,  5,  5, 10, 10,  5,  5,-10,
        -10,  0, 10, 10, 10, 10,  0,-10,
        -10, 10, 10, 10, 10, 10, 10,-10,
        -10,  5,  0,  0,  0,  0,  5,-10,
        -20,-10,-10,-10,-10,-10,-10,-20,
    ],
    'R': [
         0,  0,  0,  0,  0,  0,  0,  0,
         5, 10, 10, 10, 10, 10, 10,  5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
         0,  0,  0,  5,  5,  0,  0,  0,
    ],
    'Q': [
        -20,-10,-10, -5, -5,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5,  5,  5,  5,  0,-10,
         -5,  0,  5,  5,  5,  5,  0, -5,
          0,  0,  5,  5,  5,  5,  0, -5,
        -10,  5,  5,  5,  5,  5,  0,-10,
        -10,  0,  5,  0,  0,  0,  0,-10,
        -20,-10,-10, -5, -5,-10,-10,-20,
    ],
    'K': [
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -20,-30,-30,-40,-40,-30,-30,-20,
        -10,-20,-20,-20,-20,-20,-20,-10,
         20, 20,  0,  0,  0,  0, 20, 20,
         20, 30, 10,  0,  0, 10, 30, 20,
    ],
}

# ── Piece / Board logic ───────────────────────────────────────────────────────

def init_board():
    board = [[None]*8 for _ in range(8)]
    order = ['R','N','B','Q','K','B','N','R']
    for c, color in [(0,'b'), (7,'w')]:
        for f, p in enumerate(order):
            board[c][f] = (color, p)
        pawn_row = 1 if color == 'b' else 6
        for f in range(8):
            board[pawn_row][f] = (color, 'P')
    return board

def on_board(r, c):
    return 0 <= r < 8 and 0 <= c < 8

def pseudo_moves(board, r, c, en_passant=None):
    """Generate pseudo-legal moves (may leave king in check)."""
    piece = board[r][c]
    if piece is None:
        return []
    color, ptype = piece
    enemy = 'b' if color == 'w' else 'w'
    moves = []

    def slide(dr, dc):
        nr, nc = r+dr, c+dc
        while on_board(nr, nc):
            if board[nr][nc] is None:
                moves.append((nr, nc))
            elif board[nr][nc][0] == enemy:
                moves.append((nr, nc))
                break
            else:
                break
            nr += dr; nc += dc

    if ptype == 'P':
        direction = -1 if color == 'w' else 1
        start_row = 6 if color == 'w' else 1
        # Forward
        nr = r + direction
        if on_board(nr, c) and board[nr][c] is None:
            moves.append((nr, c))
            # Double push
            if r == start_row and board[r+2*direction][c] is None:
                moves.append((r+2*direction, c))
        # Captures
        for dc in [-1, 1]:
            nr, nc = r+direction, c+dc
            if on_board(nr, nc):
                if board[nr][nc] and board[nr][nc][0] == enemy:
                    moves.append((nr, nc))
                elif en_passant == (nr, nc):
                    moves.append((nr, nc))

    elif ptype == 'N':
        for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            nr, nc = r+dr, c+dc
            if on_board(nr, nc) and (board[nr][nc] is None or board[nr][nc][0] == enemy):
                moves.append((nr, nc))

    elif ptype == 'B':
        for dr, dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
            slide(dr, dc)

    elif ptype == 'R':
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            slide(dr, dc)

    elif ptype == 'Q':
        for dr, dc in [(-1,-1),(-1,1),(1,-1),(1,1),(-1,0),(1,0),(0,-1),(0,1)]:
            slide(dr, dc)

    elif ptype == 'K':
        for dr, dc in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
            nr, nc = r+dr, c+dc
            if on_board(nr, nc) and (board[nr][nc] is None or board[nr][nc][0] == enemy):
                moves.append((nr, nc))

    return moves

def is_in_check(board, color):
    # Find king
    king_pos = None
    for r in range(8):
        for c in range(8):
            if board[r][c] == (color, 'K'):
                king_pos = (r, c)
    if king_pos is None:
        return True
    enemy = 'b' if color == 'w' else 'w'
    for r in range(8):
        for c in range(8):
            if board[r][c] and board[r][c][0] == enemy:
                if king_pos in pseudo_moves(board, r, c):
                    return True
    return False

def apply_move(board, fr, fc, tr, tc, en_passant=None, promote='Q'):
    board = copy.deepcopy(board)
    piece = board[fr][fc]
    color, ptype = piece
    captured = board[tr][tc]

    board[tr][tc] = piece
    board[fr][fc] = None

    # En passant capture
    if ptype == 'P' and en_passant == (tr, tc):
        direction = -1 if color == 'w' else 1
        board[tr - direction][tc] = None

    # Promotion
    if ptype == 'P' and (tr == 0 or tr == 7):
        board[tr][tc] = (color, promote)

    return board

def castling_moves(board, color, castling_rights):
    moves = []
    row = 7 if color == 'w' else 0
    if color == 'w':
        k_side, q_side = 'K', 'Q'
    else:
        k_side, q_side = 'k', 'q'

    if k_side in castling_rights:
        if board[row][5] is None and board[row][6] is None:
            if not is_in_check(board, color):
                b2 = apply_move(board, row, 4, row, 5)
                if not is_in_check(b2, color):
                    b3 = apply_move(board, row, 4, row, 6)
                    if not is_in_check(b3, color):
                        moves.append((row, 6, 'castle_k'))

    if q_side in castling_rights:
        if board[row][3] is None and board[row][2] is None and board[row][1] is None:
            if not is_in_check(board, color):
                b2 = apply_move(board, row, 4, row, 3)
                if not is_in_check(b2, color):
                    b3 = apply_move(board, row, 4, row, 2)
                    if not is_in_check(b3, color):
                        moves.append((row, 2, 'castle_q'))
    return moves

def legal_moves(board, color, en_passant=None, castling_rights=None):
    if castling_rights is None:
        castling_rights = set()
    result = []
    for r in range(8):
        for c in range(8):
            if board[r][c] and board[r][c][0] == color:
                for tr, tc in pseudo_moves(board, r, c, en_passant):
                    nb = apply_move(board, r, c, tr, tc, en_passant)
                    if not is_in_check(nb, color):
                        result.append((r, c, tr, tc))
    # Castling
    for move in castling_moves(board, color, castling_rights):
        result.append((move[0], 4, move[0], move[1]))
    return result

# ── AI (Minimax + Alpha-Beta) ────────────────────────────────────────────────

def evaluate(board):
    score = 0
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece is None:
                continue
            color, ptype = piece
            val = PIECE_VALUE[ptype]
            idx = r*8 + c if color == 'w' else (7-r)*8 + c
            pos_val = PST[ptype][idx]
            if color == 'w':
                score += val + pos_val
            else:
                score -= val + pos_val
    return score

def minimax(board, depth, alpha, beta, maximizing, color, en_passant, castling_rights, deadline):
    if time.time() > deadline:
        return evaluate(board), None

    moves = legal_moves(board, color, en_passant, castling_rights)
    enemy = 'b' if color == 'w' else 'w'

    if depth == 0 or not moves:
        if not moves:
            if is_in_check(board, color):
                return (-99999 if maximizing else 99999), None
            return 0, None
        return evaluate(board), None

    best_move = None
    if maximizing:
        best = -float('inf')
        for fr, fc, tr, tc in moves:
            nb = apply_move(board, fr, fc, tr, tc, en_passant)
            # Update castling rights
            ncr = update_castling(castling_rights, fr, fc, tr, tc, board[fr][fc])
            nep = get_en_passant(board, fr, fc, tr, tc)
            handle_castling_rook(nb, fr, fc, tr, tc)
            val, _ = minimax(nb, depth-1, alpha, beta, False, enemy, nep, ncr, deadline)
            if val > best:
                best = val
                best_move = (fr, fc, tr, tc)
            alpha = max(alpha, best)
            if beta <= alpha:
                break
        return best, best_move
    else:
        best = float('inf')
        for fr, fc, tr, tc in moves:
            nb = apply_move(board, fr, fc, tr, tc, en_passant)
            ncr = update_castling(castling_rights, fr, fc, tr, tc, board[fr][fc])
            nep = get_en_passant(board, fr, fc, tr, tc)
            handle_castling_rook(nb, fr, fc, tr, tc)
            val, _ = minimax(nb, depth-1, alpha, beta, True, enemy, nep, ncr, deadline)
            if val < best:
                best = val
                best_move = (fr, fc, tr, tc)
            beta = min(beta, best)
            if beta <= alpha:
                break
        return best, best_move

def update_castling(rights, fr, fc, tr, tc, piece):
    rights = set(rights)
    if piece == ('w', 'K'):
        rights.discard('K'); rights.discard('Q')
    elif piece == ('b', 'K'):
        rights.discard('k'); rights.discard('q')
    elif piece == ('w', 'R'):
        if fr == 7 and fc == 7: rights.discard('K')
        if fr == 7 and fc == 0: rights.discard('Q')
    elif piece == ('b', 'R'):
        if fr == 0 and fc == 7: rights.discard('k')
        if fr == 0 and fc == 0: rights.discard('q')
    return rights

def get_en_passant(board, fr, fc, tr, tc):
    piece = board[fr][fc]
    if piece and piece[1] == 'P' and abs(tr - fr) == 2:
        ep_row = (fr + tr) // 2
        return (ep_row, fc)
    return None

def handle_castling_rook(board, fr, fc, tr, tc):
    piece = board[tr][tc]
    if piece and piece[1] == 'K':
        row = fr
        if tc == 6:  # King-side
            board[row][5] = board[row][7]
            board[row][7] = None
        elif tc == 2:  # Queen-side
            board[row][3] = board[row][0]
            board[row][0] = None

# ── Game State ────────────────────────────────────────────────────────────────

class GameState:
    def __init__(self):
        self.board = init_board()
        self.turn = 'w'
        self.en_passant = None
        self.castling_rights = {'K', 'Q', 'k', 'q'}
        self.selected = None
        self.legal = []
        self.last_move = None
        self.history = []  # for undo
        self.captured_w = []
        self.captured_b = []
        self.status = 'playing'  # playing / checkmate / stalemate / draw
        self.promotion_pending = None  # (tr, tc) waiting for promotion choice
        self.move_log = []  # algebraic notation log

    def select(self, r, c):
        if self.status != 'playing':
            return
        if self.selected == (r, c):
            self.selected = None
            self.legal = []
            return
        piece = self.board[r][c]
        if piece and piece[0] == self.turn:
            self.selected = (r, c)
            all_legal = legal_moves(self.board, self.turn, self.en_passant, self.castling_rights)
            self.legal = [(tr, tc) for fr, fc, tr, tc in all_legal if fr == r and fc == c]
        elif self.selected and (r, c) in self.legal:
            self.move(self.selected[0], self.selected[1], r, c)
        else:
            self.selected = None
            self.legal = []

    def move(self, fr, fc, tr, tc, bot_promote='Q'):
        piece = self.board[fr][fc]
        color, ptype = piece
        captured = self.board[tr][tc]

        # Save state for undo
        self.history.append({
            'board': copy.deepcopy(self.board),
            'turn': self.turn,
            'en_passant': self.en_passant,
            'castling_rights': set(self.castling_rights),
            'last_move': self.last_move,
            'captured_w': list(self.captured_w),
            'captured_b': list(self.captured_b),
            'move_log': list(self.move_log),
        })

        # En passant capture
        ep_capture = None
        if ptype == 'P' and self.en_passant == (tr, tc):
            direction = -1 if color == 'w' else 1
            ep_capture = self.board[tr - direction][tc]
            self.board[tr - direction][tc] = None

        self.board[tr][tc] = piece
        self.board[fr][fc] = None

        # Castling rook move
        if ptype == 'K':
            if tc == 6:
                self.board[fr][5] = self.board[fr][7]
                self.board[fr][7] = None
            elif tc == 2:
                self.board[fr][3] = self.board[fr][0]
                self.board[fr][0] = None

        # Track captured
        cap = captured or ep_capture
        if cap:
            if cap[0] == 'w':
                self.captured_w.append(cap[1])
            else:
                self.captured_b.append(cap[1])

        # Update castling rights
        self.castling_rights = update_castling(self.castling_rights, fr, fc, tr, tc, piece)

        # En passant target
        self.en_passant = get_en_passant(self.board, fr, fc, tr, tc)

        # Promotion
        if ptype == 'P' and (tr == 0 or tr == 7):
            if self.turn == 'w' and bot_promote == 'Q':
                self.promotion_pending = (tr, tc)
                self.last_move = (fr, fc, tr, tc)
                self.selected = None
                self.legal = []
                return  # wait for user promotion choice
            else:
                self.board[tr][tc] = (color, bot_promote)

        self.last_move = (fr, fc, tr, tc)
        self.selected = None
        self.legal = []
        self._finalize_move()

    def promote(self, piece_type):
        if self.promotion_pending is None:
            return
        tr, tc = self.promotion_pending
        color = self.board[tr][tc][0]
        self.board[tr][tc] = (color, piece_type)
        self.promotion_pending = None
        self._finalize_move()

    def _finalize_move(self):
        self.turn = 'b' if self.turn == 'w' else 'w'
        next_moves = legal_moves(self.board, self.turn, self.en_passant, self.castling_rights)
        if not next_moves:
            if is_in_check(self.board, self.turn):
                self.status = 'checkmate'
            else:
                self.status = 'stalemate'

    def undo(self):
        if not self.history:
            return
        state = self.history.pop()
        self.board = state['board']
        self.turn = state['turn']
        self.en_passant = state['en_passant']
        self.castling_rights = state['castling_rights']
        self.last_move = state['last_move']
        self.captured_w = state['captured_w']
        self.captured_b = state['captured_b']
        self.move_log = state['move_log']
        self.selected = None
        self.legal = []
        self.status = 'playing'
        self.promotion_pending = None

    def bot_move(self, difficulty=3):
        """Run minimax to pick bot move (plays as black)."""
        deadline = time.time() + 5.0
        _, move = minimax(
            self.board, difficulty, -float('inf'), float('inf'),
            False, 'b', self.en_passant, self.castling_rights, deadline
        )
        if move:
            fr, fc, tr, tc = move
            self.move(fr, fc, tr, tc, bot_promote='Q')

# ── Renderer ─────────────────────────────────────────────────────────────────

class Renderer:
    def __init__(self, screen):
        self.screen = screen
        pygame.font.init()
        # Load fonts
        self.font_piece   = pygame.font.SysFont('segoeuisymbol', int(SQUARE * 0.78))
        self.font_label   = pygame.font.SysFont('consolas', 13)
        self.font_ui      = pygame.font.SysFont('segoeui', 17)
        self.font_title   = pygame.font.SysFont('Georgia', 28, bold=True)
        self.font_status  = pygame.font.SysFont('segoeui', 22, bold=True)
        self.font_btn     = pygame.font.SysFont('segoeui', 15, bold=True)
        self.font_promo   = pygame.font.SysFont('segoeuisymbol', int(SQUARE * 0.65))
        self.font_log     = pygame.font.SysFont('consolas', 12)

    def draw_board(self, gs: GameState, flipped=False):
        # Board background glow
        glow_rect = pygame.Rect(BOARD_X - 6, BOARD_Y - 6, BOARD_SIZE + 12, BOARD_SIZE + 12)
        pygame.draw.rect(self.screen, (50, 60, 80), glow_rect, border_radius=4)

        for row in range(8):
            for col in range(8):
                dr = 7 - row if flipped else row
                dc = 7 - col if flipped else col
                x = BOARD_X + col * SQUARE
                y = BOARD_Y + row * SQUARE
                rect = pygame.Rect(x, y, SQUARE, SQUARE)

                # Base square colour
                light = (dr + dc) % 2 == 0
                color = C_LIGHT if light else C_DARK
                pygame.draw.rect(self.screen, color, rect)

                # Last move highlight
                if gs.last_move and (dr, dc) in [(gs.last_move[0], gs.last_move[1]), (gs.last_move[2], gs.last_move[3])]:
                    surf = pygame.Surface((SQUARE, SQUARE), pygame.SRCALPHA)
                    surf.fill(C_LAST_MOVE)
                    self.screen.blit(surf, rect)

                # Check highlight
                if gs.status != 'checkmate':
                    for r2 in range(8):
                        for c2 in range(8):
                            if gs.board[r2][c2] == (gs.turn, 'K') and is_in_check(gs.board, gs.turn):
                                if (r2, c2) == (dr, dc):
                                    surf = pygame.Surface((SQUARE, SQUARE), pygame.SRCALPHA)
                                    surf.fill(C_CHECK)
                                    self.screen.blit(surf, rect)

                # Selected highlight
                if gs.selected == (dr, dc):
                    surf = pygame.Surface((SQUARE, SQUARE), pygame.SRCALPHA)
                    surf.fill(C_SELECTED)
                    self.screen.blit(surf, rect)

                # Legal move dots
                if (dr, dc) in gs.legal:
                    surf = pygame.Surface((SQUARE, SQUARE), pygame.SRCALPHA)
                    if gs.board[dr][dc] is not None:
                        pygame.draw.rect(surf, (*C_MOVE_DOT[:3], 120), surf.get_rect(), 5)
                    else:
                        cx, cy = SQUARE // 2, SQUARE // 2
                        pygame.draw.circle(surf, C_MOVE_DOT, (cx, cy), SQUARE // 7)
                    self.screen.blit(surf, rect)

                # Piece
                piece = gs.board[dr][dc]
                if piece:
                    sym = UNICODE_PIECES[piece]
                    shadow = self.font_piece.render(sym, True, (0, 0, 0, 120))
                    glyph  = self.font_piece.render(sym, True, C_WHITE_PIECE if piece[0] == 'w' else C_BLACK_PIECE)
                    cx = x + SQUARE // 2 - glyph.get_width() // 2
                    cy = y + SQUARE // 2 - glyph.get_height() // 2
                    self.screen.blit(shadow, (cx + 2, cy + 2))
                    self.screen.blit(glyph, (cx, cy))

        # Rank / file labels
        files = 'abcdefgh'
        for i in range(8):
            fi = 7 - i if flipped else i
            ri = 7 - i if flipped else i
            fc = self.font_label.render(files[fi], True, C_TEXT_DIM)
            self.screen.blit(fc, (BOARD_X + fi * SQUARE + SQUARE - 14, BOARD_Y + BOARD_SIZE + 2))
            rc = self.font_label.render(str(8 - ri), True, C_TEXT_DIM)
            self.screen.blit(rc, (BOARD_X - 14, BOARD_Y + ri * SQUARE + 2))

    def draw_panel(self, gs: GameState, mode, difficulty):
        panel_x = BOARD_X + BOARD_SIZE + 20
        panel_w = WIDTH - panel_x - 15
        panel_rect = pygame.Rect(panel_x, 10, panel_w, HEIGHT - 20)
        pygame.draw.rect(self.screen, C_PANEL, panel_rect, border_radius=10)
        pygame.draw.rect(self.screen, C_BORDER, panel_rect, 1, border_radius=10)

        # Title
        title = self.font_title.render("♟ CHESS", True, C_ACCENT)
        self.screen.blit(title, (panel_x + (panel_w - title.get_width()) // 2, 22))

        # Mode tag
        mode_str = "2 Player" if mode == '2p' else f"vs Bot  (depth {difficulty})"
        mt = self.font_ui.render(mode_str, True, C_TEXT_DIM)
        self.screen.blit(mt, (panel_x + (panel_w - mt.get_width()) // 2, 58))

        y = 95
        # Turn indicator
        turn_color = C_WHITE_PIECE if gs.turn == 'w' else C_BLACK_PIECE
        turn_text = "White to move" if gs.turn == 'w' else "Black to move"
        circle_x = panel_x + 18
        pygame.draw.circle(self.screen, turn_color, (circle_x, y + 9), 8)
        pygame.draw.circle(self.screen, C_BORDER, (circle_x, y + 9), 8, 1)
        tt = self.font_ui.render(turn_text, True, C_TEXT_MAIN)
        self.screen.blit(tt, (circle_x + 14, y))
        y += 32

        # Status
        if gs.status == 'checkmate':
            winner = "White" if gs.turn == 'b' else "Black"
            st = self.font_status.render(f"Checkmate! {winner} wins", True, (220, 100, 80))
            self.screen.blit(st, (panel_x + (panel_w - st.get_width()) // 2, y))
        elif gs.status == 'stalemate':
            st = self.font_status.render("Stalemate! Draw", True, (180, 180, 80))
            self.screen.blit(st, (panel_x + (panel_w - st.get_width()) // 2, y))
        elif is_in_check(gs.board, gs.turn):
            st = self.font_status.render("Check!", True, (220, 80, 80))
            self.screen.blit(st, (panel_x + (panel_w - st.get_width()) // 2, y))
        y += 30

        # Divider
        pygame.draw.line(self.screen, C_BORDER, (panel_x + 10, y), (panel_x + panel_w - 10, y))
        y += 12

        # Captured pieces
        self.screen.blit(self.font_ui.render("Captured:", True, C_TEXT_DIM), (panel_x + 10, y))
        y += 22
        cap_font = pygame.font.SysFont('segoeuisymbol', 17)

        # White captured (by black)
        label_w = self.font_label.render("White's losses:", True, C_TEXT_DIM)
        self.screen.blit(label_w, (panel_x + 10, y))
        y += 16
        row_str = ''.join(UNICODE_PIECES[('w', p)] for p in sorted(gs.captured_w))
        if row_str:
            cs = cap_font.render(row_str, True, C_WHITE_PIECE)
            self.screen.blit(cs, (panel_x + 10, y))
        y += 22

        label_b = self.font_label.render("Black's losses:", True, C_TEXT_DIM)
        self.screen.blit(label_b, (panel_x + 10, y))
        y += 16
        row_str2 = ''.join(UNICODE_PIECES[('b', p)] for p in sorted(gs.captured_b))
        if row_str2:
            cs2 = cap_font.render(row_str2, True, C_BLACK_PIECE)
            self.screen.blit(cs2, (panel_x + 10, y))
        y += 26

        # Divider
        pygame.draw.line(self.screen, C_BORDER, (panel_x + 10, y), (panel_x + panel_w - 10, y))
        y += 10

        # Move log
        self.screen.blit(self.font_ui.render("Move Log", True, C_TEXT_DIM), (panel_x + 10, y))
        y += 20
        log_area_h = 120
        log_surf = pygame.Surface((panel_w - 20, log_area_h), pygame.SRCALPHA)
        log_surf.fill((0, 0, 0, 0))
        # Generate move log from history
        log_lines = []
        for i, h in enumerate(gs.history):
            pass  # move log placeholder
        # Simple ply count display
        total_plies = len(gs.history)
        for i in range(max(0, total_plies - 8), total_plies):
            n = i // 2 + 1
            side = "W" if i % 2 == 0 else "B"
            log_lines.append(f"{n}.{side}  ply {i+1}")
        for li, line in enumerate(log_lines[-8:]):
            lt = self.font_log.render(line, True, C_TEXT_DIM)
            log_surf.blit(lt, (4, li * 14))
        self.screen.blit(log_surf, (panel_x + 10, y))
        y += log_area_h + 6

        # Divider
        pygame.draw.line(self.screen, C_BORDER, (panel_x + 10, y), (panel_x + panel_w - 10, y))
        y += 10

        return panel_x, panel_w, y

    def draw_buttons(self, panel_x, panel_w, y, mouse_pos):
        buttons = {}
        btn_data = [
            ('undo',    '⟵ Undo',    C_BTN),
            ('new',     '↺ New Game', C_BTN),
            ('flip',    '⇅ Flip',     C_BTN),
        ]
        bw = panel_w - 20
        bh = 30
        for i, (key, label, base_color) in enumerate(btn_data):
            bx = panel_x + 10
            by = y + i * (bh + 8)
            rect = pygame.Rect(bx, by, bw, bh)
            hover = rect.collidepoint(mouse_pos)
            col = C_BTN_HOVER if hover else base_color
            pygame.draw.rect(self.screen, col, rect, border_radius=6)
            pygame.draw.rect(self.screen, C_BORDER, rect, 1, border_radius=6)
            lt = self.font_btn.render(label, True, C_TEXT_MAIN)
            self.screen.blit(lt, (bx + bw // 2 - lt.get_width() // 2, by + bh // 2 - lt.get_height() // 2))
            buttons[key] = rect
        return buttons

    def draw_promotion(self, color):
        """Draw promotion choice overlay."""
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        choices = ['Q', 'R', 'B', 'N']
        total_w = len(choices) * (SQUARE + 10) - 10
        sx = (WIDTH - total_w) // 2
        sy = HEIGHT // 2 - SQUARE // 2

        title = self.font_status.render("Choose promotion piece:", True, C_TEXT_MAIN)
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, sy - 40))

        rects = {}
        for i, p in enumerate(choices):
            rx = sx + i * (SQUARE + 10)
            rect = pygame.Rect(rx, sy, SQUARE, SQUARE)
            pygame.draw.rect(self.screen, C_PANEL, rect, border_radius=8)
            pygame.draw.rect(self.screen, C_ACCENT, rect, 2, border_radius=8)
            sym = UNICODE_PIECES[(color, p)]
            g = self.font_promo.render(sym, True, C_WHITE_PIECE if color == 'w' else C_BLACK_PIECE)
            self.screen.blit(g, (rx + SQUARE // 2 - g.get_width() // 2, sy + SQUARE // 2 - g.get_height() // 2))
            rects[p] = rect
        return rects

    def draw_menu(self, mouse_pos):
        self.screen.fill(C_BG)
        # Background pattern
        for i in range(0, WIDTH, 60):
            for j in range(0, HEIGHT, 60):
                if (i // 60 + j // 60) % 2 == 0:
                    pygame.draw.rect(self.screen, (22, 22, 30), (i, j, 60, 60))

        title = self.font_title.render("♟  CHESS", True, C_ACCENT)
        sub   = self.font_ui.render("A classic game of strategy", True, C_TEXT_DIM)
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 160))
        self.screen.blit(sub,   (WIDTH // 2 - sub.get_width() // 2,  200))

        buttons = {}
        btn_labels = [
            ('2p',    '⚔  2 Player'),
            ('bot_e', '🤖  vs Bot (Easy)'),
            ('bot_m', '🤖  vs Bot (Medium)'),
            ('bot_h', '🤖  vs Bot (Hard)'),
        ]
        bw, bh = 280, 50
        for i, (key, label) in enumerate(btn_labels):
            bx = WIDTH // 2 - bw // 2
            by = 260 + i * (bh + 15)
            rect = pygame.Rect(bx, by, bw, bh)
            hover = rect.collidepoint(mouse_pos)
            col = C_BTN_ACTIVE if hover else C_BTN
            pygame.draw.rect(self.screen, col, rect, border_radius=10)
            pygame.draw.rect(self.screen, C_BORDER, rect, 1, border_radius=10)
            lt = self.font_btn.render(label, True, C_TEXT_MAIN)
            self.screen.blit(lt, (bx + bw // 2 - lt.get_width() // 2, by + bh // 2 - lt.get_height() // 2))
            buttons[key] = rect

        credit = self.font_label.render("White = bottom   |   Black = top", True, C_TEXT_DIM)
        self.screen.blit(credit, (WIDTH // 2 - credit.get_width() // 2, HEIGHT - 40))
        return buttons

    def draw_thinking(self):
        t = self.font_status.render("Bot is thinking...", True, C_TEXT_DIM)
        bx = BOARD_X + BOARD_SIZE // 2 - t.get_width() // 2
        by = BOARD_Y + BOARD_SIZE + 14
        self.screen.blit(t, (bx, by))

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Chess")
    clock  = pygame.time.Clock()
    renderer = Renderer(screen)

    # State
    scene = 'menu'   # 'menu' | 'game'
    gs    = None
    mode  = '2p'     # '2p' | 'bot'
    difficulty = 3
    flipped = False
    bot_thinking = False
    bot_timer    = 0

    while True:
        mouse_pos = pygame.mouse.get_pos()

        # ── Events ──────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if scene == 'menu':
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    btns = renderer.draw_menu(mouse_pos)
                    for k, r in btns.items():
                        if r.collidepoint(mouse_pos):
                            gs = GameState()
                            flipped = False
                            bot_thinking = False
                            if k == '2p':
                                mode = '2p'; difficulty = 0
                            elif k == 'bot_e':
                                mode = 'bot'; difficulty = 2
                            elif k == 'bot_m':
                                mode = 'bot'; difficulty = 3
                            elif k == 'bot_h':
                                mode = 'bot'; difficulty = 4
                            scene = 'game'

            elif scene == 'game':
                # Promotion overlay
                if gs.promotion_pending:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        promo_rects = renderer.draw_promotion(gs.board[gs.promotion_pending[0]][gs.promotion_pending[1]][0])
                        for p, r in promo_rects.items():
                            if r.collidepoint(mouse_pos):
                                gs.promote(p)
                    continue  # don't process board clicks while promoting

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Check panel buttons
                    # (buttons drawn in draw_panel + draw_buttons; re-compute rects)
                    bw = WIDTH - (BOARD_X + BOARD_SIZE + 20) - 20 - 15
                    bx_base = BOARD_X + BOARD_SIZE + 30
                    btn_y_base = HEIGHT - 3 * (30 + 8) - 20

                    undo_rect  = pygame.Rect(bx_base, btn_y_base,           bw, 30)
                    new_rect   = pygame.Rect(bx_base, btn_y_base + 38,      bw, 30)
                    flip_rect  = pygame.Rect(bx_base, btn_y_base + 76,      bw, 30)

                    if undo_rect.collidepoint(mouse_pos):
                        gs.undo()
                        if mode == 'bot':  # undo twice to get back to human turn
                            gs.undo()
                        bot_thinking = False
                    elif new_rect.collidepoint(mouse_pos):
                        gs = GameState()
                        bot_thinking = False
                    elif flip_rect.collidepoint(mouse_pos):
                        flipped = not flipped
                    elif gs.status == 'playing' and not bot_thinking:
                        # Board click
                        bx = event.pos[0] - BOARD_X
                        by = event.pos[1] - BOARD_Y
                        if 0 <= bx < BOARD_SIZE and 0 <= by < BOARD_SIZE:
                            col = bx // SQUARE
                            row = by // SQUARE
                            if flipped:
                                col = 7 - col
                                row = 7 - row
                            # Only allow human to move when it's their turn
                            if mode == 'bot' and gs.turn == 'b':
                                pass  # bot's turn
                            else:
                                gs.select(row, col)
                                # If move was made and bot mode, trigger bot
                                if mode == 'bot' and gs.turn == 'b' and gs.status == 'playing' and not gs.promotion_pending:
                                    bot_thinking = True
                                    bot_timer = pygame.time.get_ticks()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        scene = 'menu'
                    elif event.key == pygame.K_u:
                        gs.undo()
                        if mode == 'bot': gs.undo()
                        bot_thinking = False
                    elif event.key == pygame.K_f:
                        flipped = not flipped

        # ── Bot thinking (non-blocking via timer) ───────────────────────
        if scene == 'game' and bot_thinking and gs and gs.status == 'playing':
            if pygame.time.get_ticks() - bot_timer > 300:  # short delay for UX
                gs.bot_move(difficulty)
                bot_thinking = False

        # ── Draw ─────────────────────────────────────────────────────────
        if scene == 'menu':
            renderer.draw_menu(mouse_pos)

        elif scene == 'game' and gs:
            screen.fill(C_BG)
            renderer.draw_board(gs, flipped)
            px, pw, btn_start_y = renderer.draw_panel(gs, mode, difficulty)

            # Position buttons near bottom of panel
            btn_y = HEIGHT - 3 * (30 + 8) - 20
            # Adjust panel button draw y
            renderer.draw_buttons(px, pw, btn_y, mouse_pos)

            if bot_thinking:
                renderer.draw_thinking()

            # Promotion overlay (on top)
            if gs.promotion_pending:
                piece_color = gs.board[gs.promotion_pending[0]][gs.promotion_pending[1]][0]
                renderer.draw_promotion(piece_color)

            # Game over overlay
            if gs.status in ('checkmate', 'stalemate'):
                overlay = pygame.Surface((BOARD_SIZE, 60), pygame.SRCALPHA)
                overlay.fill((10, 10, 20, 200))
                screen.blit(overlay, (BOARD_X, BOARD_Y + BOARD_SIZE // 2 - 30))
                if gs.status == 'checkmate':
                    winner = "White" if gs.turn == 'b' else "Black"
                    msg = f"Checkmate! {winner} wins  |  Press U to undo"
                else:
                    msg = "Stalemate! It's a draw  |  Press U to undo"
                mt = renderer.font_status.render(msg, True, C_TEXT_MAIN)
                screen.blit(mt, (BOARD_X + BOARD_SIZE // 2 - mt.get_width() // 2,
                                 BOARD_Y + BOARD_SIZE // 2 - mt.get_height() // 2))

            # ESC hint
            hint = renderer.font_label.render("ESC = Menu   U = Undo   F = Flip", True, C_TEXT_DIM)
            screen.blit(hint, (BOARD_X, HEIGHT - 18))

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == '__main__':
    main()
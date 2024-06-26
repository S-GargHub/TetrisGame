import pygame
import random
import asyncio
import os

pygame.init()
SCREEN = WIDTH, HEIGHT = 300, 500
win = pygame.display.set_mode(SCREEN, pygame.NOFRAME)

CELLSIZE = 20
ROWS = (HEIGHT-120) // CELLSIZE
COLS = WIDTH // CELLSIZE

clock = pygame.time.Clock()
FPS = 24

# COLORS *********************************************************************

BLACK = (21, 24, 29)
BLUE = (31, 25, 76)
RED = (252, 91, 122)
WHITE = (255, 255, 255)

# Images ********************************************************************* 

img1 = pygame.image.load('Assets/1.png')
img2 = pygame.image.load('Assets/2.png')
img3 = pygame.image.load('Assets/3.png')
img4 = pygame.image.load('Assets/4.png')

Assets = {
	1 : img1,
	2 : img2,
	3 : img3,
	4 : img4
}

# FONTS **********************************************************************

font = pygame.font.Font('Fonts/Alternity-8w7J.ttf', 50)
font2 = pygame.font.SysFont('cursive', 25)


def draw_text(text, x, y, color):
  text_surface = font2.render(text, True, color)
  win.blit(text_surface, (x, y))

# Intro Screen
async def intro_screen():
	running = True
	player_name = ""
	while running:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_RETURN:
					if not player_name:
						draw_text("Please enter a name!", WIDTH // 3, HEIGHT // 2, RED)
					else:
						running = False  # Exit intro screen
				elif event.key == pygame.K_BACKSPACE:
					player_name = player_name[:-1]  # Remove last character from player name
				else:
					player_name += event.unicode  # Add character to player name

		win.fill(WHITE)
		draw_text("Welcome to Tetris!", WIDTH // 3 - 30, HEIGHT // 3, RED)
		draw_text("Enter your name:", WIDTH // 3 - 50, HEIGHT // 2 - 30, RED)
		draw_text(player_name, WIDTH // 3, HEIGHT // 2, BLUE)
		pygame.display.update()

		clock.tick(FPS)
		await asyncio.sleep(0)
	return player_name

# OBJECTS ********************************************************************

class Tetramino:
	# matrix
	# 0   1   2   3
	# 4   5   6   7
	# 8   9   10  11
	# 12  13  14  15

	FIGURES = {
		'I' : [[1, 5, 9, 13], [4, 5, 6, 7]],
		'Z' : [[4, 5, 9, 10], [2, 6, 5, 9]],
		'S' : [[6, 7, 9, 10], [1, 5, 6, 10]],
		'L' : [[1, 2, 5, 9], [0, 4, 5, 6], [1, 5, 9, 8], [4, 5, 6, 10]],
		'J' : [[1, 2, 6, 10], [5, 6, 7, 9], [2, 6, 10, 11], [3, 5, 6, 7]],
		'T' : [[1, 4, 5, 6], [1, 4, 5, 9], [4, 5, 6, 9], [1, 5, 6, 9]],
		'O' : [[1, 2, 5, 6]]
	}

	TYPES = ['I', 'Z', 'S', 'L', 'J', 'T', 'O']

	def __init__(self, x, y):
		self.x = x
		self.y = y
		#Additional: Shuffled the list to generate random figure everytime
		random.shuffle(self.TYPES)  # Shuffle the list of tetromino types
		self.type = self.TYPES[0]
		self.shape = self.FIGURES[self.type]
		self.color = random.randint(1, 4)
		self.rotation = 0

	def image(self):
		return self.shape[self.rotation]

	def rotate(self):
		self.rotation = (self.rotation + 1) % len(self.shape)


class Tetris:
	def __init__(self, rows, cols):
		self.rows = rows
		self.cols = cols
		self.score = 0
		self.level = 1
		self.board = [[0 for j in range(cols)] for i in range(rows)]
		self.next = None
		#Additional: Introduced pause game and hold piece features
		self.held = None  # New attribute for holding a Tetramino piece
		self.paused = False  # Initialize pause state
		self.gameover = False
		
		self.new_figure()

	def draw_grid(self):
		for i in range(self.rows+1):
			pygame.draw.line(win, WHITE, (0, CELLSIZE*i), (WIDTH, CELLSIZE*i))
		for j in range(self.cols):
			pygame.draw.line(win, WHITE, (CELLSIZE*j, 0), (CELLSIZE*j, HEIGHT-120))

	def new_figure(self):
		if not self.next:
			self.next = Tetramino(5, 0)
		self.figure = self.next
		self.next = Tetramino(5, 0)

	def intersects(self):
		intersection = False
		for i in range(4):
			for j in range(4):
				if i * 4 + j in self.figure.image():
					if i + self.figure.y > self.rows - 1 or \
					   j + self.figure.x > self.cols - 1 or \
					   j + self.figure.x < 0 or \
					   self.board[i + self.figure.y][j + self.figure.x] > 0:
						intersection = True
		return intersection

	def remove_line(self):
		rerun = False
		for y in range(self.rows-1, 0, -1):
			is_full = True
			for x in range(0, self.cols):
				if self.board[y][x] == 0:
					is_full = False
			if is_full:
				del self.board[y]
				self.board.insert(0, [0 for i in range(self.cols)])
				self.score += 1
				if self.score % 10 == 0:
					self.level += 1
				rerun = True

		if rerun:
			self.remove_line()

	def freeze(self):
		for i in range(4):
			for j in range(4):
				if i * 4 + j in self.figure.image():
					self.board[i + self.figure.y][j + self.figure.x] = self.figure.color
		self.remove_line()
		self.new_figure()
		if self.intersects():
			self.gameover = True

	def go_space(self):
		while not self.intersects():
			self.figure.y += 1
		self.figure.y -= 1
		self.freeze()

	def go_down(self):
		self.figure.y += 1
		if self.intersects():
			self.figure.y -= 1
			self.freeze()

	def go_side(self, dx):
		self.figure.x += dx
		if self.intersects():
			self.figure.x -= dx

	def rotate(self):
		rotation = self.figure.rotation
		self.figure.rotate()
		if self.intersects():
			self.figure.rotation = rotation

	def hold(self):
		if not self.held:  # If no piece is currently held
			self.held = self.figure
			self.new_figure()  # Generate a new piece
		else:  # If there is a piece already held
			self.figure, self.held = self.held, self.figure
			self.figure.x = 5
			self.figure.y = 0
			# Check if the new position of the held piece intersects with existing pieces
			if self.intersects():
				# If the new position intersects, revert the swap and set the game to over
				self.figure, self.held = self.held, self.figure
				self.figure.x = 5
				self.figure.y = 0
				self.gameover = True

tetris = Tetris(ROWS, COLS)



# Define high_scores dictionary
high_scores = {}

def load_high_scores():
	try:
		with open("high_scores.txt", "r") as file:
			data = file.readlines()
			for line in data:
				name, score = line.strip().split(":")
				high_scores[name] = int(score)
	except FileNotFoundError:
		print("High scores file not found. Creating a new one...")
		# Create a new high scores file with default values
		save_high_scores()
	except Exception as e:
		print(f"An error occurred while loading high scores: {e}")


# Save high scores to a file
def save_high_scores():
	with open("high_scores.txt", "w") as file:
		print("High scores file path:", os.path.abspath("high_scores.txt"))
		for name, score in high_scores.items():
			file.write(f"{name}:{score}\n")

# Update high scores
def update_high_scores(player_name, score):
	# If there are no existing high scores, or if the current score is higher than any existing high score
	if not high_scores or score > max(high_scores.values()):
		high_scores[player_name] = score
		save_high_scores()
		

# Load high scores at the beginning of the game
load_high_scores()

async def main():
	running = True
	counter = 0
	move_down = False
	can_move = True
	high_score_updated = False

	# Get player name
	player_name = await intro_screen()

	if not player_name:
		running = False

	while running:
		win.fill(BLACK)

		counter += 1
		if counter >= 10000:
			counter = 0

		if can_move and not tetris.paused:
			if counter % (FPS // (tetris.level * 2)) == 0 or move_down:
				if not tetris.gameover:
					tetris.go_down()


		# EVENT HANDLING *********************************************************
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
				#Additional - Quit the game window
				pygame.quit()

			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_p:  # Pause the game when 'P' is pressed
					tetris.paused = not tetris.paused
		
				if can_move and not tetris.gameover and not tetris.paused:
					if event.key == pygame.K_LEFT:
						tetris.go_side(-1)

					if event.key == pygame.K_RIGHT:
						tetris.go_side(1)

					if event.key == pygame.K_UP:
						tetris.rotate()

					if event.key == pygame.K_DOWN:
						move_down = True

					if event.key == pygame.K_SPACE:
						tetris.go_space()

				if event.key == pygame.K_r:
					tetris.__init__(ROWS, COLS)
					high_score_updated = False

				if event.key == pygame.K_p:
					can_move = not can_move

				if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
					running = False

			if event.type == pygame.KEYUP:
				if event.key == pygame.K_DOWN:
					move_down = False

			if event.type == pygame.KEYDOWN:
				if can_move and not tetris.gameover and not tetris.paused:
					# Existing key events...
					
					# New key event for holding a piece
					if event.key == pygame.K_c:
						tetris.hold()

		# tetris.draw_grid()
		for x in range(ROWS):
			for y in range(COLS):
				if tetris.board[x][y] > 0:
					val = tetris.board[x][y]
					img = Assets[val]
					win.blit(img, (y*CELLSIZE, x*CELLSIZE))
					pygame.draw.rect(win, WHITE, (y*CELLSIZE, x*CELLSIZE,
										CELLSIZE, CELLSIZE), 1)
		
		if tetris.figure:
			for i in range(4):
				for j in range(4):
					if i * 4 + j in tetris.figure.image():
						img = Assets[tetris.figure.color]
						x = CELLSIZE * (tetris.figure.x + j)
						y = CELLSIZE * (tetris.figure.y + i)
						win.blit(img, (x, y))
						pygame.draw.rect(win, WHITE, (x, y, CELLSIZE, CELLSIZE), 1)
		

		# GAMEOVER ***************************************************************
		if tetris.gameover:
			if high_score_updated == False:
				# Update high scores
				update_high_scores(player_name, tetris.score)
				high_score_updated = True

			rect = pygame.Rect((50, 140, WIDTH-100, HEIGHT-350))
			pygame.draw.rect(win, BLACK, rect)
			pygame.draw.rect(win, RED, rect, 2)

			over = font2.render('Game Over', True, WHITE)
			msg1 = font2.render('Press r to restart', True, RED)
			msg2 = font2.render('Press q to quit', True, RED)

			win.blit(over, (rect.centerx-over.get_width()/2, rect.y + 20))
			win.blit(msg1, (rect.centerx-msg1.get_width()/2, rect.y + 80))
			win.blit(msg2, (rect.centerx-msg2.get_width()/2, rect.y + 110))

		# HUD ********************************************************************
		pygame.draw.rect(win, BLUE, (0, HEIGHT-120, WIDTH, 120))
		if tetris.next:
			for i in range(4):
				for j in range(4):
					if i * 4 + j in tetris.next.image():
						img = Assets[tetris.next.color]
						x = CELLSIZE * (tetris.next.x + j - 4)
						y = HEIGHT - 100 + CELLSIZE * (tetris.next.y + i)
						win.blit(img, (x, y))

		scoreimg = font.render(f'{tetris.score}', True, WHITE)
		levelimg = font2.render(f'Level : {tetris.level}', True, WHITE)
		win.blit(scoreimg, (250-scoreimg.get_width()//2, HEIGHT-110))
		#win.blit(levelimg, (10, HEIGHT-30))  # Adjusted position for level
		win.blit(levelimg, (250-levelimg.get_width()//2, HEIGHT-30))

		player_text = "Hello, " + player_name + "!!"
		player_render = font2.render(player_text, True, RED)
		player_text_width = player_render.get_width()
		x_coordinate = (WIDTH - player_text_width) // 2
		win.blit(player_render, (x_coordinate, HEIGHT-120))
		
		if high_scores:
			score_text = "Highest Score: "
			for i, (_, score) in enumerate(high_scores.items(), start=1):
				score_text += f"{score}"
				score_render = font2.render(score_text, True, RED)
				win.blit(score_render, (10, HEIGHT-30))  # Adjusted position for high score below next block
		else:
			# No high scores yet
			no_scores_text = font2.render("No high scores yet", True, RED)
			win.blit(no_scores_text, (10, HEIGHT-30))  # Adjusted position for high score below next block


		pygame.draw.rect(win, BLUE, (0, 0, WIDTH, HEIGHT - 120), 2)
		clock.tick(FPS)
		pygame.display.update()
		await asyncio.sleep(0)
	pygame.quit()
asyncio.run(main())
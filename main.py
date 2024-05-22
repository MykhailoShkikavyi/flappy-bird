import os
import pygame
from pygame.locals import *
import random
import neat

pygame.init()

clock = pygame.time.Clock()
fps = 60

# game resolution 
screenWidth = 764
screenLength = 836

screen = pygame.display.set_mode((screenWidth, screenLength))
pygame.display.set_caption("Flappy Bird")

# define font
font = pygame.font.SysFont("Bauhaus 93", 60)

# define colors
white = (255, 255, 255)

# game variables
groundScroll = 0
scrollSpeed = 4
flying = False
gameOver = False
pipeGap = 150
pipeFrequency = 1200  # in milliseconds
lastPipe = pygame.time.get_ticks() - pipeFrequency
score = 0
passPipe = False

# load game images
backgroundImage = pygame.image.load("FlappyBird/backgound.png")
groundImage = pygame.image.load("FlappyBird/ground.png")
buttonImage = pygame.image.load("FlappyBird/restart.png")
backButtonImage = pygame.image.load("FlappyBird/button_menu.png")
pipe_img = pygame.image.load("FlappyBird/pipe.png")
base_img = pygame.image.load("FlappyBird/ground.png")
startGameImage = pygame.image.load("FlappyBird/playButton.png")
startAiImage = pygame.image.load("FlappyBird/playAiButton.png")
exitButton = pygame.image.load("FlappyBird/exitButton.png")
titleButton = pygame.image.load("FlappyBird/titleButton.png")

gen = 0

def draw_text(text, font, textColor, x, y):
    img = font.render(text, True, textColor)
    screen.blit(img, (x, y))

def resetGame():
    pipeGroup.empty()
    flappy.rect.x = 100
    flappy.rect.y = int(screenLength / 2)
    score = 0
    return score

class Bird(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        self.index = 0
        self.counter = 0
        for num in range(1, 4):
            img = pygame.image.load(f"FlappyBird/bird{num}.png")
            self.images.append(img)
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.velocity = 0
        self.clicked = False
    
    def update(self):
        if flying:
            self.velocity += 0.5
            if self.velocity > 8:
                self.velocity = 8
            if self.rect.bottom < 668:
                self.rect.y += int(self.velocity)

        if not gameOver:
            if (pygame.mouse.get_pressed()[0] == 1 or pygame.key.get_pressed()[pygame.K_SPACE]) and not self.clicked:
                self.clicked = True
                self.velocity = -10
            if pygame.mouse.get_pressed()[0] == 0 and not pygame.key.get_pressed()[pygame.K_SPACE]:
                self.clicked = False           

            self.counter += 1
            flapCooldown = 5
            if self.counter > flapCooldown:
                self.counter = 0
                self.index += 1
                if self.index >= len(self.images):
                    self.index = 0
                
            self.image = self.images[self.index]
            self.image = pygame.transform.rotate(self.images[self.index], -2 * self.velocity)
        else:
            self.image = pygame.transform.rotate(self.images[self.index], -90)

class Pipe(pygame.sprite.Sprite):
    def __init__(self, x, y, position): 
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("FlappyBird/pipe.png")
        self.rect = self.image.get_rect()
        if position == 1:
            self.image = pygame.transform.flip(self.image, False, True)
            self.rect.bottomleft = [x, y - int(pipeGap / 2)]
        if position == -1:
            self.rect.topleft = [x, y + int(pipeGap / 2)]
    def update(self):
        self.rect.x -= scrollSpeed
        if self.rect.x < -100:
            self.kill()

class Button():
    def __init__(self, x, y, image, scale=1, action=None):
        self.raw_image = image
        self.image = pygame.transform.scale(image, (image.get_width() * scale, image.get_height() * scale))
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.action = action

    def draw(self):
        action = False
        mousePosition = pygame.mouse.get_pos()
        if self.rect.collidepoint(mousePosition):
            if pygame.mouse.get_pressed()[0] == 1:
                action = True
                if self.action:
                    self.action()
        screen.blit(self.image, (self.rect.x, self.rect.y))
        return action



class PipeAI:
    GAP = 170
    VEL = 5

    def __init__(self, x):
        self.x = x
        self.height = 0
        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(pipe_img, False, True)
        self.PIPE_BOTTOM = pipe_img
        self.passed = False
        self.set_height()

    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VEL

    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))
        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)
        if b_point or t_point:
            return True
        return False

class Base:
    """
    Represents the moving floor of the game
    """
    VEL = 5
    WIDTH = base_img.get_width()
    IMG = base_img

    def __init__(self, y):
        """
        Initialize the object
        :param y: int
        :return: None
        """
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        """
        move floor so it looks like its scrolling
        :return: None
        """
        self.x1 -= self.VEL
        self.x2 -= self.VEL
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        """
        Draw the floor. This is two images that move together.
        :param win: the pygame surface/window
        :return: None
        """
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))

def back_to_main_menu():
    global gameOver
    gameOver = False

birdGroup = pygame.sprite.Group()
pipeGroup = pygame.sprite.Group()
flappy = Bird(100, int(screenLength / 2))
birdGroup.add(flappy)

# restart and bring back to menu button instance
button = Button(screenWidth // 2 - 50, screenLength // 2 - 200, buttonImage, 1, back_to_main_menu)
backButton = Button(screenWidth // 2 - 50, screenLength // 2 - 150, backButtonImage, 3)

#main menu buttons
start_button = Button((screenWidth - int(startGameImage.get_width() * 0.14)) // 2, screenLength // 2 - 100, startGameImage, 0.14)
ai_button = Button((screenWidth - int(startAiImage.get_width() * 0.14)) // 2, screenLength // 2, startAiImage, 0.14)
exit_button = Button((screenWidth - int(exitButton.get_width() * 0.14)) // 2, screenLength // 2 + 100, exitButton, 0.14)
title_button = Button((screenWidth - int(exitButton.get_width() * 0.25)) // 2, 75, titleButton, 0.25)


def main_menu():
    screen.blit(backgroundImage, (0, 0))
    screen.blit(groundImage, (groundScroll, 668))

    if start_button.draw():
        return "start"
    if ai_button.draw():
        return "ai"
    if exit_button.draw():
        pygame.quit()
        exit()
    title_button.draw()
    
    
    pygame.display.update()
    
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            quit()
    return None

DRAW_LINES = False

def blitRotateCenter(surf, image, topleft, angle):
    rotated_image = pygame.transform.rotate(image, angle)
    new_rect = rotated_image.get_rect(center=image.get_rect(topleft=topleft).center)
    surf.blit(rotated_image, new_rect.topleft)

def draw_window_ai(win, birds, pipes, base, score, gen, pipe_ind):
    # Set the minimum generation to 1 if it is 0
    if gen == 0:
        gen = 1
    
    # Draw the background image
    win.blit(backgroundImage, (0, 0))
    
    # Draw each pipe in the pipes list
    for pipe in pipes:
        pipe.draw(win)
    
    # Draw the base (ground) of the game
    base.draw(win)
    
    # Draw each bird in the birds list
    for bird in birds:
        if DRAW_LINES:
            try:
                # Draw lines from the bird to the top and bottom pipes
                pygame.draw.line(win, (255, 0, 0), 
                                 (bird.x + bird.img.get_width() / 2, bird.y + bird.img.get_height() / 2),
                                 (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_TOP.get_width() / 2, pipes[pipe_ind].height), 5)
                pygame.draw.line(win, (255, 0, 0), 
                                 (bird.x + bird.img.get_width() / 2, bird.y + bird.img.get_height() / 2),
                                 (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_BOTTOM.get_width() / 2, pipes[pipe_ind].bottom), 5)
            except:
                pass
        # Draw the bird
        bird.draw(win)
    
    # Display the current score
    score_label = font.render("Score: " + str(score), 1, (255, 255, 255))
    win.blit(score_label, (screenWidth - score_label.get_width() - 15, 10))
    
    # Display the current generation
    gen_label = font.render("Gen: " + str(gen), 1, (255, 255, 255))
    win.blit(gen_label, (10, 10))

    # Display additional AI training information
    info_label1 = font.render(f"Birds in generation: 20", 1, (255, 255, 255))
    info_label2 = font.render(f"Alive: {len(birds)}", 1, (255, 255, 255))
    info_label3 = font.render(f"Died: {20 - len(birds)}", 1, (255, 255, 255))
    win.blit(info_label1, (10, 50))
    win.blit(info_label2, (10, 90))
    win.blit(info_label3, (10, 130))

    # Update the display
    pygame.display.update()

class BirdAi:
    MAX_ROTATION = 25
    IMGS = [pygame.image.load(f"FlappyBird/bird{num}.png") for num in range(1, 4)]
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        self.vel = -10.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1
        displacement = self.vel * self.tick_count + 0.5 * 3 * self.tick_count ** 2
        if displacement >= 16:
            displacement = (displacement / abs(displacement)) * 16
        if displacement < 0:
            displacement -= 2
        self.y += displacement
        if displacement < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win):
        self.img_count += 1
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME * 2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME * 3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME * 4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME * 4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME * 2
        blitRotateCenter(win, self.img, (self.x, self.y), self.tilt)

    def get_mask(self):
        return pygame.mask.from_surface(self.img)

def main_ai(genomes, config):
    global gen
    gen += 1

    nets = []
    ge = []
    birds = []

    for genome_id, genome in genomes:
        genome.fitness = 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        birds.append(BirdAi(230,350))
        ge.append(genome)

    base = Base(730)
    pipes = [PipeAI(700)]
    score = 0
    win = screen
    clock = pygame.time.Clock()
    run = True

    while run:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
                break

        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        else:
            run = False
            break

        for x, bird in enumerate(birds):
            bird.move()
            ge[x].fitness += 0.1

            output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

            if output[0] > 0.5:
                bird.jump()

        base.move()
        add_pipe = False
        rem = []
        for pipe in pipes:
            pipe.move()
            for x, bird in enumerate(birds):
                if pipe.collide(bird):
                    ge[x].fitness -= 1
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)

                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

        if add_pipe:
            score += 1
            for genome in ge:
                genome.fitness += 5
        if len(pipes) == 0 or pipes[-1].x < 400:  # Adjust this condition to control pipe frequency
            pipes.append(PipeAI(700))



        for r in rem:
            pipes.remove(r)

        for x, bird in enumerate(birds):
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)

        draw_window_ai(win, birds, pipes, base, score, gen, pipe_ind)

def run(config_file):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_file)

    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    winner = p.run(main_ai,50)

    print('\nBest genome:\n{!s}'.format(winner))

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join("FlappyBird", 'configuration.txt')

    while True:
        menu_choice = main_menu()
        if menu_choice == "start":
            while True:
                clock.tick(fps)
                for event in pygame.event.get():
                    if event.type == QUIT:
                        pygame.quit()
                        quit()
                    if (event.type == KEYDOWN and event.key == pygame.K_SPACE) or (pygame.mouse.get_pressed()[0] == 1 and not flying and not gameOver):
                        flying = True
                screen.blit(backgroundImage, (0, 0))
                birdGroup.draw(screen)
                birdGroup.update()
                pipeGroup.draw(screen)
                screen.blit(groundImage, (groundScroll, 668))
                if len(pipeGroup) > 0:
                    if birdGroup.sprites()[0].rect.left > pipeGroup.sprites()[0].rect.left \
                        and birdGroup.sprites()[0].rect.right < pipeGroup.sprites()[0].rect.right \
                        and not passPipe:
                        passPipe = True
                    if passPipe:
                        if birdGroup.sprites()[0].rect.left > pipeGroup.sprites()[0].rect.right:
                            score += 1
                            passPipe = False

                draw_text(str(score), font, white, int(screenWidth / 2), 20)

                if pygame.sprite.groupcollide(birdGroup, pipeGroup, False, False) or flappy.rect.top < 0:
                    gameOver = True

                if flappy.rect.bottom >= 668:
                    gameOver = True
                    flying = False

                if not gameOver and flying:
                    timeNow = pygame.time.get_ticks()
                    if timeNow - lastPipe > pipeFrequency:
                        pipeHeight = random.randint(-100, 100)
                        btmPipe = Pipe(screenWidth, int(screenLength / 2) + pipeHeight, -1)
                        topPipe = Pipe(screenWidth, int(screenLength / 2) + pipeHeight, 1)
                        pipeGroup.add(btmPipe)
                        pipeGroup.add(topPipe)
                        lastPipe = timeNow
                    groundScroll -= scrollSpeed
                    if abs(groundScroll) > 35:
                        groundScroll = 0
                    pipeGroup.update()
                if gameOver:
                    if button.draw():
                        gameOver = False
                        score = resetGame()
                    if backButton.draw():  # Back to main menu button
                        break 
                pygame.display.update()
        elif menu_choice == "ai":
            run(config_path)
        elif menu_choice == "exit":
            pygame.quit()
            quit()
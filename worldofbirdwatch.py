import pygame, sys, csv, asyncio
from random import randint
from pygame.locals import *

### directories
DEFAULT_CONTROLS = [K_UP, K_DOWN, K_LEFT, K_RIGHT, K_SPACE]
IMG_MANAGER = {}
AVIARY = {}
MAX_WINDOW = (1280, 720) #render everything to this, scale up to different resolutions
gamestate = "OVERWORLD"

### READ ME ###
### Birdwatch: build 0.0.1 gimpzillayt & meticulac
### please keep funcitons and classes alphabetized


### main
async def main():
    pygame.init()
    pygame.mixer.init()
    root = pygame.display.set_mode(MAX_WINDOW, pygame.RESIZABLE)
    window_w, window_h = 1280, 720
    clock = pygame.time.Clock()
    global AVIARY
    global gamestate

    #pygame.mixer.music.load("./assets/dsiraqo.wav")
    #pygame.mixer.music.play(-1)

    AVIARY = read_csv("./assets/aviary.csv")
    journal_icon = load_image("./assets/journal_icon.png", True)
    player_journal = Cursor(load_image("./assets/journal.png", True), DEFAULT_CONTROLS, 2, "bookie")
    player_journal.pages.append(load_image("./assets/ctrl.png", False))
    start_journal_images(player_journal)

    player_cursor = Cursor(load_image("./assets/cursor_binos.png", True), DEFAULT_CONTROLS, 10, "tester")
    while True:
        events = pygame.event.get()
        for event in events:
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.VIDEORESIZE:
                window_w, window_h = event.w, event.h
                root = pygame.display.set_mode((window_w, window_h), pygame.RESIZABLE)
        
        ###go to function: send back canvas. print canvas to root in main
        if gamestate == "OVERWORLD":
            canvas = overworld(player_journal, player_cursor, events)
        elif gamestate == "ZOOM":
            canvas = zoom_zone(player_journal, events)##take room num
        
        #journal is accessible in any gamestate
        if player_journal.open == True:
            canvas =  journal(canvas, player_journal, events)
        else:
            player_journal.book_check(events)
        
        canvas.blit(journal_icon, (MAX_WINDOW[0]-250, MAX_WINDOW[1]-250))
        resolution = pygame.transform.scale(canvas, (window_w, window_h))
        root.blit(resolution, (0,0))
        pygame.display.flip()
        ###pygame.display.flip() or .update() : basically same thing
        clock.tick(60)
        await asyncio.sleep(0)

    return


### classes
class Bird:
    def __init__ (self, image_file, x, y):
        self.image = image_file
        self.x = x
        self.y = y
        self.rect = self.image.get_rect(topleft=(self.x, self.y))

class Cursor:
    def __init__(self, image_file, arr_controls, speed, name):
        self.name = name
        self.image = image_file
        self.x = rng(MAX_WINDOW[0])
        self.y = rng(MAX_WINDOW[1])
        self.rect = self.image.get_rect(topleft=(self.x, self.y))
        self.speed = speed
        self.open = False
        self.pages =[]
        self.kup = arr_controls[0]
        self.kdown = arr_controls[1]
        self.kleft = arr_controls[2]
        self.kright = arr_controls[3]
        self.kfire = arr_controls[4]

    def bind_book(self):
        x = (MAX_WINDOW[0]/2-420)
        y = (MAX_WINDOW[1]/2)
        if self.rect.x > x:
            self.rect.x = x
        if self.rect.y < y:
            self.rect.y = y
    
    def book_check(self, events):
        for event in events:
            if event.type == KEYDOWN:
                if event.key == pygame.K_j:
                    self.open = True 


    def draw(self, canvas):
        canvas.blit(self.image, self.rect)

    def click(self, events): #returns T/F if they fired
        for event in events:
            if event.type == KEYDOWN:
                if event.key == self.kfire:
                    return True                                 
        return False     

    def move(self):
        keys = pygame.key.get_pressed()

        if keys[self.kup]: #up
            self.rect.y -= self.speed
        if keys[self.kdown]: #down
            self.rect.y += self.speed
        if keys[self.kleft]: #left
            self.rect.x -= self.speed
        if keys[self.kright]: #right
            self.rect.x += self.speed   
        
        if self.rect.y < 0:#boundry edge
            self.rect.y = 0
        if self.rect.y > MAX_WINDOW[1]:
            self.rect.y = MAX_WINDOW[1]
        if self.rect.x < 0:
            self.rect.x = 0
        if self.rect.x > MAX_WINDOW[0]-100:
            self.rect.x = MAX_WINDOW[0]-100

class Gamestate:
    def __init__(self):
        self.scene = "OVERWORLD"
        self.score = 0

class Widget:
    def __init__(self, image_file, x, y):
        self.image = image_file
        self.x = x
        self.y = y
        self.rect = self.image.get_rect(topleft=(self.x, self.y))
    
    def draw(self, canvas):
        canvas.blit(self.image, self.rect)



### functions
def collision(canvas, mybox : list[Cursor], single_target_rect):
    #checks if you hit specific thing, T/F
    if mybox.rect.colliderect(single_target_rect):
        pygame.draw.rect(canvas,(255,0,0), single_target_rect)
        return True
    return False

def collision_bus(root, mybox : list[Cursor], list_of_rects):
    #checks if you hit something in list, returns what you hit
    for monster in list_of_rects:
        if mybox.rect.colliderect(monster.rect):
            pygame.draw.rect(root,(255,0,0), monster.rect)
            return True
    return False

def load_image(filename, alpha_bool):
    if filename not in IMG_MANAGER:
        if alpha_bool == True:
            IMG_MANAGER[filename] = pygame.image.load(filename).convert_alpha()
        else:
            IMG_MANAGER[filename] = pygame.image.load(filename).convert()
    ### loads and stores images to prevent lag/repeated loads
    return IMG_MANAGER[filename]

def read_csv(filename):
    dictionary = {}
    for row in csv.reader(open(filename)):
        ## kinda makes a temp array with a cubby for every item() seperated by commas (csv)
        ## then uses that temp array to initialize a dict {cool : stuff : dude} and it 
        ## turns the 'stuff' into a list[] so i can pull stuff by saying call["cool"]["stuff"] == dude
        name = row[0].lower()
        found = bool(row[1])
        image = row[2].lower()
        zone = row[3].lower()
        rarity = row[4].lower()
        wingspan = int(row[5])

        dictionary[name] = {"found" : found, "image" : image, "zone" : zone,
                             "rarity" : rarity, "wingspan" : wingspan}
    return dictionary
    ## since dict variables are mutable i can return a full dict and work it over there

def rng(n):
    return randint(0,n)

def start_journal_images(journal : Cursor):
    global AVIARY
    keys = list(AVIARY.keys())
    for key in keys:
        journal.pages.append(load_image(AVIARY[key]["image"], True))

### scenes
def journal(canvas, journal : Cursor, events):

    for event in events:
        if event.type == pygame.KEYDOWN: 
            if event.key == pygame.K_j:
                journal.open = False
                pygame.event.clear(pygame.KEYDOWN)



    journal.bind_book()
    journal.move()
    journal.draw(canvas)
    canvas.blit(journal.pages[3], (journal.rect.x+45, journal.rect.y+45)) ##bird image
    canvas.blit(journal.pages[0], ((journal.rect.x + 300), journal.rect.y+50)) ##Bird Image
    canvas.blit(journal.pages[2], ((journal.rect.x + 345), journal.rect.y +145)) ##Bird Image
    ##idea is loop through pages and display the bird with all the info
    return canvas

def overworld(journal, cursor : Cursor, events):
    canvas = pygame.Surface(MAX_WINDOW)
    global gamestate

    #sound_fx = pygame.mixer.Sound("./assets/bird.ogg")
    #sound_fx.play()

    my_font = pygame.font.SysFont('Arial', 36)
    text_box = my_font.render("Hello World", True, (0, 0, 0))
    menu_rectangle = Widget(text_box, (MAX_WINDOW[0]/2), (MAX_WINDOW[1]/2) )
    
    background = load_image("./assets/background1.png", False)
    #background_layer = load_image("./assets/background2.png", True)
    
    test_tuple = (300, 300, 300, 300)
    test_tuple2 = (42, 42, 42, 42)
    ###generally build a list[] then cycle all the objects
    
    canvas.blit(background, (0,0))
    collision(canvas, cursor, pygame.draw.rect(canvas, (255,180,180), test_tuple))
    collision(canvas, cursor, pygame.draw.rect(canvas, (255,180,180), test_tuple2))
    if cursor.click(events) and collision(canvas, cursor, pygame.draw.rect(canvas, (255,180,180), test_tuple)):
        gamestate = "ZOOM"
    elif cursor.click(events) and collision(canvas, cursor, pygame.draw.rect(canvas, (255,180,180), test_tuple2)):
        gamestate = "ZOOM"
    canvas.blit(text_box, (0, 0)) 
    menu_rectangle.draw(canvas)
        ###various examples of printing rectangles
        ###collision just checks if two rectangles overlap, rectangles can be square images

    cursor.move()
    cursor.draw(canvas)

    return canvas    

def zoom_zone(journal : Cursor, events):
    global gamestate
    canvas = pygame.Surface(MAX_WINDOW)
    canvas.fill((255,180,180))    
    canvas.blit(load_image("./assets/zoom_overlay.png", True), (0,0))

    if journal.click(events) == True:
        gamestate = "OVERWORLD"

    return canvas

### exe
asyncio.run(main())
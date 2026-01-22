import pygame, sys, csv, asyncio
from random import randint
from pygame.locals import *


### directories
DEFAULT_CONTROLS = [K_UP, K_DOWN, K_LEFT, K_RIGHT, K_SPACE]
IMG_MANAGER = {}
AVIARY = {}
MAX_WINDOW = (1280, 720) #render everything to this, scale up to different resolutions (1280, 720)
gamestate = "OVERWORLD"

### READ ME ###
### Birdwatch: build 0.0.2 developer: gimpzillayt; art: pontax; QA/testing: meticulac & newguy
###
### please keep funcitons and classes alphabetized:
### the journal knows all.. if youre looking for a variable its probably attached to journal
### Cursor/journal acts kinda like game_state tracker and im too deep to unravel it all

### in progress: ecosystem manager!!, animatied sprites
### low priority: overlapped sprites(known bug), edge of map + zoom, window scaling, audio crashes 

### main
async def main():
    pygame.init()
    pygame.mixer.init()
    root = pygame.display.set_mode(MAX_WINDOW, pygame.RESIZABLE)
    window_w, window_h = 1280, 720
    clock = pygame.time.Clock()
    
    global AVIARY
    global gamestate

    pygame.mixer.music.load("./assets/dsiraqo.wav")
    pygame.mixer.music.play(-1)

    AVIARY = read_csv("./assets/aviary.csv")
    player_journal = Cursor(load_image("./assets/notebook.png", True), DEFAULT_CONTROLS, 100, "bookie", 40, MAX_WINDOW[1]-100)
    start_journal_pages(player_journal)

    player_cursor = Cursor(load_image("./assets/cursor_binos.png", True), DEFAULT_CONTROLS, 15, "tester", rng(1000), rng(700))
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
            canvas = zoom_zone(player_journal, events)
        
        #journal is accessible in any gamestate
        canvas =  journal(canvas, player_journal, events)
        
        
        
        ##placehodler printing text box example
        #write_textbox("hello world", 650, 350).draw(canvas)
        
        ##
        resolution = pygame.transform.scale(canvas, (window_w, window_h))
        root.blit(resolution, (0,0))
        pygame.display.flip()
        ###pygame.display.flip() or .update() : basically same thing
        clock.tick(60)
        await asyncio.sleep(0)

    return


### classes
class Bird:
    def __init__ (self, name, image_file, x, y):
        global AVIARY
        self.image = image_file
        self.name = name
        self.habitat = AVIARY[name]["zone"]
        self.x = x
        self.y = y
        self.rect = self.image.get_rect(topleft=(self.x, self.y))
        ### maybe build ecosystem here, Bird is used in overworld, 
        ###ecosystem() handles overworld spawn, returns(x,y)
        ###call ecosystem on spawn call Bird to move dependant on
        ### "zone" variable in Aviary[name]["zone"] == "ocean"
        

class Cursor:
    def __init__(self, image_file, arr_controls, speed, name, x, y):
        self.name = name
        self.image = image_file
        self.x = x
        self.y = y
        self.rect = self.image.get_rect(topleft=(self.x, self.y))
        self.speed = speed
        self.open = False
        self.page = 0
        self.list_birds = []
        self.active_bird = self.random_bird()
        self.active_flock = self.start_overworld(rng(5)+1)
        self.zoom_cords = []
        self.habitat = {"wetlands" : (666,666), "ocean" : (700,260), "forest" : (1000,555),
                        "grasslands" : (45,555), "victory lane" : (-420,-69)} 
        self.checklist = {}
        self.win = False
        self.kup = arr_controls[0]
        self.kdown = arr_controls[1]
        self.kleft = arr_controls[2]
        self.kright = arr_controls[3]
        self.kfire = arr_controls[4]

    def bind_book(self):
        x = (MAX_WINDOW[0]/2-520)
        y = (MAX_WINDOW[1]/2)
        if self.rect.x < 100:
            self.rect.x = 170
        if self.rect.x > x:
            self.rect.x = x - 100
        if self.rect.y < y:
            self.rect.y = y
        ##cant simulate the same nudge every time maybe manually animate it
        ##felt good to have wobble in the book
    
    def book_check(self, events):
        for event in events:
            if event.type == KEYDOWN:
                if event.key == pygame.K_j:
                    self.open = True 
    
    def click(self, events): #returns T/F if they fired
        for event in events:
            if event.type == KEYDOWN:
                if event.key == self.kfire or event.key == pygame.K_ESCAPE:
                    return True                                 
        return False 


    def draw(self, canvas):
        canvas.blit(self.image, self.rect)
   

    def ecosystem_shuffle(self):
            #changes the spawn points in journal to randomize spawns
            x = rng(1200)
            y = rng(700)
            print (x//4, y//40)
            self.habitat["wetlands"] = (x//4 + 600, y//4 + 600)
            self.habitat["ocean"] = (x//6 + 500, y//3 + 200)
            self.habitat["grasslands"] = (x//5+25, y//6+400)
            self.habitat["forest"] = (x//4+800, y//4+400)
            return 

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
        if self.rect.y > MAX_WINDOW[1]-100:
            self.rect.y = MAX_WINDOW[1]-100
        if self.rect.x < 0:
            self.rect.x = 0
        if self.rect.x > MAX_WINDOW[0]-100:
            self.rect.x = MAX_WINDOW[0]-100

    def random_bird(self):
        global AVIARY
        arr = list(AVIARY.keys())
        n = rng(len(arr))-1
        self.active_bird = arr[n]
        return arr[n]

    def start_overworld(self, n):
        global AVIARY
        animal_list = []
        for _ in range(n): 
            animal_list.append(self.random_bird())
        self.active_flock = animal_list
        return animal_list

class Widget:
    def __init__(self, image_file, x, y):
        self.image = image_file
        self.x = x
        self.y = y
        self.rect = self.image.get_rect(topleft=(self.x, self.y))
        ###takes any image and makesa rectangle
    def draw(self, canvas):
        canvas.blit(self.image, self.rect)



### functions
def collision(mybox : list[Cursor], single_target_rect):
    #checks if you hit specific thing, T/F
    if mybox.rect.colliderect(single_target_rect):
        return True
    return False

def collision_bus(mybox : list[Cursor], list_of_rects):
    #checks if you hit something in list, returns what you hit
    for monster in list_of_rects:
        if mybox.rect.colliderect(monster.rect):
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
        fact = row[6].lower()

        dictionary[name] = {"found" : found, "image" : image, "zone" : zone,
                             "rarity" : rarity, "wingspan" : wingspan, "fact" : fact}
    return dictionary
    ## since dict variables are mutable i can return a full dict and work it over there

def rng(n):
    return randint(0,n)

def start_journal_pages(journal : Cursor):
    global AVIARY
    keys = list(AVIARY.keys())
    for key in keys:
        journal.list_birds.append(key)
    journal.list_birds.append(journal.list_birds[0])

def sustain_journal_pages(canvas, journal):
    ##can be massively optomized, but.. time
    my_font = pygame.font.SysFont('Arial', 30)
    small_font = pygame.font.SysFont('Arial', 22)
    questionmark = pygame.font.SysFont('Arial', 77)
    
    if journal.win == False:   
        if len(journal.list_birds)-1 == len(list(journal.checklist.keys())):
            AVIARY["thank you"] = {"found" : 0, "image" : "./assets/victory.png", "zone" : "victory lane",
                             "rarity" :  "R", "wingspan" : 42, "fact" : "GimpzillaYT&Pontax"}
            journal.checklist["thank you"] = True
            journal.list_birds.append("thank you")
            journal.win = True
        

    if journal.page == 0:
        text_box = my_font.render(f"[J] ournal :", True, (0,0,0))
        canvas.blit(text_box, (journal.rect.x+115,journal.rect.y+55))

        text_box = my_font.render(f"<-", True, (0,0,0))
        canvas.blit(text_box, (journal.rect.x+80,journal.rect.y+155))

        text_box = my_font.render(f"->", True, (0,0,0))
        canvas.blit(text_box, (journal.rect.x+560,journal.rect.y+155))
        


        image_bd = load_image("./assets/ctrl.png", True)
        image_mugshot = pygame.transform.scale(image_bd, (200, 200))
        canvas.blit(image_mugshot, (journal.rect.x+100, journal.rect.y+100))

    if journal.page > 0:
        if journal.list_birds[journal.page] not in journal.checklist:
            text_box = my_font.render(f"[J] ournal :", True, (0,0,0))
            canvas.blit(text_box, (journal.rect.x+115,journal.rect.y+55))

            text_box = my_font.render(f"<-", True, (0,0,0))
            canvas.blit(text_box, (journal.rect.x+80,journal.rect.y+155))

            text_box = my_font.render(f"->", True, (0,0,0))
            canvas.blit(text_box, (journal.rect.x+560,journal.rect.y+155))

            text_box = questionmark.render(f"?", True, (0,0,0))
            canvas.blit(text_box, (journal.rect.x+150, journal.rect.y+150))

            text_box = my_font.render(f"{journal.list_birds[journal.page]}", True, (0,0,0))
            canvas.blit(text_box, (journal.rect.x+300,journal.rect.y+55))

            text_box = my_font.render(f"habitat: {AVIARY[journal.list_birds[journal.page]]['zone']}", True, (0,0,0))
            canvas.blit(text_box, (journal.rect.x+325,journal.rect.y+125))
        
            text_box = my_font.render(f"wingspan: {AVIARY[journal.list_birds[journal.page]]['wingspan']} in.", True, (0,0,0))
            canvas.blit(text_box, (journal.rect.x+325,journal.rect.y+165))

            return canvas

        text_box = my_font.render(f"[J] ournal :", True, (0,0,0))
        canvas.blit(text_box, (journal.rect.x+115,journal.rect.y+55))

        text_box = my_font.render(f"<-", True, (0,0,0))
        canvas.blit(text_box, (journal.rect.x+80,journal.rect.y+155))

        text_box = my_font.render(f"->", True, (0,0,0))
        canvas.blit(text_box, (journal.rect.x+560,journal.rect.y+155))

        text_box = my_font.render(f"{journal.list_birds[journal.page]}", True, (0,0,0))
        canvas.blit(text_box, (journal.rect.x+300,journal.rect.y+55)) ##name##need css style tips
    
        image_bd = load_image(AVIARY[journal.list_birds[journal.page]]["image"], True)
        image_mugshot = pygame.transform.scale(image_bd, (200, 200))
        canvas.blit(image_mugshot, (journal.rect.x+100, journal.rect.y+75))##image

        text_box = my_font.render(f"habitat: {AVIARY[journal.list_birds[journal.page]]['zone']}", True, (0,0,0))
        canvas.blit(text_box, (journal.rect.x+325,journal.rect.y+125))
        
        text_box = my_font.render(f"wingspan: {AVIARY[journal.list_birds[journal.page]]['wingspan']} in.", True, (0,0,0))
        canvas.blit(text_box, (journal.rect.x+325,journal.rect.y+165))

        text_box = small_font.render(f"pg. {journal.page}", True, (0,0,0))
        canvas.blit(text_box, (journal.rect.x+515,journal.rect.y+275))

        text_box = my_font.render(f"fact: {AVIARY[journal.list_birds[journal.page]]['fact']}", True, (0,0,0))
        canvas.blit(text_box, (journal.rect.x+115,journal.rect.y+265))
        
        
    ##idea is loop through pages and display the bird with all the info
    return canvas

def write_textbox(string, x, y):
    my_font = pygame.font.SysFont('Arial', 99)
    text_box = my_font.render(f"{string}", True, (0, 255, 170))
    return Widget(text_box, x, y)

### scenes
def journal(canvas, journal : Cursor, events):
    global AVIARY
    for event in events:
        if event.type == pygame.KEYDOWN: 
            if event.key == pygame.K_j or event.key == pygame.K_ESCAPE:
                if journal.open == False:
                    journal.open = True
                    journal.rect.y = MAX_WINDOW[1]/2
                elif journal.open == True:   
                    journal.open = False
                    journal.rect.y = MAX_WINDOW[1]-100

    if journal.open == True:
        
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT and journal.page != 0:
                    journal.rect.x = 0
                    journal.page -= 1

                if event.key == pygame.K_RIGHT and journal.page < len(journal.list_birds)-1:
                    journal.page += 1
                    ##append credits later insted of -1
                    
    journal.bind_book()
    journal.draw(canvas)
    return sustain_journal_pages(canvas, journal)


def overworld(journal : Cursor, cursor : Cursor, events):
    canvas = pygame.Surface(MAX_WINDOW)
    global gamestate
    global AVIARY
    

    #sound_fx = pygame.mixer.Sound("./assets/bird.ogg")
    #sound_fx.play()
    
    background = load_image("./assets/background1.png", False)
    #background_layer = load_image("./assets/background2.png", True)
    canvas.blit(background, (0,0))

    #spawn animals outside of this loop, so they can do something in here instead
    #attach to the holy journal
    animal_house = []
    for animal in journal.active_flock:
        if animal == "thank you":
            small_bird = Bird("woodpecker", load_image("./assets/woodpecker.png", True), 20, 400)
            animal_house.append(small_bird)
            continue
        small_scale = pygame.transform.scale((load_image(AVIARY[animal]["image"], True)), (100, 100))
        small_bird = Bird(animal, small_scale, journal.habitat[AVIARY[animal]["zone"]][0],
                          journal.habitat[AVIARY[animal]["zone"]][1]) #eco return(x,y) tuple
        animal_house.append(small_bird)
        
    
    ##check eco system before spawn


    for animal in animal_house:
        canvas.blit(animal.image, (animal.rect.x, animal.rect.y))
        if cursor.click(events) and collision(cursor, animal.rect):
            gamestate = "ZOOM"
            journal.zoom_cords = []
            journal.zoom_cords.append((animal.rect.x-100))
            journal.zoom_cords.append((animal.rect.y-100))
            journal.checklist[animal.name] = True
            journal.active_bird = animal.name

    if journal.open == False: #cant move if journal open
        cursor.move()
    cursor.draw(canvas)
    return canvas    

def zoom_zone(journal : Cursor, events):
    global gamestate
    global AVIARY
    zoom_power = 2
    scaled_w = MAX_WINDOW[0]*zoom_power
    scaled_h = MAX_WINDOW[1]*zoom_power
    target_x = journal.zoom_cords[0]*zoom_power
    target_y = journal.zoom_cords[1]*zoom_power 
    draw_x = MAX_WINDOW[0]/2 - target_x
    draw_y = MAX_WINDOW[1]/2 - target_y
    if draw_x > 0: 
        draw_x = 0
        journal.zoom_cords[0]
    if draw_x < MAX_WINDOW[0] - scaled_w: ##major bag alert
        draw_x = MAX_WINDOW[0] - scaled_w
        journal.zoom_cords[0]
    if draw_y > 0:
        draw_y = 0
    if draw_y < MAX_WINDOW[1] - scaled_h:
        draw_y = MAX_WINDOW[1] - scaled_h 
    
    ##need to make background a widget so players can move it zoomed in
   
    canvas = pygame.Surface(MAX_WINDOW)
    temp_drawing = pygame.Surface(MAX_WINDOW)

    ##create a temp_canvas with all birds then zooms on it
    active = load_image(AVIARY[journal.active_bird]["image"], True)
    active = pygame.transform.scale(active, (300, 300))
    background = load_image("./assets/background1.png", False)
    temp_drawing.blit(background, (0,0))
    temp_drawing.blit(active, (journal.zoom_cords[0], journal.zoom_cords[1] -150))
    
    zoom_background = pygame.transform.scale(temp_drawing, (scaled_w, scaled_h))
    canvas.blit(zoom_background, (draw_x, draw_y))    
    canvas.blit(load_image("./assets/zoom_overlay.png", True), (0,0))

    if journal.click(events) == True:
        gamestate = "OVERWORLD"
        journal.active_flock = journal.start_overworld(rng(5)+1)
        journal.ecosystem_shuffle()
        

    return canvas


### exe
asyncio.run(main())
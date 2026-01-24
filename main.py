import pygame, sys, csv, asyncio
#import js, json
#js imports only work in html after pygbag.. comment out to run local
##comment sections at lines 2, 50, ~600
##online pulls from localstorage() a dict{}, then fills book with past achievements
from random import randint
from pygame.locals import *


### directories
DEFAULT_CONTROLS = [K_UP, K_DOWN, K_LEFT, K_RIGHT, K_SPACE]
IMG_MANAGER = {}
AVIARY = {}
MAX_WINDOW = (1280, 720) #render everything to this, scale up to different resolutions (1280, 720)
gamestate = "OVERWORLD"

### READ ME ###
### Birdwatch: build 0.1.24 developer: gimpzillayt; art: pontax; music: duke siraqo QA/testing: meticulac
###
### 
### the journal knows all.. if youre looking for a variable its probably attached to journal
### Cursor/journal acts kinda like game_state tracker and im too deep to unravel it all

### lock scene until natural respawns.. add player [Y]ell option to scatter all
### birds and get new spawns, yell on cooldown, needs to be alert but not annoying

### in progress: bird sounds on rares, living ecosystem, fastforward/yell
### low priority: edge of map + zoom, page0 text, subsurfaces, journal match active bird
### low prio: window_scaling, bird and nature sounds

### main
async def main():
    pygame.init()
    pygame.mixer.init()
    root = pygame.display.set_mode(MAX_WINDOW, pygame.RESIZABLE)
    pygame.mixer.music.load("./assets/dsiraqo.wav") 
    #load music early, play music last for download time
    window_w, window_h = 1280, 720
    clock = pygame.time.Clock()
    
    global AVIARY
    global gamestate
    AVIARY = read_csv("./assets/aviary.csv")


    player_journal = Cursor(load_image("./assets/notebook.png", True), DEFAULT_CONTROLS, 100, "bookie", 40, MAX_WINDOW[1]-100)
    start_journal_pages(player_journal)

    player_cursor = Cursor(load_image("./assets/cursor_binos.png", True), DEFAULT_CONTROLS, 15, "tester", rng(1000), rng(700))

    ##online use only, comment out if local
    #achievements = online_load_game()
    #for key in achievements:
    #    player_journal.checklist[key] = True
    ########

    
    pygame.mixer.music.play(-1)
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
        canvas =  journal(canvas, player_journal, events, player_cursor)
        
        
        
        ##placehodler printing text box example
        #write_textbox("hello world", 650, 350).draw(canvas)
        
        ##
        resolution = pygame.transform.scale(canvas, (window_w, window_h))
        root.blit(resolution, (0,0))
        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

    return


### classes

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
        self.active_flock = []
        self.active_photo = []
        self.zoom_cords = []
        self.checklist = {}
        self.win = False
        self.last_mouse_movement = pygame.mouse.get_pos()
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
            if event.type == MOUSEBUTTONDOWN:    
                self.rect.center = event.pos
                return True
            elif event.type == KEYDOWN:
                if event.key == self.kfire or event.key == pygame.K_ESCAPE:
                    return True                                     
        return False 
    
    def click_nomove(self, events): #returns T/F if they fired
        for event in events:
            if event.type == MOUSEBUTTONDOWN:    
                return True
            elif event.type == KEYDOWN:
                if event.key == self.kfire or event.key == pygame.K_ESCAPE:
                    return True                                     
        return False 


    def draw(self, canvas):
        canvas.blit(self.image, self.rect)
   
    ##wasd ctrl with boundaries
    def move(self):
        pos_mouse = pygame.mouse.get_pos()
        keys = pygame.key.get_pressed()

        if keys[self.kup]: #up
            self.rect.y -= self.speed
        if keys[self.kdown]: #down
            self.rect.y += self.speed
        if keys[self.kleft]: #left
            self.rect.x -= self.speed
        if keys[self.kright]: #right
            self.rect.x += self.speed   

        if self.last_mouse_movement != pos_mouse:    
            self.rect.center = pos_mouse
            self.last_mouse_movement = pos_mouse
        
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
        
    def build_bird_overworld(self, n):
        ##randoms spawn points and rarity of birds
        #appends Birds so you .remove(Bird) then summon this
        global AVIARY
        for _ in range(n):
            rng_god = rng(100)
            rng_helper = rng(5)+1
            rng_mega = rng_god*rng_helper
            rarity_final = "c"
            zone_final = "ocean"
            x_final = rng_god*rng_helper*2
            y_final = 360
            if rng_mega%4 == 0:
                zone_final = "ocean"
                x_final = MAX_WINDOW[0]
                y_final -= 175+rng_god+rng_helper
            elif rng_mega%4 == 1:
                zone_final = "wetlands"
                x_final = 666
                y_final = 666-rng_helper*2
            elif rng_mega%4 == 2: 
                zone_final = "grasslands"
                x_final = x_final/2-42
            elif rng_mega%4 == 3: 
                zone_final = "forest"
                x_final = 600+rng_god*rng_helper
            
            rng_second = rng(100)
            if rng_second < 75: 
                rarity_final = "c"
                y_final += rng_god    
            elif rng_second < 95: #"uncommon"
                rarity_final = "u"
            else: #"rare"
                rarity_final = "r" 
                y_final += rng_helper*rng_helper

            final_contestants = []
            nerd = 0
            for name, stats in AVIARY.items():    
                if stats["zone"] == zone_final and stats["rarity"] == rarity_final:
                    final_contestants.append(name)
                    nerd += 1
            if nerd == 0:
                for name, stats in AVIARY.items():
                    if stats["zone"] == zone_final:
                        final_contestants.append(name)
                
            
            orc_ruler_master_of_doom = final_contestants[rng(len(final_contestants)-1)]
            small_birdy = pygame.transform.scale((load_image(AVIARY[orc_ruler_master_of_doom]["image"], True)), (100, 100))
            ##makebird and append to flock
            self.active_flock.append(Bird(orc_ruler_master_of_doom, small_birdy, x_final, y_final))
        
        return

class Widget:
    def __init__(self, image_file, x, y):
        self.image = image_file
        self.x = x
        self.y = y
        self.rect = self.image.get_rect(topleft=(self.x, self.y))
        ###takes any image and makesa rectangle
    def draw(self, canvas):
        canvas.blit(self.image, self.rect)


class Bird:
    def __init__ (self, name, image_file, x, y):
        global AVIARY
        self.zoom_cords = []
        self.image = image_file
        self.name = name
        self.habitat = AVIARY[name]["zone"]
        self.bool_direction = rng(1)
        self.frames = 0
        self.x = x
        self.y = y
        self.speed = self.set_speed()
        self.rect = self.image.get_rect(center=(self.x, self.y))
        if self.bool_direction < 1: #bool 1 == right-to-left, 0 == left-to-right
            self.image = pygame.transform.flip(self.image, True, False)
            if self.habitat == "ocean":
                self.rect.x = 0
            if self.habitat == "wetlands":
                self.rect.x = MAX_WINDOW[1] #this was a typo but also kinda what i want
        ### movement will attach here. but list[] of Bird store in journal
        ### move object here and keep cords stationary through book
        
        
    def move(self, journal : Cursor): 
        self.frames += 1
        if self.habitat == "ocean":
            if self.bool_direction == 0:
                self.rect.x += self.speed
                if self.rect.x > MAX_WINDOW[0]:
                    journal.active_flock.remove(self) 
            else:        
                self.rect.x -= self.speed  ##right to left
                if self.rect.x < -80:
                    journal.active_flock.remove(self)
               
        if self.habitat == "wetlands":
            if self.rect.x > MAX_WINDOW[0]:
                    journal.active_flock.remove(self)     
            if self.bool_direction == 1:
                self.rect.x -= self.speed  ##right to left 
                if self.rect.x <= 450:
                    self.image = pygame.transform.flip(self.image, True, False)
                    self.bool_direction = 0  
            elif self.bool_direction == 0:
                self.rect.x += self.speed        
                if self.rect.x > 800:
                    self.image = pygame.transform.flip(self.image, True, False)
                    self.bool_direction = 1

            if self.frames > 666: #the number of the duck ;)
                self.speed = 1
                if self.bool_direction == 1:
                    self.image = pygame.transform.flip(self.image, True, False)
                    self.bool_direction = 0
                self.rect.x += self.speed  ##left to right
                

        if self.habitat == "grasslands":    
            ##stand still for n frames, goes off screen
            if self.rect.x < -80 or self.rect.x > MAX_WINDOW[0]:
                    journal.active_flock.remove(self)
            if self.frames > 400:
                if self.rect.x < MAX_WINDOW[0]/2:
                    if self.bool_direction == 0:
                        self.bool_direction = 1
                        self.image = pygame.transform.flip(self.image, True, False)    
                    self.rect.x -= self.speed
                elif self.rect.x >= MAX_WINDOW[0]/2:
                    if self.bool_direction == 1:
                        self.bool_direction = 0
                        self.image = pygame.transform.flip(self.image, True, False)    
                    self.rect.x += self.speed
                
        if self.habitat == "forest":    
            if self.rect.x < -80 or self.rect.x > MAX_WINDOW[0]:
                    journal.active_flock.remove(self)
            if self.frames > 550:  
                if self.rect.x < MAX_WINDOW[0]/2:
                    if self.bool_direction == 0:
                        self.bool_direction = 1
                        self.image = pygame.transform.flip(self.image, True, False)    
                    self.rect.x -= self.speed
                elif self.rect.x >= MAX_WINDOW[0]/2:
                    if self.bool_direction == 1:
                        self.bool_direction = 0
                        self.image = pygame.transform.flip(self.image, True, False)    
                    self.rect.x += self.speed
                
                   
    def set_speed(self):
        rng_god = rng(100)
        if self.habitat == "ocean":
            return rng_god%10+1
        if self.habitat == "wetlands":
            return rng_god%3
        if self.habitat == "grasslands":
            return rng_god%4+7
        if self.habitat == "forest":
            return rng_god%4+5

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

def online_load_game():
    saved_str = js.window.localStorage.getItem("my_personal_bird_dict")
    
    if saved_str is None:
        # First time playing! Create default data
        return  {}
    return json.loads(saved_str)

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


    #literally all the printing to journal pages
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

        #image_bd = load_image("./assets/ctrl.png", True)
        #image_mugshot = pygame.transform.scale(image_bd, (200, 200))
        #canvas.blit(image_mugshot, (journal.rect.x+100, journal.rect.y+100))

        write_textbox("enjoy the wonderful world of birdwatching. there is", journal.rect.x+90, journal.rect.y+100).draw(canvas)
        write_textbox("no hurry, no one is watching you. play at your own", journal.rect.x+90, journal.rect.y+133).draw(canvas)
        write_textbox("pace, your progress and discoveries will be saved", journal.rect.x+90, journal.rect.y+166).draw(canvas)
        write_textbox("in this journal; <and your device>", journal.rect.x+90, journal.rect.y+200).draw(canvas)
        write_textbox("-prof. gamezilla", journal.rect.x+400, journal.rect.y+250).draw(canvas)

    if journal.page > 0:
        if journal.list_birds[journal.page] not in journal.checklist:
            text_box = my_font.render(f"[J] ournal :", True, (0,0,0))
            canvas.blit(text_box, (journal.rect.x+115,journal.rect.y+55))

            text_box = questionmark.render(f"?", True, (0,0,0))
            canvas.blit(text_box, (journal.rect.x+150, journal.rect.y+150))

            text_box = my_font.render(f"{journal.list_birds[journal.page]}", True, (0,0,0))
            canvas.blit(text_box, (journal.rect.x+300,journal.rect.y+55))

            text_box = my_font.render(f"habitat: {AVIARY[journal.list_birds[journal.page]]['zone']}", True, (0,0,0))
            canvas.blit(text_box, (journal.rect.x+325,journal.rect.y+125))
        
            text_box = my_font.render(f"wingspan: {AVIARY[journal.list_birds[journal.page]]['wingspan']} in.", True, (0,0,0))
            canvas.blit(text_box, (journal.rect.x+325,journal.rect.y+165))

            text_box = small_font.render(f"pg. {journal.page}", True, (0,0,0))
            canvas.blit(text_box, (journal.rect.x+515,journal.rect.y+275))

            return canvas

        text_box = my_font.render(f"[J] ournal :", True, (0,0,0))
        canvas.blit(text_box, (journal.rect.x+115,journal.rect.y+55))

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
    my_font = pygame.font.SysFont('Arial', 21)
    text_box = my_font.render(f"{string}", True, (0, 0, 0))
    return Widget(text_box, x, y)

### scenes
def journal(canvas, journal : Cursor, events, cursor : Cursor):
    global AVIARY
    my_font = pygame.font.SysFont('Arial', 26)
    journal.draw(canvas) ## drawing reguardless

    for event in events:
        if event.type == pygame.KEYDOWN: 
            if event.key == pygame.K_j:
                if journal.open == False:
                    journal.open = True
                    journal.rect.y = MAX_WINDOW[1]/2
                elif journal.open == True:   
                    journal.open = False
                    journal.rect.y = MAX_WINDOW[1]-100
            if event.key == pygame.K_x or event.key == pygame.K_ESCAPE: 
                if journal.open == True:   
                    journal.open = False
                    journal.rect.y = MAX_WINDOW[1]-100

    if journal.open == True:
        
        left_arrow = Widget(my_font.render(f"<-", True, (0,0,0)), journal.rect.x+80,journal.rect.y+220)
        right_arrow = Widget(my_font.render(f"->", True, (0,0,0)), journal.rect.x+560,journal.rect.y+220)
        exit_pane = Widget(my_font.render(f"[X]", True, (0,0,0)), journal.rect.x+560,journal.rect.y+50)
        exit_pane.draw(canvas)
        left_arrow.draw(canvas)
        right_arrow.draw(canvas)
        
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                cursor.rect.center = pygame.mouse.get_pos()
                if collision(cursor, left_arrow.rect) and journal.page != 0:
                    journal.page -= 1

                if collision(cursor, right_arrow.rect) and journal.page < len(journal.list_birds)-1:
                    journal.page += 1
                
                if collision(cursor, exit_pane.rect):
                    journal.open = False
                    journal.rect.y = MAX_WINDOW[1]-100

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT and journal.page != 0:                    
                    journal.page -= 1

                if event.key == pygame.K_RIGHT and journal.page < len(journal.list_birds)-1:
                    journal.page += 1

                if event.key == pygame.K_DOWN:
                    journal.page = 0     

    open_click_box_thing = Widget(my_font.render(f"[J]                                              ",
                                                  True, (0,0,0)), journal.rect.x+115,journal.rect.y+55)
    if journal.open == False:
        for event in events:
            if event.type == MOUSEBUTTONDOWN:
                if (collision(cursor, open_click_box_thing)):
                    journal.open = True
                    journal.rect.y = MAX_WINDOW[1]/2    
                    
    journal.bind_book()
    return sustain_journal_pages(canvas, journal)


def overworld(journal : Cursor, cursor : Cursor, events):
    canvas = pygame.Surface(MAX_WINDOW)
    global gamestate
    global AVIARY
    
    
    if len(journal.active_flock) < 3:
        journal.build_bird_overworld(rng(4)+1)
    #sound_fx = pygame.mixer.Sound("./assets/bird.ogg")
    #sound_fx.play()
    
    background = load_image("./assets/background1.png", False)
    #background_layer = load_image("./assets/background2.png", True)
    canvas.blit(background, (0,0))

    #spawn animals outside of this loop, so they can do something in here instead
    #attach to the holy journal

    for animal in journal.active_flock:
        animal.move(journal)
        canvas.blit(animal.image, (animal.rect.x, animal.rect.y))
        if cursor.click(events) and collision(cursor, animal.rect) and journal.open == False:
            gamestate = "ZOOM"
            journal.zoom_cords = []
            animal.zoom_cords.append((animal.rect.x))
            animal.zoom_cords.append((animal.rect.y))
            journal.zoom_cords.append((animal.rect.x))
            journal.zoom_cords.append((animal.rect.y))
            journal.checklist[animal.name] = True
            journal.active_bird = animal.name
            journal.active_photo.append(animal)

            ##online use only, comment out if local
                #Saves progress to the browser immediately
            #js.window.localStorage.setItem("my_personal_bird_dict", json.dumps(journal.checklist))
            ########

    if journal.open == False: #cant move if journal open
        cursor.move()
    cursor.draw(canvas)
    return canvas    

def zoom_zone(journal : Cursor, events):
    global gamestate
    global AVIARY

    if journal.click_nomove(events) == True and journal.open == False:
            gamestate = "OVERWORLD"
            for animal in journal.active_photo:
                for active in journal.active_flock:
                    if animal.name == active.name:
                        journal.active_flock.remove(active)
            journal.active_photo = [] 

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
    if draw_x < MAX_WINDOW[0] - scaled_w: 
        draw_x = MAX_WINDOW[0] - scaled_w
        journal.zoom_cords[0]
    if draw_y > 0:
        draw_y = 0
    if draw_y < MAX_WINDOW[1] - scaled_h:
        draw_y = MAX_WINDOW[1] - scaled_h 
    
    ##need to make background a widget so players can move it zoomed in
   
    canvas = pygame.Surface(MAX_WINDOW)
    temp_drawing = pygame.Surface(MAX_WINDOW)

    background = load_image("./assets/background1.png", False)
    temp_drawing.blit(background, (0,0))
    for animal in journal.active_photo:
        active = load_image(AVIARY[animal.name]["image"], True)
        active = pygame.transform.scale(active, (300, 300))
        temp_drawing.blit(active, (animal.zoom_cords[0], animal.zoom_cords[1]-100))    
    ##create a temp_canvas with all birds then zooms on it
    
    zoom_background = pygame.transform.scale(temp_drawing, (scaled_w, scaled_h))
    canvas.blit(zoom_background, (draw_x, draw_y))    
    canvas.blit(load_image("./assets/zoom_overlay.png", True), (0,0)) 
                
    return canvas


### exe
asyncio.run(main())

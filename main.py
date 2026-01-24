import pygame, sys, csv
from random import randint
from pygame.locals import *
pygame.init()


###### directories
DEFAULT_CONTROLS = [K_UP, K_DOWN, K_LEFT, K_RIGHT, K_SPACE]
DEFAULT_P2 = [K_w, K_s, K_a, K_d, K_TAB]
MAX_WINDOW = (1280, 720) #images are blit onto a canvas, then blit to root
window_w, window_h = 1280, 720
IMG_MANAGER = {}


### ITS DUCK HUNT! EXCEPT UNLIMITED PLAYERS ON ONE KEYBOARD! ###

### Features im working on adding; user_input_controls, double_kill(), load screen 
### Dream List; Gun Classes, Upgrade/Debuff Crosshairs, more art
### doneDone; window_RESIZABLE, localized images, persistent high score
### doneDone; reloading, audio, 

##### main
def main():
    MY_ICON = pygame.image.load("./assets/myicon.png")
    pygame.display.set_icon(MY_ICON)
    pygame.display.set_caption("Ribeye of the Sky")
    root = pygame.display.set_mode(MAX_WINDOW, pygame.RESIZABLE)

    main_menu(root, load_image("./assets/controls.png", True))
    return


##### classes
class Crosshair:
    def __init__(self, image_file, x, y, speed, magsize, arr_controls, name):
        global MAX_WINDOW
        self.special = 0
        self.reloadspeed = 120
        self.reloadmag = False
        self.name = name
        self.image = image_file 
        self.rect = self.image.get_rect(topleft=(x, y))
        self.score = 0
        self.speed = speed
        self.img_ammo = load_image("./assets/ammo.png", True)
        self.ammo = magsize
        self.magsize = magsize
        self.kup = arr_controls[0]
        self.kdown = arr_controls[1]
        self.kleft = arr_controls[2]
        self.kright = arr_controls[3]
        self.kfire = arr_controls[4]

    def draw(self, root):
        root.blit(self.image, self.rect)
        
    def draw_ammo(self, root, x, y):
        blank = self.magsize - self.ammo  
        for bullet in range(self.ammo): 
            root.blit(self.img_ammo, (x, y))
            x += 40
        for _ in range(blank):
            x += 40
        return x  

    def fire(self, events): #returns T/F if they fired
        for event in events:
            if event.type == KEYDOWN and event.key == self.kfire:
                print(self.rect)
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
        if self.rect.x > MAX_WINDOW[0]-40:
            self.rect.x = MAX_WINDOW[0]-40
        


class Monster: 
    def __init__(self, img_file):
        self.image = img_file
        self.bool_direction = rng(1)
        self.x = MAX_WINDOW[0]
        self.y = rng(MAX_WINDOW[1])
        self.speed = randint(1,6)
        self.rect = self.image.get_rect(topleft=(self.x, self.y))
        if self.bool_direction < 1: #right-to-left
            self.x = 0
            self.image = pygame.transform.flip(self.image, True, False)
        

    def death(self):
        score = self.speed
        self.x = MAX_WINDOW[0]
        self.y = rng(MAX_WINDOW[1])
        self.speed = randint(1,5)
        self.rect = self.image.get_rect(topleft=(self.x, self.y))
        return score

    def draw(self, root):
        root.blit(self.image, self.rect)    

    def move(self): 
        if self.bool_direction > 0: 
            self.rect.x -= self.speed
            if self.rect.x < -80:
                self.speed = randint(1,5)
                self.rect.x = MAX_WINDOW[0]
                self.rect.y = rng(MAX_WINDOW[1])
        else:
            self.rect.x += self.speed
            if self.rect.x > MAX_WINDOW[0]:
                self.speed = randint(1,5)
                self.rect.x = -80
                self.rect.y = rng(MAX_WINDOW[1])
            
    

class Window:
    def __init__(self, img_file, x, y): #builds rect for collide with any image
        self.frames = 0
        self.x = x
        self.y = y
        self.image = img_file
        self.rect = self.image.get_rect(topleft=(x,y))
        self.score = 0

    
    def death(self):
        return -1

    def draw(self, root):
        root.blit(self.image, self.rect)

###### functions

def bus_monster(root, arr : list[Monster]):
    for monster in arr:
        monster.move()
        monster.draw(root)

def bus_player(root, arr : list[Crosshair]):
    x = 0
    for player in arr:
        player.move()
        player.draw(root)
        x = player.draw_ammo(root, x, 50)
        x += 120

#want to add collision detect for single objects, not just lists
def collision_bus(root, mybox : list[Crosshair], boxtarget : list[Monster], bool_blood):
    #checks if you hit something, if you did returns a number, if not 0
    gun_sfx = pygame.mixer.Sound("./assets/doublekill.mp3")
    score = 0
    double_kill = 0
    for monster in boxtarget:
        if mybox.rect.colliderect(monster.rect):
            double_kill += 1
            if bool_blood == True:
                pygame.draw.rect(root,(255,0,0), monster.rect)
            score += monster.death()
    if double_kill > 1:
        score = score*double_kill
        gun_sfx.play()
    return score*10

def highscore_did_i_break_it(time_var, name): #add player input dont need name
    highscores = read_csv("./assets/score.csv")
    if time_var < highscores[5]["time"]:
        score_maker = name #playerinput()
        for score in highscores.values(): #.values() looks in the dict, just dict looks at only keys
            if score["time"] > time_var:
                i = score["time"]
                n = score["name"]
                score["time"] = time_var
                score["name"] = score_maker
                time_var = i
                score_maker = n
        rewrite_csv("./assets/score.csv", highscores) 

def highscore_draw(root, filename, x, y):
    highscores = read_csv(filename)
    my_font = pygame.font.SysFont('Arial', 22)
    header = my_font.render("Highscores:", True, (255, 255, 255))
    root.blit(header, (x, y))
    
    for i in range(len(highscores)):
        y += 30
        text_content = f"{highscores[i+1]['name']} : {highscores[i+1]['time']} seconds"
        text_box = my_font.render(text_content, True, (255,255,255))
        root.blit(text_box, (x, y))
    return

def load_image(filename, alpha_bool):
    if filename not in IMG_MANAGER:
        if alpha_bool == True:
            IMG_MANAGER[filename] = pygame.image.load(filename).convert_alpha()
        else:
            IMG_MANAGER[filename] = pygame.image.load(filename).convert()

    return IMG_MANAGER[filename]

def load_monster(n, img_file): #returns filled list with n monsters
    monster_pool = []
    for _ in range(n):
        frankenstien = Monster(img_file)
        monster_pool.append(frankenstien)
    return monster_pool
    
def options(events, root):
    for event in events:
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.VIDEORESIZE:
            window_w, window_h = event.w, event.h
            root = pygame.display.set_mode((window_w, window_h), pygame.RESIZABLE)
    return root

def read_csv(filename):
    dictionary = {}
    for row in csv.reader(open(filename)):
        ## kinda makes a temp array with a cubby for every item() seperated by commas (csv)
        ## then uses that temp array to initialize a dict {cool : stuff} and it 
        ## turns the 'stuff' into a list[] so i can pull stuff by saying call[cool]["stuff"]
        key = int(row[0])
        title = row[1]
        duration = int(row[2])
        dictionary[key] = {"name" : title, "time" : duration}
    ## returns a mutable dictionary {n : ["name", "time"]}
    return dictionary

def rewrite_csv(file_scores, update):
    with open(file_scores, 'w', newline='') as file:
        to_text = csv.writer(file)
        for key, data in update.items():
            to_text.writerow([key, data["name"], data["time"]])
    return 0

def rng(n):
    return randint(0, n)

def scale_up(root): #TBD
    return

#### gameplay
def main_menu(root, advertisement):
    pygame.mixer.music.load("./assets/dsiraqo.wav")
    pygame.mixer.music.play(-1)
    gun_sfx = pygame.mixer.Sound("./assets/shotgun.mp3")
    my_font = pygame.font.SysFont('Arial', 12)

    clock = pygame.time.Clock()
    canvas = pygame.Surface(MAX_WINDOW)
    print(read_csv("./assets/score.csv")) ##
    global window_h
    global window_w
    
    monster_pool = load_monster(rng(5), load_image("./assets/bird.png", True))
    background = load_image("./assets/background1.png", False)
    background_layer = load_image("./assets/background2.png", True)
    player = Crosshair(load_image("./assets/crosshair1.png", True),
                        rng(700), rng(600), 7, -1, DEFAULT_CONTROLS, "Player 1")
    
    
    menu_img = (load_image("./assets/menu.png", True))
    menu_rect = Window(menu_img, MAX_WINDOW[0]/2 - (menu_img.get_width())/2, (menu_img.get_height())+100)
    menu2_rect = Window(advertisement, (MAX_WINDOW[0]/2 - (advertisement.get_width())/2), (MAX_WINDOW[1]-advertisement.get_height()*2.5))
    menu_pool = [menu_rect]
    build_info = my_font.render("Build 0.0.1: gimpzillaYT: music by DukeSiraqo.", True, (255, 255, 255))
    
    
    while True:
        canvas.blit(background, (0,0))
        canvas.blit(build_info, (0, 0))
        bus_monster(canvas, monster_pool)
        canvas.blit(background_layer, (0,0))
        menu2_rect.draw(canvas)
        for menu in menu_pool:
            menu.draw(canvas) ##add animation loop to Window Class
        highscore_draw(canvas, "./assets/score.csv", (MAX_WINDOW[0]/2-100), 20)
        player.move()
        events = pygame.event.get()
        ###options
        for event in events:
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.VIDEORESIZE:
                window_w, window_h = event.w, event.h
                root = pygame.display.set_mode((window_w, window_h), pygame.RESIZABLE)
        ###more optimal to keep here, only update root if window changes
        if player.fire(events) == True:
            gun_sfx.play()
            if collision_bus(canvas, player, menu_pool, False) < 0:
                new_game(root, DEFAULT_CONTROLS, DEFAULT_P2)
            collision_bus(canvas, player, monster_pool, True)
        player.draw(canvas)

        resolution = pygame.transform.scale(canvas, (window_w, window_h))
        root.blit(resolution, (0,0))
        pygame.display.flip()
        clock.tick(60)

def new_game(root, p1_controls, p2_controls):
    time_var: int = 0
    clock = pygame.time.Clock()
    canvas = pygame.Surface(MAX_WINDOW)
    gun_sfx = pygame.mixer.Sound("./assets/shotgun.mp3")
    global window_w
    global window_h

    my_font = pygame.font.SysFont('Arial', 30)
    background = load_image("./assets/background1.png", False)
    background_layer = load_image("./assets/background2.png", True)

    img_reload = load_image("./assets/reload.png", True)
    img_tree = pygame.transform.scale(load_image("./assets/tree.png", True), (260, 470))
    trees = [Window(img_tree, 65, 244), Window(img_tree, 1020, 380)]
    img_tree = load_image("./assets/tree.png", True)
    monster_pool = load_monster(randint(14,34), load_image("./assets/bird.png", True))
    
    p1 = Crosshair(load_image("./assets/crosshair1.png", True),
                        rng(MAX_WINDOW[0]), rng(MAX_WINDOW[1]), 10, 4, p1_controls, "Player 1")
    p2 = Crosshair(load_image("./assets/crosshair.png", True),
                        rng(MAX_WINDOW[0]), rng(MAX_WINDOW[1]), 10, 4, p2_controls, "Player 2")
    team = [p1, p2]

    while True:
        time_var += 1
        text_box = my_font.render(f"{p1.name, p1.score} Vs. {p2.name, p2.score}", True, (255, 219, 88))
        canvas.blit(background, (0,0))
        canvas.blit(text_box, (50,0)) ##need css style tips
        bus_monster(canvas, monster_pool)
        canvas.blit(background_layer, (0,0))

        if p1.score >= 1000 or p2.score >= 1000:
            break

        events = pygame.event.get()
        bus_player(canvas, team)
        ##keeping collision seperate from player bus for now
        for p in team:
            if p.special > 0:
                p.special -= 1
                canvas.blit(img_tree, (p.rect.x, (p.rect.y)-100))
            if p.reloadmag == True:
                p.reloadspeed -= 1
                canvas.blit(img_reload, ((p.rect.x-100), (p.rect.y-100)))
                if p.reloadspeed == 0:
                    p.ammo = p.magsize ##need to make a gun class that fills
                    p.reloadspeed = 120 ##p.mag p.reload etc etc
                    p.reloadmag = False
                continue #if reloading skip everything in _p for loop

            if p.ammo == 0:
                p.reloadmag = True
            elif p.fire(events) == True:
                p.ammo -= 1
                gun_sfx.play()
                if collision_bus(canvas, p, trees, False) == 0:
                    p.score += collision_bus(canvas, p, monster_pool, True)
                else:
                    if rng(2) == 0:
                        p.special = 24
                    else: 
                        p.score += collision_bus(canvas, p, monster_pool, True)
        
        ###options
        for event in events:
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.VIDEORESIZE:
                window_w, window_h = event.w, event.h
                root = pygame.display.set_mode((window_w, window_h), pygame.RESIZABLE)
        ###more optimal to keep here, only update root if window changes
        
        resolution = pygame.transform.scale(canvas, (window_w, window_h))
        root.blit(resolution, (0,0))
        pygame.display.flip()
        clock.tick(60)

    time_var = round(time_var/60)
    text_box = my_font.render(f"{p1.name, p1.score} Vs. {p2.name, p2.score} Time: {round(time_var)} seconds", True, (255, 219, 88))
    root.blit(text_box, ((MAX_WINDOW[0]/2), 500))
    highscore_did_i_break_it(time_var, p1.name) #needs to be player input 
    
    main_menu(root, text_box)

###### exe
main()

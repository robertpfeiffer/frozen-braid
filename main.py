import pygame
import copy
import random
import webbrowser
import pickle
import glob
import datetime
import json

pygame.init()
playername=None

zoom=1
fullscreen=False
for x,y in pygame.display.list_modes():
    while 640*(zoom+1)<x and 480*(zoom+1)<y:
        zoom+=1

screen_mode=(640*zoom,480*zoom)
if fullscreen:
    screen = pygame.display.set_mode(screen_mode,pygame.DOUBLEBUF|pygame.FULLSCREEN)
else:
    screen = pygame.display.set_mode(screen_mode,pygame.DOUBLEBUF)

screen_real=screen

if zoom>1:
    screen=pygame.Surface((640,480)).convert()

jump=pygame.mixer.Sound("jump.wav")
pew=pygame.mixer.Sound("pew.wav")
bang=pygame.mixer.Sound("bang.wav")
boom=pygame.mixer.Sound("boom.wav")
hurt=pygame.mixer.Sound("hurt.wav")

pygame.mixer.music.load(random.choice(glob.glob("*ogg")))
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1, 0.0)

clock = pygame.time.Clock() # create clock object

def intro(filename):
    logo=pygame.transform.scale(pygame.image.load(filename).convert_alpha(),screen_mode)
    screen_real.blit(logo, (0,0))
    pygame.display.flip()

    for i in range(3*30):
        clock.tick(30)
        pygame.event.pump()
        keys = pygame.key.get_pressed()
        mouse = pygame.mouse.get_pressed()
        if keys[pygame.K_SPACE] or mouse[0]:
            break
        screen_real.blit(logo, (0,0))
        pygame.display.flip()

intro("logo.png")

font0=pygame.font.Font("Orbitron Medium.ttf", 18)
fonth=pygame.font.Font("Ubuntu-R.ttf", 18*zoom)
font=pygame.font.Font("orbitron-black.ttf", 36)
font_win=pygame.font.Font("Ostrich Black.ttf", 150)

FPS=30
SECONDS=10

spritesheets=[pygame.image.load("red.png").convert_alpha(),pygame.image.load("green.png").convert_alpha()]

player_colors=[(180,0,0),(0,180,0),(255,255,255)]

class Unit(object):
    def __init__(self,x,y,player_idx,weapon="machinegun"):
        self.look=1
        self.pos=x,y
        self.downspeed=0
        self.radius=10
        self.resting=False
        self.move_speed=2
        self.health=100
        self.weapon=weapon
        self.player=player_idx
        self.spritesheet=spritesheets[self.player]
        self.anim="idle"
        self.color=player_colors[self.player]
        self.rockets=0
        if weapon=="rockets":
            self.rockets=3

class Bullet(object):
    def __init__(self,x,y,speed,life):
        self.pos=x,y
        self.speed=speed
        self.life=life
        self.dead=False

    def fly(self):
        x,y=self.pos
        dx,dy=self.speed
        self.pos=x+dx,y+dy
        self.life-=1

class Rocket(Bullet):
    pass

help_text=["The battle will last TEN SECONDS",
           "Take as long as you want to plan",
           "You can move enemy units to test your strategy",
           " ",
           "[SHIFT] rewinds time, [SHIFT]+[S] rewinds faster",
           "[SPACE] stops time",
           " ",
           "Only when time is up",
           " [N]/[M] selects next/prev unit",
           " [RETURN] ends your move (give PC to other player)",
           " ",
           "[W][A][S][D] move units",
           "[X] or [E] or clicking shoots",
           "Units have a machine gun, a shotgun or rockets",
           "Rocket Guy aims with the mouse, but has only 3 shots",
           " ",
           "1. Red makes his move while green looks away",
           "2. Green makes his move while red has a total poker face",
           "3. Both strategies are played against each other",
           "4. The player with more units after TEN SECONDS wins",
           " ",
           " ",
           "A typical Move goes like this",
           " - Control a unit until 10 seconds are over",
           " - Press N or M to select another unit",
           " - Rewind time to start",
           " - Repeat for all friendly and enemy units",
           " - Revise your strategy and repeat the above",
           " - Play until time is up",
           " - Press Return to submit your move",]

hud_help=[fonth.render(a,1,(200,200,200,200)) for a in
          help_text]

hud_grey=screen.copy().convert_alpha()
hud_grey.fill((50,50,50,190))
hud_hint=fonth.render("press [H] for help and [SHIFT] to rewind or [ESC] to leave",1,(200,200,200,150))
hud_hint2=fonth.render("press [RETURN] to confirm your move when you are ready",1,(200,200,200,150))
hud_hint3=fonth.render("hold [SHIFT][LEFT] fast rewind - [SHIFT][RIGHT] replay",1,(200,200,200,150))
hud_hint4=fonth.render("move with [W][A][S][D] - shoot with [X] or mouse",1,(200,200,200,150))
hud_hint5=fonth.render("select other unit [N]/[M]",1,(200,200,200,150))

write_replay=True
hints=True

def create_map():
    obstacles=[pygame.Rect(310, 50, 20, 100),pygame.Rect(0, 0, 20, 480),pygame.Rect(620, 0, 20, 480),pygame.Rect(0, 460, 640, 20)]	

    for i in range(6):
        for j in range(6):
            obstacles.append(pygame.Rect(i*100+random.randint(0,100), 100+j*60+random.randint(0,80), 40, 10))
    return obstacles

def write_replay_file(committed,obstacles,name=None):
    if name:
        ts=name
    else:
        ts=datetime.datetime.now().isoformat()[:19].replace(":","_")
    with open(ts+".replay.json",'w') as dumpfile:
        dumpfile.write(json.dumps((committed,[(o.topleft,o.size) for o in obstacles])))

def write_map_file(obstacles,name):
    with open(name+".map.json",'w') as dumpfile:
        dumpfile.write(json.dumps([(o.topleft,o.size) for o in obstacles]))

def write_move_file(committed,mapname,playername,color):
    with open(".".join([mapname,playername,color,"move","json"]),'w') as dumpfile:
        dumpfile.write(json.dumps(dict(committed=committed,
                                       name=playername,
                                       color=color)))

def strip_ext(fname,ext):
    return fname[:fname.rfind(ext)]

def get_map_names():
    maps=glob.glob("*.map.json")
    maps.sort()
    return [strip_ext(m,".map.json") for m in maps]

def map_is_played(mapname):
    return (glob.glob(mapname+"*.red.move.json")
            and glob.glob(mapname+"*.green.move.json"))

def map_get_moves(mapname):
    red_moves=glob.glob(mapname+"*.red.move.json")
    red_moves.sort()
    green_moves=glob.glob(mapname+"*.green.move.json")
    green_moves.sort()
    return red_moves,green_moves

def rungame(replay=None, online=False, map=None, player_index=0, replay_filename=None):
    
    #CREATE STUFF
    current_unit=0
    time=0
    maxtime=0

    obstacles=create_map()
    units=[Unit(100,100,0),Unit(110,100,0,"shotgun"),Unit(120,100,0,"rockets"),
          Unit(540,100,1),Unit(530,100,1,"shotgun"),Unit(520,100,1,"rockets")]
    bullets=[]

    state_log = [None for t in range(FPS*SECONDS)]
    event_log = [[[] for u in units] for t in range(FPS*SECONDS)]
    committed=[[[] for u in units] for t in range(FPS*SECONDS)]
    explosions=[]

    gameloop=True
    in_replay=False

    stop_state=False

    if online:
        obstacles=map
        if player_index==1:
            current_unit=3
    if replay:
        committed,obstacles=replay
        event_log=committed
        player_index=2
        in_replay=True

    while gameloop:
        clock.tick(FPS)
        events = pygame.event.get()
        keys = pygame.key.get_pressed()

        for event in events:
            if event.type == pygame.QUIT:
                raise QuitClicked()
            elif event.type == pygame.KEYDOWN and event.key==pygame.K_ESCAPE:
                return
            elif event.type == pygame.KEYDOWN and event.key==pygame.K_SPACE:
                stop_state=not stop_state

        screen.fill((10,10,50))
        direction=""

        if (stop_state and not (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])):
            direction="||"
        elif not (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and time==FPS*SECONDS:
            direction="||"
            stop_state=False
            for event in events:
                if event.type == pygame.KEYDOWN and event.key==pygame.K_n:
                    current_unit=(current_unit+1)%len(units)
                if event.type == pygame.KEYDOWN and event.key==pygame.K_m:
                    current_unit=(current_unit-1)%len(units)
                elif event.type == pygame.KEYDOWN and event.key==pygame.K_RETURN and online and player_index<2:
                    for unit_idx in range(len(units)):
                        unit=units[unit_idx]
                        for t in range(FPS*SECONDS):
                            if unit.color==player_colors[player_index]:
                                committed[t][unit_idx]=event_log[t][unit_idx]
                    return committed
                elif event.type == pygame.KEYDOWN and event.key==pygame.K_RETURN and player_index<2:
                    #commit current player's move
                    for unit_idx in range(len(units)):
                        unit=units[unit_idx]
                        for t in range(FPS*SECONDS):
                            if unit.color==player_colors[player_index]:
                                committed[t][unit_idx]=event_log[t][unit_idx]
                    current_unit=0
                    units,bullets=state_log[0]
                    state_log = [None for t in range(FPS*SECONDS)]
                    event_log = [[[] for u in units] for t in range(FPS*SECONDS)]
                    time=0
                    maxtime=0
                    player_index+=1
                    if player_index==1:
                        current_unit=3
                    if player_index==2:
                        event_log=committed
                elif event.type == pygame.KEYDOWN and event.key==pygame.K_RETURN and player_index==2:
                    if write_replay and replay_filename:
                        write_replay_file(committed,obstacles,replay_filename)
                    elif write_replay and not in_replay and not online:
                        write_replay_file(committed,obstacles)
                    gameloop=False

        elif (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]):
            stop_state=False
            if keys[pygame.K_RIGHT]:
                time+=1
                direction=">|"
            elif keys[pygame.K_LEFT] or keys[pygame.K_s]:
                time-=3
                direction="<<"
            elif time>0:
                time -=1
                direction="<"
            else:
                direction="||"

            if time<0:
                time=0
            if time>maxtime:
                time=maxtime

            units,bullets=state_log[time]

        elif time<FPS*SECONDS:
            direction=">"

            if player_index <2:
                current_events=[]
                unit=units[current_unit]

                for event in events:
                    if event.type == pygame.KEYDOWN and (event.key==pygame.K_x or event.key==pygame.K_e):
                        px,py=pygame.mouse.get_pos()
                        current_events.append(("shoot",(px/zoom,py/zoom)))
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        px,py=pygame.mouse.get_pos()
                        current_events.append(("shoot",(px/zoom,py/zoom)))
                if (keys[pygame.K_d]):
                    if  unit.look==-1:
                        current_events.append(("turn",None))
                    current_events.append(("right",None))
                if (keys[pygame.K_a]):
                    if unit.look==1:
                        current_events.append(("turn",None))
                    current_events.append(("left",None))
                if (keys[pygame.K_w]):
                    current_events.append(("jump",None))
                event_log[time][current_unit]=current_events

            bak_units=[copy.copy(u) for u in units]
            bak_bullets=[copy.copy(b) for b in bullets]
            maxtime=time
            state_log[maxtime]=(bak_units,bak_bullets)

            for unit_idx in range(len(units)):
                unit=units[unit_idx]
                unit.resting=False
                x,y=unit.pos
                unit.downspeed+=0.3
                if unit.downspeed>15:
                    unit.downspeed=15
                for obstacle in obstacles:
                    for off in [1-unit.radius,0,unit.radius-1]:
                        if unit.downspeed>=0 and obstacle.collidepoint(x+off,y+unit.radius+1+unit.downspeed):
                            y=obstacle.top-unit.radius
                            unit.downspeed=0
                            unit.resting=True
                        elif unit.downspeed<0 and obstacle.collidepoint(x+off,y-unit.radius+unit.downspeed):
                            y=obstacle.bottom+unit.radius
                            unit.downspeed=0
                unit.pos=x,y

                if unit.health>0:
                    unit.anim="idle"
                    for an_event in event_log[time][unit_idx]:
                        e,param=an_event
                        if e=="shoot":
                            x,y=unit.pos
                            if unit.weapon=="rockets":
                                if unit.rockets>0:
                                    unit.rockets-=1
                                    rx,ry=x+(2+unit.radius)*unit.look,y
                                    mx,my=param
                                    dx,dy=mx-rx,my-ry
                                    l=(dx**2+dy**2)**0.5
                                    rocket=Rocket(x+(2+unit.radius)*unit.look,y,(3*dx/l,3*dy/l),90)
                                    bullets.append(rocket)
                                    bang.play()
                            elif unit.weapon=="shotgun":
                                bullets.append(Bullet(x+(2+unit.radius)*unit.look,y,(3*unit.look,1),60))
                                bullets.append(Bullet(x+(2+unit.radius)*unit.look,y,(3.2*unit.look,0),60))
                                bullets.append(Bullet(x+(2+unit.radius)*unit.look,y,(3*unit.look,-1),60))
                                bang.play()
                            else:
                                bullets.append(Bullet(x+(2+unit.radius)*unit.look,y,(5*unit.look,0),120))
                                pew.play()

                        elif e=="left":
                            unit.anim="walk"
                            unit.look=-1
                            x,y=unit.pos
                            collide=False
                            for obstacle in obstacles:
                                if obstacle.collidepoint(x-unit.radius-unit.move_speed,y):
                                    collide=True
                                    break
                            if not collide:
                                unit.pos=x-unit.move_speed,y
                        elif e=="right":
                            unit.anim="walk"
                            unit.look=1
                            x,y=unit.pos
                            collide=False
                            for obstacle in obstacles:
                                if obstacle.collidepoint(x+unit.radius+unit.move_speed,y):
                                    collide=True
                                    break
                            if not collide:
                                unit.pos=x+unit.move_speed,y
                        elif e=="jump" and unit.resting:
                            jump.play()
                            unit.anim="idle"
                            unit.downspeed=-5
                else:
                    unit.anim="dead"
                x,y=unit.pos
                unit.pos=x,int(y+unit.downspeed)

            for b in bullets:
                b.fly()

                (x,y)=b.pos
                for u in units:
                    ux,uy=u.pos
                    if (ux-x)**2+(uy-y)**2<u.radius**2:
                        b.dead=True
                        u.health-=100
                        hurt.play()

                for o in obstacles:
                    if o.collidepoint(x,y):
                        b.dead=True

                if b.life<1:
                    b.dead=True

                if type(b)==Rocket and b.dead:
                    pygame.draw.circle(screen, (255,255,255,200), (int(x),int(y)), 40)
                    boom.play()
                    for i in range(20):
                        explosions.append((int(x),int(y)))
                    for u in units:
                        ux,uy=u.pos
                        if (ux-x)**2+(uy-y)**2<40**2:
                            u.health-=100

            bullets=[b for b in bullets if not b.dead]
            time+=1

        # RENDERING
        for obstacle in obstacles:
            pygame.draw.rect(screen, (40,40,110), obstacle, 0)
            pygame.draw.rect(screen, (50,50,100), obstacle, 2)

        if explosions:
            xpos=explosions.pop()
            pygame.draw.circle(screen, (200,200,200), xpos, 40)

        for unit in units:
            x,y=unit.pos
            look=unit.look
            r=unit.radius
            d=2*r
            if unit.anim=="walk":
                anim=unit.spritesheet.subsurface(pygame.Rect(d*((time/3)%12),0, d,d))
            else:
                anim=unit.spritesheet.subsurface(pygame.Rect(0,0, d,d))
            if unit.health<1:
                anim=pygame.transform.rotate(anim,90)
            if unit.look==-1:
                anim=pygame.transform.flip(anim,True,False)
            screen.blit(anim,(x-r,y-r))
            if unit.health>0:
                w_str=(str(unit.rockets) if unit.rockets else "")+unit.weapon[0]
                if unit==units[current_unit]:
                    w=font0.render(w_str, 1, (255,255,255))
                else:
                    w=font0.render(w_str, 1, [(n+100)/2 for n in player_colors[unit.player]])
                screen.blit(w,(x-r,y-r-20))


        for b in bullets:
            x,y=b.pos
            pygame.draw.circle(screen, (200,200,200), (int(x),int(y)), 2)

        # UI RENDERING

        if direction!=">":
            unit=units[current_unit]
            x,y=unit.pos
            pygame.draw.circle(screen, (100,100,100), (x,y), 15,2)

        hud=font.render(str(SECONDS-time/FPS)+" seconds "+["red planning","green planning", "OUTCOME"][player_index], 1, player_colors[player_index])
        hud2=font.render(direction, 1, (200,200,255))

        screen.blit(hud,(50,0))
        screen.blit(hud2,(0,0))
        if keys[pygame.K_h]:
            screen.blit(hud_grey,(0,0))

        if player_index==2 and time==FPS*SECONDS:
            p1points=0
            p2points=0
            for unit in units:
                if unit.health>0:
                    if unit.player==0:
                        p1points+=1
                    if unit.player==1:
                        p2points+=1
            if p1points>p2points:
                win="Red Wins"
            elif p1points<p2points:
                win="Green Wins"
            else:
                win="Draw"
            screen.blit(hud_grey,(0,0))
            hud_win=font_win.render(win, 1, (255,255,255))
            screen.blit(hud_win,(10,100))
            hud_win2=font.render("Press [RETURN] to leave", 1, (255,255,255))
            screen.blit(hud_win2,(10,300))

        if zoom>1:
            pygame.transform.scale(screen, screen_mode, screen_real)

        if keys[pygame.K_h]:
            for i in range(len(hud_help)):
                screen_real.blit(hud_help[i],(10*zoom,(50+i*20)*zoom))
        elif not in_replay and player_index!=2 and hints:
            if time==FPS*SECONDS or stop_state:
                screen_real.blit(hud_hint,(10*zoom,440*zoom))

            if time==FPS*SECONDS:
                commanded_units=0
                for unit in range(len(units)):
                    ev=False
                    for l in event_log:
                        if l[unit]:
                            ev=True
                    if ev:
                        commanded_units+=1
                if commanded_units>2:
                    screen_real.blit(hud_hint2,(10*zoom,400*zoom))
                else:
                    screen_real.blit(hud_hint5,(10*zoom,400*zoom))


            if direction=="<":
                screen_real.blit(hud_hint3,(10*zoom,440*zoom))

            if direction==">":
                screen_real.blit(hud_hint4,(10*zoom,440*zoom))

        pygame.display.flip()

## MENU SYSTEM

def textinput(prompt, fnt=36):
    h1=45
    h1font=pygame.font.Font("orbitron-black.ttf", h1*zoom)
    font=pygame.font.Font("orbitron-black.ttf", fnt*zoom)
    string=u""

    pad=4
    marg=30
    	
    while True:
        clock.tick(FPS)
        events = pygame.event.get()
        keys = pygame.key.get_pressed()
        
        screen_real.fill((50,50,80))
        
        screen_real.blit(h1font.render(prompt,1,(255,255,255)),(50*zoom,50*zoom))

        pygame.draw.rect(screen_real,(150,0,0),pygame.Rect(0*zoom,(150-pad)*zoom,640*zoom,(fnt+2*pad)*zoom))
	screen_real.blit(font.render(">"+string,1,(255,255,255)),(marg*zoom,150*zoom))


        for event in events:
            if event.type == pygame.QUIT:
                raise QuitClicked()
            elif event.type == pygame.KEYDOWN and event.key==pygame.K_RETURN:
                return string
            elif event.type == pygame.KEYDOWN and event.key==pygame.K_ESCAPE:
                return
            elif event.type == pygame.KEYDOWN and event.key==pygame.K_BACKSPACE:
                if string !=u"":
                    string=string[:-1]
            elif event.type == pygame.KEYDOWN and len(event.unicode)==1:
                string+=event.unicode
        pygame.display.flip()

def event_input(prompt, fnt=36):
    h1=45
    h1font=pygame.font.Font("orbitron-black.ttf", h1*zoom)
    font=pygame.font.Font("orbitron-black.ttf", fnt*zoom)
    string=u""

    pad=4
    marg=30
    	
    while True:
        clock.tick(FPS)
        events = pygame.event.get()
        keys = pygame.key.get_pressed()
        
        screen_real.fill((50,50,80))
        
        screen_real.blit(h1font.render(prompt,1,(255,255,255)),(50*zoom,50*zoom))

        pygame.draw.rect(screen_real,(150,0,0),pygame.Rect(0*zoom,(150-pad)*zoom,640*zoom,(fnt+2*pad)*zoom))
	screen_real.blit(font.render(">"+string,1,(255,255,255)),(marg*zoom,150*zoom))


        for event in events:
            if event.type == pygame.QUIT:
                raise QuitClicked()
            elif event.type == pygame.KEYDOWN and event.key==pygame.K_ESCAPE:
                return
            elif event.type == pygame.KEYDOWN:
                return event.key
        pygame.display.flip()

def key_bind_wrapper(action, bind, bind_hum):
    key=event_input("Press key or [ESC] to cancel")
    name=pygame.key.name(key)
    prompt="bind ["+name+"] to "+action
    confirm=menu([(prompt,"yes"), "cancel"],heading="Confirm")
    if confirm=="yes":
        bind[key]=action
        bind_hum[action]=name

def key_bind_menu(actions,bind,bind_hum):
    while True:
        a_key=menu([(a+" - ["+bind_hum[a]+"]",a) for a in actions]+["back"])
        if a_key in actions:
            key_bind_wrapper(a_key,bind,bind_hum)
        else:
            return

def menu(options,fnt=36,row=50, heading="Menu", h1=45, top=150,subtitle=""):
    option=0
    font=pygame.font.Font("orbitron-black.ttf", fnt*zoom)
    if fnt<30:
        font=pygame.font.Font("Ubuntu-R.ttf", fnt*zoom)
    h1font=pygame.font.Font("orbitron-black.ttf", h1*zoom)
    subfont=pygame.font.Font("Orbitron Medium.ttf", (h1*zoom)/3)

    top0=top
    time=0
    
    if heading=="Frozen Braid":
        subtitle=random.choice(["2 players, 6 soldiers, 10 seconds - LD 27",
                                "shotgun time travel tactics",
                                "(c) 2013 Robert Pfeiffer",
                                "red player goes first",
                                "blame your loss on the randomly generated map",
                                "10 seconds of strategery",
                                "tell your friends - we have multiplayer"])
    while True:
        clock.tick(FPS)
        events = pygame.event.get()
        keys = pygame.key.get_pressed()

        time+=1
        if time==1200:
            time=0

        screen.fill((50,50,80))
        for i in (0,1):
            s=spritesheets[i]
            anim=s.subsurface(pygame.Rect(20*((time/2)%12),0, 20,20))
            screen.blit(anim,(500+40*i,50))

        if zoom>1:
            pygame.transform.scale(screen, screen_mode, screen_real)

        screen_real.blit(h1font.render(heading,1,(255,255,255)),(50*zoom,50*zoom))
        screen_real.blit(subfont.render(subtitle,1,(255,255,255)),(90*zoom,110*zoom))

        top=top0
        bottom_marg=400

        d_overlap=top+option*row-bottom_marg
        if d_overlap>0:
            top-=d_overlap

        pad=4
        marg=30
        pygame.draw.rect(screen_real,(150,0,0),pygame.Rect(0*zoom,(top-pad+option*row)*zoom,640*zoom,(fnt+2*pad)*zoom))
        for i in range(len(options)):
            if top+i*row>=top0:
                an_option=options[i]
                if type(an_option)==tuple:
                    an_option=an_option[0]
                screen_real.blit(font.render(an_option,1,(255,255,255)),(marg*zoom,(top+i*row)*zoom))

        for event in events:
            if event.type == pygame.QUIT:
                raise QuitClicked()
            elif event.type == pygame.KEYDOWN and event.key==pygame.K_RETURN:
                an_option=options[option]
                if type(an_option)==tuple:
                    an_option=an_option[1]
                return an_option
            elif event.type == pygame.KEYDOWN and event.key==pygame.K_ESCAPE:
                return None
            elif event.type == pygame.KEYDOWN and event.key==pygame.K_UP:
                if option>0:
                    option-=1
                    if options[option][0]==" " and option>0:
                        option-=1
            elif event.type == pygame.KEYDOWN and event.key==pygame.K_DOWN:
                if option<len(options)-1:
                    option+=1
                    if options[option][0]==" " and option<len(options)-1:
                        option+=1

        pygame.display.flip()

class QuitClicked(Exception):
    pass

## MAIN MENU

#key_bind_menu(actions,bind,bind_hum)

def playbymail():
    global playername
    action = "START"
    while action and action != "back":
     if not playername:
         playername=textinput("Player Name")
         if playername=="":
             menu(["Player name can not be empty"],heading="Player Name")
             continue
         elif not playername:
             return
     action=menu(["Create Map", "Make Move", "Game Outcome", "Map Status", "Change Name", "back"], heading="Play by Mail", subtitle="playing as "+playername)

     if action=="Create Map":
        mapname=textinput("Map Name")
        if mapname=="":
            menu(["Map name can not be empty"],heading="Map Name")
            continue
        elif not mapname:
            continue
        mapcontent=create_map()
        write_map_file(mapcontent,mapname)
     elif action=="Change Name":
         newname=textinput("Player Name")
         if newname:
             playername=newname
     elif action=="Make Move":
        mapnames=get_map_names()
        if not mapnames:
            menu(["No Maps Found"],heading="Select Map")
            continue
        mapname=menu(mapnames,heading="Select Map")
        if not mapname:continue
        selected_color=menu(["red","green"],heading="Select Color")
        if not selected_color:continue
        with open(mapname+".map.json") as loadfile:
            map_s=loadfile.read()
        mapcontent=json.loads(map_s)
        mapcontent=[pygame.Rect(a,b) for (a,b) in mapcontent]
        pl_index={"red":0,"green":1}[selected_color]
        move=rungame(online=True,map=mapcontent,player_index=pl_index)
        if not move:
            continue
        write_move_file(move,mapname,playername,selected_color)
     elif action=="Map Status":
        mapnames=get_map_names()
        if not mapnames:
            menu(["No Maps Found"],heading="Select Map")
            continue
        map_desc=[]
        for mapname in mapnames:
            red_moves,green_moves=map_get_moves(mapname)
            map_desc.append(mapname+": "
                            +str(len(red_moves))+" red,"
                            +str(len(green_moves))+" green")
        menu(map_desc,heading="Map List")
     elif action=="Game Outcome":
        mapnames=get_map_names()
        mapnames=[m for m in mapnames if map_is_played(m)]
        if not mapnames:
            menu(["No played maps found"],heading="Select Map")
            continue
        else:
            mapname=menu(mapnames,heading="Select Map")
        if not mapname:continue
        red_moves,green_moves=map_get_moves(mapname)
        if not red_moves or not green_moves:
            menu(["No Matching Moves Found"],heading="Select Moves")
            continue
        if len(red_moves)==1:
            selected_red_move=red_moves[0]
        else:
            selected_red_move=menu(red_moves,heading="Select Red Move")
            if not selected_red_move: continue
        if len(green_moves)==1:
            selected_green_move=green_moves[0]
        else:
            selected_green_move=menu(green_moves,heading="Select Green Move")
            if not selected_green_move:continue
        with open(selected_red_move) as loadfile:
            red_s=loadfile.read()
        move_red=json.loads(red_s)
        committed_red=move_red["committed"]
        with open(selected_green_move) as loadfile:
            green_s=loadfile.read()
        move_green=json.loads(green_s)
        committed_green=move_green["committed"]
        committed=[[[] for u in range(6)] for t in range(FPS*SECONDS)]
        for t in range(FPS*SECONDS):
            for redunit in [0,1,2]:
                committed[t][redunit]=committed_red[t][redunit]
            for greenunit in [3,4,5]:
                committed[t][greenunit]=committed_green[t][greenunit]
        with open(mapname+".map.json") as loadfile:
            map_s=loadfile.read()
        mapcontent=json.loads(map_s)
        mapcontent=[pygame.Rect(a,b) for (a,b) in mapcontent]
        replay_filename=".".join([mapname,move_green["name"],move_red["name"]])
        rungame((committed,mapcontent),replay_filename=replay_filename)



options=["Start Game", "Help", "Replays", "Options", "Website", "Quit"]

def mainmenu():
 global write_replay
 global hints
 try:
  while True:
    chosen=menu(options,heading="Frozen Braid",h1=60)
    if chosen=="Start Game":
        gametype=menu(["Local Multiplayer", "Play by Mail", "back"], heading="Start Game")
	if gametype=="Local Multiplayer":
            rungame()
        elif gametype=="Play by Mail":
            playbymail()
    elif chosen=="Help":
        menu(help_text,18,20,heading="Help")
    elif chosen=="Website":
        webbrowser.open("http://www.ludumdare.com/compo/ludum-dare-27/?action=preview&uid=7968")
    elif chosen=="Options":
        option =""
        while option!="back":
            option=menu(["red and green sprites", "colorblind mode",
                        " ", ("disable replays" if write_replay else "auto save replays"), 
                        ("turn music off" if pygame.mixer.music.get_busy() else "turn music on"),
                        ("turn hints off" if hints else "turn hints on (show suggested buttons)"),
                        " ", "back"],30,35,heading="Options", top=120)
            if option=="red and green sprites":
                spritesheets[1]=pygame.image.load("green.png").convert_alpha()
            elif option=="colorblind mode":
                spritesheets[1]=pygame.image.load("colorblind-green.png").convert_alpha()
            elif option=="auto save replays":
                write_replay=True
            elif option=="disable replays":
                write_replay=False
            elif option=="turn music on":
                pygame.mixer.music.play()
            elif option=="turn music off":
                pygame.mixer.music.stop()
            elif option=="turn hints on (show suggested buttons)":
                hints=True
            elif option=="turn hints off":
                hints=False
    elif chosen=="Replays":
        replays=glob.glob("*.replay.json")
        replays.sort()
        replays=[strip_ext(r,".replay.json") for r in replays]
        replay=menu(replays+["back"],heading="Replays",)
        if replay!="back":
            with open(replay+".replay.json") as loadfile:
                #replay_obj=pickle.load(loadfile)
                replay_s=loadfile.read()
	        c,o=json.loads(replay_s)
	        o=[pygame.Rect(a,b) for (a,b) in o]
	        replay_obj=c,o
            rungame(replay_obj)

    elif chosen=="Quit":
        break
 except QuitClicked as e:
     pass
if __name__=="__main__":
    mainmenu()

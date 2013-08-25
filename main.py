import pygame
import copy
import random
import webbrowser
import pickle
import glob
import datetime

pygame.init()

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

font0=pygame.font.Font("orbitron-black.ttf", 18)
font=pygame.font.Font("orbitron-black.ttf", 36)
font_win=pygame.font.Font("Ostrich Black.ttf", 160)

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
           "[SHIFT] rewinds time, [SHIFT]+[LEFT] rewinds faster",
           "[SPACE] stops time",
           " ",
           "Only when time is up",
           " [N] selects next unit",
           " [RETURN] ends your move (give PC to other player)",
           " ",
           "[W][A][S][D] and arrows move units",
           "[X] or [E] shoots",
           "Units have a machine gun, a shotgun or rockets",
           "Rocket Guy aims with the mouse, but has only 3 shots",
           " ",
           "1. Red makes his move while green looks away",
           "2. Green makes his move while red has a total poker face",
           "3. Both strategies are played against each other",
           "4. The player with more units after TEN SECONDS wins"]

hud_help=[font0.render(a,1,(200,200,200,200)) for a in
          help_text]

hud_grey=screen.copy().convert_alpha()
hud_grey.fill((50,50,50,180))
hud_hint=font0.render("press [H] for help and [SHIFT] to rewind or [L] to leave",1,(200,200,200,150))

mainloop=True
write_replay=True

def rungame(replay=None):
    global mainloop
    global write_replay
    global zoom

    #CREATE STUFF
    current_unit=0
    time=0
    maxtime=0
    player_index=0

    obstacles=[pygame.Rect(310, 50, 20, 100),pygame.Rect(0, 0, 20, 480),pygame.Rect(620, 0, 20, 480),pygame.Rect(0, 460, 640, 20)]
    units=[Unit(100,100,0),Unit(110,100,0,"shotgun"),Unit(120,100,0,"rockets"),
          Unit(540,100,1),Unit(530,100,1,"shotgun"),Unit(520,100,1,"rockets")]
    bullets=[]

    state_log = [None for t in range(FPS*SECONDS)]
    event_log = [[[] for u in units] for t in range(FPS*SECONDS)]
    committed=[[[] for u in units] for t in range(FPS*SECONDS)]

    for i in range(6):
        for j in range(6):
            obstacles.append(pygame.Rect(i*100+random.randint(0,100), 100+j*60+random.randint(0,80), 40, 10))

    gameloop=True
    in_replay=False

    if replay:
        committed,obstacles=replay
        event_log=committed
        player_index=2
        in_replay=True

    while gameloop and mainloop:
        clock.tick(FPS)
        events = pygame.event.get()
        keys = pygame.key.get_pressed()

        for event in events:
            if event.type == pygame.QUIT:
                mainloop=False
                return
            elif event.type == pygame.KEYDOWN and event.key==pygame.K_l:
                return

        screen.fill((10,10,50))
        direction=""

        if (keys[pygame.K_SPACE] and not (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])):
            direction="||"
        elif not (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and time==FPS*SECONDS:
            direction="||"
            for event in events:
                if event.type == pygame.KEYDOWN and event.key==pygame.K_n:
                    current_unit=(current_unit+1)%len(units)
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
                    if player_index==2:
                        event_log=committed
                elif event.type == pygame.KEYDOWN and event.key==pygame.K_RETURN and player_index==2:
                    if write_replay and not in_replay:
                        ts=datetime.datetime.now().isoformat()
                        with open(ts+".replay",'w') as dumpfile:
                            pickle.dump((committed,obstacles), dumpfile)
                    gameloop=False

        elif (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]):
            if keys[pygame.K_RIGHT]:
                time+=1
                direction=">|"
            elif keys[pygame.K_LEFT]:
                time-=3
                direction="<<"
            elif keys[pygame.K_DOWN]:
                time=0
                direction="||"
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
                if (keys[pygame.K_RIGHT] or keys[pygame.K_d]):
                    if  unit.look==-1:
                        current_events.append(("turn",None))
                    current_events.append(("right",None))
                if (keys[pygame.K_LEFT] or keys[pygame.K_a]):
                    if unit.look==1:
                        current_events.append(("turn",None))
                    current_events.append(("left",None))
                if (keys[pygame.K_UP] or keys[pygame.K_w]):
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
                if unit.downspeed>20:
                    unit.downspeed=20
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
                    pygame.draw.circle(screen, (100,100,100), (int(x),int(y)), 40)
                    boom.play()
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
            for i in range(len(hud_help)):
                screen.blit(hud_help[i],(10,50+i*20))
        elif time==FPS*SECONDS:
            screen.blit(hud_hint,(10,440))

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
        pygame.display.flip()


def menu(options,fnt=36,row=50, heading="Menu", h1=45):
    global mainloop
    option=0
    font=pygame.font.Font("orbitron-black.ttf", fnt)
    h1font=pygame.font.Font("orbitron-black.ttf", h1)
    time=0

    while mainloop:
        clock.tick(FPS)
        events = pygame.event.get()
        keys = pygame.key.get_pressed()
        screen.fill((50,50,80))

        screen.blit(h1font.render(heading,1,(255,255,255)),(50,50))

        time+=1
        if time==1200:
            time=0
        for i in (0,1):
            s=spritesheets[i]
            anim=s.subsurface(pygame.Rect(20*((time/2)%12),0, 20,20))
            screen.blit(anim,(500+40*i,50))

        top=150
        top1=top
        bottom_marg=400

        d_overlap=top+option*row-bottom_marg
        if d_overlap>0:
            top-=d_overlap

        for i in range(len(options)):
            if option==i:
                pad=4
                marg=30
                pygame.draw.rect(screen,(150,0,0),pygame.Rect(0,top-pad+i*row,640,fnt+2*pad))
            if top+i*row>=top1:
                screen.blit(font.render(options[i],1,(255,255,255)),(marg,top+i*row))

        for event in events:
            if event.type == pygame.QUIT:
                mainloop=False
                return
            elif event.type == pygame.KEYDOWN and event.key==pygame.K_RETURN:
                return options[option]
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
        if zoom>1:
            pygame.transform.scale(screen, screen_mode, screen_real)
        pygame.display.flip()


options=["2 player game", "Help", "Replays", "Options", "Website", "Quit"]

while mainloop:
    chosen=menu(options,heading="Frozen Braid",h1=60)
    if chosen=="2 player game":
        rungame()
    elif chosen=="Help":
        menu(help_text,18,20,heading="Help")
    elif chosen=="Website":
        pass
    elif chosen=="Options":
        option =""
        while option!="back" and mainloop:
            option=menu(["standard red and green sprites", "colorblind mode",
                        " ", "save replays", "do not save replays",
                        " ", "music on", "music off",
                        " ", "back"],20,25,heading="Options")
            if option=="standard red and green sprites":
                spritesheets[1]=pygame.image.load("green.png").convert_alpha()
            elif option=="colorblind mode":
                spritesheets[1]=pygame.image.load("colorblind-green.png").convert_alpha()
            elif option=="save replays":
                write_replay=True
            elif option=="do not save replays":
                write_replay=False
            elif option=="music on":
                pygame.mixer.music.play()
            elif option=="music off":
                pygame.mixer.music.stop()
    elif chosen=="Replays":
        replays=glob.glob("*.replay")
        replay=menu(replays+["back"],20,25,heading="Replays",)
        if replay!="back":
            with open(replay) as loadfile:
                replay_obj=pickle.load(loadfile)
            rungame(replay_obj)

    elif chosen=="Quit":
        mainloop=False
        break

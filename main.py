import pygame
import copy
import random

pygame.init()

screen_mode=(640,480)
screen = pygame.display.set_mode(screen_mode,pygame.DOUBLEBUF)


guys={}

def intro(filename):
    logo=pygame.transform.scale(pygame.image.load(filename).convert_alpha(),screen_mode)
    screen.blit(logo, (0,0))
    pygame.display.flip()

    for i in range(3*30):
        clock.tick(30)
        pygame.event.pump()
        keys = pygame.key.get_pressed()
        mouse = pygame.mouse.get_pressed()
        if keys[pygame.K_SPACE] or mouse[0]:
            break
        screen.fill([0,0,0])
        screen.blit(logo, (0,0))
        pygame.display.flip()

clock = pygame.time.Clock() # create clock object

font=pygame.font.Font("orbitron-black.ttf", 36)

FPS=30
SECONDS=10

class Unit(object):
    def __init__(self,x,y,color,weapon="rifle"):
        self.look=1
        self.pos=x,y
        self.color=color
        self.downspeed=0
        self.radius=10
        self.resting=False
        self.move_speed=2
        self.health=100
        self.weapon=weapon

units=[Unit(100,100,(180,0,0),"shotgun"),Unit(110,100,(180,0,0),"shotgun"),Unit(120,100,(180,0,0),"shotgun"),
       Unit(540,100,(0,180,0)),Unit(530,100,(0,180,0)),Unit(520,100,(0,180,0))]
current_unit=0
state_log = [None for time in range(FPS*SECONDS)]
event_log = [[[] for u in units] for time in range(FPS*SECONDS)]
time=0
maxtime=0
player_colors=[(180,0,0),(0,180,0),(255,255,255)]
player_index=0

committed=[[[] for u in units] for t in range(FPS*SECONDS)]

obstacles=[pygame.Rect(310, 50, 20, 100),pygame.Rect(0, 0, 20, 480),pygame.Rect(620, 0, 20, 480),pygame.Rect(0, 460, 640, 20)]

for i in range(6):
    for j in range(6):
        obstacles.append(pygame.Rect(i*100+random.randint(0,100), 100+j*60+random.randint(0,80), 40, 10))

bullets=[]

mainloop=True
while mainloop:
    print time,maxtime,player_index
    clock.tick(FPS)
    events = pygame.event.get()
    keys = pygame.key.get_pressed()

    for event in events:
        if event.type == pygame.QUIT:
            mainloop=False
    screen.fill((10,10,50))
    direction=""

    if ((keys[pygame.K_SPACE] and not keys[pygame.K_LSHIFT])
        or (not keys[pygame.K_LSHIFT] and time==FPS*SECONDS)):
        direction="||"
        for event in events:
            if event.type == pygame.KEYDOWN and event.key==pygame.K_n:
                current_unit=(current_unit+1)%len(units)
            if event.type == pygame.KEYDOWN and event.key==pygame.K_c:
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

    elif keys[pygame.K_LSHIFT]:
        if keys[pygame.K_RIGHT] and time < maxtime:
            time+=1
            direction=">|"
        elif keys[pygame.K_LEFT] and time > 1:
            time-=2
            direction="<<"
        elif keys[pygame.K_DOWN]:
            time=0
            direction="||"
        elif time>0:
            time -=1
            direction="<"
        else:
            direction="||"

        units,bullets=state_log[time]

    elif time<FPS*SECONDS:
        direction=">"

        if player_index <2:
            current_events=[]
            unit=units[current_unit]

            for event in events:
                if event.type == pygame.KEYDOWN and event.key==pygame.K_x:
                    current_events.append("shoot")
            if keys[pygame.K_RIGHT]:
                if  unit.look==-1:
                    current_events.append("turn")
                current_events.append("right")
            if keys[pygame.K_LEFT]:
                if unit.look==1:
                    current_events.append("turn")
                current_events.append("left")
            if keys[pygame.K_UP]:
                current_events.append("jump")
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
                for e in event_log[time][unit_idx]:
                    if e=="shoot":
                        x,y=unit.pos
                        if unit.weapon=="shotgun":
                            bullets.append(((x+(2+unit.radius)*unit.look,y),(3*unit.look,1),time))
                            bullets.append(((x+(2+unit.radius)*unit.look,y),(3*unit.look,-1),time))
                            bullets.append(((x+(2+unit.radius)*unit.look,y),(3*unit.look,0),time))
                        else:
                            bullets.append(((x+(2+unit.radius)*unit.look,y),(5*unit.look,0),time))

                    if e=="left":
                        unit.look=-1
                        x,y=unit.pos
                        collide=False
                        for obstacle in obstacles:
                            if obstacle.collidepoint(x-unit.radius-unit.move_speed,y):
                                collide=True
                                break
                        if not collide:
                            unit.pos=x-unit.move_speed,y
                    if e=="right":
                        unit.look=1
                        x,y=unit.pos
                        collide=False
                        for obstacle in obstacles:
                            if obstacle.collidepoint(x+unit.radius+unit.move_speed,y):
                                collide=True
                                break
                        if not collide:
                            unit.pos=x+unit.move_speed,y
                    if e=="jump" and unit.resting:
                        unit.downspeed=-5
            x,y=unit.pos
            unit.pos=x,int(y+unit.downspeed)

        for i in range(len(bullets)):
            (x,y),(dx,dy),spawntime=bullets[i]
            bullets[i]=(x+dx,y+dy),(dx,dy),spawntime

        for b in bullets[:]:
            (x,y),(dx,dy),spawntime=b
            for u in units:
                ux,uy=u.pos
                if (ux-x)**2+(uy-y)**2<u.radius**2:
                    bullets.remove(b)
                    u.health-=100

        for b in bullets[:]:
            (x,y),(dx,dy),spawntime=b
            for o in obstacles:
                if o.collidepoint(x,y):
                    bullets.remove(b)

        time+=1

    for unit in units:
        x,y=unit.pos
        look=unit.look
        if unit.health<1:
            pygame.draw.circle(screen, (50,50,50), (x,y), 10)
        else:
            pygame.draw.circle(screen, unit.color, (x,y), 10)
        pygame.draw.circle(screen, (100,100,100), (x+look*3,y), 5)

    if direction!=">":
        unit=units[current_unit]
        x,y=unit.pos
        pygame.draw.circle(screen, (100,100,100), (x,y), 15,2)

    for obstacle in obstacles:
        #pygame.draw.rect(screen, (100,0,100), obstacle, 2)
        pygame.draw.rect(screen, (50,50,100), obstacle, 2)

    hud=font.render(str(SECONDS-time/FPS)+" seconds", 1, player_colors[player_index])
    hud2=font.render(direction, 1, (200,200,255))

    for b in bullets:
        bpos,bspeed,bspawn=b
        pygame.draw.circle(screen, (200,200,200), bpos, 2)
    screen.blit(hud,(50,0))
    screen.blit(hud2,(0,0))

    pygame.display.flip()

import pygame

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

font=pygame.font.Font("orbitron-black.ttf", 18)

FPS=30
SECONDS=10

class Unit(object):
    def __init__(self,x,y,color):
        self.look=1
        self.pos=x,y
        self.color=color
        self.downspeed=0

units=[Unit(100,100,(0,0,255)),Unit(130,100,(0,180,0))]
current_unit=0
impact_log = [[] for i in range(FPS*SECONDS)]
land_log = [[] for i in range(FPS*SECONDS)]
event_log = [[[] for u in units] for time in range(FPS*SECONDS)]
time=0


obstacles=[pygame.Rect(350, 50, 50, 100),pygame.Rect(0, 150, 200, 500)]
bullets=[]

mainloop=True
while mainloop:
    clock.tick(FPS)
    events = pygame.event.get()
    keys = pygame.key.get_pressed()

    for event in events:
        if event.type == pygame.QUIT:
            mainloop=False
    screen.fill((10,10,50))
    direction=""

    if ((keys[pygame.K_SPACE] and not keys[pygame.K_LSHIFT])
        or (keys[pygame.K_LSHIFT] and time==0)
        or (not keys[pygame.K_LSHIFT] and time==FPS*SECONDS)):
        direction="||"
        for event in events:
            if event.type == pygame.KEYDOWN and event.key==pygame.K_n:
                current_unit=(current_unit+1)%len(units)
    elif keys[pygame.K_LSHIFT] and time>0:
        direction="<"
        time-=1
        for d in impact_log[time]:
            bullets.append(d)

        landings=land_log[time]
        for unit,speed in landings:
            unit.downspeed=speed

        for unit_idx in range(len(units)):
            unit=units[unit_idx]
            x,y=unit.pos
            unit.pos=x,y-unit.downspeed
            for e in event_log[time][unit_idx]:
                if e=="left":
                    x,y=unit.pos
                    unit.pos=x+1,y
                if e=="right":
                    x,y=unit.pos
                    unit.pos=x-1,y
                if e=="turn":
                    unit.look*=-1

        for i in range(len(bullets)):
            (x,y),(dx,dy),spawntime=bullets[i]
            bullets[i]=(x-dx,y-dy),(dx,dy),spawntime
        bullets=[b for b in bullets if b[2]<time]

    elif time<FPS*SECONDS:
        direction=">"
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
            if unit.downspeed==0 and obstacle.collidepoint(x+5,y):
                current_events.append("jump")
        event_log[time][current_unit]=current_events

        landings=[]
        for unit_idx in range(len(units)):
            unit=units[unit_idx]
            for e in event_log[time][unit_idx]:
                if e=="shoot":
                    bullets.append((unit.pos,(2*unit.look,0),time))
                if e=="left":
                    unit.look=-1
                    x,y=unit.pos
                    unit.pos=x-1,y
                if e=="right":
                    unit.look=1
                    x,y=unit.pos
                    unit.pos=x+1,y
                if e=="jump":
                    unit.downspeed-=5
            for obstacle in obstacles:
                x,y=unit.pos
                if unit.downspeed>0 and obstacle.collidepoint(x+5,y):
                    landings.append((unit_idx,unit.downspeed))
                    unit.downspeed=0
                elif unit.downspeed<0 and obstacle.collidepoint(x-5,y):
                    landings.append((unit_idx,unit.downspeed))
                    unit.downspeed=0
                elif obstacle.collidepoint(x+5,y):
                    pass
                else:
                    y+=unit.downspeed
                    unit.downspeed+=1
        land_log[time]=landings

        for i in range(len(bullets)):
            (x,y),(dx,dy),spawntime=bullets[i]
            bullets[i]=(x+dx,y+dy),(dx,dy),spawntime

        deaths=[]

        for b in bullets:
            (x,y),(dx,dy),spawntime=b
            if obstacle.collidepoint(x,y):
                deaths.append(b)
                bullets.remove(b)
        impact_log[time]=deaths
        event_log[time][current_unit]=current_events
        time+=1

    for unit in units:
        x,y=unit.pos
        look=unit.look
        pygame.draw.circle(screen, unit.color, (x,y), 10)
        pygame.draw.circle(screen, (100,100,100), (x+look*3,y), 5)

    if direction in("||", "<"):
        unit=units[current_unit]
        x,y=unit.pos
        look=unit.look
        pygame.draw.circle(screen, (100,100,100), (x,y), 15,2)

    for obstacle in obstacles:
        pygame.draw.rect(screen, (100,0,100), obstacle, 2)

    hud=font.render(direction+str(10-time/30), 1, (255,255,0))

    for b in bullets:
        bpos,bspeed,bspawn=b
        pygame.draw.circle(screen, (200,200,200), bpos, 2)
    screen.blit(hud,(0,0))
    pygame.display.flip()

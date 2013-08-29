import json
import sys

mapfile=sys.argv[1]
redmove=sys.argv[2]
greenmove=sys.argv[3]

replayname=sys.argv[4]

with open(redmove) as loadfile:
    red_s=loadfile.read()
committed_red=json.loads(red_s)["committed"]
with open(greenmove) as loadfile:
    green_s=loadfile.read()
committed_green=json.loads(green_s)["committed"]
committed=[[[] for u in range(6)] for t in range(FPS*SECONDS)]
for t in range(FPS*SECONDS):
    for redunit in [0,1,2]:
        committed[t][redunit]=committed_red[t][redunit]
    for greenunit in [3,4,5]:
        committed[t][greenunit]=committed_green[t][greenunit]
with open(mapfile) as loadfile:
    map_s=loadfile.read()

mapcontent=json.loads(map_s)

with open(replayname+".replay.json",'w') as dumpfile:
    dumpfile.write(json.dumps((committed,mapcontent)))

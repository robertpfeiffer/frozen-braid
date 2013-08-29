import pickle
import json
import glob

replays=glob.glob("*.replay")
replays.sort()
for replay in replays:
    with open(replay) as loadfile:
        committed,obstacles=pickle.load(loadfile)
    with open(replay+".json",'w') as dumpfile:
        dumpfile.write(json.dumps((committed,[(o.topleft,o.size) for o in obstacles])))


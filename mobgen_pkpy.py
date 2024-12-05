# This file generates mobs and maybe a simple map(default map is just a rectangel)
# mobs gather like bacterias, and for notation, # is wall, . is empty, */$/@ et cetra are mobs

# Environment: Python, we only need the algorithm, later will deploy on pkpy

# NOTICE:  all the function mixed up x & y axis, but that doesn't matter..if everybody is wrong, everybody is right

import random
import time
from array2d import array2d
from linalg import vec2i
from dataclasses import dataclass
# from dataclasses import field

globalrand = random.Random()
globalrand.seed(int(time.time()))
mob_database = [("👾","．"),
                ("💀", "．"),
                ("👽", "．", "💦"),
                ("👻", "💦")]

@dataclass
class mob:
    emoji: str
    num: int
    terrain: list[str]
    
def get_random_mob(num_preset:tuple[int,int] = (4,7)) -> mob:
    """
    get a random kind of mob from the database\n
    @num_preset: (min, max) of the number of mobs\n
    """
    mob_num = globalrand.randint(num_preset[0], num_preset[1])
    mob_choice = globalrand.choice(mob_database)
    return mob(mob_choice[0], mob_num, mob_choice[1:])

class Layer:
    """
    Creates copy of map.\n
    @OriginTerrain: original terrain without mobs\n
    @Occupied: the cells occupied by mobs, cannot generate mobs again on them
    """

    OriginTerrain: array2d
    Occupied: array2d

    def __init__(self, map: array2d) -> None:
        x = map.width
        y = map.height
        self.OriginTerrain = map.copy()
        self.Occupied = array2d(x, y, 0)


def generate_noise(x: int, y: int, prob: int, seed: float | None = None) -> array2d:
    randcls = random.Random()
    if seed is None:
        seed = int(time.time())
    randcls.seed(seed)
    map = array2d(x, y)
    for x, y, _ in map:
        map[x, y] = "💦" if randcls.randint(1, 100) <= prob else "．"
    return map


def postfix_noise(map: array2d, loop: int, f1: int, f2: int = 0) -> array2d:
    """
    process the impulse noise map\n
    @map: the noise map\n
    @loop: times of postfx\n
    @f1: threshold of tiles being walls with 1 step, != 0\n
    @f2: threshold of tiles being walls with 2 steps, can be 0\n
    """
    x = map.width
    y = map.height
    nummap = map.map(lambda x: 1 if x == "💦" else 0)
    all1map = array2d(x, y, 1)
    f1cnt = array2d(x, y, 0)
    f2cnt = array2d(x, y, 0)
    kernelf1 = array2d(3, 3, 1)
    kernelf2 = array2d(5, 5, 1)
    kernelf2[0, 0] = kernelf2[4, 0] = kernelf2[0, 4] = kernelf2[4, 4] = 0  # exclude the corners
    for _ in range(loop):
        f1cnt = nummap.convolve(kernelf1, 0)
        if f2 != 0:
            f2cnt = nummap.convolve(kernelf2, 0)
        for tuple1, tuple2 in zip(f1cnt, f2cnt):
            _x, _y, f1val = tuple1
            _, _, f2val = tuple2
            if 0 < _x < x - 1 and 0 < _y < y - 1:
                if f1val >= f1 or (f2 != 0 and f2val <= f2):
                    all1map[_x, _y] = 1
                else:
                    all1map[_x, _y] = 0
        nummap = all1map
    return nummap.map(lambda x: "💦" if x == 1 else "．")
    # return nummap


def flood_fill_wall(map: array2d) -> tuple[array2d, list, list]:
    """
    floods the map and replace where it walks with wall\n
    @Return: (vis, scc_emoji, scc_count), vis with not 0 index is not empty
    @scc_emoji and scc_count are correspond to vis's indices
    """
    toreplace = map.get(0, 0)
    vis, visnum = map.get_connected_components(toreplace, "von Neumann")
    for _x, _y, val in vis:
        if val == 1:
            map[_x, _y] = "🧱"
    scc_emoji = ["．", "🧱"]
    for _ in range(visnum - 1):
        scc_emoji.append("💦")
    scc_count = []
    for cnt in range(visnum+1):
        scc_count.append(vis.count(cnt))
    return (vis, scc_emoji, scc_count)


def select_valid_pos(
    layer: Layer,
    scc: array2d,
    scc_emoji: list,
    scc_cnt: list,
    mob: mob,
    myscore: float
) -> tuple[int, int, tuple[int, int, int, int]]:
    """
    @layer: Layer class\n
    @scc: return of get_connected_components\n
    @mob_num: the number needed for chosen mob\n
    @mob: mobBase class\n
    """
    randcls = globalrand
    x = scc.width
    y = scc.height
    while True:
        anchorx = randcls.randint(0, x - 1)
        anchory = randcls.randint(0, y - 1)
        if scc_emoji[scc[anchorx, anchory]] in mob.terrain and scc_cnt[scc[anchorx, anchory]] >= mob.num:
            scores = score(layer, mob, anchorx, anchory, myscore)
            return (anchorx, anchory, scores)
        
def score(layer:Layer, mob:mob, x:int, y:int, score:float) -> tuple[int, int, int, int]:
    """
    The score function which controls the distribution of mob hordes,
    returns the border coord of the horde\n
    @myscore: size of horde, >0, and not too big\n
    @return: upleft(x,y) and downright(x,y)
    """
    assert score > 0
    borderx = layer.OriginTerrain.width
    bordery = layer.OriginTerrain.height
    griddim = int((mob.num - 1) * score + 1)
    cnt = 0
    expected_cnt = griddim * griddim
    if expected_cnt < mob.num:
        expected_cnt = mob.num
    upx = x - griddim
    upy = y - griddim
    downx = x + griddim
    downy = y + griddim
    if upx < 0:
        upx = 0
    if upy < 0:
        upy = 0
    if downx >= borderx:
        downx = borderx - 1
    if downy >= bordery:
        downy = bordery - 1
    while True:
        for tx in range(upx, downx + 1):
            for ty in range(upy, downy + 1):
                if (layer.OriginTerrain[tx,ty] in mob.terrain and layer.Occupied[tx,ty] == 0):
                    cnt += 1
        if cnt >= expected_cnt:
            return (upx, upy, downx, downy)
        else:
            if upx > 0:
                upx -= 1
            if upy > 0:
                upy -= 1
            if downx < borderx - 1:
                downx += 1
            if downy < bordery - 1:
                downy += 1
            cnt = 0

def spawn_splash(map: array2d, layer:Layer, i:int, mob:mob, x:int, y:int, rect:tuple[int,int,int,int], splash:float, center:bool = True) -> None:
    """
    generate horde sample\n
    @i: the index of horde, should be i + 1 of the current loop\n
    @x: anchor x, the center of horde\n
    @y: anchor y, the center of horde\n
    @rect: the border of horde\n
    @splash: the splash range of horde, close to 0 will be more concentrate\n
    @center: True will generate around the (x,y)\n
    """
    
    pass

if __name__ == "__main__":
    mymap = generate_noise(50, 30, 40, 2024)
    mymap = postfix_noise(mymap, 4, 5, 1)
    mymap = postfix_noise(mymap, 3, 5)
    scc, scc_emoji, scc_cnt = flood_fill_wall(mymap)
    # for x, y, val in mymap:
    #     print(val, end=" ")
    #     if x == mymap.width - 1:
    #         print("\n")

    # for x, y, val in scc:
    #     print(val, end=" ")
    #     if x == mymap.width - 1:
    #         print("\n")

    layer = Layer(mymap)
    for i in range(10):
        current_mob = get_random_mob()
        x,y, rect = select_valid_pos(layer, scc, scc_emoji, scc_cnt, current_mob, 0.3)
        upx, upy, downx, downy = rect
        for xx in range(upx, downx + 1):
            for yy in range(upy, downy + 1):
                if (layer.OriginTerrain[xx,yy] in current_mob.terrain and layer.Occupied[xx,yy] == 0):
                    layer.Occupied[xx,yy] = i + 1
                    mymap[xx,yy] = current_mob.emoji
        print("*" * 40, i)
        for x, y, val in mymap:
            print(val, end=" ")
            if x == mymap.width - 1:
                print("\n")
    test = mob("!", 3, ["💦"])
    test1 = mob("!", 3, ["e"])
    
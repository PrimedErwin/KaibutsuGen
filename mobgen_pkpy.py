# This file generates mobs and maybe a simple map(default map is just a rectangel)
# mobs gather like bacterias, and for notation, # is wall, . is empty, */$/@ et cetra are mobs

# Environment: Python, we only need the algorithm, later will deploy on pkpy

# NOTICE:  all the function mixed up x & y axis, but that doesn't matter..if everybody is wrong, everybody is right

import random
import time
from array2d import array2d
from linalg import vec2i
from dataclasses import dataclass


# mob_database = [("👾","．"),
#                 ("💀", "．"),
#                 ("👽", "．", "💦"),
#                 ("👻", "💦")]

mob_terrain : dict[str, list[str]] = {
    "👾": ["．"],
    "💀": ["．"],
    "👽": ["．", "💦"],
    "👻": ["💦"]
}

mob_list = list(mob_terrain.keys())

@dataclass
class Mob:
    emoji: str
    num: int
    terrain: list[str]
    
def get_random_mob(mob_num_range:tuple[int,int] = (4,7)) -> Mob:
    """
    get a random kind of mob from the database\n
    @num_preset: (min, max) of the number of mobs\n
    """
    min_num, max_num = mob_num_range
    mob_num = random.randint(min_num, max_num)
    mob_choice = random.choice(mob_list)
    return Mob(mob_choice, mob_num, mob_terrain[mob_choice])

class Layer:
    """
    Creates copy of map.\n
    Including original map and cells ocuupied by mobs\n
    """

    terrain: array2d
    occupied: array2d

    def __init__(self, map: array2d) -> None:
        self.terrain = map.copy()
        self.occupied = array2d(map.width, map.height, 0)


def generate_noise(x: int, y: int, prob: int, seed: float | None = None) -> array2d:
    randcls = random.Random()
    if seed is None:
        seed = int(time.time())
    randcls.seed(seed)
    map = array2d(x, y)
    map.apply_(lambda x: "💦" if randcls.randint(1, 100) <= prob else "．")
    return map

def border_assist(map: array2d, kernelf1: array2d, kernelf2:array2d, f1:int, f2:int) -> array2d:
    """
    assist function for postfix_noise\n
    Make sure the border of the map is wall\n
    """
    w = map.width
    h = map.height
    retmap = array2d(w, h, 1)#a temporary map with all 1 inside
    f1cnt = map.convolve(kernelf1, 0)
    if f2 != 0:
        f2cnt = map.convolve(kernelf2, 0)
    else:
        f2cnt = array2d(w, h, 0)
    for y in range(1, h-1):
        for x in range(1, w-1):
            coordinate = vec2i(x, y)
            f1val = f1cnt[coordinate]
            f2val = f2cnt[coordinate]
            if f1val >= f1 or (f2 != 0 and f2val <= f2):
                retmap[coordinate] = 1
            else:
                retmap[coordinate] = 0
    return retmap

def postfix_noise(map: array2d, loop: int, f1: int, f2: int = 0) -> array2d:
    """
    process the impulse noise map\n
    The function loops 'loop' times, and replace the cell judging with threshold f1 and f2.\n
    """
    w = map.width
    h = map.height
    nummap = map.map(lambda x: 1 if x == "💦" else 0)
    kernelf1 = array2d(3, 3, 1)
    kernelf2 = array2d(5, 5, 1)
    kernelf2[0, 0] = kernelf2[4, 0] = kernelf2[0, 4] = kernelf2[4, 4] = 0  # exclude the corners
    nummap = border_assist(nummap, kernelf1, kernelf2, f1, f2)
    for _ in range(loop-1):
        f1cnt = nummap.convolve(kernelf1, 0)
        if f2 != 0:
            f2cnt = nummap.convolve(kernelf2, 0)
        else:
            f2cnt = array2d(w, h, 0)
        for y in range(1, h-1):
            for x in range(1, w-1):
                coordinate = vec2i(x, y)
                f1val = f1cnt[coordinate]
                f2val = f2cnt[coordinate]
                if f1val >= f1 or (f2 != 0 and f2val <= f2):
                    nummap[coordinate] = 1
                else:
                    nummap[coordinate] = 0
    return nummap.map(lambda x: "💦" if x == 1 else "．")
    # return nummap


def flood_fill_wall(map: array2d) -> tuple[array2d, list, list]:
    """
    floods the map and replace where it walks with wall\n
    @Return: (vis, scc_emoji, scc_area), vis with not 0 index is not empty
    """
    toreplace = map[vec2i(0,0)]
    assert toreplace == "💦"
    vis, visnum = map.get_connected_components(toreplace, "von Neumann")
    for _xy, val in vis:
        if val == 1:
            map[_xy] = "🧱"
    scc_emoji = ["．", "🧱"]
    for _ in range(visnum - 1):
        scc_emoji.append("💦")
    scc_area = []
    for cnt in range(visnum+1):
        scc_area.append(vis.count(cnt))
    return (vis, scc_emoji, scc_area)


def select_valid_pos(
    layer: Layer,
    scc: array2d,
    scc_emoji: list,
    scc_cnt: list,
    mob: Mob,
    myscore: float
) -> tuple[int, int, tuple[int, int, int, int]]:
    """
    select a valid place for the mob horde.\n
    @Return: the center position and the border coordinate of the rectangle\n
    """
    w = scc.width
    h = scc.height
    while True:
        #find a random center position and evaluate it's nearby cells by 'score' func
        anchorx = random.randint(0, w - 1)
        anchory = random.randint(0, h - 1)
        if scc_emoji[scc[anchorx, anchory]] in mob.terrain and scc_cnt[scc[anchorx, anchory]] >= mob.num:
            scores = score(layer, mob, anchorx, anchory, myscore)
            return (anchorx, anchory, scores)
        
def score(layer:Layer, mob:Mob, x:int, y:int, score:float) -> tuple[int, int, int, int]:
    """
    The score function which controls the distribution of mob hordes,
    returns the border coord of the horde\n
    @myscore: size of horde, >0, and better not bigger than 1\n
    @return: upleft(x,y) and downright(x,y)
    """
    assert score > 0
    borderx = layer.terrain.width
    bordery = layer.terrain.height
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
                if (layer.terrain[tx,ty] in mob.terrain and layer.occupied[tx,ty] == 0):
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

def spawn_splash(map: array2d, layer:Layer, i:int, mob:Mob, x:int, y:int, rect:tuple[int,int,int,int], splash:float, center:bool = True) -> None:
    """
    generate horde sample\n
    @i: the index of horde, should be i + 1 of the current loop, for layer.Occupied propose\n
    @x: anchor x, the center of horde\n
    @y: anchor y, the center of horde\n
    @rect: the border of horde\n
    @splash: the splash range of horde, close to 0 will be more concentrate\n
    @center: True will generate around the (x,y)\n
    """
    upx, upy, downx, downy = rect
    
        
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
                if (layer.terrain[xx,yy] in current_mob.terrain and layer.occupied[xx,yy] == 0):
                    layer.occupied[xx,yy] = i + 1
                    mymap[xx,yy] = current_mob.emoji
        print("*" * 40, i)
        for xy, val in mymap:
            print(val, end=" ")
            if xy.x == mymap.width - 1:
                print("\n")

    
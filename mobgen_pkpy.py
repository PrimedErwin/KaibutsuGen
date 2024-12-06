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
    @set occupied = -1 if generated mob on it
    """

    terrain: array2d[str]
    occupied: array2d[int]

    def __init__(self, mymap: array2d[str]) -> None:
        self.terrain = mymap.copy()
        self.occupied = array2d(mymap.width, mymap.height, 0)


def generate_noise(x: int, y: int, prob: int, seed: float | None = None) -> array2d[str]:
    randcls = random.Random()
    if seed is None:
        seed = int(time.time())
    randcls.seed(seed)
    mymap = array2d(x, y)
    mymap.apply_(lambda x: "💦" if randcls.randint(1, 100) <= prob else "．")
    return mymap

def _border_assist(mymap: array2d[int], kernelf1: array2d[int], kernelf2:array2d[int], f1:int, f2:int) -> array2d[int]:
    """
    assist function for postfix_noise\n
    Make sure the border of the map is wall\n
    """
    w = mymap.width
    h = mymap.height
    retmap = array2d(w, h, 1)#a temporary map with all 1 inside
    f1cnt = mymap.convolve(kernelf1, 0)
    if f2 != 0:
        f2cnt = mymap.convolve(kernelf2, 0)
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

def postfix_noise(mymap: array2d[str], loop: int, f1: int, f2: int = 0) -> array2d[str]:
    """
    process the impulse noise map\n
    The function loops 'loop' times, and replace the cell judging with threshold f1 and f2.\n
    """
    w = mymap.width
    h = mymap.height
    nummap = mymap.map(lambda x: 1 if x == "💦" else 0)
    #convolution kernels
    kernelf1 = array2d(3, 3, 1)
    kernelf2 = array2d(5, 5, 1)
    kernelf2[0, 0] = kernelf2[4, 0] = kernelf2[0, 4] = kernelf2[4, 4] = 0  # exclude the corners
    nummap = _border_assist(nummap, kernelf1, kernelf2, f1, f2)
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


def flood_fill_wall(mymap: array2d[str]) -> tuple[array2d[int], list, list]:
    """
    floods the map and replace where it walks with wall\n
    @Return: (vis, scc_emoji, scc_area), vis with not 0 index is not empty
    """
    toreplace = mymap[vec2i(0,0)]
    assert toreplace == "💦"
    vis, visnum = mymap.get_connected_components(toreplace, "von Neumann")
    for _xy, val in vis:
        if val == 1:
            mymap[_xy] = "🧱"
    scc_emoji = ["．", "🧱"]
    for _ in range(visnum - 1):
        scc_emoji.append("💦")
    scc_area = []
    for cnt in range(visnum+1):
        scc_area.append(vis.count(cnt))
    return (vis, scc_emoji, scc_area)


def select_valid_pos(
    layer: Layer,
    scc: array2d[int],
    scc_emoji: list,
    scc_area: list,
    mob: Mob,
    myscore: float
) -> tuple[int, int, tuple[int, int, int, int]]:
    """
    select a valid area for the mob horde. Border points are INCLUDED\n
    @Return: the center position and the border coordinate of the rectangle\n
    """
    w = scc.width
    h = scc.height
    while True:
        #find a random center position and evaluate it's nearby cells by '_score' func
        anchorx = random.randint(0, w - 1)
        anchory = random.randint(0, h - 1)
        if scc_emoji[scc[anchorx, anchory]] in mob.terrain and scc_area[scc[anchorx, anchory]] >= mob.num:
            scores = _score(layer, mob, anchorx, anchory, myscore)
            return (anchorx, anchory, scores)
        
def _score(layer:Layer, mob:Mob, x:int, y:int, score:float) -> tuple[int, int, int, int]:
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
        for _x in range(upx, downx + 1):#Border points are INCLUDED, so downx + 1 here
            for _y in range(upy, downy + 1):
                if (layer.terrain[_x, _y] in mob.terrain and layer.occupied[_x ,_y] == 0):
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

def _dist_unsqrt(coord1: vec2i, coord2: vec2i) -> int:
    """
    calculate the distance between coord1 and coord2, not sqrted\n
    """
    return abs(coord1.x-coord2.x)**2 + abs(coord1.y-coord2.y)**2

def _splash_factor_assist(current_pos:vec2i, center_pos:vec2i, splash_factor: float, range: int, basic_prob: int) -> bool:
    """
    return True if here can generate a mob\n
    """
    dist = _dist_unsqrt(current_pos, center_pos)
    
    return False
    

def spawn_splash(mymap: array2d[str], layer:Layer, i:int, mob:Mob, x:int, y:int, rect:tuple[int,int,int,int], splash_factor:float) -> None:
    """
    generate horde sample\n
    factor = (0,1) 0=closer
    - TODO
    Imagine a largest circle on the rect, which has its center on (x,y). 
    As we know the basic param of a circle is d and r (d=2r), so with the
    splash_factor, we have r_new = r * splash_factor.
    Thus we have a new circle. Points in the circle have a high probablity 
    to generate mobs, while those outside have a lower probablity. 
    
    But the probablity cannot be set to a step func, which would lead
    to ridiculous result.
    
    The probability func should be: input factor, range, return prob
    factor close to 1, almost equal prob within the range
    factor close to 0, decreasing prob along with range
    """
    upx, upy, downx, downy = rect
    #calculate the maximum distance from the center
    max_x = max(abs(x - upx), abs(x - downx))
    max_y = max(abs(y - upy), abs(y - downy))
    max_range = max_x**2 + max_y**2
    new_range = int(max_range * splash_factor)
    center_pos = vec2i(x, y)
    #calculate the basic probablity
    area = abs(upx-downx)*abs(upy-downy)
    basic_prob = int(mob.num/area*100)
    
    generated_mob_cnt = 0
    
    for _y in range(upy, downy + 1):
        for _x in range(upx, downx + 1):
            coord = vec2i(_x, _y)
            if layer.occupied == i and layer.terrain[coord] in mob.terrain and generated_mob_cnt < mob.num:
                #valid terrain and not occupied by other mobs
                result = _splash_factor_assist(coord, center_pos, splash_factor, new_range, basic_prob)
                if result:
                    layer.occupied[coord] = -1
                    mymap[coord] = mob.emoji
                    generated_mob_cnt += 1
    

if __name__ == "__main__":
    mymap = generate_noise(50, 30, 40, 2024)
    mymap = postfix_noise(mymap, 4, 5, 1)
    mymap = postfix_noise(mymap, 3, 5)
    scc, scc_emoji, scc_area = flood_fill_wall(mymap)
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
        x,y, rect = select_valid_pos(layer, scc, scc_emoji, scc_area, current_mob, 0.3)
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

    
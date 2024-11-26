# This file generates mobs and maybe a simple map(default map is just a rectangel)
# mobs gather like bacterias, and for notation, # is wall, . is empty, */$/@ et cetra are mobs

# Environment: Python, we only need the algorithm, later will deploy on pkpy

# NOTICE:  all the function mixed up x & y axis, but that doesn't matter..if everybody is wrong, everybody is right

import random
import time
import queue


class Mob:
    """
    Include simple map gen, different ways to gen mobs\n
    @Param: mob_kind, mob_list, mob_preset\n
    @mob_list: current kinds of mobs can be generated
    """

    mob_kind: int
    mob_list: list
    mob_preset: list

    def __init__(self, mob_kind: int) -> None:
        """mob_kind = count of mobs' kind <= 6"""
        self.mob_preset = ["👻", "👾", "💀", "👽", "&", "*"]
        self.mob_kind = mob_kind
        self.mob_list = []
        for i in range(mob_kind):
            self.mob_list.append(self.mob_preset[i])

    @staticmethod
    def generate_map(x: int, y: int) -> list:
        """generate empty map with x * y"""
        map = []
        for i in range(x):
            row = []
            for j in range(y):
                if i == 0 or i == x - 1 or j == 0 or j == y - 1:
                    row.append("＃")
                else:
                    row.append("．")
            map.append(row)
        return map

    @staticmethod
    def generate_noise(x: int, y: int, prob: int) -> list:
        """generate random map with x * y\n
        @prob: the probability of a tile being a wall
        """
        randcls = random.Random()
        randcls.seed(2024)
        map = [[""] * y for _ in range(x)]
        for i in range(x):
            for j in range(y):
                if randcls.randint(1, 100) <= prob:
                    map[i][j] = "💦"
                else:
                    map[i][j] = "．"
        return map

    @staticmethod
    def postfx_noise(map: list, loop: int, f1: int, f2: int = 0) -> list:
        """
        process the impulse noise map\n
        @map: the noise map\n
        @loop: times of postfx\n
        @f1: threshold of tiles being walls with 1 step, != 0\n
        @f2: threshold of tiles being walls with 2 steps, can be 0\n
        """
        x = len(map)
        y = len(map[0])
        all_wall = [["💦"] * y for _ in range(x)]
        # f1_cnt = [[0]*y for _ in range(x)]
        # f2_cnt = [[0]*y for _ in range(x)]
        for _ in range(loop):
            for i in range(1, x - 1):
                for j in range(1, y - 1):
                    f1_cnt = 0
                    f2_cnt = 0
                    for dx in range(-1, 2):
                        for dy in range(-1, 2):
                            if map[i + dx][j + dy] == "💦":
                                f1_cnt += 1
                    if f2 != 0:
                        for dx in range(-2, 3):
                            for dy in range(-2, 3):
                                if (
                                    0 <= i + dx < x
                                    and 0 <= j + dy < y
                                    and map[i + dx][j + dy] == "💦"
                                    and abs(dx) + abs(dy) < 4
                                ):
                                    f2_cnt += 1
                    if f1_cnt >= f1 or (f2 != 0 and f2_cnt <= f2):
                        all_wall[i][j] = "💦"
                    else:
                        all_wall[i][j] = "．"
            for i in range(x):
                for j in range(y):
                    map[i][j] = all_wall[i][j]
        return map

    @staticmethod
    def flood_fill_wall(
        postfx_map: list, x: int, y: int, anchorx: int, anchory: int
    ) -> None:
        """
        turn the wall of the border into air
        """
        if postfx_map[anchorx][anchory] != "💦":
            return None
        vis = [[0] * y for _ in range(x)]
        direc = list(zip([0, 0, 1, -1], [1, -1, 0, 0]))
        myqueue = queue.Queue()
        myqueue.put((anchorx, anchory))
        vis[anchorx][anchory] = 1
        while myqueue.empty() == False:
            current = myqueue.get()
            postfx_map[current[0]][current[1]] = "🧱"
            for i in range(4):
                newx = direc[i][0] + current[0]
                newy = direc[i][1] + current[1]
                if (
                    0 <= newx < x
                    and 0 <= newy < y
                    and vis[newx][newy] == 0
                    and postfx_map[newx][newy] == "💦"
                ):
                    myqueue.put((newx, newy))
                    vis[newx][newy] = 1

    def generate_mobs_cluster(
        self, map: list, num_cluster: int, cluster_size: int, num_mob: int
    ) -> list:
        """
        divide map into clusters + generate num_cluster in each cluster\n
        so u will get at most num_cluster * num_mob mobs\n
        @cluster_size: the final cluster is cluster_size * 2 * cluster_size * 2
        """
        x = len(map)
        y = len(map[0])
        if x - cluster_size * 2 <= 0 or y - cluster_size * 2 <= 0:
            print("Too large cluster size")
            return map
        for _ in range(num_cluster):
            cluster_x = random.randint(1, x - cluster_size - 1)
            cluster_y = random.randint(1, y - cluster_size - 1)
            i = random.randint(0, self.mob_kind - 1)
            mob_kind = self.mob_list[i]
            for _ in range(num_mob):
                mob_x = cluster_x + random.randint(-cluster_size, cluster_size)
                mob_y = cluster_y + random.randint(-cluster_size, cluster_size)
                if (
                    0 < mob_x < x - 1
                    and 0 < mob_y < y - 1
                    and map[mob_x][mob_y] == "．"
                ):
                    map[mob_x][mob_y] = mob_kind
        return map


class mobBase:
    name: str
    emoji: str
    terrain: list
    boss: dict
    squad: dict
    scout: dict

    def __init__(self) -> None:
        self.name = ""
        self.emoji = ""
        self.terrain = []
        self.boss = {"condition": 1}  # condition is reserved for.. is_boss_room
        self.squad = {"condition": 0, "num": (4, 7)}
        self.scout = {"condition": 0, "num": (1, 3)}

    def getnum(self, mobname: str) -> int:
        """
        getnum will return a random number of preset mobs\n
        """
        randcls = random.Random()
        randcls.seed(time.time())
        try:
            if mobname == "boss":
                return 1
            elif mobname == "squad":
                return randcls.randint(self.squad["num"][0], self.squad["num"][1])
            elif mobname == "scout":
                return randcls.randint(self.scout["num"][0], self.scout["num"][1])
            else:
                raise ValueError
        except ValueError:
            print("Invalid mobname")
            raise NotImplemented


class mobMonst(mobBase):
    def __init__(self) -> None:
        super().__init__()
        self.name = "id_monst"
        self.emoji = "👾"
        self.terrain = ["．"]


class mobSkull(mobBase):
    def __init__(self) -> None:
        super().__init__()
        self.name = "id_skull"
        self.emoji = "💀"
        self.terrain = ["．"]


class mobAlien(mobBase):
    def __init__(self) -> None:
        super().__init__()
        self.name = "id_alien"
        self.emoji = "👽"
        self.terrain = ["．", "💦"]


class mobGhost(mobBase):
    def __init__(self) -> None:
        super().__init__()
        self.name = "id_ghost"
        self.emoji = "👻"
        self.terrain = ["💦"]


class PresetMob:
    """
    Presets for mobs, including: \n
    dotMob: "👾", "💀", "👽"\n
    sharpMob: "👻", "👽"\n
    dot = ".", sharp = "💦"
    """

    dotMob: list
    sharpMob: list
    id_monst: mobMonst
    id_skull: mobSkull
    id_alien: mobAlien
    id_ghost: mobGhost

    def __init__(self) -> None:
        id_monst = mobMonst()
        id_skull = mobSkull()
        id_alien = mobAlien()
        id_ghost = mobGhost()
        self.dotMob = [id_monst, id_skull, id_alien]
        self.sharpMob = [id_ghost, id_alien]

    def choose_preset(self, terrain: str) -> mobBase:
        """choose a preset randomly due to the terrain"""
        # randcls = random.Random()
        # randcls.seed(time.time())
        try:
            if terrain == "．":
                return random.choice(self.dotMob)
            elif terrain == "💦":
                return random.choice(self.sharpMob)
            else:
                raise ValueError
        except ValueError:
            print("Invalid terrain")
            raise NotImplemented


class Layer:
    """
    Creates copy of map.\n
    @OriginTerrain: original terrain without mobs\n
    @Occupied: the cells occupied by mobs, cannot generate mobs again on them
    """

    OriginTerrain: list
    Occupied: list

    def __init__(self, map: list) -> None:
        x = len(map)
        y = len(map[0])
        self.OriginTerrain = list(list(map[i]) for i in range(x))
        self.Occupied = [[0] * y for _ in range(x)]


# compute SCC, will be replaced by array2d.get_connected_components in pkpy
def get_connected_components(map: list) -> tuple[list, list, list]:
    """
    @map: the postfx map\n
    @tuple[list, list]: the scc map, scc list, scc emoji\n
    """
    x = len(map)
    y = len(map[0])
    vis = [[0] * y for _ in range(x)]
    scc_index = 1
    scc_list = []
    scc_emoji = []
    myqueue = queue.Queue()
    direc = list(zip([0, 0, 1, -1], [1, -1, 0, 0]))
    for _x in range(x):
        for _y in range(y):
            if vis[_x][_y] != 0:
                continue
            myqueue.put((_x, _y))
            vis[_x][_y] = scc_index
            scc_emoji.append(map[_x][_y])
            scc_list.append(0)
            while myqueue.empty() == False:
                scc_list[-1] += 1
                current = myqueue.get()
                for i in range(4):
                    newx = direc[i][0] + current[0]
                    newy = direc[i][1] + current[1]
                    if (
                        0 <= newx < x
                        and 0 <= newy < y
                        and vis[newx][newy] == 0
                        and map[newx][newy] == map[current[0]][current[1]]
                    ):
                        myqueue.put((newx, newy))
                        vis[newx][newy] = scc_index
            scc_index += 1
    return (vis, scc_list, scc_emoji)


def select_valid_pos(
    layer: Layer, scc: tuple[list, list, list], mob_num: int, mob: mobBase
) -> tuple[int, int]:
    """
    @layer: Layer class
    @scc: return of get_connected_components
    @mob_num: the number needed for chosen mob
    @mob: mobBase class
    """
    x = len(layer.OriginTerrain)
    y = len(layer.OriginTerrain[0])
    while True:
        anchorx = random.randint(0, x - 1)
        anchory = random.randint(0, y - 1)
        if (
            scc[2][scc[0][anchorx][anchory] - 1] in mob.terrain
            and scc[1][scc[0][anchorx][anchory] - 1] > mob_num
            and layer.Occupied[anchorx][anchory] == 0
        ):
            return (anchorx, anchory)


if __name__ == "__main__":
    # mymob = Mob(6)
    # map = Mob.generate_map(20, 40)
    # map_with_mobs = mymob.generate_mobs_cluster(map, 5, 2, 9)

    # for row in map_with_mobs:
    #     print("".join(row))
    times = time.perf_counter()
    noise_map = Mob.generate_noise(30, 50, 40)
    postfx_map = Mob.postfx_noise(noise_map, 4, 5, 1)
    postfx_map = Mob.postfx_noise(postfx_map, 3, 5, 0)
    for row in postfx_map:
        print("".join(row))
    print("\n\n\n\n")
    Mob.flood_fill_wall(postfx_map, len(postfx_map), len(postfx_map[0]), 0, 0)
    for row in postfx_map:
        print("".join(row))
    print(time.perf_counter() - times)

    scc = get_connected_components(postfx_map)
    for row in scc[0]:
        for col in row:
            print("{:3d}".format(col), end="")
        print("\n")
    print(scc[1])
    print(scc[2])

    initMob = PresetMob()
    # auto = initMob.choose_preset("．")
    # print(auto.emoji, auto.getnum("squad"))
    layer = Layer(postfx_map)
    for i in range(30):
        chosen = initMob.choose_preset(random.choice(["．", "💦"]))
        chosen_type = random.choice(["squad", "scout"])
        chosen_num = chosen.getnum(chosen_type)
        x, y = select_valid_pos(layer, scc, chosen_num, chosen)
        # TODO: add minions around leader, and fill the occupied layer

        postfx_map[x][y] = chosen.emoji
        layer.Occupied[x][y] = 1

    for row in postfx_map:
        print("".join(row))

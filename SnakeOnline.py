from copy import copy
import typing
import lib.lib as lib
from random import randint

# file type -----------------------

localhost = lib.localhost
localport = 8000
socket_type = input("Input you type (s | c) --> ")
input_host = input("Input you host --> ")

host = localhost if input_host == "" else input_host


input_port = input("Input you port --> ")
port = localport if input_port == "" else input_port

if socket_type == "s":
    max_clients = int(input("Max clients --> "))
    map_size = int(input("Map size --> "))
else:
    id = randint(0, 999999999999)
    name = input("You name --> ")
    print(id)


# file type -----------------------

# game clases ---------------------


class Grid:
    def __init__(self, size: typing.Tuple[int, int]) -> None:
        self._size = size
        self._apples = []
        self._max_apples = self._size[0]
        self.timer = 0

    def generate(self):
        self.timer += 1
        if self.timer % 50 == 0:
            if len(self._apples) < self._max_apples:
                pos = [randint(0, self._size[0] - 1), randint(0, self._size[1] - 1)]
                self._apples.append(pos)
        if len(self._apples) > self._max_apples:
            self._apples = self._apples[: self._max_apples]


class Snake:
    def __init__(self, grid_: Grid, id, name) -> None:
        self._grid = grid_
        self._id = id
        self.name = name
        self.pos = [
            randint(0, self._grid._size[0] - 1),
            randint(0, self._grid._size[1] - 1),
        ]
        self.color = lib.Color.random().rgb
        self.napr = [False, False, False, False]
        self.time = 0

        self.speed = [0, 0]
        self.lenght = 20
        self.segments = []
        self.enemy_segments = []
        self.score = 0

    def setNapr(self, napr):
        self.napr = napr

    def Update(self, GRID):
        if self.napr[0] == True and self.speed != [0, 1]:
            self.speed = [0, -1]
        if self.napr[1] == True and self.speed != [1, 0]:
            self.speed = [-1, 0]
        if self.napr[2] == True and self.speed != [0, -1]:
            self.speed = [0, 1]
        if self.napr[3] == True and self.speed != [-1, 0]:
            self.speed = [1, 0]

        self.time += 1
        if self.time % 5 == 0:
            self.pos[0] += self.speed[0]
            self.pos[1] += self.speed[1]

        self.pos[0] = self._grid._size[0] - 1 if self.pos[0] < 0 else self.pos[0]
        self.pos[0] = 0 if self.pos[0] == self._grid._size[0] else self.pos[0]

        self.pos[1] = self._grid._size[1] - 1 if self.pos[1] < 0 else self.pos[1]
        self.pos[1] = 0 if self.pos[1] == self._grid._size[1] else self.pos[1]

        for i in range(len(GRID._apples)):
            if self.pos == GRID._apples[i]:
                self.lenght += 1
                self.score += 1
                del GRID._apples[i]
                break
        self.score = max(self.score, 0)
        if self.time % 5 == 0:
            self.segments.append(copy(self.pos))
            self.segments = self.segments[-self.lenght :]

        for anysnake in snakes_list:
            if anysnake._id != self._id:
                if anysnake.pos in self.segments:
                    index = self.segments.index(anysnake.pos)

                    if index != 0:
                        eatt = self.segments[: -(len(self.segments) - index)]
                        self.lenght = len(self.segments) - index
                        self._grid._apples.extend(eatt)
                        self.score -= len(eatt)

                    break


snakes_list: typing.Tuple[Snake] = []


# game clases ---------------------

# server --------------------------

server: lib.Server = None
inputs_pack = []


def start_server():
    global server
    server = lib.Server(port_=int(port), host_=host, max_client_=max_clients)
    GRID = Grid([map_size, map_size])
    _wait_con(GRID)

    _sand_packet_snakes()
    _sand_packet_map(GRID)

    _recv_inputs()
    _clients_update(GRID)
    _generate_apples(GRID)


@lib.NewProcess
def _wait_con(GRID):
    while server.max_connected:
        server.waitcon(0.05)
        if server.clientcon:
            iddata = server._end_conn_client.recv(1024).decode()
            iddata = lib.string_to_list(iddata)
            print(iddata)
            snakes_list.append(Snake(GRID, [iddata[1][0]], iddata[1][1]))


def create_packet():
    all_data = []
    for snake in snakes_list:
        data = [
            snake.color,
            snake.pos,
            snake.segments,
            snake._id,
            snake.score,
            snake.name,
        ]
        all_data.append(data)
    return all_data


@lib.NewProcess
def _sand_packet_snakes():
    while True:
        lib.socket_sleep(0.02)
        packet = create_packet()
        pack = lib.packing(packet, "snakes")
        server.send_packet(pack)


@lib.NewProcess
def _generate_apples(GRID):
    while True:
        lib.socket_sleep(0.1)
        GRID.generate()


@lib.NewProcess
def _sand_packet_map(GRID):
    while True:
        lib.socket_sleep(0.02)
        packet = [map_size, map_size, GRID._apples]
        pack = lib.packing(packet, "map")
        server.send_packet(pack)


@lib.NewProcess
def _recv_inputs():
    global inputs_pack
    while True:
        lib.socket_sleep(0.01)
        try:
            inputs = server.recv_packet(2048)
            inputs_pack = inputs
        except:
            ...


@lib.NewProcess
def _clients_update(GRID):
    while True:
        lib.socket_sleep(0.01)

        for snake in snakes_list:
            for input in inputs_pack:
                if snake._id[0] == input[1][0]:
                    snake.setNapr(input[1][1:])
            snake.Update(GRID)


# server --------------------------

# clent ---------------------------
client: lib.Client = None
packet_snakes = []
packet_map = []
packet_apples = []
global_pos = [0, 0]
block_size = 20
my_color = (0, 0, 0)

snake_color = "white"
score_text = lib.Text("Arial", 70, bold=True)
snake_name_text = lib.Text("Arial", 20, bold=True)

lider_text = lib.Text("Arial", 15)


score = 0

cam_x_ = 0
cam_y_ = 0


def camera_(pers_pos, center_pos, delta=0.05):
    global cam_x_, cam_y_
    cam_x_ = (center_pos[0] - pers_pos[0]) * delta
    cam_y_ = (center_pos[1] - pers_pos[1]) * delta


def start_client():
    global client
    client = lib.Client(int(port), host)
    client.send_packet(lib.packing([id, name], "id"))

    App()


@lib.NewProcess
def _recv_packet():
    global packet_snakes, packet_map, packet_apples
    while True:
        lib.socket_sleep(0.01)
        packet = client.recv_packet(1024 * 10)
        try:
            packet = lib.string_to_list(packet)

            _give_pack_nakes = lib.packet_with_name(packet, "snakes")
            if _give_pack_nakes is not None:
                packet_snakes = _give_pack_nakes

            _give_pack_nakes = lib.packet_with_name(packet, "map")
            if _give_pack_nakes is not None:
                packet_map = _give_pack_nakes[:2]
                packet_apples = _give_pack_nakes[2]

            _give_pack_nakes = lib.packet_with_name(packet, "apples")
            if _give_pack_nakes is not None:
                packet_apples = _give_pack_nakes
        except:
            ...


def create_input_pack():
    w = lib.Keyboard.key_pressed_win("w")
    a = lib.Keyboard.key_pressed_win("a")
    s = lib.Keyboard.key_pressed_win("s")
    d = lib.Keyboard.key_pressed_win("d")

    pack = lib.packing([id, w, a, s, d], "napr_input")
    return pack


@lib.NewProcess
def _send_packet_inputs():
    while True:
        lib.socket_sleep(0.02)
        pack = create_input_pack()
        client.send_packet(pack)


def draw_map(win: lib.Window):
    global global_pos

    [
        lib.Draw.draw_vline(
            win(),
            global_pos[0] + x * block_size,
            global_pos[1],
            global_pos[1] + packet_map[1] * block_size,
            1,
            color=(50, 50, 50),
        )
        for x in range(packet_map[0] + 1)
    ]
    [
        lib.Draw.draw_hline(
            win(),
            global_pos[1] + x * block_size,
            global_pos[0],
            global_pos[0] + packet_map[0] * block_size,
            1,
            color=(50, 50, 50),
        )
        for x in range(packet_map[1] + 1)
    ]


def draw_apples(win: lib.Window):
    for apple in packet_apples:
        pos = [
            global_pos[0] + apple[0] * block_size,
            global_pos[1] + apple[1] * block_size,
        ]
        lib.Draw.draw_rect(win(), pos, [block_size], "red")


def draw_snakes(win: lib.Window):
    global score, snake_color, my_color
    for snake in packet_snakes:
        snake_color = snake[0]

        for segpos in snake[2]:
            snake_pos = [
                global_pos[0] + segpos[0] * block_size,
                global_pos[1] + segpos[1] * block_size,
            ]

            lib.Draw.draw_rect(win(), snake_pos, [block_size], snake_color)

        snake_name_text.draw(
            win(),
            [
                snake[1][0] * block_size + block_size / 2 + global_pos[0] + 1,
                snake[1][1] * block_size - block_size + global_pos[1] + 1,
            ],
            True,
            str(snake[5]),
            "black",
        )
        snake_name_text.draw(
            win(),
            [
                snake[1][0] * block_size + block_size / 2 + global_pos[0],
                snake[1][1] * block_size - block_size + global_pos[1],
            ],
            True,
            str(snake[5]),
            snake_color,
        )

        if snake[3][0] == id:
            camera_(
                [
                    snake[1][0] * block_size + global_pos[0],
                    snake[1][1] * block_size + global_pos[1],
                ],
                win.center,
                0.05,
            )
            score = snake[4]
            my_color = snake[0]

    # print(cam_x_, cam_y_)
    global_pos[0] += cam_x_
    global_pos[1] += cam_y_


def draw_lider_board(win: lib.Window):
    player_names_and_scores = list(map(lambda elem: [elem[5], elem[4]], packet_snakes))
    player_names_and_scores = sorted(
        player_names_and_scores, key=lambda elem: elem[1], reverse=True
    )
    for i in range(len(player_names_and_scores)):
        n = player_names_and_scores[i][0]
        s = player_names_and_scores[i][1]
        if n == name:
            color = "orange"
        else:
            color = "gray"
        lider_text.draw(win(), [10, 10 + i * 17], text=n, color=color)
        lider_text.draw(win(), [100, 10 + i * 17], text=str(s), color=color)


def draw_ui(win: lib.Window):
    score_text.draw(win(), [win.center[0], 50], True, str(score), my_color)


def App():
    win = lib.Window([1200, 800], flag=lib.Flags.win_resize)
    _recv_packet()
    _send_packet_inputs()

    while win.update(base_color="black"):
        if len(packet_map) == 2:
            draw_map(win)
        draw_apples(win)
        draw_snakes(win)
        draw_ui(win)
        draw_lider_board(win)


# clent ---------------------------


# logic ---------------------------
if socket_type == "s":
    start_server()
elif socket_type == "c":
    start_client()


# logic ---------------------------

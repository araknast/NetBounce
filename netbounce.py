#!/usr/bin/env python3
# this program requires python >= 3.8 because for some reason it took 
# the tkinter devs 19 years to implement canvas.moveto

from tkinter import *
import random
import time
import socket

tk = Tk()
tk.title("Game")
tk.resizable(0, 0)
tk.wm_attributes("-topmost", 1)
canvas = Canvas(tk, width=500, height=400, bd=0, highlightthickness=0)
canvas.create_line(0, 200, 500, 200, dash=(5, 2))
canvas.pack()
tk.update()


class Scoreboard:
    def __init__(self, canvas, players = ["",""]):
        self.score: list = [0, 0] # opponent score is first for rendering reasons
        self.players = players
        self.canvas = canvas
        self.canvas_height = self.canvas.winfo_height()
        self.canvas_width = self.canvas.winfo_width()
        self.text = str(self.score).strip("][").replace(", ", "\n")
        self.id = canvas.create_text(
            self.canvas_width / 2, self.canvas_height / 2, text=self.text
        )
        self.player_display = canvas.create_text(
            self.canvas_width / 2, self.canvas_height / 2, text=""
        )
        
    def add(self, opponent: bool = False):
        if opponent:
            self.score[0] += 1
        else:
            self.score[1] += 1

    def draw(self):
        self.text = str(self.score).strip("][").replace(", ", "\n")
        self.player_names = str(self.players).strip("][").replace(", ", "\n\n\n\n").replace("'", "")
        self.canvas.itemconfigure(self.id, text=self.text)
        self.canvas.itemconfigure(self.player_display, text=self.player_names)



class Ball:
    def __init__(self, canvas, paddle, remote_paddle, color):
        self.canvas = canvas
        self.paddle = paddle
        self.remote_paddle = remote_paddle
        self.width = 10
        self.height = 10
        self.id = canvas.create_oval(self.width, self.height, 25, 25, fill=color)
        self.canvas.move(self.id, 245, 100)
        starts = [-3, -2, -1, 1, 2, 3]
        random.shuffle(starts)
        self.x = starts[0]
        self.y = -3
        self.canvas_height = self.canvas.winfo_height()
        self.canvas_width = self.canvas.winfo_width()

    def reset(self):
            self.canvas.moveto(
                self.id,
                self.canvas_width / 2,
                self.canvas_height / 2,
            )

    def draw(self, remote = False, coords = None):
        if remote:
            self.canvas.moveto(
                self.id,
                self.canvas_width - float(coords[0]) - self.width,
                self.canvas_height - float(coords[1]) - self.height,
            )
        else:
            pos = self.canvas.coords(self.id)
            self.canvas.move(self.id, self.x, self.y)
            if pos[1] <= 0:
                self.y = 3
            if pos[3] >= self.canvas_height:
                self.y = -3
            if self.hit_paddle(pos) == True:
                self.y = -3
            if self.hit_remote_paddle(pos) == True:
                self.y = 3
            if pos[0] <= 0:
                self.x = 3
            if pos[2] >= self.canvas_width:
                self.x = -3

    def hit_paddle(self, pos):
        paddle_pos = self.canvas.coords(self.paddle.id)
        if pos[2] >= paddle_pos[0] and pos[0] <= paddle_pos[2]:
            if pos[3] >= paddle_pos[1] and pos[3] <= paddle_pos[3]:
                return True

    def hit_remote_paddle(self, pos):
        paddle_pos = self.canvas.coords(self.remote_paddle.id)
        if pos[2] >= paddle_pos[0] and pos[0] <= paddle_pos[2]:
            if pos[1] <= paddle_pos[3] and pos[1] >= paddle_pos[1]:
                return True
        return False


class RemotePaddle:
    def __init__(self, canvas, color):
        self.canvas = canvas
        self.height = 10
        self.width = 100
        self.offset = 10
        self.id = self.canvas.create_rectangle(0, 0, self.width, self.height, fill=color)
        self.canvas.move(self.id, 0, self.offset)
        self.speed = 5
        self.x = 0
        self.canvas_width = self.canvas.winfo_width()

    def draw(self, xcoord):
        current_x = self.canvas.coords(self.id)[0]
        try:
            xcoord = float(xcoord)
        except ValueError:
            xcoord = current_x

        self.canvas.moveto(
            self.id, self.canvas_width - xcoord - self.width, self.offset
        )


class Paddle:
    def __init__(self, canvas, color):
        self.canvas = canvas
        self.id = canvas.create_rectangle(0, 0, 100, 10, fill=color)
        self.width = 100
        self.height = 10
        self.offset = 10
        self.canvas.move(
            self.id,
            canvas.winfo_reqwidth() - self.width,
            canvas.winfo_reqheight() - self.height - self.offset,
        )
        self.speed = 5
        self.x = 0
        self.canvas_width = self.canvas.winfo_width()
        self.canvas.bind_all("<KeyPress-Left>", self.turn_left)
        self.canvas.bind_all("<KeyPress-Right>", self.turn_right)
        self.canvas.bind_all("<KeyRelease-Left>", self.stop)
        self.canvas.bind_all("<KeyRelease-Right>", self.stop)

    def turn_left(self, evt):
        self.x = self.speed * -1

    def turn_right(self, evt):
        self.x = self.speed

    def stop(self, evt):
        if evt.keysym == "Right" and self.x > 0:
            self.x = 0
        if evt.keysym == "Left" and self.x < 0:
            self.x = 0

    def draw(self):
        self.canvas.move(self.id, self.x, 0)
        pos = self.canvas.coords(self.id)
        # print(self.canvas.coords(self.id))
        if pos[0] <= 0:
            self.canvas.move(self.id, (self.speed), 0)
        elif pos[2] >= self.canvas_width:
            self.canvas.move(self.id, (self.speed * -1), 0)


state = "NORMAL"
player_name = ""
player2 = False

paddle = Paddle(canvas, "blue")
opponent = RemotePaddle(canvas, "red")
ball = Ball(canvas, paddle, opponent, "red")
scoreboard = Scoreboard(canvas)
opponent.draw(100.0)

socket = socket.socket()
socket.connect(("localhost", 6969))

while 1:
    data = socket.recv(1024)
#    print(data)
    if state == "NORMAL":
        if data == b"GIVE NAME\r\n":
            player_name = input("What is your name? ")  # TODO: make these dialogue boxes
            socket.send(bytes(player_name + "\r\n", "utf-8"))
            continue
        elif data == b"NEED MORE PLAYERS\r\n":
            socket.send(b"STATE\r\n")
            print("Waiting for another player...")
            time.sleep(0.1)
            continue
        if b"PLAYER 2\r\n" in data:
            player2 = True
            socket.send(b"STATE\r\n")
            print("You are player 2")
        if b"PLAY\r\n" in data:
            state = "PLAY"
            socket.send(b"STATE\r\n")
    elif state == "PLAY":
        board_state = "{}|{}|{}|{}".format(
            str(canvas.coords(paddle.id)[0]), str(canvas.coords(ball.id)), str(scoreboard.score), player_name
        )

        socket.send(bytes(board_state + "\r\n", "utf-8"))
        if player2:
            try:
                ball.draw(
                    remote=True,
                    coords=data.decode("utf-8")
                    .strip()
                    .split("|")[1]
                    .strip("][")
                    .split(", "),
                )
                new_score = data.decode("utf-8").strip().split("|")[2].strip("][").split(", ")
                new_score = [ int(x) for x in new_score ]
                scoreboard.score = new_score
            except IndexError:
                ball.draw()
        else:
            ball.draw()

        try:
            opponent_name = data.decode("utf-8").strip().split("|")[3]
        except IndexError:
            opponent_name = ""
        scoreboard.players = [opponent_name, player_name]
        if canvas.coords(ball.id)[1] <= 0:
            scoreboard.add(opponent=False)
            ball.reset()
        elif canvas.coords(ball.id)[3] >= canvas.winfo_height():
            scoreboard.add(opponent=True)
            ball.reset()

        scoreboard.draw()
        paddle.draw()
        opponent.draw(xcoord=data.decode("utf-8").strip().split("|")[0])
        tk.update_idletasks()
        tk.update()
        time.sleep(0.01)

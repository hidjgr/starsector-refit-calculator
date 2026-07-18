import math
from core.api import list_weapons

SHIP_COUNTER = [0]

class Files:

    def __init__(self):
        self.game_path = None

    def set_game_path(self, game_path):
        self.game_path = game_path


class Fleet:

    def __init__(self, view, mouse):
        self.ships = []
        self.view = view
        self.mouse = mouse
        self.target_pos_x = 0
        self.target_pos_y = 0

        self.canvas = None
        self.center_x = None
        self.center_y = None

        self.target_ids = None

        self.focused_ship = None

        self.ship_stats_window = None
        self.weapon_list_window = None

        self.gui_callbacks = {}

    def update_fleet(self, event):
        for s in self.ships:
            s.update_ship(event)
        self.draw_target()

    def click(self, event):
        self.mouse[0][0] = event.x
        self.mouse[0][1] = event.y
        self.mouse[1][0] = event.x
        self.mouse[1][1] = event.y

        for s in self.ships:
            uhf = s.update_handle_focus(event)
            usf = s.update_slot_focus(event)
            if uhf or usf:
                self.focused_ship = s.ship_id
                self.update_window(self.ship_stats_window, s.show_stats)
                if usf:
                    self.update_window(self.weapon_list_window, s.show_weapons)

                
    def update_window(self, win, source):
        pos = win.master.yview()[0]
        for v in list(win.children.values()):
            v.destroy()
        source(lambda *args: self.gui_callbacks["list_item"](win, *args))
        win.master.after_idle(lambda: win.master.yview_moveto(pos))

    def right_click(self, event):
        self.target_pos_x =   event.x - self.center_x - self.view[0]
        self.target_pos_y = - event.y + self.center_y + self.view[1]
        self.draw_target()

    def draw_target(self):
        if self.target_ids:
            for i in self.target_ids:
                self.canvas.delete(i)

        id1 = self.canvas.create_line(
                self.target_pos_x - 5 + self.center_x + self.view[0],
              - self.target_pos_y - 5 + self.center_y + self.view[1],
                self.target_pos_x + 6 + self.center_x + self.view[0],
              - self.target_pos_y + 6 + self.center_y + self.view[1],
                fill="blue")
        id2 = self.canvas.create_line(
                self.target_pos_x - 5 + self.center_x + self.view[0],
              - self.target_pos_y + 5 + self.center_y + self.view[1],
                self.target_pos_x + 6 + self.center_x + self.view[0],
              - self.target_pos_y - 6 + self.center_y + self.view[1],
                fill="blue")

        self.target_ids = (id1, id2)
        
    def release(self, event):
        self.mouse[2][0] = event.x
        self.mouse[2][1] = event.y

        for s in self.ships:
            s.handle_focus = 0

    def drag(self, event):

        handle_dragged = False

        for s in self.ships:
            handle_dragged |= s.drag_handle(event)

        if handle_dragged:
            return

        self.view[0] += event.x - self.mouse[1][0]
        self.view[1] += event.y - self.mouse[1][1]

        self.update_fleet(event)

        self.mouse[1][0] = event.x
        self.mouse[1][1] = event.y


class Hullmod:
    
    def __init__(self):
        pass


class Ship:

    def __init__(self, ship_data, canvas, view, mouse, fleet):

        self.ship_id = SHIP_COUNTER[0]
        SHIP_COUNTER[0] += 1

        self.fleet = fleet

        self.data = ship_data
        self.canvas = canvas

        self.canvas_ship_id = None
        self.canvas_move_handle_id = None
        self.canvas_rotate_handle_id = None
                                             #sqr  #arc  #barc #sde1 #sde2
        self.weapon_canvas_ids = {k["id"] : [None, None, None, None, None] for k in self.data["weaponSlots"]}

        self.center_x = self.canvas.winfo_width()  // 2 - 1
        self.center_y = self.canvas.winfo_height() // 2 - 1

        self.view = view
        self.mouse = mouse

        self.pos_x = -view[0]
        self.pos_y = view[1]
        self.rot = 0

        self.handle_focus = 0

        self.weapons = {k["id"] : None for k in self.data["weaponSlots"]}

        self.focused_slot = None

        self.capacitors = 0
        self.vents = 0
        self.hullmods = []

        self.draw()

    def _translate(self, x, y):
        return (self.center_x + self.pos_x + x,
                self.center_y - self.pos_y - y)


    def _rotate_translate(self, x, y, rot=None):
        if not rot:
            rot = self.rot

        def norm(x, y):
            return (x**2 + y**2)**(1/2)
        def add_angle(x, y):
            return math.atan2(x, y) + rot
        def rotate_comp(x, y, f):
            return f(add_angle(x, y)) * norm(x, y)
        return (self.center_x + self.view[0] + self.pos_x + rotate_comp(x, -y, math.cos),
                self.center_y + self.view[1] - self.pos_y - rotate_comp(x, -y, math.sin))

    def update_ship(self, event):
        self.draw(event)

    def update_handle_focus(self, event):
        mx1, my1, mx2, my2 = self.get_handle_bounds(0, 0)
        rx1, ry1, rx2, ry2 = self.get_handle_bounds(30, 30)

        if (mx1 <= event.x <= mx2) and (my1 <= event.y <= my2):
            for s in self.fleet.ships:
                s.handle_focus = 0
            self.handle_focus = 1
            return True
        elif (rx1 <= event.x <= rx2) and (ry1 <= event.y <= ry2):
            for s in self.fleet.ships:
                s.handle_focus = 0
            self.handle_focus = 2
            return True
        self.handle_focus = 0
        return False

    def update_slot_focus(self, event):
        for slot in self.data["weaponSlots"]:

            if slot["mount"] == "HIDDEN" or slot["type"] in ("SYSTEM", "DECORATIVE", "STATION_MODULE"):
                continue

            sx1, sy1, sx2, sy2 = self.get_handle_bounds(slot["locations"][0], -slot["locations"][1])

            if (sx1 <= event.x <= sx2) and (sy1 <= event.y <= sy2):
                self.focused_slot = slot["id"]
                return True
        self.focused_slot = None
        return False


    def drag_handle(self, event):

        def norm(x, y):
            return (x**2 + y**2)**(1/2)

        if self.handle_focus == 0:
            return False

        if self.handle_focus == 1:
            self.pos_x += - self.pos_x - self.view[0] + event.x - self.center_x
            self.pos_y += - self.pos_y + self.view[1] - event.y + self.center_y
        if self.handle_focus == 2:
            self.rot = - math.pi/4 + math.atan2(
                - self.pos_y + self.view[1] - event.y + self.center_y,
                - self.pos_x - self.view[0] + event.x - self.center_x)

        self.update_ship(event)

        return True

    def draw(self, event=None):
        self.draw_ship()
        self.draw_weapons()

        if not event:
            return

        def norm(x, y):
            return (x**2 + y**2)**(1/2)

        distance = norm(event.x - self.center_x - self.view[0] - self.pos_x,
                        event.y - self.center_y - self.view[1] + self.pos_y)

        if distance < 50:
            self.draw_move_handle()
            self.draw_rotate_handle()
        else:
            self.clear_move_handle()
            self.clear_rotate_handle()

    def clear_ship(self):
        if self.canvas_ship_id:
            self.canvas.delete(self.canvas_ship_id)
            self.canvas_ship_id = None

    def draw_ship(self):
        self.clear_ship()
        rotated = [
            coord
            for x, y in zip(self.data["bounds"][::2], self.data["bounds"][1::2])
            for coord in self._rotate_translate(x, y)
        ]

        self.canvas_ship_id = self.canvas.create_polygon(rotated, fill="white")

    def get_arc_points(self, cx, cy, radius, direction, angle, sides=30):
        direction *= math.pi/180
        angle *= math.pi/180
        points = []
        for i in range(sides+1):
            point = direction - angle/2 + i * angle/sides
            points.append(cx - math.sin(point) * radius)
            points.append(cy - math.cos(point) * radius)
        return points

    def draw_arc(self, points):
        return self.canvas.create_line(points, fill="grey")

    def draw_weapons(self):
        def arc_radius(slot):
            if self.weapons[slot["id"]]:
                return self.weapons[slot["id"]]["range"]
            return 50

        for slot in self.data["weaponSlots"]:

            if slot["mount"] == "HIDDEN" or slot["type"] in ("SYSTEM", "DECORATIVE", "STATION_MODULE"):
                continue

            for i in range(5):
                if self.weapon_canvas_ids[slot["id"]][i]:
                    self.canvas.delete(self.weapon_canvas_ids[slot["id"]][i])
                    self.weapon_canvas_ids[slot["id"]][i] = None

            self.weapon_canvas_ids[slot["id"]][0] = self.canvas.create_rectangle(
                    *self.get_handle_bounds(slot["locations"][0], -slot["locations"][1]))

            arc_points = self.get_arc_points(
                    *self._rotate_translate(slot["locations"][0],
                                            slot["locations"][1]),
                    arc_radius(slot), slot["angle"]+self.rot*180/math.pi, slot["arc"])

            back_arc_points = self.get_arc_points(
                    *self._rotate_translate(slot["locations"][0],
                                            slot["locations"][1]),
                    10, (180+slot["angle"]+self.rot*180/math.pi)%360, 360-slot["arc"])

            self.weapon_canvas_ids[slot["id"]][1] = self.draw_arc(arc_points)
            self.weapon_canvas_ids[slot["id"]][2] = self.draw_arc(back_arc_points)

            self.weapon_canvas_ids[slot["id"]][3] = self.canvas.create_line(arc_points[:2], back_arc_points[-2:], fill="grey")
            self.weapon_canvas_ids[slot["id"]][4] = self.canvas.create_line(arc_points[-2:], back_arc_points[:2], fill="grey")

    def get_handle_bounds(self, cx, cy):
        return tuple(i+j for i in (-3, 3) for j in self._rotate_translate(cx, -cy))

    def clear_move_handle(self):
        if self.canvas_move_handle_id:
            self.canvas.delete(self.canvas_move_handle_id)
            self.canvas_move_handle_id = None

    def draw_move_handle(self):
        self.clear_move_handle()

        self.canvas_move_handle_id = self.canvas.create_rectangle(
                *self.get_handle_bounds(0, 0),
                fill="green")

    def clear_rotate_handle(self):
        if self.canvas_rotate_handle_id:
            self.canvas.delete(self.canvas_rotate_handle_id)
            self.canvas_rotate_handle_id = None

    def draw_rotate_handle(self):
        self.clear_rotate_handle()

        self.canvas_rotate_handle_id = self.canvas.create_rectangle(
                *self.get_handle_bounds(30, 30),
                fill="red")

    def show_stats(self, callback):

        def change_attr(attr, value):
            if attr == "cap":
                self.capacitors += value
            if attr == "vent":
                self.vents += value
            self.fleet.update_window(self.fleet.ship_stats_window, self.show_stats)

        callback("Capacitors: " + str(self.capacitors), (("-", None, lambda x: change_attr("cap", -1)), ("+", None, lambda x: change_attr("cap", 1))))
        callback("Vent: " + str(self.vents), (("-", None, lambda x: change_attr("vent", -1)), ("+", None, lambda x: change_attr("vent", 1))))

        for k, v in self.data.items():
            callback(k + " : " + str(v))

    def show_weapons(self, callback):

        def select_weapon(weapon):
            self.weapons[self.focused_slot] = weapon
            self.update_ship(None)

        slot = [i for i in self.data["weaponSlots"] if i["id"] == self.focused_slot][0]

        weapons = list_weapons(slot["size"], slot["type"])
        
        for w in weapons:
            callback(w["name"], (("CLR", None, lambda x: select_weapon(None)), ("SEL", None, lambda x: select_weapon(w))))

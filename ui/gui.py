import core.api as api
import tkinter as tk

root = tk.Tk()
root.title("Starsector Refit Calculator")

main = tk.Frame(root)
main.grid()

view = [0, 0,  # center
        1.0]   # zoom

mouse = [[0, 0],   # Button-1
         [0, 0],   # B1-Motion
         [0, 0]]   # ButtonRelease-1

from core.data import Fleet, Ship
MOCK_FLEET = Fleet(view, mouse)

def create_view_port(height=500, width=500):
    canvas = tk.Canvas(main, bg="black", height=height, width=width)
    canvas.grid(row=0, column=0, rowspan=3)
    canvas.bind("<Motion>", lambda event: MOCK_FLEET.update_fleet(event))
    canvas.bind("<Button-1>", lambda event: MOCK_FLEET.click(event))
    canvas.bind("<ButtonRelease-1>", lambda event: MOCK_FLEET.release(event))
    canvas.bind("<B1-Motion>", lambda event: MOCK_FLEET.drag(event))
    canvas.bind("<Button-3>", lambda event: MOCK_FLEET.right_click(event))

    MOCK_FLEET.canvas = canvas
    MOCK_FLEET.center_x = height // 2
    MOCK_FLEET.center_y = width  // 2

    return canvas

view_port = create_view_port()

def scrolling_canvas(parent, height, width):
    root = tk.Frame(parent, bd=1, relief="solid")
    canvas = tk.Canvas(root, height=height, width=width)
    scrollbar = tk.Scrollbar(root)

    canvas.pack(side="left", fill="y", expand=False)
    scrollbar.pack(side="right", fill="y")
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.config(command=canvas.yview)

    inner_frame = tk.Frame(canvas)

    window_id = canvas.create_window(
        (0, 0),
        window=inner_frame,
        anchor="nw"
    )

    def on_inner_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    inner_frame.bind("<Configure>", on_inner_configure)

    def on_canvas_configure(event):
        canvas.itemconfigure(window_id, width=event.width)

    canvas.bind("<Configure>", on_canvas_configure)
    
    def _on_mousewheel(event):
        if event.num == 4:
            canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            canvas.yview_scroll(1, "units")


    def _bind_mousewheel(event):
        canvas.bind_all("<Button-4>", _on_mousewheel)
        canvas.bind_all("<Button-5>", _on_mousewheel)


    def _unbind_mousewheel(event):
        canvas.unbind_all("<Button-4>")
        canvas.unbind_all("<Button-5>")


    inner_frame.bind("<Enter>", _bind_mousewheel)
    inner_frame.bind("<Leave>", _unbind_mousewheel)
    
    return root, inner_frame

def ship_card(parent, ship):
    rowframe = tk.Frame(parent)
    label = tk.Label(rowframe, bd=1, relief="solid", pady=0, text=ship["name"], highlightthickness=0)
    button = tk.Button(rowframe, text="+",
                       command=lambda: MOCK_FLEET.ships.append(Ship(ship, view_port, view, mouse, MOCK_FLEET)),
                       padx=4, pady=0, highlightthickness=0)
    label.pack(side="left", fill="x", expand=True, padx=0, pady=0)
    button.pack(side="right", padx=0, pady=0)
    rowframe.pack(fill="x", expand=True)
    return rowframe

sroot1, scanvas1 = scrolling_canvas(main, 500//3, 200)
sroot1.grid(row=0, column=1)
sroot2, scanvas2 = scrolling_canvas(main, 500//3, 200)
sroot2.grid(row=1, column=1)
sroot3, scanvas3 = scrolling_canvas(main, 500//3, 200)
sroot3.grid(row=2, column=1)

for s in api.list_ships():
    if s["name"]:
        if (("bounds" in s)
            and not (s["hints"] and "UNBOARDABLE" in s["hints"])
            and (s["hullSize"] != "FIGHTER")):
            ship_card(scanvas1, s)#s["name"], s["bounds"])

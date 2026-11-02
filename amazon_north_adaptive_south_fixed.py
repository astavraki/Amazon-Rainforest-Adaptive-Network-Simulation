"""Interactive matched comparison: northern adaptive, southern fixed-coupling.
Python standard library only.
Run: python amazon_tkinter.py
"""
import tkinter as tk
from tkinter import ttk

NAMES = ('NW', 'N', 'NE', 'SW', 'S', 'SE')
POS = ((100, 110), (300, 110), (500, 110), (100, 265), (300, 265), (500, 265))
EDGES = ((2, 1), (1, 0), (5, 4), (4, 3))
DT = 0.02
T_END = 100


def simulate(severity):
    """Euler integration with hysteresis; frozen initial weights in control case."""
    adaptive = [0.85] * 6
    fixed = [0.85] * 6
    active = [True] * 4
    snapshots = []
    for step in range(round(T_END / DT) + 1):
        t = step * DT
        if step % 5 == 0:
            snapshots.append((adaptive.copy(), fixed.copy(), active.copy()))
        if t >= T_END:
            break
        c = 1.0 - severity if 10 <= t < 36 else 1.0
        for e, (source, _) in enumerate(EDGES):
            if active[e] and adaptive[source] < 0.35:
                active[e] = False
            elif not active[e] and adaptive[source] > 0.55:
                active[e] = True
        moisture = [0.0] * 6
        frozen_moisture = [0.0] * 6
        for e, (source, target) in enumerate(EDGES):
            if active[e]:
                moisture[target] += 0.38 * adaptive[source]
            frozen_moisture[target] += 0.38 * 0.85
        new_a, new_f = [], []
        for i in range(6):
            baseline = 0.72 if i in (2, 5) else 0.28
            def grow(p, rain):
                s = max(0.0, min(1.0, (rain - 0.20) / 0.50))
                return max(0.0, min(1.0, p + DT * (
                    0.45 * p * (1 - p) * s - 0.22 * p * (1 - s))))
            new_a.append(grow(adaptive[i], baseline * c + moisture[i]))
            new_f.append(grow(fixed[i], baseline * c + frozen_moisture[i]))
        adaptive, fixed = new_a, new_f
    return snapshots


class App:
    def __init__(self, root):
        self.root = root
        root.title('Amazon forest: north adaptive vs south fixed coupling')
        root.geometry('850x770')
        self.severity = tk.IntVar(value=60)
        self.time = tk.DoubleVar(value=0)
        self.playing = False
        controls = ttk.Frame(root, padding=12)
        controls.pack(fill='x')
        self.play_button = ttk.Button(controls, text='Play', command=self.toggle)
        self.play_button.pack(side='left')
        ttk.Button(controls, text='Reset', command=self.reset).pack(side='left', padx=8)
        ttk.Label(controls, text='Drought reduction (%)').pack(side='left', padx=(18, 4))
        ttk.Scale(controls, from_=10, to=90, variable=self.severity,
                  command=self.change_severity, length=180).pack(side='left')
        self.severity_label = ttk.Label(controls, text='60%')
        self.severity_label.pack(side='left', padx=8)
        ttk.Label(root, text='Time: 0 to 100 (drought occurs from 10 to 36)',
                  padding=(12, 4)).pack(anchor='w')
        ttk.Scale(root, from_=0, to=100, variable=self.time,
                  command=lambda _: self.draw()).pack(fill='x', padx=15)
        self.canvas = tk.Canvas(root, width=820, height=350, bg='#fafbf9', highlightthickness=0)
        self.canvas.pack(fill='x', padx=10, pady=5)
        ttk.Label(root, text='Matched comparison: N (adaptive) vs S (fixed coupling)',
                  padding=(12, 2)).pack(anchor='w')
        self.chart = tk.Canvas(root, width=820, height=240, bg='white', highlightthickness=1,
                               highlightbackground='#dddddd')
        self.chart.pack(fill='x', padx=10)
        self.status = ttk.Label(root, text='', padding=12)
        self.status.pack(anchor='w')
        self.snapshots = simulate(0.60)
        self.draw()

    def change_severity(self, _=None):
        self.snapshots = simulate(self.severity.get() / 100)
        self.severity_label.config(text=f'{self.severity.get()}%')
        self.draw()

    def toggle(self):
        self.playing = not self.playing
        self.play_button.config(text='Pause' if self.playing else 'Play')
        if self.playing:
            if self.time.get() >= 100:
                self.time.set(0)
            self.tick()

    def tick(self):
        if not self.playing:
            return
        self.time.set(min(100, self.time.get() + 0.5))
        self.draw()
        if self.time.get() >= 100:
            self.playing = False
            self.play_button.config(text='Play')
        else:
            self.root.after(40, self.tick)

    def reset(self):
        self.playing = False
        self.play_button.config(text='Play')
        self.time.set(0)
        self.draw()

    def draw(self):
        index = min(len(self.snapshots) - 1, int(round(self.time.get() * 10)))
        a, f, edges = self.snapshots[index]
        self.canvas.delete('all')
        t = self.time.get()
        phase = 'DROUGHT' if 10 <= t < 36 else ('RECOVERY' if t >= 36 else 'NORMAL RAINFALL')
        self.canvas.create_text(400, 25, text=f'Time = {t:.1f}     {phase}', font=('Arial', 15, 'bold'))
        # Top row is the adaptive experiment. Bottom row is the fixed-coupling control.
        for e, (source, target) in enumerate(EDGES):
            xs, ys = POS[source]
            xt, yt = POS[target]
            is_adaptive = e < 2
            if is_adaptive and not edges[e]:
                self.canvas.create_line(xs-34, ys, xt+34, yt, fill='#b87373',
                                        width=2, dash=(5, 5))
            else:
                strength = (0.38 * a[source]) if is_adaptive else (0.38 * 0.85)
                self.canvas.create_line(xs-34, ys, xt+34, yt, fill='#247cb2' if is_adaptive else '#d08838',
                                        width=max(1, 1 + 5 * strength / .38), arrow=tk.LAST,
                                        arrowshape=(12, 13, 5))
        for i, (x, y) in enumerate(POS):
            density = a[i] if i < 3 else f[i]
            r = 9 + 25 * density**0.5
            color = '#50996c' if density >= 0.55 else '#b0aa58' if density >= 0.3 else '#c47d72'
            self.canvas.create_oval(x-r, y-r, x+r, y+r, fill=color, outline='#234835', width=1.5)
            self.canvas.create_text(x, y, text=NAMES[i], fill='white', font=('Arial', 11, 'bold'))
            self.canvas.create_text(x, y+r+13, text=f'{density:.3f}', font=('Arial', 10))
        self.canvas.create_text(400, 66, text='NORTH: ADAPTIVE COUPLING', fill='#247c61',
                                font=('Arial', 11, 'bold'))
        self.canvas.create_text(400, 220, text='SOUTH: FIXED COUPLING (CONTROL)', fill='#b8752a',
                                font=('Arial', 11, 'bold'))
        self.canvas.create_text(400, 330,
                                text='Circle size = forest density; blue = adaptive link; orange = fixed link; dashed = broken',
                                fill='#555555', font=('Arial', 9))
        self.chart.delete('all')
        # Reserve space above for the legend, left for the y-axis label,
        # and below for numerical time ticks and the x-axis title.
        left, top, right, bottom = 85, 45, 795, 190
        self.chart.create_rectangle(left + 0.10 * (right-left), top,
                                    left + 0.36 * (right-left), bottom,
                                    fill='#f5f0e9', outline='')
        self.chart.create_line(left, bottom, right, bottom, fill='#666666')
        self.chart.create_line(left, top, left, bottom, fill='#666666')
        for v in (0, .25, .5, .75, 1):
            yy = bottom - v * (bottom-top)
            self.chart.create_line(left, yy, right, yy, fill='#eeeeee')
            self.chart.create_text(left-10, yy, text=f'{v:.2f}', anchor='e', font=('Arial', 9))
        for tick in (0, 20, 40, 60, 80, 100):
            xx_tick = left + tick/100*(right-left)
            self.chart.create_line(xx_tick, bottom, xx_tick, bottom+4, fill='#666666')
            self.chart.create_text(xx_tick, bottom+14, text=str(tick), font=('Arial', 9))
        self.chart.create_text((left+right)/2, 228, text='Time (arbitrary units)', font=('Arial', 10))
        self.chart.create_text(15, (top+bottom)/2, text='Forest density', angle=90,
                               font=('Arial', 10))
        # Both curves show the complete time interval, with the current time
        # indicated by a dashed vertical cursor.
        for source_index, color in ((0, '#247c61'), (1, '#d08838')):
            coords = []
            for q, (aa, ff, _) in enumerate(self.snapshots):
                val = aa[1] if source_index == 0 else ff[4]
                coords.extend((left+q/(len(self.snapshots)-1)*(right-left),
                               bottom-val*(bottom-top)))
            self.chart.create_line(*coords, fill=color, width=2, smooth=False)
        xx = left + t/100*(right-left)
        self.chart.create_line(xx, top, xx, bottom, fill='#444444', dash=(3, 3))
        # Legend is separate from both coordinate axes.
        self.chart.create_line(285, 22, 313, 22, fill='#247c61', width=3)
        self.chart.create_text(320, 22, text='Adaptive N', anchor='w', font=('Arial', 10))
        self.chart.create_line(450, 22, 478, 22, fill='#d08838', width=3)
        self.chart.create_text(485, 22, text='Fixed S', anchor='w', font=('Arial', 10))
        self.status.config(text=f'Adaptive north links: {sum(edges[:2])}/2    N (adaptive): {a[1]:.3f}    S (fixed): {f[4]:.3f}')


if __name__ == '__main__':
    root = tk.Tk()
    App(root)
    root.mainloop()

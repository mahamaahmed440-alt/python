# -*- coding: utf-8 -*-
"""
Created on Wed May 13 13:32:54 2026

@author: MAHAMAH AHMED ZAKIU,KNUST
"""
import numpy as np
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from tkinter import messagebox
from tkinter import filedialog
import csv
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

app = tk.Tk()
app.title('Continuous Beam Solver')
app.geometry('900x620')
app.resizable(True,True)
menuBar = tk.Menu(app)
app.configure(menu=menuBar)

support_data = {}
span_data    = {}
beam_info    = {}


canvasFrame = tk.LabelFrame(app, text='Beam Preview')
canvasFrame.grid(row=2, column=0, columnspan=6, padx=10, pady=10, sticky='ew')

beamCanvas = tk.Canvas(canvasFrame, width=860, height=160, bg='white', relief='sunken', bd=2)
beamCanvas.pack(padx=5, pady=5)

def draw_beam():
    beamCanvas.delete('all')

    if not support_data:
        beamCanvas.create_text(430, 80, text='Enter beam details and save supports to see the beam preview.', fill='grey', font=('Arial', 10, 'italic'))
        return

    positions = sorted(rec['position'] for rec in support_data.values())
    if len(positions) < 2:
        beamCanvas.create_text(430, 80, text='Save at least 2 supports to preview the beam.', fill='grey', font=('Arial', 10, 'italic'))
        return

    beam_start = positions[0]
    beam_end   = positions[-1]
    if 'length' in beam_info:
        beam_start = min(0.0, positions[0])
        beam_end   = max(beam_info['length'], positions[-1])
    beam_len   = beam_end - beam_start
    if beam_len == 0:
        return

    margin_l, margin_r = 60, 60
    draw_w = 860 - margin_l - margin_r
    beam_y = 90

    def to_px(x):
        return margin_l + (x - beam_start) / beam_len * draw_w


    beamCanvas.create_line(to_px(beam_start), beam_y, to_px(beam_end), beam_y,width=6, fill='#2c3e50')

    sorted_by_pos = sorted(support_data.values(), key=lambda r: r['position'])
    leftmost_pos  = sorted_by_pos[0]['position']  if sorted_by_pos else None

    for rec in support_data.values():
        px = to_px(rec['position'])
        stype = rec.get('support_type', 'Pin')
        if stype == 'Fixed':
            if rec['position'] == leftmost_pos:
                wall_x1, wall_x2 = px - 12, px
                hatch_dir = -1
            else:
                wall_x1, wall_x2 = px, px + 12
                hatch_dir = 1
            wall_top    = beam_y - 15
            wall_bottom = beam_y + 15
            beamCanvas.create_rectangle(wall_x1, wall_top, wall_x2, wall_bottom,fill='#555', outline='#555')
            hatch_x = wall_x1 if hatch_dir == -1 else wall_x2
            for hy in range(wall_top, wall_bottom + 1, 6):
                beamCanvas.create_line(hatch_x, hy,hatch_x + hatch_dir * 8, hy + 8, fill='#555', width=1)
            beamCanvas.create_text(px, beam_y + 28, text=f"{rec['position']}m (Fixed)",font=('Arial', 7), fill='#2c3e50')                              
        else:
            beamCanvas.create_polygon(px, beam_y + 3, px - 10, beam_y + 20, px + 10, beam_y + 20,fill='orange', outline='black')
            beamCanvas.create_text(px, beam_y + 30, text=f"{rec['position']}m (Pin)", font=('Arial', 7), fill='orange')


    sorted_supports = sorted(support_data.values(), key=lambda r: r['position'])
    for span_name, rec in span_data.items():
        if span_name == 'Left Overhang':
            span_start_x = beam_start
            span_end_x   = sorted_supports[0]['position']
        elif span_name == 'Right Overhang':
            span_start_x = sorted_supports[-1]['position']
            span_end_x   = beam_end
        else:
            try:
                span_idx = int(span_name.split()[-1]) - 1
            except (ValueError, IndexError):
                continue
            if span_idx >= len(sorted_supports) - 1:
                continue

            span_start_x = sorted_supports[span_idx]['position']
            span_end_x   = sorted_supports[span_idx + 1]['position']
        if span_end_x == span_start_x:
            continue


        if rec['load_type'] == 'UDL':
            mag = rec.get('magnitude', 0)
            x1 = to_px(span_start_x)
            x2 = to_px(span_end_x)
            top_y    = beam_y - 45
            bottom_y = beam_y - 8
            beamCanvas.create_rectangle(x1, top_y, x2, top_y + 10,fill='red', outline='red')

            num_arrows = max(2, int((x2 - x1) // 30))
            for k in range(num_arrows + 1):
                ax = x1 + (x2 - x1) * k / num_arrows
                beamCanvas.create_line(ax, top_y + 10, ax, bottom_y, arrow=tk.LAST, fill='red', width=2)

            beamCanvas.create_text((x1 + x2) / 2, top_y - 8,text=f'{mag} kN/m', fill='red', font=('Arial', 8))
        elif rec['load_type'] == 'Point Load':
            for load in rec.get('loads', []):
                px = to_px(load['position'])
                beamCanvas.create_line(px, beam_y - 35, px, beam_y - 5,arrow=tk.LAST, fill='red', width=2)
                beamCanvas.create_text(px, beam_y - 45,text=f"{load['magnitude']} kN", fill='red',font=('Arial', 8))

        if 'end_moment' in rec and span_name in ('Left Overhang', 'Right Overhang'):
            m_val = -rec['end_moment'] if rec.get('moment_type') == 'Hogging Moment(-)' else rec['end_moment']
            tip_x = to_px(span_start_x) if span_name == 'Left Overhang' else to_px(span_end_x)
            beamCanvas.create_text(tip_x, beam_y + 15,
                                   text=f"{'↺' if m_val > 0 else '↻'} {abs(m_val)} kNm",
                                   fill='#9b59b6', font=('Arial', 8, 'bold'))

    beamCanvas.create_text(to_px((beam_start + beam_end) / 2), beam_y + 50,text=f'Total beam length: {beam_end - beam_start} m',font=('Arial', 9, 'bold'), fill='#2c3e50')


draw_beam()

def newModel():
    framePrprts = tk.LabelFrame(app, text='Beam Model')
    framePrprts.grid(row=0, column=0, padx=10, pady=10, sticky='n')
    label1 = tk.Label(framePrprts, text='Beam Length(m)')
    label1.grid(row=0, column=0)
    beamLength = tk.Entry(framePrprts)
    beamLength.grid(row=0, column=1)
    label2 = tk.Label(framePrprts, text='Number of Supports (minimum 2)')
    label2.grid(row=1, column=0)
    numSupport = tk.Entry(framePrprts)
    numSupport.grid(row=1, column=1)

    def support_proceed():
        global listOfSupports
        support_data.clear()
        span_data.clear()
        if not beamLength.get().strip():
            messagebox.showwarning('Missing Input', 'Please enter the beam length.')
            return
        try:
            beam_info['length'] = float(beamLength.get().strip())
        except ValueError:
            messagebox.showerror('Invalid Input', 'Beam length must be a number.')
            return
        if not numSupport.get().strip():
            messagebox.showwarning('Missing Input', 'Please enter the number of supports.')
            return
        try:
            value = int(numSupport.get())
        except ValueError:
            messagebox.showerror('Invalid Input', 'Number of supports must be an integer.')
            return
        if value < 2:
            messagebox.showwarning('Invalid Input', 'Number of supports must be at least 2.')
            return
        listOfSupports = []
        for i in range(value):
            listOfSupports.append('Support '+ str(i+1))
        comboSupport = ttk.Combobox(framePrprts, values=listOfSupports)
        comboSupport.grid(row=3, column=1)
        label3 = tk.Label(framePrprts, text='Support Position')
        label3.grid(row=3, column=0)
        app.inputFrame = None

        def supportSelected(event):
            try:
                app.inputFrame.destroy()
            except Exception:
                pass

            support_name = comboSupport.get()
            lbl_font  = ('Arial', 9)
            head_font = ('Arial', 9, 'bold')
            hint_font = ('Arial', 8, 'italic')
            app.inputFrame = tk.LabelFrame(app, text=' ' + support_name + ' Information ',font=head_font, padx=12, pady=8)
            app.inputFrame.grid(row=1, column=0, padx=10, pady=5, sticky='n')

            tk.Label(app.inputFrame, text='Position (m)', font=lbl_font).grid(row=0, column=0, sticky='w', pady=2)
            pos_supp_en = tk.Entry(app.inputFrame, width=14, justify='center')
            pos_supp_en.grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=2)
            tk.Label(app.inputFrame, text='Measured from the left end of the beam.',font=hint_font, fg='grey').grid(row=1, column=0, columnspan=2, sticky='w')

            tk.Label(app.inputFrame, text='Support Type', font=lbl_font).grid(row=2, column=0, sticky='w', pady=(6, 2))
            comboSuppType = ttk.Combobox(app.inputFrame, values=['Pin', 'Fixed'], state='readonly', width=11)
            comboSuppType.grid(row=2, column=1, sticky='ew', padx=(10, 0), pady=(6, 2))
            comboSuppType.set('Pin')

            mom_widgets = {}
            saved = support_data.get(support_name, {})
            if saved.get('support_type'):
                comboSuppType.set(saved['support_type'])
            if saved:
                pos_supp_en.insert(0, str(saved.get('position', '')))

            moment_types = ['Sagging Moment(+)', 'Hogging Moment(-)']

            def on_position_change(*_):
                for w in mom_widgets.values():
                    try:
                        w.destroy()
                    except Exception:
                        pass
                mom_widgets.clear()

                raw = pos_supp_en.get().strip()
                try:
                    pos = float(raw)
                except ValueError:
                    return

                try:
                    beam_len = float(beamLength.get().strip())
                except ValueError:
                    return

                if pos != 0.0 and pos != beam_len:
                    return

                momFrame = tk.LabelFrame(app.inputFrame, text='End Moment (optional)',font=lbl_font, padx=8, pady=6)
                momFrame.grid(row=3, column=0, columnspan=2, sticky='ew', pady=(8, 0))
                tk.Label(momFrame, text='Magnitude (kNm)', font=lbl_font).grid(row=0, column=0, sticky='w', pady=2)
                mag_en = tk.Entry(momFrame, width=14, justify='center')
                mag_en.grid(row=0, column=1, padx=(10, 0), pady=2)
                tk.Label(momFrame, text='Moment Type', font=lbl_font).grid(row=1, column=0, sticky='w', pady=2)
                comboMomType = ttk.Combobox(momFrame, values=moment_types, state='readonly', width=18)
                comboMomType.grid(row=1, column=1, padx=(10, 0), pady=2)
                if saved:
                    em = saved.get('end_moment', '')
                    mt = saved.get('moment_type', '')
                    if em != '':
                        mag_en.insert(0, str(em))
                    if mt:
                        comboMomType.set(mt)

                mom_widgets['momFrame']     = momFrame
                mom_widgets['mag_en']       = mag_en
                mom_widgets['comboMomType'] = comboMomType

            pos_supp_en.bind('<KeyRelease>', on_position_change)

            def saveSupport():
                raw = pos_supp_en.get().strip()
                if not raw:
                    messagebox.showwarning('Missing Input',f'Please enter a position for {support_name}.')
                    return
                try:
                    position = float(raw)
                except ValueError:
                    messagebox.showerror('Invalid Input', 'Position must be a number.')
                    return

                record = {'position': position, 'support_type': comboSuppType.get()}

                if mom_widgets:
                    raw_mom  = mom_widgets['mag_en'].get().strip()
                    mom_type = mom_widgets['comboMomType'].get()

                    if raw_mom and not mom_type:
                        messagebox.showwarning('Missing Input', 'Please select a moment type.')
                        return
                    if mom_type and not raw_mom:
                        messagebox.showwarning('Missing Input','Please enter the end moment magnitude.')
                        return
                    if raw_mom:
                        try:
                            record['end_moment']  = float(raw_mom)
                            record['moment_type'] = mom_type
                        except ValueError:
                            messagebox.showerror('Invalid Input','End moment magnitude must be a number.')
                            return

                support_data[support_name] = record
                refresh_span_list()
                draw_beam()
                try:
                    app.inputFrame.destroy()
                except Exception:
                    pass

            save_btn = tk.Button(app.inputFrame, text='Save Support', command=saveSupport, font=head_font,bg='#2c3e50', fg='white', activebackground='#34495e', activeforeground='white',padx=10, pady=3)
            save_btn.grid(row=4, column=0, columnspan=2, sticky='ew', pady=(10, 0))

            on_position_change()

        comboSupport.bind('<<ComboboxSelected>>', supportSelected)

        frameSpan = tk.LabelFrame(app, text='Span Information')
        frameSpan.grid(row=0, column=3, padx=20, pady=10, sticky='n')
        val = int(numSupport.get()) - 1
        listOfSpans = []
        for i in range(val):
            listOfSpans.append('Span '+str(i+1))
        comboSpan = ttk.Combobox(frameSpan, values=listOfSpans)
        comboSpan.grid(row=0, column=3)

        def refresh_span_list():
            names = ['Span '+str(i+1) for i in range(val)]
            if len(support_data) >= value:
                ps = [r['position'] for r in support_data.values()]
                if min(ps) > 0:
                    names.insert(0, 'Left Overhang')
                else:
                    span_data.pop('Left Overhang', None)
                if max(ps) < beam_info['length']:
                    names.append('Right Overhang')
                else:
                    span_data.pop('Right Overhang', None)
            comboSpan['values'] = names
            if comboSpan.get() not in names:
                comboSpan.set('')

        app.inputSpan  = None
        app.pointFrame = None
        app.udlFrame   = None
        app._active_load_entries = {}

        def spanSelected(event):
            for attr in ('inputSpan', 'pointFrame', 'udlFrame', 'momFrame'):
                try:
                    getattr(app, attr).destroy()
                except Exception:
                    pass
            app._active_load_entries.clear()

            span_name   = comboSpan.get()
            is_overhang = span_name in ('Left Overhang', 'Right Overhang')
            saved_span  = span_data.get(span_name, {})
            lbl_font    = ('Arial', 9)
            head_font   = ('Arial', 9, 'bold')
            hint_font   = ('Arial', 8, 'italic')
            moment_types = ['Sagging Moment(+)', 'Hogging Moment(-)']

            app.inputSpan = tk.LabelFrame(app, text=' ' + span_name + ' Information ',font=head_font, padx=12, pady=8)
            app.inputSpan.grid(row=1, column=3, padx=20, pady=5, sticky='n')

            typeOfLoad = ['Point Load', 'UDL'] + (['End Moment'] if is_overhang else [])
            tk.Label(app.inputSpan, text='Type of Load', font=lbl_font).grid(row=0, column=0, sticky='w', pady=(0, 6))
            comboLoad = ttk.Combobox(app.inputSpan, values=typeOfLoad, state='readonly', width=18)
            comboLoad.grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=(0, 6))

            detailFrame = tk.Frame(app.inputSpan)
            detailFrame.grid(row=1, column=0, columnspan=2, sticky='ew')
            app.pointFrame = None
            app.udlFrame   = None
            app.momFrame   = None

            def loadSelected(event=None):
                for w in detailFrame.winfo_children():
                    w.destroy()
                app._active_load_entries.clear()
                app.pointFrame = app.udlFrame = app.momFrame = None

                selectedLoad = comboLoad.get()

                if selectedLoad == 'Point Load':
                    app.pointFrame = tk.LabelFrame(detailFrame, text='Point Loads', font=lbl_font, padx=8, pady=6)
                    app.pointFrame.pack(fill='x')

                    countRow = tk.Frame(app.pointFrame)
                    countRow.pack(fill='x', pady=(0, 4))
                    tk.Label(countRow, text='Number of point loads', font=lbl_font).pack(side='left')
                    numPload = tk.Entry(countRow, width=5, justify='center')
                    numPload.pack(side='left', padx=8)
                    app._active_load_entries['numPload'] = numPload
                    app._active_load_entries['point_rows'] = []
                    rowsFrame = tk.Frame(app.pointFrame)
                    rowsFrame.pack(fill='x')
                    tk.Label(app.pointFrame, text='Positions are measured from the left end of the beam.',
                             font=hint_font, fg='grey').pack(anchor='w', pady=(4, 0))

                    def pointLoads(silent=True):
                        try:
                            num = int(numPload.get().strip())
                        except ValueError:
                            if not silent:
                                messagebox.showerror('Invalid Input','Number of point loads must be an integer.')
                            return
                        if not 1 <= num <= 20:
                            if not silent:
                                messagebox.showerror('Invalid Input','Number of point loads must be between 1 and 20.')
                            return

                        old = [(m.get(), p.get()) for m, p in app._active_load_entries['point_rows']]
                        if len(old) == num:
                            return
                        if not old and saved_span.get('load_type') == 'Point Load':
                            old = [(str(l['magnitude']), str(l['position'])) for l in saved_span.get('loads', [])]

                        for w in rowsFrame.winfo_children():
                            w.destroy()
                        app._active_load_entries['point_rows'] = []
                        for c, h in enumerate(('#', 'Magnitude (kN)', 'Position (m)')):
                            tk.Label(rowsFrame, text=h, font=head_font).grid(row=0, column=c, padx=4)
                        for i in range(num):
                            tk.Label(rowsFrame, text=str(i + 1), font=lbl_font).grid(row=i + 1, column=0)
                            mag_entry = tk.Entry(rowsFrame, width=12, justify='center')
                            mag_entry.grid(row=i + 1, column=1, padx=4, pady=2)
                            pos_entry = tk.Entry(rowsFrame, width=12, justify='center')
                            pos_entry.grid(row=i + 1, column=2, padx=4, pady=2)
                            if i < len(old):
                                mag_entry.insert(0, old[i][0])
                                pos_entry.insert(0, old[i][1])
                            app._active_load_entries['point_rows'].append((mag_entry, pos_entry))

                    numPload.bind('<KeyRelease>', lambda e: pointLoads(True))
                    tk.Button(countRow, text='Set', command=lambda: pointLoads(False)).pack(side='left')

                    if saved_span.get('load_type') == 'Point Load' and saved_span.get('loads'):
                        numPload.insert(0, str(len(saved_span['loads'])))
                        pointLoads(True)

                elif selectedLoad == 'UDL':
                    app.udlFrame = tk.LabelFrame(detailFrame, text='Uniformly Distributed Load',font=lbl_font, padx=8, pady=6)
                    app.udlFrame.pack(fill='x')
                    tk.Label(app.udlFrame, text='Magnitude of UDL (kN/m)', font=lbl_font).grid(row=0, column=0, sticky='w')
                    udl_en = tk.Entry(app.udlFrame, width=12, justify='center')
                    udl_en.grid(row=0, column=1, padx=(10, 0))
                    app._active_load_entries['udl'] = udl_en
                    if saved_span.get('load_type') == 'UDL':
                        udl_en.insert(0, str(saved_span.get('magnitude', '')))

                elif selectedLoad == 'End Moment':
                    app.momFrame = tk.LabelFrame(detailFrame, text='Moment at Free End of Overhang',font=lbl_font, padx=8, pady=6)
                    app.momFrame.pack(fill='x')
                    tk.Label(app.momFrame, text='Magnitude (kNm)', font=lbl_font).grid(row=0, column=0, sticky='w', pady=2)
                    mom_en = tk.Entry(app.momFrame, width=12, justify='center')
                    mom_en.grid(row=0, column=1, padx=(10, 0), pady=2)
                    tk.Label(app.momFrame, text='Moment Type', font=lbl_font).grid(row=1, column=0, sticky='w', pady=2)
                    comboMomType = ttk.Combobox(app.momFrame, values=moment_types, state='readonly', width=18)
                    comboMomType.grid(row=1, column=1, padx=(10, 0), pady=2)
                    app._active_load_entries['mom_en']   = mom_en
                    app._active_load_entries['mom_type'] = comboMomType
                    if saved_span.get('load_type') == 'End Moment':
                        mom_en.insert(0, str(saved_span.get('end_moment', '')))
                        comboMomType.set(saved_span.get('moment_type', ''))

            comboLoad.bind('<<ComboboxSelected>>', loadSelected)

            def saveSpan():
                load_type = comboLoad.get()
                if not load_type:
                    messagebox.showwarning('Missing Input', 'Please select a load type.')
                    return
                record = {'load_type': load_type}

                if load_type == 'Point Load':
                    rows = app._active_load_entries.get('point_rows', [])
                    if not rows:
                        messagebox.showwarning('Missing Input','Please enter the number of point loads and fill them in.')
                        return
                    loads = []
                    for i, (mag_e, pos_e) in enumerate(rows, start=1):
                        raw_mag = mag_e.get().strip()
                        raw_pos = pos_e.get().strip()
                        if not raw_mag or not raw_pos:
                            messagebox.showwarning('Missing Input', f'Please fill in magnitude and position for Point Load {i}.')
                            return
                        try:
                            mag = float(raw_mag)
                            pos = float(raw_pos)
                        except ValueError:
                            messagebox.showerror('Invalid Input',f'Point Load {i}: values must be numbers.')
                            return
                        loads.append({'magnitude': mag, 'position': pos})
                    record['loads'] = loads

                elif load_type == 'UDL':
                    udl_en = app._active_load_entries.get('udl')
                    if udl_en is None:
                        messagebox.showwarning('Missing Input', 'Please select UDL again.')
                        return
                    raw = udl_en.get().strip()
                    if not raw:
                        messagebox.showwarning('Missing Input', 'Please enter the UDL magnitude.')
                        return
                    try:
                        record['magnitude'] = float(raw)
                    except ValueError:
                        messagebox.showerror('Invalid Input', 'UDL magnitude must be a number.')
                        return

                elif load_type == 'End Moment':
                    mom_en       = app._active_load_entries.get('mom_en')
                    comboMomType = app._active_load_entries.get('mom_type')
                    if mom_en is None:
                        messagebox.showwarning('Missing Input', 'Please select End Moment again.')
                        return
                    raw_mom  = mom_en.get().strip()
                    mom_type = comboMomType.get()
                    if not raw_mom:
                        messagebox.showwarning('Missing Input','Please enter the end moment magnitude.')
                        return
                    if not mom_type:
                        messagebox.showwarning('Missing Input', 'Please select a moment type.')
                        return
                    try:
                        record['end_moment']  = float(raw_mom)
                        record['moment_type'] = mom_type
                    except ValueError:
                        messagebox.showerror('Invalid Input','End moment magnitude must be a number.')
                        return

                span_data[span_name] = record
                draw_beam()
                for attr in ('inputSpan', 'pointFrame', 'udlFrame', 'momFrame'):
                    try:
                        getattr(app, attr).destroy()
                    except Exception:
                        pass
                app._active_load_entries.clear()

            tk.Button(app.inputSpan, text='Save Span', command=saveSpan, font=head_font, bg='#2c3e50', fg='white', activebackground='#34495e', activeforeground='white',padx=10, pady=3).grid(row=2, column=0, columnspan=2, sticky='ew', pady=(10, 0))

            if saved_span.get('load_type') in typeOfLoad:
                comboLoad.set(saved_span['load_type'])
                loadSelected()

        comboSpan.bind('<<ComboboxSelected>>', spanSelected)

    supportProceed = tk.Button(framePrprts, text='Proceed', command=support_proceed)
    supportProceed.grid(row=2, column=1)


class ContinuousBeam:
    def __init__(self, support_positions, udl_per_span, point_loads=None, end_moments=None,
                 left_end=None, right_end=None, left_udl=0.0, right_udl=0.0,
                 left_moment=0.0, right_moment=0.0):
        self.positions = sorted(support_positions)
        self.udls      = udl_per_span
        self.loads     = point_loads or []
        self.n         = len(self.positions)
        self.spans     = [self.positions[i+1] - self.positions[i] for i in range(self.n - 1)]
        raw = end_moments or {}
        self.end_moments = {(self.n - 1 if k == -1 else k): v for k, v in raw.items()}
        self.left_end  = self.positions[0]  if left_end  is None else left_end
        self.right_end = self.positions[-1] if right_end is None else right_end
        self.left_udl, self.right_udl = left_udl, right_udl
        self.left_moment, self.right_moment = left_moment, right_moment
        self.left_oh  = [(p, m) for p, m in self.loads if self.left_end <= p < self.positions[0]]
        self.right_oh = [(p, m) for p, m in self.loads if self.positions[-1] < p <= self.right_end]
        a_l = self.positions[0] - self.left_end
        a_r = self.right_end - self.positions[-1]
        self.oh_M = [left_moment  - (left_udl*a_l**2/2 + sum(m*(self.positions[0] - p) for p, m in self.left_oh)),
                     right_moment - (right_udl*a_r**2/2 + sum(m*(p - self.positions[-1]) for p, m in self.right_oh))]
        self.oh_W = [left_udl*a_l + sum(m for p, m in self.left_oh),
                     right_udl*a_r + sum(m for p, m in self.right_oh)]
        self.M = self._solve_moments()
        self.R = self._calc_reactions()

    def _solve_moments(self):
        M = [0.0] * self.n
        M[0]        = self.end_moments.get(0, 0.0) + self.oh_M[0]
        M[self.n-1] = self.end_moments.get(self.n-1, 0.0) + self.oh_M[1]
        n_int = self.n - 2
        if n_int < 1:
            return M
        A = np.zeros((n_int, n_int))
        b = np.zeros(n_int)
        for i in range(n_int):
            L1, L2 = self.spans[i], self.spans[i + 1]
            w1, w2 = self.udls[i],  self.udls[i + 1]
            A[i, i] = 2 * (L1 + L2)
            if i > 0:        A[i, i-1] = L1
            if i < n_int-1:  A[i, i+1] = L2
            b[i] = -(w1*L1**3/4 + w2*L2**3/4)
            xL, xR = self.positions[i], self.positions[i + 1]
            for pos, mag in self.loads:
                if xL <= pos < xR:
                    a = pos - xL
                    b[i] -= mag * a * (L1**2 - a**2) / L1
                if xR <= pos < self.positions[i + 2]:
                    a = pos - xR
                    b[i] -= mag * a * (L2**2 - a**2) / L2
            if i == 0:       b[i] -= M[0]        * L1
            if i == n_int-1: b[i] -= M[self.n-1] * L2
        sol = np.linalg.solve(A, b)
        for i in range(n_int):
            M[i + 1] = sol[i]
        return M

    def _calc_reactions(self):
        R = [0.0] * self.n
        for i, (L, w, x0) in enumerate(zip(self.spans, self.udls, self.positions)):
            dM      = (self.M[i+1] - self.M[i]) / L
            R_left  = w*L/2 + dM
            R_right = w*L/2 - dM
            for pos, mag in self.loads:
                if x0 <= pos < x0 + L:
                    d = pos - x0
                    R_left  += mag * (L - d) / L
                    R_right += mag * d       / L
            R[i]   += R_left
            R[i+1] += R_right
        R[0]        += self.oh_W[0]
        R[self.n-1] += self.oh_W[1]
        return R

    def _build_diagrams(self, npts=400):
        all_x, all_V, all_BM = [], [], []
        for i, (L, w, x0) in enumerate(zip(self.spans, self.udls, self.positions)):
            dM     = (self.M[i+1] - self.M[i]) / L
            R_left = w*L/2 + dM
            for pos, mag in self.loads:
                if x0 <= pos < x0 + L:
                    R_left += mag * (L - (pos - x0)) / L
            xs = np.linspace(0, L, npts)
            V  = R_left - w*xs
            BM = self.M[i] + R_left*xs - w*xs**2/2
            for pos, mag in self.loads:
                if x0 <= pos < x0 + L:
                    a = pos - x0; mask = xs >= a
                    V[mask]  -= mag
                    BM[mask] -= mag * (xs[mask] - a)
            all_x.append(xs + x0); all_V.append(V); all_BM.append(BM)
        if self.positions[0] > self.left_end:
            xs = np.linspace(self.left_end, self.positions[0], npts)
            d  = xs - self.left_end
            V  = -self.left_udl*d
            BM = self.left_moment - self.left_udl*d**2/2
            for pos, mag in self.left_oh:
                mask = xs >= pos
                V[mask]  -= mag
                BM[mask] -= mag * (xs[mask] - pos)
            all_x.insert(0, xs); all_V.insert(0, V); all_BM.insert(0, BM)
        if self.right_end > self.positions[-1]:
            xs = np.linspace(self.positions[-1], self.right_end, npts)
            d  = self.right_end - xs
            V  = self.right_udl*d
            BM = self.right_moment - self.right_udl*d**2/2
            for pos, mag in self.right_oh:
                mask = xs <= pos
                V[mask]  += mag
                BM[mask] -= mag * (pos - xs[mask])
            all_x.append(xs); all_V.append(V); all_BM.append(BM)
        return np.concatenate(all_x), np.concatenate(all_V), np.concatenate(all_BM)

    def print_results(self):
        _, V, BM = self._build_diagrams()
        W = 60
        print("=" * W)
        print("          RESULTS SUMMARY")
        print("=" * W)
        print("")
        print("  Geometry")
        print("  " + "-" * (W - 4))
        print("  Number of spans    : {}".format(self.n - 1))
        print("  Span lengths       : {} m".format([round(s, 2) for s in self.spans]))
        print("  Support positions  : {} m".format([round(p, 2) for p in self.positions]))
        if self.positions[0] > self.left_end:
            print("  Left overhang      : {:.2f} m".format(self.positions[0] - self.left_end))
        if self.right_end > self.positions[-1]:
            print("  Right overhang     : {:.2f} m".format(self.right_end - self.positions[-1]))

        if self.end_moments:
            print("")
            print("  Applied End Moments")
            print("  " + "-" * (W - 4))
            for idx, val in self.end_moments.items():
                print("  Support {0} (x={1} m) : {2:.3f} kN.m".format(idx + 1, self.positions[idx], val))

        print("")
        print("  Support Reactions")
        print("  " + "-" * (W - 4))
        for i in range(self.n):
            print("  R{0}  (x={1:.2f} m) : {2:+.3f} kN".format(i + 1, self.positions[i], self.R[i]))
        print("  Total reaction     : {:.3f} kN".format(sum(self.R)))

        if self.oh_M[0] != 0.0 or self.oh_M[1] != 0.0:
            print("")
            print("  Overhang Moments at End Supports")
            print("  " + "-" * (W - 4))
            if self.oh_M[0] != 0.0:
                print("  M1  (x={0:.2f} m) : {1:+.3f} kN.m".format(self.positions[0], self.oh_M[0]))
            if self.oh_M[1] != 0.0:
                print("  M{0}  (x={1:.2f} m) : {2:+.3f} kN.m".format(self.n, self.positions[-1], self.oh_M[1]))

        if self.n > 2:
            print("")
            print("  Bending Moments at Interior Supports")
            print("  " + "-" * (W - 4))
            for i in range(1, self.n - 1):
                print("  M{0}  (x={1:.2f} m) : {2:+.3f} kN.m".format(i + 1, self.positions[i], self.M[i]))

        print("")
        print("  Envelope Values")
        print("  " + "-" * (W - 4))
        print("  Max |shear force|        : {:.3f} kN".format(np.max(np.abs(V))))
        print("  Max |bending moment|     : {:.3f} kN.m".format(np.max(np.abs(BM))))
        print("  Max sagging moment (+ve) : {:.3f} kN.m".format(np.max(BM)))
        print("  Max hogging moment (-ve) : {:.3f} kN.m".format(np.min(BM)))
        print("")
        print("=" * W)
        

    def build_sfd_bmd_figure(self):
        x, V, BM = self._build_diagrams()
        fig = Figure(figsize=(7, 6), dpi=100)
        for k, (data, color, title, ylabel) in enumerate([
                (V,  "#2980b9", "Shear Force Diagram (kN)",      "V (kN)"),
                (BM, "#27ae60", "Bending Moment Diagram (kN·m)", "M (kN·m)")], start=1):
            ax = fig.add_subplot(2, 1, k)
            ax.set_title(title, fontweight="bold")
            ax.fill_between(x, data, alpha=0.3, color=color)
            ax.plot(x, data, color=color, lw=2)
            ax.axhline(0, color="grey", lw=0.8, linestyle="--")
            for pos in self.positions:
                ax.axvline(pos, color="orange", lw=0.8, linestyle=":")
            ax.set_xlabel("x (m)"); ax.set_ylabel(ylabel)
            ax.grid(True, linestyle=":", alpha=0.4)
        fig.tight_layout()
        return fig

    def plot(self):
        x, V, BM = self._build_diagrams()
        fig, axes = plt.subplots(3, 1, figsize=(12, 10))
        fig.suptitle(f"Continuous Beam – {self.n} Supports, {self.n-1} Spans",fontsize=13, fontweight="bold")
        ax = axes[0]; ax.axis("off"); ax.set_title("Beam Diagram", fontweight="bold")
        ax.barh(0, self.right_end-self.left_end, left=self.left_end,height=0.25, color="#2c3e50")
        for i, pos in enumerate(self.positions):
            ax.annotate("", xy=(pos, 0.2), xytext=(pos, -0.6),arrowprops=dict(arrowstyle="->", color="orange", lw=2))
            ax.text(pos, -0.85, f"R{i+1}={self.R[i]:.1f}kN",ha="center", color="orange", fontsize=8)
        for pos, mag in self.loads:
            ax.annotate("", xy=(pos, 0.12), xytext=(pos, 0.9),arrowprops=dict(arrowstyle="->", color="red", lw=2.5))
            ax.text(pos, 1.0, f"{mag}kN", ha="center", color="red", fontsize=9)
        for idx, val in self.end_moments.items():
            sym = "↺" if val > 0 else "↻"
            ax.text(self.positions[idx], 0.5, f"{sym} {abs(val):.1f} kN·m",ha="center", color="#9b59b6", fontsize=9, fontweight="bold")
        for tip_x, val in ((self.left_end, self.left_moment), (self.right_end, self.right_moment)):
            if val != 0.0:
                sym = "↺" if val > 0 else "↻"
                ax.text(tip_x, 0.5, f"{sym} {abs(val):.1f} kN·m",ha="center", color="#9b59b6", fontsize=9, fontweight="bold")
        ax.set_xlim(self.left_end-0.5, self.right_end+0.5); ax.set_ylim(-1.2, 1.4)
        for ax, data, color, title, ylabel in [
            (axes[1], V,  "#2980b9", "Shear Force Diagram (kN)",      "V (kN)"),
            (axes[2], BM, "#27ae60", "Bending Moment Diagram (kN·m)", "M (kN·m)"),]:
            ax.set_title(title, fontweight="bold")
            ax.fill_between(x, data, alpha=0.3, color=color)
            ax.plot(x, data, color=color, lw=2)
            ax.axhline(0, color="grey", lw=0.8, linestyle="--")
            for pos in self.positions:
                ax.axvline(pos, color="orange", lw=0.8, linestyle=":")
            ax.set_xlabel("x (m)"); ax.set_ylabel(ylabel)
            ax.grid(True, linestyle=":", alpha=0.4)
        for idx, val in self.end_moments.items():
            axes[2].plot(self.positions[idx], val, "D", color="#9b59b6", ms=8)
        plt.tight_layout(); plt.show()


def save_results(parent, kind, reaction_rows, x, V, BM):
    reaction_header = ['Support', 'Type', 'Position (m)', 'Reaction R (kN)', 'Moment M (kN.m)']
    diagram_header  = ['x (m)', 'Shear V (kN)', 'Bending Moment M (kN.m)']
    diagram_rows    = [[round(float(a), 6) + 0.0, round(float(b), 6) + 0.0, round(float(c), 6) + 0.0] for a, b, c in zip(x, V, BM)]

    if kind == 'xlsx':
        path = filedialog.asksaveasfilename(parent=parent, title='Save results as Excel file', defaultextension='.xlsx', initialfile='beam_results.xlsx', filetypes=[('Excel Workbook', '*.xlsx')])
            
    else:
        path = filedialog.asksaveasfilename(parent=parent, title='Save results as CSV file', defaultextension='.csv', initialfile='beam_results.csv', filetypes=[('CSV File', '*.csv')])

    if not path:
        return

    try:
        if kind == 'xlsx':
            try:
                from openpyxl import Workbook
                from openpyxl.chart import ScatterChart, Reference, Series
                from openpyxl.styles import Font
            except ImportError:
                messagebox.showerror('Missing Library','Saving as Excel needs the openpyxl package (pip install openpyxl).\n' 'You can still save the results as a CSV file.', parent=parent)
                                     
                return
            wb = Workbook()
            ws = wb.active
            ws.title = 'Reactions'
            ws.append(reaction_header)
            for row in reaction_rows:
                ws.append(row)
            wd = wb.create_sheet('SFD & BMD')
            wd.append(diagram_header)
            for row in diagram_rows:
                wd.append(row)
            for sheet, header in ((ws, reaction_header), (wd, diagram_header)):
                for col, h in enumerate(header, start=1):
                    sheet.cell(row=1, column=col).font = Font(bold=True)
                    sheet.column_dimensions[sheet.cell(row=1, column=col).column_letter].width = max(16, len(h) + 4)
            last = len(diagram_rows) + 1
            xref = Reference(wd, min_col=1, min_row=2, max_row=last)
            for col, title, anchor in ((2, 'Shear Force Diagram', 'E2'), (3, 'Bending Moment Diagram', 'E20')):
                chart = ScatterChart()
                chart.title = title
                chart.style = 13
                chart.x_axis.title = 'x (m)'
                chart.y_axis.title = 'V (kN)' if col == 2 else 'M (kN.m)'
                chart.x_axis.delete = False
                chart.y_axis.delete = False
                chart.legend = None
                chart.height, chart.width = 8, 16
                series = Series(Reference(wd, min_col=col, min_row=2, max_row=last), xref, title=title)
                series.marker.symbol = 'none'
                chart.series.append(series)
                wd.add_chart(chart, anchor)
            wb.save(path)
        else:
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['SUPPORT REACTIONS'])
                writer.writerow(reaction_header)
                writer.writerows(reaction_rows)
                writer.writerow([])
                writer.writerow(['SHEAR FORCE AND BENDING MOMENT DIAGRAM DATA'])
                writer.writerow(diagram_header)
                writer.writerows(diagram_rows)
    except PermissionError:
        messagebox.showerror('Save Failed', 'Could not write the file. Close it if it is open in another program and try again.', parent=parent)
        return
    except Exception as e:
        messagebox.showerror('Save Failed', f'Could not save the file:\n{e}', parent=parent)
        return
    messagebox.showinfo('Saved', f'Results saved to:\n{path}', parent=parent)


def runAnalysis():
    n_supports = len(listOfSupports)
    n_spans    = n_supports - 1

    if len(support_data) < n_supports:
        messagebox.showwarning('Incomplete Data',f'Please save all {n_supports} support positions before solving.')
        return
    if sum(1 for k in span_data if k.startswith('Span ')) < n_spans:
        messagebox.showwarning('Incomplete Data',f'Please save all {n_spans} span loads before solving.')
        return

    support_positions = []
    end_moments       = {}
    support_types     = []

    for i, name in enumerate(listOfSupports):
        rec = support_data[name]
        support_positions.append(rec['position'])
        support_types.append(rec.get('support_type', 'Pin'))
        if 'end_moment' in rec:
            mag = rec['end_moment']
            if rec.get('moment_type') == 'Hogging Moment(-)':
                mag = -mag
            end_moments[i] = mag

    beam_L       = beam_info.get('length', max(support_positions))
    left_oh_len  = min(support_positions)
    right_oh_len = beam_L - max(support_positions)
    if left_oh_len < 0 or right_oh_len < 0:
        messagebox.showerror('Invalid Input', 'All supports must lie within the beam length.')
        return
    if (left_oh_len > 0 and support_types[0] == 'Fixed') or (right_oh_len > 0 and support_types[-1] == 'Fixed'):
        messagebox.showerror('Invalid Input', 'A Fixed support must be at the end of the beam (no overhang beyond it).')
        return

    phantom_left  = support_types[0]  == 'Fixed'
    phantom_right = support_types[-1] == 'Fixed'

    adj_left_span  = support_positions[1]  - support_positions[0]
    adj_right_span = support_positions[-1] - support_positions[-2]

    if phantom_left:
        support_positions = [support_positions[0] - adj_left_span] + support_positions
        udl_per_span_adj  = [0.0]
    else:
        udl_per_span_adj  = []

    if phantom_right:
        support_positions = support_positions + [support_positions[-1] + adj_right_span]

    udl_per_span = []
    point_loads  = []

    for i in range(n_spans):
        name = 'Span ' + str(i + 1)
        rec  = span_data[name]
        if rec['load_type'] == 'UDL':
            udl_per_span.append(rec['magnitude'])
        else:
            udl_per_span.append(0.0)
            for load in rec.get('loads', []):
                point_loads.append((load['position'], load['magnitude']))

    left_udl = right_udl = 0.0
    left_moment = right_moment = 0.0
    for oh_name, oh_len in (('Left Overhang', left_oh_len), ('Right Overhang', right_oh_len)):
        rec = span_data.get(oh_name)
        if oh_len <= 0 or rec is None:
            continue
        if 'end_moment' in rec:
            tip_m = -rec['end_moment'] if rec.get('moment_type') == 'Hogging Moment(-)' else rec['end_moment']
            if oh_name == 'Left Overhang':
                left_moment = tip_m
            else:
                right_moment = tip_m
        if rec['load_type'] == 'UDL':
            if oh_name == 'Left Overhang':
                left_udl = rec['magnitude']
            else:
                right_udl = rec['magnitude']
        else:
            for load in rec.get('loads', []):
                if oh_name == 'Left Overhang':
                    ok = 0 <= load['position'] < min(support_positions)
                else:
                    ok = max(support_positions) < load['position'] <= beam_L
                if not ok:
                    messagebox.showwarning('Invalid Input', f'A point load on the {oh_name} lies outside the overhang.')
                    return
                point_loads.append((load['position'], load['magnitude']))

    full_udl = udl_per_span_adj + udl_per_span + ([0.0] if phantom_right else [])

    offset = 1 if phantom_left else 0
    shifted_moments = {k + offset: v for k, v in end_moments.items()}

    beam = ContinuousBeam(support_positions, full_udl, point_loads, shifted_moments,left_end  = 0.0    if left_oh_len  > 0 else None,right_end = beam_L if right_oh_len > 0 else None,left_udl=left_udl, right_udl=right_udl,left_moment=left_moment, right_moment=right_moment)

    beam.print_results()

    results_win = tk.Toplevel(app)
    results_win.title('RESULTS SUMMARY')
    results_win.geometry('760x800')

    real_start = 1 if phantom_left  else 0
    real_end   = beam.n - (1 if phantom_right else 0)

    for i in range(beam.n):
        if i < real_start or i >= real_end:
            label = f'Phantom support {i+1}:  M = {beam.M[i]:.3f} kN·m  (zero-load span)'
            tk.Label(results_win, text=label, anchor='w', fg='grey').pack(padx=20, pady=2)
        else:
            real_i  = i - real_start
            sname   = listOfSupports[real_i]
            stype   = support_data[sname].get('support_type', 'Pin')
            tk.Label(results_win,
                     text=f'Support {real_i+1} ({stype}):  R = {beam.R[i]:.3f} kN    M = {beam.M[i]:.3f} kN·m',anchor='w').pack(padx=20, pady=2)

    diagramFrame = tk.LabelFrame(results_win, text='SFD and BMD')
    diagramFrame.pack(fill='both', expand=True, padx=10, pady=10)
    diagramCanvas = FigureCanvasTkAgg(beam.build_sfd_bmd_figure(), master=diagramFrame)
    diagramCanvas.draw()
    diagramCanvas.get_tk_widget().pack(fill='both', expand=True)
    results_win.update()

    reaction_rows = []
    for i in range(real_start, real_end):
        sname = listOfSupports[i - real_start]
        reaction_rows.append([sname, support_data[sname].get('support_type', 'Pin'),
                              round(float(beam.positions[i]), 6), round(float(beam.R[i]), 6), round(float(beam.M[i]), 6)])
    x_all, V_all, BM_all = beam._build_diagrams()
    keep = np.ones(len(x_all), dtype=bool)
    if phantom_left:
        keep &= x_all >= beam.positions[real_start] - 1e-9
    if phantom_right:
        keep &= x_all <= beam.positions[real_end - 1] + 1e-9
    x_all, V_all, BM_all = x_all[keep], V_all[keep], BM_all[keep]

    resultsMenu = tk.Menu(results_win, tearoff=0)
    results_win.config(menu=resultsMenu)
    saveMenu = tk.Menu(resultsMenu, tearoff=0)
    resultsMenu.add_cascade(label='File', menu=saveMenu)
    saveMenu.add_command(label='Save as Excel (.xlsx)...', command=lambda: save_results(results_win, 'xlsx', reaction_rows, x_all, V_all, BM_all))
    saveMenu.add_command(label='Save as CSV (.csv)...', command=lambda: save_results(results_win, 'xlsx', reaction_rows, x_all, V_all, BM_all))
    saveMenu.add_separator()
    saveMenu.add_command(label='Close', command=results_win.destroy)

    beam.plot()


fileMenu = tk.Menu(menuBar)
menuBar.add_cascade(label='File', menu=fileMenu)
fileMenu.add_command(label='New beam...', command=newModel)
fileMenu.add_separator()
fileMenu.add_command(label='Solve', command=runAnalysis)

app.mainloop()

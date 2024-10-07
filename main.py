version = '0.1.0 pre3'

import requests
import json
import math
import socket
import tkinter as tk
from tkinter import ttk
from ttkthemes import *
from tkinter import colorchooser
from tkinter import PhotoImage
from tkinter import messagebox
import webbrowser
import configparser

# --- READ CONFIG ---
config = configparser.ConfigParser()
config.read('config.ini')

alwaysontop = config.get('display', 'alwaysontop')
translucentpercentage = config.getint('display', 'translucentpercentage')
refreshinterval = config.getint('display', 'refreshinterval')
row = config.getint('display', 'row')
size = config.getint('display', 'size')
showboat = config.get('display', 'showboat')
avgdist = config.get('display', 'avgdist')
percent_0 = config.get('theme', 'percent_0')
percent_50 = config.get('theme', 'percent_50')
percent_100 = config.get('theme', 'percent_100')
notify_newversion = config.get('other', 'notify_newversion')

# ===== DEFS =====
def save_config():
  config['display']['alwaysontop'] = str(alwaysontop_var.get())
  config['display']['translucentpercentage'] = str(translucentpercentage_scale.get())
  config['display']['refreshinterval'] = str(int(refreshinterval_scale.get()*1000))
  config['display']['row'] = str(5) # str(row_combobox.get()) 
  if size_combobox.get() == 'Medium':
    config['display']['size'] = str(2)
  else:
    config['display']['size'] = str(1)
  config['display']['showboat'] = str(showboat_var.get())
  config['display']['avgdist'] = str(avgdist_var.get())
  config['theme']['percent_0'] = str(percent_0)
  config['theme']['percent_50'] = str(percent_50)
  config['theme']['percent_100'] = str(percent_100)
  config['other']['notify_newversion'] = str(notify_newversion_var.get())

  with open('config.ini', 'w') as f:
    config.write(f)

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb_color):
    return '#{:02x}{:02x}{:02x}'.format(*rgb_color)

def interpolate_colors(color1, color2, steps):
    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)

    interpolated_colors = []
    for step in range(steps):
        r = int(rgb1[0] + (rgb2[0] - rgb1[0]) * step / (steps - 1))
        g = int(rgb1[1] + (rgb2[1] - rgb1[1]) * step / (steps - 1))
        b = int(rgb1[2] + (rgb2[2] - rgb1[2]) * step / (steps - 1))
        interpolated_colors.append(rgb_to_hex((r, g, b)))
    return interpolated_colors

def get_colors(color1, color2, steps, getstep):
  colors = interpolate_colors(color1, color2, steps)
  for i, color in enumerate(colors):
    if getstep == i:
      return color

def choose_color(n):
  global percent_0, percent_50, percent_100
  if n == 0:
    percent_0 = colorchooser.askcolor()[1]
    percent_0_label['foreground'] = percent_0
    percent_25_label['foreground'] = get_colors(percent_0, percent_50, 51, 25)
  if n == 1:
    percent_50 = colorchooser.askcolor()[1]
    percent_50_label['foreground'] = percent_50
    percent_75_label['foreground'] = get_colors(percent_50, percent_100, 51, 25)
    percent_25_label['foreground'] = get_colors(percent_0, percent_50, 51, 25)
  if n == 2:
    percent_100 = colorchooser.askcolor()[1]
    percent_100_label['foreground'] = percent_100
    percent_75_label['foreground'] = get_colors(percent_50, percent_100, 51, 25)

def apiget():
  api_version = 1
  ip = socket.gethostbyname(socket.gethostname())

  # --- STLONGHOLD ---
  try:
    url_format = f'http://{ip}:52533/api/v{api_version}'
    url = requests.get(f'{url_format}/stronghold')
    data = json.loads(url.text)
    ohters_label['text'] = ''
    for n in range(row):
      Chunk_list_label[n]['text'] = f'({data['predictions'][n]['chunkX']}, {data['predictions'][n]['chunkZ']})'
      Chunk_list_label[1]['foreground'] = fg
      Percent_list_label[n]['text'] = f'{'{:.1f}'.format(data['predictions'][n]['certainty']*100)}%'
      if 50 <= data['predictions'][n]['certainty']*100:
        Percent_list_label[n]['foreground'] = f'{get_colors(percent_50, percent_100, 51, math.floor(data['predictions'][n]['certainty']*100)-50)}'
      else:
        Percent_list_label[n]['foreground'] = f'{get_colors(percent_0, percent_50, 51, math.floor(data['predictions'][n]['certainty']*100))}'
      Dist_list_label[n]['text'] = f'{math.floor(data['predictions'][n]['overworldDistance'])}'
      Nether_list_label[n]['text'] = f'({data['predictions'][n]['chunkX']*2}, {data['predictions'][n]['chunkZ']*2})'
  except IndexError:
    for n in range(row):
      Chunk_list_label[n]['text'] = ''
      Percent_list_label[n]['text'] = ''
      Dist_list_label[n]['text'] = ''
      Nether_list_label[n]['text'] = ''
    try:
      if 0 == len(data['predictions']):
        if len(data['eyeThrows']):
          ohters_label['text'] = 'Could not determine the stronghold chunk.\nYou probably misread one of the eyes.'
    except Exception as e:
      print(f'Error: {e}')
  except Exception as e:
      print(f'Error: {e}')
      
  try:
    l = 0
    for n in range(min(0, len(data['eyeThrows'])-2), max(2, len(data['eyeThrows']))):
      if l < len(data['eyeThrows']):
        x_list_label[l]['text'] = f'{'{:.0f}'.format(data['eyeThrows'][n]['xInOverworld'])}'
        z_list_label[l]['text'] = f'{'{:.0f}'.format(data['eyeThrows'][n]['zInOverworld'])}'
        if '0.00000' == '{:.5f}'.format(data['eyeThrows'][n]['correction']).lstrip('-'):
          D_Angle_list_Text[l].configure(state='normal')
          D_Angle_list_Text[l].delete('1.0', 'end')
          D_Angle_list_Text[l].insert('end', f'{'{:.2f}'.format(data['eyeThrows'][n]['angleWithoutCorrection'])}')
          D_Angle_list_Text[l].tag_add('center', '1.0', 'end')
          D_Angle_list_Text[l].configure(state='disabled')
        elif 0 < data['eyeThrows'][n]['correction']:
          D_Angle_list_Text[l].configure(state='normal')
          D_Angle_list_Text[l].delete('1.0', 'end')
          D_Angle_list_Text[l].insert('end', f'{'{:.2f}'.format(data['eyeThrows'][n]['angleWithoutCorrection'])}')
          D_Angle_list_Text[l].insert('end', f'+{'{:.2f}'.format(data['eyeThrows'][n]['correction'])}', 'angle_plus')
          D_Angle_list_Text[l].tag_add('center', '1.0', 'end')
          D_Angle_list_Text[l].configure(state='disabled')
        else:
          D_Angle_list_Text[l].configure(state='normal')
          D_Angle_list_Text[l].delete('1.0', 'end')
          D_Angle_list_Text[l].insert('end', f'{'{:.2f}'.format(data['eyeThrows'][n]['angleWithoutCorrection'])}')
          D_Angle_list_Text[l].insert('end', f'{'{:.2f}'.format(data['eyeThrows'][n]['correction'])}', 'angle_minus')
          D_Angle_list_Text[l].tag_add('center', '1.0', 'end')
          D_Angle_list_Text[l].configure(state='disabled')
      else:
        x_list_label[l]['text'] = ''
        z_list_label[l]['text'] = ''
        D_Angle_list_Text[l].configure(state='normal')
        D_Angle_list_Text[l].delete('1.0', 'end')
        D_Angle_list_Text[l].configure(state='disabled')
      l += 1
  except IndexError:
    pass
  except Exception as e:
    print(f'Error: {e}')

  # --- BLIND ---
  try:
    url_format = f'http://{ip}:52533/api/v{api_version}'
    url = requests.get(f'{url_format}/blind')
    data = json.loads(url.text)
    if data['isBlindModeEnabled']:
      Chunk_list_label[0]['text'] = f'{'{:.0f}'.format(data['blindResult']['xInNether'])}, {'{:.0f}'.format(data['blindResult']['zInNether'])}'
      Percent_list_label[0]['text'] = '<400'
      Percent_list_label[0]['foreground'] = fg
      Percent_list_label[1]['text'] = f'{'{:.1f}'.format(data['blindResult']['highrollProbability']*100)}%'
      if data['blindResult']['evaluation'] == 'EXCELLENT':
        Chunk_list_label[1]['text'] = 'excellent'
        Chunk_list_label[1]['foreground'] = get_colors(percent_50, percent_100, 51, 50)
        Percent_list_label[1]['foreground'] = get_colors(percent_50, percent_100, 51, 50)
      if data['blindResult']['evaluation'] == 'HIGHROLL_GOOD':
        Chunk_list_label[1]['text'] = 'highroll good'
        Chunk_list_label[1]['foreground'] = get_colors(percent_50, percent_100, 51, 40)
        Percent_list_label[1]['foreground'] = get_colors(percent_50, percent_100, 51, 40)
      if data['blindResult']['evaluation'] == 'HIGHROLL_OKAY':
        Chunk_list_label[1]['text'] = 'highroll okay'
        Chunk_list_label[1]['foreground'] = get_colors(percent_50, percent_100, 51, 25)
        Percent_list_label[1]['foreground'] = get_colors(percent_50, percent_100, 51, 25)
      if data['blindResult']['evaluation'] == 'BAD_BUT_IN_RING':
        Chunk_list_label[1]['text'] = 'not good'
        Chunk_list_label[1]['foreground'] = get_colors(percent_50, percent_100, 51, 0)
        Percent_list_label[1]['foreground'] = get_colors(percent_50, percent_100, 51, 0)
      if data['blindResult']['evaluation'] == 'BAD':
        Chunk_list_label[1]['text'] = 'bad'
        Chunk_list_label[1]['foreground'] = get_colors(percent_0, percent_50, 51, 25)
        Percent_list_label[1]['foreground'] = get_colors(percent_0, percent_50, 51, 25)
      if data['blindResult']['evaluation'] == 'NOT_IN_RING':
        Chunk_list_label[1]['text'] = 'not in ring'
        Chunk_list_label[1]['foreground'] = get_colors(percent_0, percent_50, 51, 0)
        Percent_list_label[1]['foreground'] = get_colors(percent_0, percent_50, 51, 0)
      if avgdist == 'True':
        Dist_list_label[0]['text'] = 'avg'
        Dist_list_label[1]['text'] = '{:.0f}'.format(data['blindResult']['averageDistance'])
  except Exception as e:
      print(f'Error: {e}')

  # --- BOAT ---
  try:
    if showboat == 'True':
      url_format = f'http://{ip}:52533/api/v{api_version}'
      url = requests.get(f'{url_format}/boat')
      data = json.loads(url.text)
      if data['boatState'] == 'NONE':
        boat_label['image'] = img[0]
      if data['boatState'] == 'MEASURING':
        boat_label['image'] = img[1]
      if data['boatState'] == 'VALID':
        boat_label['image'] = img[2]
      if data['boatState'] == 'ERROR':
        boat_label['image'] = img[3]
  except Exception as e:
      print(f'Error: {e}')

  root.after(refreshinterval, apiget)

# notofy new version
if notify_newversion == 'True':
  url = 'https://raw.githubusercontent.com/mebuki117/Ninview-Plus/main/meta'
  data = requests.get(url).content
  if str(version) < str(data).replace('b', '').replace("'", ''):
    m = messagebox.askquestion('Ninview+', 'Found Update', detail='Open the download page?')
    if m == 'yes':
      webbrowser.open('https://github.com/mebuki117/Ninview-Plus/releases')

# colors
bg1 = '#55585a'
bg2 = '#424242'
fg = '#ffffff'
abg = '#446e9e'
tr = '#3c3f41'
hl = '#3c3f41'
sl = '#3c3f41'
sty = '#55585a'

# font
font = 'Consolas'
if size == 2:
  font_size = 12
else:
  font_size = 10
label_pady = -2

# window setup
root = ThemedTk(theme='black')
style = ttk.Style()
style.configure('TCombobox', fieldbackground= f'{sty}', background= f'{sty}', foreground=fg)
root.option_add("*TCombobox*Listbox*Background", f'{sty}')
root.option_add('*TCombobox*Listbox*Foreground', f'{fg}')
root.option_add('*TCombobox*Listbox*selectBackground', f'{sty}')
root.option_add('*TCombobox*Listbox*selectForeground', f'{fg}')

root.resizable(False, False)
root.attributes('-topmost', alwaysontop)
root.attributes('-alpha', (100-translucentpercentage)/100)
if size == 2:
  root.geometry(f'{295+(font_size-10)*38}x{27+(23)*4+(23)*row}')
  note = ttk.Notebook(root, width=295+(font_size-10)*38, height=27+(23)*4+(23)*row)
else:
  root.geometry(f'{295+(font_size-10)*38}x{27+19*4+19*row}')
  note = ttk.Notebook(root, width=295+(font_size-10)*38, height=27+19*4+19*row)

root.title(f'Ninview+ v{version}')
root.iconbitmap(default='ico/blaze_powder.ico')

# create tabs
tab = []
for l in range(3):
  tab.append(ttk.Frame(root))
note.add(tab[0], text='Calculator')
note.add(tab[1], text='General Settings')
note.add(tab[2], text='Theme Settings')
note.pack()

# boat icons
img = []
img.append(PhotoImage(file='png/gray_boat.png'))
img.append(PhotoImage(file='png/blue_boat.png'))
img.append(PhotoImage(file='png/green_boat.png'))
img.append(PhotoImage(file='png/red_boat.png'))

# ===== Ninjabrain bot =====
# --- HEADERS ---
Chunk_label = tk.Label(tab[0], text='Chunk', width=14, background=bg2, foreground=fg, font=(font, font_size), pady=label_pady)
Chunk_label.grid(column=1, row=1)

Percent_label = tk.Label(tab[0], text='%', width=6, background=bg2, foreground=fg, font=(font, font_size), pady=label_pady)
Percent_label.grid(column=2, row=1)

Dist_label = tk.Label(tab[0], text=' Dist.', width=6, background=bg2, foreground=fg, font=(font, font_size), pady=label_pady)
Dist_label.grid(column=3, row=1)

Nether_label = tk.Label(tab[0], text='Nether', width=12, background=bg2, foreground=fg, font=(font, font_size), pady=label_pady)
Nether_label.grid(column=4, row=1)

# Angle_label = tk.Label(tab[0], text='Angle', width=17, background=bg2, foreground=fg, font=(font, font_size), pady=label_pady)
# Angle_label.grid(column=5, row=1)

boat_label = tk.Label(tab[0])
boat_label['background'] = bg2
boat_label.grid(column=4, row=1, sticky='e')

# --- RESULTS ---
Chunk_list_label = []
Percent_list_label = []
Dist_list_label = []
Nether_list_label = []

for n in range(row):
  Chunk_list_label.append(tk.Label(tab[0], background=bg2, foreground=fg, font=(font, font_size), pady=label_pady))
  Chunk_list_label[n].grid(column=1, row=2+n)

  Percent_list_label.append(tk.Label(tab[0], background=bg2, foreground=fg, font=(font, font_size), pady=label_pady))
  Percent_list_label[n].grid(column=2, row=2+n)

  Dist_list_label.append(tk.Label(tab[0], background=bg2, foreground=fg, font=(font, font_size), pady=label_pady))
  Dist_list_label[n].grid(column=3, row=2+n)

  Nether_list_label.append(tk.Label(tab[0], background=bg2, foreground=fg, font=(font, font_size), pady=label_pady))
  Nether_list_label[n].grid(column=4, row=2+n)

  # Angle_list_label = tk.Label(tab[0], background=bg2, foreground=fg, font=(font, font_size), pady=label_pady)
  # Angle_list_label.grid(column=5, row=2+n)

ohters_label = tk.Label(tab[0], background=bg2, foreground=fg, font=(font, font_size), pady=label_pady)
if size == 2:
  ohters_label.place(y=23)
else:
  ohters_label.place(y=19)

# --- DETAILS HEADERS---
x_label = tk.Label(tab[0], text='x', width=6, background=bg2, foreground=fg, font=(font, font_size), pady=label_pady)
x_label.grid(column=1, row=7)

z_label = tk.Label(tab[0], text='z', width=6, background=bg2, foreground=fg, font=(font, font_size), pady=label_pady)
z_label.grid(column=2, row=7)

D_Angle_label = tk.Label(tab[0], text='Angle', width=6, background=bg2, foreground=fg, font=(font, font_size), pady=label_pady)
D_Angle_label.grid(column=4, row=7)

# --- DETAILS DATA ---
x_list_label = []
z_list_label = []
D_Angle_list_Text = []

for n in range(2):
  x_list_label.append(tk.Label(tab[0],background=bg2, foreground=fg, font=(font, font_size), pady=label_pady))
  x_list_label[n].grid(column=1, row=8+n)

  z_list_label.append(tk.Label(tab[0], background=bg2, foreground=fg, font=(font, font_size), pady=label_pady))
  z_list_label[n].grid(column=2, row=8+n)

  D_Angle_list_Text.append(tk.Text(tab[0], width=12, height=1, background=bg2, foreground=fg, font=(font, font_size), pady=label_pady, state='disabled', relief='flat'))
  D_Angle_list_Text[n].grid(column=4, row=8+n)
  D_Angle_list_Text[n].tag_configure('center', justify='center')
  D_Angle_list_Text[n].tag_configure('angle_plus', foreground=percent_100)
  D_Angle_list_Text[n].tag_configure('angle_minus', foreground=percent_0)

# ===== Settings ======
translucentpercentage_scale = tk.Scale(
  tab[1], from_=0, to=100, resolution=5, orient='horizontal',
  background=bg1, foreground=fg, activebackground=abg, troughcolor=tr, highlightcolor=hl, highlightthickness=0,
  label='Translucent (%)', sliderrelief='flat'
  )
translucentpercentage_scale.grid(column=1, row=1, padx=5, pady=5)
translucentpercentage_scale.set(translucentpercentage)

refreshinterval_scale = tk.Scale(
  tab[1], from_=0, to=5, resolution=0.05, orient='horizontal',
  length=167, background=bg1, foreground=fg, activebackground=abg, troughcolor=tr, highlightcolor=hl, highlightthickness=0,
  label='Refresh Interval (sec)', sliderrelief='flat'
  )
refreshinterval_scale.grid(column=2, row=1, padx=5, pady=5)
refreshinterval_scale.set(refreshinterval/1000)

alwaysontop_var = tk.BooleanVar() ; alwaysontop_var.set(alwaysontop)
alwaysontop_checkbox = tk.Checkbutton(tab[1], text='Always on top', background=bg2, activebackground=bg2, foreground=fg, activeforeground=fg, selectcolor=sl, variable=alwaysontop_var)
alwaysontop_checkbox.grid(column=1, row=2, padx=5, pady=5, sticky='w')

showboat_var = tk.BooleanVar() ; showboat_var.set(showboat)
showboat_checkbox = tk.Checkbutton(tab[1], text='Show boat icon', background=bg2, activebackground=bg2, foreground=fg, activeforeground=fg, selectcolor=sl, variable=showboat_var)
showboat_checkbox.grid(column=2, row=2, padx=5, pady=5, sticky='w')

size_label = tk.Label(tab[1], text='Size:', width=4, background=bg2, foreground=fg)
size_label.grid(column=1, row=3, padx=5, pady=5, sticky='w')

size_option =['Small', 'Medium']
size_combobox = ttk.Combobox(tab[1], width=8, values=size_option, textvariable=tk.StringVar(), state='readonly')
size_combobox.grid(column=1, row=3, padx=5, pady=5, sticky='e')
size_combobox.set(size_option[size-1])

avgdist_var = tk.BooleanVar() ; avgdist_var.set(avgdist)
avgdist_checkbox = tk.Checkbutton(tab[1], text='Show avg distance (bata)', background=bg2, activebackground=bg2, foreground=fg, activeforeground=fg, selectcolor=sl, variable=avgdist_var)
avgdist_checkbox.grid(column=2, row=3, padx=5, pady=5, sticky='w')

# row_label = tk.Label(tab[1], text='Rows:', width=4, background=bg2, foreground=fg)
# row_label.grid(column=1, row=3, padx=5, pady=5, sticky='w')

# row_option =['2', '3', '4', '5']
# row_combobox = ttk.Combobox(tab[1], width=6, values=row_option, textvariable=tk.StringVar(), state='readonly')
# row_combobox.grid(column=1, row=3, padx=5, pady=5, sticky='e')
# row_combobox.set(row_option[row-2])

notify_newversion_var = tk.BooleanVar() ; notify_newversion_var.set(notify_newversion)
notify_newversion_checkbox = tk.Checkbutton(tab[1], text='Check for updates', background=bg2, activebackground=bg2, foreground=fg, activeforeground=fg, selectcolor=sl, variable=notify_newversion_var)
notify_newversion_checkbox.grid(column=2, row=4, padx=5, pady=5, sticky='w')

save_button = tk.Button(tab[1], text='Save', width=4, background=bg1, foreground=fg, activebackground=abg, relief='flat', command=save_config)
save_button.grid(column=2, row=4, padx=5, pady=5, sticky='e')

# ===== Theme Settings =====
percent_100_button = tk.Button(tab[2], text='Certainty 100%', width=12, background=bg1, foreground=fg, activebackground=abg, relief='flat', command=lambda:choose_color(2))
percent_100_button.grid(column=1, row=1, padx=5, pady=5)
percent_100_label = tk.Label(tab[2], text='100%', background=bg2, foreground=percent_100, font=(font, font_size), pady=label_pady)
percent_100_label.grid(column=2, row=1, padx=5, pady=5)

percent_75_label = tk.Label(tab[2], text='75%', background=bg2, foreground=get_colors(percent_50, percent_100, 51, 25), font=(font, font_size), pady=label_pady)
percent_75_label.grid(column=2, row=2, padx=5, pady=5)

percent_50_button = tk.Button(tab[2], text='Certainty 50%', width=12, background=bg1, foreground=fg, activebackground=abg, relief='flat', command=lambda:choose_color(1))
percent_50_button.grid(column=1, row=3, padx=5, pady=5)
percent_50_label = tk.Label(tab[2], text='50%', background=bg2, foreground=percent_50, font=(font, font_size), pady=label_pady)
percent_50_label.grid(column=2, row=3, padx=5, pady=5)

percent_25_label = tk.Label(tab[2], text='25%', background=bg2, foreground=get_colors(percent_0, percent_50, 51, 25), font=(font, font_size), pady=label_pady)
percent_25_label.grid(column=2, row=4, padx=5, pady=5)

percent_0_button = tk.Button(tab[2], text='Certainty 0%', width=12, background=bg1, foreground=fg, activebackground=abg, relief='flat', command=lambda:choose_color(0))
percent_0_button.grid(column=1, row=5, padx=5, pady=5)
percent_0_label = tk.Label(tab[2], text='0%', background=bg2, foreground=percent_0, font=(font, font_size), pady=label_pady)
percent_0_label.grid(column=2, row=5, padx=5, pady=5)

save_button = tk.Button(tab[2], text='Save', width=4, background=bg1, foreground=fg, activebackground=abg, relief='flat', command=save_config)
save_button.grid(column=3, row=5, padx=5, pady=5, sticky='e')

# ===== LOOP =====
if __name__ == '__main__':
  apiget()
  root.mainloop()
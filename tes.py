import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
import time

from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer

# Membuat dan melatih instance chatterbot
chatbot = ChatBot('CharacterBot')
trainer = ChatterBotCorpusTrainer(chatbot)
trainer.train("chatterbot.corpus.english")  # Ganti dengan corpus bahasa Indonesia jika Anda memiliki satu

root = tk.Tk()
root.iconbitmap('jarwo.ico')
root.title("JARWO - Your AI Assistant")
root.geometry("600x430")
root.configure(bg="black")

video_source = r"C:\Users\Sebastian\Desktop\Kuliah\Semester 2\Pengantar Kecerdasan Buatan\TB_Chatbot\Chatbot_Sebastian\jarwo.mp4"
video_cap = cv2.VideoCapture(video_source)

# Pastikan sumber video dibuka
if not video_cap.isOpened():
    raise ValueError("Unable to open video source")

fps = video_cap.get(cv2.CAP_PROP_FPS)
max_frames = int(fps * 3.5)  #durasi video

stop_video = False

def update_video_frames(canvas, video_cap):
    global stop_video, max_frames

    if stop_video:
        return

    current_frame = int(video_cap.get(cv2.CAP_PROP_POS_FRAMES))

    if current_frame >= max_frames:
        video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    ret, frame = video_cap.read()

    if not ret:
        # Jika video berakhir, ulangi dari awal
        video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    else:
        #Ubah setiap frame jadi gambar
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = Image.fromarray(frame)

        # Atur ukuran frame sesuai dengan ukuran canvas
        frame = frame.resize((canvas.winfo_width(), canvas.winfo_height()), Image.LANCZOS)

        frame = ImageTk.PhotoImage(frame)
        canvas.create_image(0, 0, image=frame, anchor=tk.NW)
        canvas.image = frame

    # Schedule the next frame update
    canvas.after(30, update_video_frames, canvas, video_cap)

#Tampilkan video
canvas = tk.Canvas(root, width=580, height=290, highlightthickness=0)
canvas.pack(pady=5)

#load video di sini
video_cap = cv2.VideoCapture('jarwo.mp4')

# Update the video frames on the canvas
update_video_frames(canvas, video_cap)

def on_closing():
    global video_cap
    video_cap.release()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

def send_message(event):
    user_message = entry_chat.get()
    
    if user_message == 'CLEAR':
        chat_history.configure(state='normal')
        chat_history.delete('1.0', tk.END)
        chat_history.configure(state='disabled')
        entry_chat.delete(0, tk.END)
        return
    
    # Tampilkan pesan pengguna di chat history
    chat_history.configure(state='normal')
    chat_history.insert(tk.END, 'You: ' + user_message + '\n')
    chat_history.configure(state='disabled')
    
    # Dapatkan dan tampilkan respons chatterbot
    bot_response = chatbot.get_response(user_message)
    
    chat_history.configure(state='normal')
    chat_history.insert(tk.END, 'Bot: ' + str(bot_response) + '\n')
    chat_history.configure(state='disabled')
    
    # Hapus input pengguna
    entry_chat.delete(0, tk.END)

def start_chatbot():
    global chat_history, entry_chat, marquee

    # Hapus tombol start dan video awal
    marquee.destroy_marquee()
    button_start.destroy()
    stop_video = True
    canvas.destroy()
    
    # Membuat loading bar
    style = ttk.Style()
    style.configure("big.Horizontal.TProgressbar", thickness=30)
    
    label_loading = tk.Label(root, text="LOADING CUY", font=("Boulder", 30),fg="white",bg="black")
    label_loading.pack(pady=100)
    label_loading1 = tk.Label(root, text="Loading ini tidak ada gunanya, biar keren saja", 
                              font=("Arial Rounded", 15),fg="white",bg="black")
    label_loading1.pack(pady=5)
    loading_bar = ttk.Progressbar(root, length=500, mode='determinate', maximum=100, style="big.Horizontal.TProgressbar")
    loading_bar.pack(pady=20)

    root.update()

    # Simulasi waktu loading dan update value
    loading_duration = 5  # Atur waktu loading di sini
    for i in range(100):
        loading_bar['value'] = i
        root.update()
        time.sleep(loading_duration / 100)

    # Hapus label loading dan loading bar
    loading_bar.destroy()
    label_loading.destroy()
    label_loading1.destroy()
    
    marquee = Marquee(root, "(INFO) Jika respons chatbot tidak sesuai konteks, ketik 'FIX' untuk memperbaiki respons dari chatbot. Ketik 'CLEAR' untuk menghapus history.",
                      width=600, height=35, bg="dark grey")
    marquee.pack(padx=20,pady=12)

    # Munculkan teks history
    chat_history = tk.Text(root, height=20, width=80, wrap=tk.WORD)
    chat_history.configure(state='disabled')
    entry_chat = tk.Entry(root, width=70)

    chat_history.pack(side=tk.TOP, padx=0, pady=0)
    entry_chat.pack(side=tk.LEFT, padx=85, pady=0)
    entry_chat.focus_set()

    entry_chat.bind('<Return>', send_message)

    # Buat pengumuman di chat history
    chat_history.configure(state='normal', font = ('Arial Rounded', 10))
    announcement = ""
    
    # Configure text tags for center alignment
    chat_history.tag_configure('center', justify='center')
    chat_history.tag_configure('red', foreground='red')

    # Insert the announcement text with the 'center' and 'red' tags
    chat_history.insert(tk.END, announcement, ('center', 'red'))
    chat_history.configure(state='disabled')
    
    chat_history.insert(tk.END, announcement, ('margin', 'red'))
    chat_history.configure(state='disabled')

button_start = tk.Button(root, text="      START      ", font=("Boulder", 30), bg="black", fg="white", 
                         borderwidth=0, relief="raised", command=lambda: start_chatbot())
button_start.pack(pady=5, padx=100)

marquee = Marquee(root, "Selamat datang di Chatbot Jarwo. Chatbot ini adalah tugas besar mata kuliah pengantar kecerdasan buatan yang dibuat oleh Sebastianus Lukito (41522110051) dan Bayu Randuaji Widodo (41522110016) yang diampu oleh Bapak Muhaimin Hasanudin", width=600, height=35, bg="dark grey")
marquee.pack(padx=20,pady=0)

root.mainloop()

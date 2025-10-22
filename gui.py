import customtkinter as ctk
from tkinter import messagebox, scrolledtext, filedialog
from PIL import Image, ImageTk
import os
import pygame
import pandas as pd
import tempfile
import base64
from datetime import datetime
import threading
from fat_system import FATFileSystem

pygame.mixer.init()

class FATFileSystemGUI(ctk.CTk):
    def __init__(self, current_user, user_role):
        super().__init__()
        
        self.system = FATFileSystem()
        self.system.initialize_system()
        
        self.current_user = current_user
        self.user_role = user_role
        
        self.current_image = None
        self.current_audio_file = None
        self.temp_files = []
        self.loading = False
        
        self.title(f"🚀 Sistema de Archivos FAT - Usuario: {current_user}")
        self.geometry("1400x800")
        self.minsize(1200, 700)
        
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        self.current_file = None
        
        self.create_widgets()
        self.update_file_list()
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def on_closing(self):
        self.cleanup_temp_files()
        self.destroy()
    
    def cleanup_temp_files(self):
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception:
                pass
        self.temp_files = []
    
    def create_widgets(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.create_sidebar()
        self.create_main_area()
        self.create_status_bar()
    
    def create_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#2b2b2b")
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(16, weight=1)
        
        title_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        title_frame.grid(row=0, column=0, padx=10, pady=15, sticky="ew")
        
        title_label = ctk.CTkLabel(
            title_frame, 
            text="💾 Sistema FAT", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack()
        
        user_frame = ctk.CTkFrame(sidebar, corner_radius=8)
        user_frame.grid(row=1, column=0, padx=10, pady=8, sticky="ew")
        
        user_icon = ctk.CTkLabel(user_frame, text="👤", font=ctk.CTkFont(size=14))
        user_icon.pack(side="left", padx=(8, 3), pady=6)
        
        user_info_frame = ctk.CTkFrame(user_frame, fg_color="transparent")
        user_info_frame.pack(side="left", fill="x", expand=True, padx=3, pady=3)
        
        user_label = ctk.CTkLabel(
            user_info_frame, 
            text=self.current_user,
            font=ctk.CTkFont(weight="bold", size=11)
        )
        user_label.pack(anchor="w")
        
        role_label = ctk.CTkLabel(
            user_info_frame, 
            text=f"🔧 {self.user_role}",
            font=ctk.CTkFont(size=9),
            text_color="lightblue"
        )
        role_label.pack(anchor="w")
        
        separator = ctk.CTkFrame(sidebar, height=1, fg_color="gray30")
        separator.grid(row=2, column=0, padx=15, pady=8, sticky="ew")
        
        buttons = [
            ("📁 Subir", self.upload_file_dialog, "#4CAF50"),
            ("📄 Crear", self.create_file_dialog, "#2196F3"),
            ("📋 Listar", self.update_file_list, "#FF9800"),
            ("👁️ Abrir", self.open_file_dialog, "#9C27B0"),
            ("✏️ Modificar", self.modify_file_dialog, "#FFC107"),
            ("🗑️ Papelera", self.show_recycle_bin, "#757575"),
            ("🔐 Permisos", self.manage_permissions_dialog, "#E91E63"),
            ("🔄 Actualizar", self.update_file_list, "#00BCD4"),
            ("💾 Backup", self.create_backup_dialog, "#673AB7"),
            ("📂 Restaurar", self.restore_backup_dialog, "#009688")
        ]
        
        for i, (text, command, color) in enumerate(buttons, 3):
            btn = ctk.CTkButton(
                sidebar,
                text=text,
                command=command,
                height=35,
                font=ctk.CTkFont(size=12),
                fg_color=color,
                hover_color=self.darken_color(color),
                corner_radius=6
            )
            btn.grid(row=i, column=0, padx=10, pady=3, sticky="ew")
        
        if self.user_role == "admin":
            user_buttons_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
            user_buttons_frame.grid(row=13, column=0, padx=10, pady=5, sticky="ew")
            user_buttons_frame.grid_columnconfigure(0, weight=1)
            user_buttons_frame.grid_columnconfigure(1, weight=1)
            
            create_user_btn = ctk.CTkButton(
                user_buttons_frame,
                text="👥 Crear",
                command=self.create_user_dialog,
                height=35,
                font=ctk.CTkFont(size=11),
                fg_color="#4CAF50",
                hover_color="#45a049",
                corner_radius=6
            )
            create_user_btn.grid(row=0, column=0, padx=2, sticky="ew")
            
            delete_user_btn = ctk.CTkButton(
                user_buttons_frame,
                text="🗑️ Eliminar",
                command=self.delete_user_dialog,
                height=35,
                font=ctk.CTkFont(size=11),
                fg_color="#f44336",
                hover_color="#da190b",
                corner_radius=6
            )
            delete_user_btn.grid(row=0, column=1, padx=2, sticky="ew")
        
        logout_btn = ctk.CTkButton(
            sidebar,
            text="🚪 Salir",
            command=self.logout,
            height=35,
            font=ctk.CTkFont(size=12),
            fg_color="#f44336",
            hover_color="#da190b",
            corner_radius=6
        )
        logout_btn.grid(row=14, column=0, padx=10, pady=8, sticky="ew")
    
    def darken_color(self, color):
        color = color.lstrip('#')
        rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        darkened = tuple(max(0, c - 30) for c in rgb)
        return f'#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}'
    
    def create_main_area(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=8)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        self.create_tabs()
    
    def create_tabs(self):
        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        
        self.tabview.add("📁 Archivos")
        self.tabview.add("👁️ Vista Previa")
        self.tabview.add("📊 Metadatos")
        
        self.tabview.tab("📁 Archivos").grid_columnconfigure(0, weight=1)
        self.tabview.tab("📁 Archivos").grid_rowconfigure(1, weight=1)
        
        self.tabview.tab("👁️ Vista Previa").grid_columnconfigure(0, weight=1)
        self.tabview.tab("👁️ Vista Previa").grid_rowconfigure(0, weight=1)
        
        self.tabview.tab("📊 Metadatos").grid_columnconfigure(0, weight=1)
        
        self.setup_files_tab()
        self.setup_preview_tab()
        self.setup_metadata_tab()
    
    def setup_files_tab(self):
        tab = self.tabview.tab("📁 Archivos")
        
        search_frame = ctk.CTkFrame(tab)
        search_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        search_frame.grid_columnconfigure(0, weight=1)
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="🔍 Buscar...",
            height=35
        )
        self.search_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.search_entry.bind("<KeyRelease>", self.filter_files)
        
        list_frame = ctk.CTkFrame(tab)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)
        
        self.file_listbox = ctk.CTkScrollableFrame(
            list_frame,
            scrollbar_button_color="#2b2b2b"
        )
        self.file_listbox.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
    
    def setup_preview_tab(self):
        tab = self.tabview.tab("👁️ Vista Previa")
        
        self.preview_frame = ctk.CTkFrame(tab)
        self.preview_frame.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self.preview_frame.grid_columnconfigure(0, weight=1)
        self.preview_frame.grid_rowconfigure(1, weight=1)
        
        self.preview_title = ctk.CTkLabel(
            self.preview_frame,
            text="Seleccione un archivo para ver la vista previa",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.preview_title.grid(row=0, column=0, padx=15, pady=8, sticky="w")
        
        self.preview_content = ctk.CTkFrame(self.preview_frame)
        self.preview_content.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)
        self.preview_content.grid_columnconfigure(0, weight=1)
        self.preview_content.grid_rowconfigure(0, weight=1)
        
        self.show_preview_message("Seleccione un archivo para ver su contenido")
    
    def setup_metadata_tab(self):
        tab = self.tabview.tab("📊 Metadatos")
        
        self.metadata_content = ctk.CTkScrollableFrame(tab)
        self.metadata_content.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        
        self.metadata_message = ctk.CTkLabel(
            self.metadata_content,
            text="Seleccione un archivo para ver sus metadatos",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.metadata_message.pack(pady=40)
    
    def create_status_bar(self):
        status_frame = ctk.CTkFrame(self, height=30, corner_radius=0)
        status_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        status_frame.grid_columnconfigure(0, weight=1)
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="✅ Sistema listo",
            font=ctk.CTkFont(size=11)
        )
        self.status_label.grid(row=0, column=0, padx=12, pady=4, sticky="w")
        
        self.file_count_label = ctk.CTkLabel(
            status_frame,
            text="📊 Archivos: 0",
            font=ctk.CTkFont(size=11)
        )
        self.file_count_label.grid(row=0, column=1, padx=12, pady=4, sticky="e")
    
    def logout(self):
        self.cleanup_temp_files()
        self.destroy()
    
    def upload_file_dialog(self):
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo para subir",
            filetypes=[
                ("Todos los archivos", "*.*"),
                ("Imágenes", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff"),
                ("Documentos", "*.txt *.pdf *.doc *.docx *.xls *.xlsx"),
                ("Audio", "*.mp3 *.wav *.ogg *.flac"),
                ("Videos", "*.mp4 *.avi *.mkv *.mov")
            ]
        )
        
        if file_path:
            self.show_loading("Subiendo archivo...")
            
            def upload_thread():
                try:
                    file_size = os.path.getsize(file_path)
                    
                    # Límite de archivo: 10MB
                    max_file_size = 10 * 1024 * 1024  # 10 MB
                    if file_size > max_file_size:
                        self.after(0, lambda: messagebox.showerror("Error", 
                            f"El archivo es demasiado grande. Tamaño máximo: 10MB. Tu archivo: {file_size/1024/1024:.1f}MB"))
                        return
                    
                    with open(file_path, 'rb') as file:
                        file_content = file.read()
                    
                    encoded_content = base64.b64encode(file_content).decode('utf-8')
                    filename = os.path.basename(file_path)
                    
                    if self.system.create_file(filename, encoded_content, self.current_user, is_binary=True):
                        self.after(0, lambda: messagebox.showinfo("Éxito", f"Archivo '{filename}' subido correctamente"))
                        self.after(0, self.update_file_list)
                    else:
                        self.after(0, lambda: messagebox.showerror("Error", "No se pudo subir el archivo (¿ya existe?)"))
                        
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo subir el archivo: {str(e)}")
                finally:
                    self.after(0, self.hide_loading)
            
            threading.Thread(target=upload_thread, daemon=True).start()
        
    
    def show_loading(self, message="Cargando..."):
        self.loading = True
        self.status_label.configure(text=f"⏳ {message}")
    
    def hide_loading(self):
        self.loading = False
        self.status_label.configure(text="✅ Sistema listo")
    
    def show_preview_message(self, message):
        for widget in self.preview_content.winfo_children():
            widget.destroy()
        
        label = ctk.CTkLabel(
            self.preview_content,
            text=message,
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        label.pack(expand=True)
    
    def display_content(self, filename, content, is_binary=False):
        for widget in self.preview_content.winfo_children():
            widget.destroy()
        
        if hasattr(self, 'current_audio_file'):
            pygame.mixer.music.stop()
        
        if is_binary:
            self.show_loading("Procesando archivo...")
            
            def process_binary():
                try:
                    binary_content = base64.b64decode(content)
                    
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1])
                    temp_file.write(binary_content)
                    temp_file.close()
                    self.temp_files.append(temp_file.name)
                    
                    ext = os.path.splitext(filename)[1].lower()
                    
                    if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff']:
                        self.after(0, lambda: self.display_image(temp_file.name))
                    elif ext in ['.mp3', '.wav', '.ogg', '.flac']:
                        self.after(0, lambda: self.display_audio(temp_file.name, filename))
                    elif ext in ['.xlsx', '.xls']:
                        self.after(0, lambda: self.display_excel(temp_file.name, filename))
                    elif ext == '.pdf':
                        self.after(0, lambda: self.display_pdf_message(filename))
                    else:
                        self.after(0, lambda: self.display_binary_info(filename, len(binary_content)))
                        
                except Exception: 
                    self.after(0, lambda: self.show_preview_message("❌ No se pudo cargar el archivo o no tiene permisos de lectura"))
                finally:
                    self.after(0, self.hide_loading)
            
            threading.Thread(target=process_binary, daemon=True).start()
        else:
            self.display_text(content, filename)
    
    def display_image(self, image_path):
        try:
            image = Image.open(image_path)
            max_size = (600, 400)
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            
            image_label = ctk.CTkLabel(self.preview_content, image=photo, text="")
            image_label.image = photo
            image_label.pack(expand=True, padx=15, pady=15)
            
        except Exception as e:
            self.show_preview_message(f"Error al cargar imagen: {str(e)}")
    
    def display_audio(self, audio_path, filename):
        audio_frame = ctk.CTkFrame(self.preview_content)
        audio_frame.pack(expand=True, padx=15, pady=15)
        
        title_label = ctk.CTkLabel(
            audio_frame,
            text=f"🎵 {filename}",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title_label.pack(pady=8)
        
        controls_frame = ctk.CTkFrame(audio_frame)
        controls_frame.pack(pady=15)
        
        def play_audio():
            try:
                pygame.mixer.music.load(audio_path)
                pygame.mixer.music.play()
                self.current_audio_file = audio_path
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo reproducir el audio: {str(e)}")
        
        def stop_audio():
            pygame.mixer.music.stop()
        
        play_btn = ctk.CTkButton(
            controls_frame,
            text="▶️ Reproducir",
            command=play_audio,
            fg_color="#4CAF50",
            hover_color="#45a049"
        )
        play_btn.pack(side="left", padx=8)
        
        stop_btn = ctk.CTkButton(
            controls_frame,
            text="⏹️ Detener",
            command=stop_audio,
            fg_color="#f44336",
            hover_color="#da190b"
        )
        stop_btn.pack(side="left", padx=8)
    
    def display_excel(self, excel_path, filename):
        try:
            df = pd.read_excel(excel_path)
            
            table_frame = ctk.CTkScrollableFrame(self.preview_content)
            table_frame.pack(fill="both", expand=True, padx=8, pady=8)
            
            title_label = ctk.CTkLabel(
                table_frame,
                text=f"📊 {filename} - {len(df)} filas × {len(df.columns)} columnas",
                font=ctk.CTkFont(size=12, weight="bold")
            )
            title_label.pack(pady=8)
            
            display_df = df.head(50)
            
            for i, (index, row) in enumerate(display_df.iterrows()):
                row_frame = ctk.CTkFrame(table_frame)
                row_frame.pack(fill="x", padx=4, pady=1)
                
                for j, value in enumerate(row):
                    cell = ctk.CTkLabel(
                        row_frame,
                        text=str(value)[:30] + ("..." if len(str(value)) > 30 else ""),
                        width=100,
                        height=22,
                        font=ctk.CTkFont(size=9),
                        anchor="w"
                    )
                    cell.pack(side="left", padx=1, pady=1, fill="x", expand=True)
            
            if len(df) > 50:
                info_label = ctk.CTkLabel(
                    table_frame,
                    text=f"Mostrando 50 de {len(df)} filas",
                    text_color="gray",
                    font=ctk.CTkFont(size=9)
                )
                info_label.pack(pady=8)
                
        except Exception as e:
            self.show_preview_message(f"Error al leer archivo Excel: {str(e)}")
    
    def display_pdf_message(self, filename):
        pdf_frame = ctk.CTkFrame(self.preview_content)
        pdf_frame.pack(expand=True, padx=15, pady=15)
        
        message = ctk.CTkLabel(
            pdf_frame,
            text=f"📄 {filename}\n\nLos archivos PDF pueden ser visualizados\ndescargando el archivo y abriéndolo\ncon un visor de PDF.",
            font=ctk.CTkFont(size=12),
            justify="center"
        )
        message.pack(pady=15)
    
    def display_binary_info(self, filename, size):
        info_frame = ctk.CTkFrame(self.preview_content)
        info_frame.pack(expand=True, padx=15, pady=15)
        
        message = ctk.CTkLabel(
            info_frame,
            text=f"📦 {filename}\n\nTipo: Archivo binario\nTamaño: {size} bytes\n\nEste tipo de archivo puede ser descargado\npara su uso externo.",
            font=ctk.CTkFont(size=12),
            justify="center"
        )
        message.pack(pady=15)
    
    def display_text(self, content, filename):
        text_frame = ctk.CTkFrame(self.preview_content)
        text_frame.grid(row=0, column=0, sticky="nsew")
        text_frame.grid_columnconfigure(0, weight=1)
        text_frame.grid_rowconfigure(0, weight=1)
        
        text_widget = scrolledtext.ScrolledText(
            text_frame,
            wrap="word",
            font=("Consolas", 11),
            bg="#2b2b2b",
            fg="white",
            insertbackground="white"
        )
        text_widget.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        text_widget.insert(1.0, content)
        text_widget.config(state="disabled")
    
    def update_file_list(self, files=None):
        if files is None:
            files = self.system.list_files()
        
        for widget in self.file_listbox.winfo_children():
            widget.destroy()
        
        if not files:
            empty_label = ctk.CTkLabel(
                self.file_listbox,
                text="📭 No hay archivos disponibles",
                text_color="gray",
                font=ctk.CTkFont(size=11)
            )
            empty_label.pack(padx=8, pady=15)
            self.file_count_label.configure(text="📊 Archivos: 0")
            return
        
        for file_info in files:
            self.add_file_to_list(file_info)
        
        self.update_status(f"✅ Mostrando {len(files)} archivos")
        self.file_count_label.configure(text=f"📊 Archivos: {len(files)}")
    
    def add_file_to_list(self, file_info):
        file_frame = ctk.CTkFrame(self.file_listbox, corner_radius=6)
        file_frame.pack(fill="x", padx=4, pady=2)
        
        filename = file_info['filename']
        ext = os.path.splitext(filename)[1].lower()
        
        if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            icon = "🖼️"
        elif ext in ['.mp3', '.wav', '.ogg']:
            icon = "🎵"
        elif ext in ['.xlsx', '.xls']:
            icon = "📊"
        elif ext == '.pdf':
            icon = "📄"
        elif ext in ['.txt', '.doc', '.docx']:
            icon = "📝"
        else:
            icon = "📦"
        
        info_text = f"{icon} {filename}\n   📏 {file_info['total_chars']} chars • 👤 {file_info['owner']}"
        
        file_label = ctk.CTkLabel(
            file_frame,
            text=info_text,
            font=ctk.CTkFont(size=11),
            anchor="w",
            justify="left"
        )
        file_label.pack(side="left", padx=12, pady=8, fill="x", expand=True)
        
        btn_frame = ctk.CTkFrame(file_frame, fg_color="transparent")
        btn_frame.pack(side="right", padx=4, pady=4)
        
        select_btn = ctk.CTkButton(
            btn_frame,
            text="Abrir",
            width=70,
            height=30,
            command=lambda f=file_info['filename']: self.select_file(f),
            fg_color="#2196F3",
            hover_color="#1976D2"
        )
        select_btn.pack(side="left", padx=1)
        
        if file_info['owner'] == self.current_user:
            delete_btn = ctk.CTkButton(
                btn_frame,
                text="🗑️",
                width=35,
                height=30,
                command=lambda f=file_info['filename']: self.delete_file_dialog(f),
                fg_color="#757575",
                hover_color="#616161"
            )
            delete_btn.pack(side="left", padx=1)
    
    def select_file(self, filename):
        self.current_file = filename
        
        self.preview_title.configure(text=f"👁️ Vista previa: {filename}")
        self.tabview.set("👁️ Vista Previa")
        
        self.show_loading("Cargando archivo...")
        
        def load_file_thread():
            file_info, content = self.system.open_file(filename, self.current_user)
            
            if file_info and content is not None:
                is_binary = file_info.get('is_binary', False)
                self.after(0, lambda: self.display_content(filename, content, is_binary))
                self.after(0, lambda: self.show_metadata(file_info))
            else:
                self.after(0, lambda: self.show_preview_message("❌ No se pudo cargar el archivo o no tiene permisos de lectura"))
                self.after(0, self.hide_metadata)
            self.after(0, self.hide_loading)
        
        threading.Thread(target=load_file_thread, daemon=True).start()
    
    def show_metadata(self, file_info):
        for widget in self.metadata_content.winfo_children():
            widget.destroy()
        
        self.metadata_content.grid_columnconfigure(1, weight=1)
        
        title_label = ctk.CTkLabel(
            self.metadata_content,
            text="📊 Metadatos del Archivo",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=15)
        
        labels = [
            ("📝 Nombre:", file_info['filename']),
            ("👤 Propietario:", file_info['owner']),
            ("📏 Tamaño:", f"{file_info['total_chars']} caracteres"),
            ("📅 Creación:", file_info['creation_date'][:19]),
            ("✏️ Modificación:", file_info['modification_date'][:19]),
            ("🗑️ En Papelera:", "✅ Sí" if file_info['in_recycle_bin'] else "❌ No"),
            ("🔧 Tipo:", "📦 Binario" if file_info.get('is_binary', False) else "📝 Texto")
        ]
        
        for i, (label, value) in enumerate(labels, 1):
            lbl = ctk.CTkLabel(
                self.metadata_content, 
                text=label, 
                font=ctk.CTkFont(weight="bold", size=11)
            )
            lbl.grid(row=i, column=0, padx=12, pady=6, sticky="w")
            
            val = ctk.CTkLabel(self.metadata_content, text=value, font=ctk.CTkFont(size=11))
            val.grid(row=i, column=1, padx=12, pady=6, sticky="w")
        
        perms_label = ctk.CTkLabel(
            self.metadata_content, 
            text="🔐 Permisos:", 
            font=ctk.CTkFont(weight="bold", size=11)
        )
        perms_label.grid(row=len(labels)+1, column=0, padx=12, pady=6, sticky="w")
        
        perms_text = "\n".join([f"• {user}: {', '.join(perms)}" for user, perms in file_info['permissions'].items()])
        perms_value = ctk.CTkLabel(
            self.metadata_content, 
            text=perms_text, 
            font=ctk.CTkFont(size=11),
            justify="left"
        )
        perms_value.grid(row=len(labels)+1, column=1, padx=12, pady=6, sticky="w")
    
    def hide_metadata(self):
        for widget in self.metadata_content.winfo_children():
            widget.destroy()
        
        self.metadata_message = ctk.CTkLabel(
            self.metadata_content,
            text="Seleccione un archivo para ver sus metadatos",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.metadata_message.pack(pady=40)
    
    def filter_files(self, event=None):
        search_term = self.search_entry.get().lower()
        all_files = self.system.list_files()
        
        if not search_term:
            filtered_files = all_files
        else:
            filtered_files = [
                f for f in all_files 
                if search_term in f['filename'].lower() or search_term in f['owner'].lower()
            ]
        
        self.update_file_list(filtered_files)
    
    def create_file_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("📄 Crear Nuevo Archivo")
        dialog.geometry("550x450")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(True, True)
        
        self.center_dialog(dialog, 550, 450)
        
        ctk.CTkLabel(dialog, text="📝 Nombre del archivo:", font=ctk.CTkFont(weight="bold")).pack(pady=8)
        name_entry = ctk.CTkEntry(dialog, width=350, height=30)
        name_entry.pack(pady=4)
        
        ctk.CTkLabel(dialog, text="📋 Contenido:", font=ctk.CTkFont(weight="bold")).pack(pady=8)
        content_text = scrolledtext.ScrolledText(dialog, height=12, width=60)
        content_text.pack(pady=4, padx=15, fill="both", expand=True)
        
        def create_file():
            filename = name_entry.get().strip()
            content = content_text.get(1.0, "end").strip()
            
            if not filename:
                messagebox.showerror("Error", "❌ El nombre del archivo es requerido")
                return
            
            if self.system.create_file(filename, content, self.current_user):
                messagebox.showinfo("Éxito", "✅ Archivo creado correctamente")
                self.update_file_list()
                dialog.destroy()
            else:
                messagebox.showerror("Error", "❌ No se pudo crear el archivo (¿ya existe?)")
        
        ctk.CTkButton(
            dialog, 
            text="💾 Crear Archivo", 
            command=create_file,
            height=35,
            fg_color="#4CAF50",
            hover_color="#45a049"
        ).pack(pady=8)
    
    def create_user_dialog(self):
        from user_manager import UserManager
        user_manager = UserManager()
        
        dialog = ctk.CTkToplevel(self)
        dialog.title("👥 Crear Nuevo Usuario")
        dialog.geometry("350x400")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(True, True)
        
        self.center_dialog(dialog, 350, 400)
        
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        ctk.CTkLabel(
            main_frame,
            text="👥 Crear Nuevo Usuario",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=15)
        
        form_frame = ctk.CTkFrame(main_frame)
        form_frame.pack(fill="x", padx=8, pady=8)
        
        ctk.CTkLabel(form_frame, text="Nuevo Usuario:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(8, 3))
        new_user_entry = ctk.CTkEntry(form_frame)
        new_user_entry.pack(fill="x", pady=3)
        
        ctk.CTkLabel(form_frame, text="Contraseña:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(8, 3))
        new_pass_entry = ctk.CTkEntry(form_frame, show="•")
        new_pass_entry.pack(fill="x", pady=3)
        
        ctk.CTkLabel(form_frame, text="Confirmar Contraseña:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(8, 3))
        confirm_pass_entry = ctk.CTkEntry(form_frame, show="•")
        confirm_pass_entry.pack(fill="x", pady=3)
        
        ctk.CTkLabel(form_frame, text="Rol:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(8, 3))
        role_var = ctk.StringVar(value="user")
        role_combo = ctk.CTkComboBox(
            form_frame,
            values=["user", "admin"],
            variable=role_var
        )
        role_combo.pack(fill="x", pady=3)
        
        status_label = ctk.CTkLabel(form_frame, text="", text_color="red")
        status_label.pack(pady=8)
        
        def create_user():
            new_user = new_user_entry.get().strip()
            new_pass = new_pass_entry.get().strip()
            confirm_pass = confirm_pass_entry.get().strip()
            role = role_var.get()
            
            if not all([new_user, new_pass, confirm_pass]):
                status_label.configure(text="Todos los campos son requeridos", text_color="red")
                return
            
            if new_pass != confirm_pass:
                status_label.configure(text="Las contraseñas no coinciden", text_color="red")
                return
            
            success, message = user_manager.create_user(new_user, new_pass, role, self.current_user)
            
            if success:
                status_label.configure(text=message, text_color="green")
                dialog.after(2000, dialog.destroy)
            else:
                status_label.configure(text=message, text_color="red")
        
        ctk.CTkButton(
            form_frame,
            text="Crear Usuario",
            command=create_user
        ).pack(fill="x", pady=8)
    
    def delete_user_dialog(self):
        from user_manager import UserManager
        user_manager = UserManager()
        
        users = user_manager.get_all_users()
        if not users:
            messagebox.showinfo("Información", "No hay usuarios para eliminar")
            return
        
        dialog = ctk.CTkToplevel(self)
        dialog.title("🗑️ Eliminar Usuario")
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(True, True)
        
        self.center_dialog(dialog, 400, 300)
        
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        ctk.CTkLabel(
            main_frame,
            text="🗑️ Eliminar Usuario",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)
        
        ctk.CTkLabel(main_frame, text="Seleccione el usuario a eliminar:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 5))
        
        user_list_frame = ctk.CTkScrollableFrame(main_frame, height=150)
        user_list_frame.pack(fill="both", expand=True, pady=5)
        
        selected_user = ctk.StringVar()
        
        for i, username in enumerate(users):
            if username != self.current_user:
                user_radio = ctk.CTkRadioButton(
                    user_list_frame,
                    text=username,
                    variable=selected_user,
                    value=username
                )
                user_radio.pack(anchor="w", padx=10, pady=3)
        
        def delete_user():
            username = selected_user.get()
            if not username:
                messagebox.showwarning("Advertencia", "Seleccione un usuario para eliminar")
                return
            
            if username == self.current_user:
                messagebox.showerror("Error", "No puede eliminarse a sí mismo")
                return
            
            result = messagebox.askyesno(
                "Confirmar Eliminación",
                f"¿Está seguro de que desea eliminar al usuario '{username}'?\n\n⚠️ Esta acción no se puede deshacer.",
                icon="warning"
            )
            
            if result:
                success, message = user_manager.delete_user(username, self.current_user)
                if success:
                    messagebox.showinfo("Éxito", message)
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", message)
        
        ctk.CTkButton(
            main_frame,
            text="🗑️ Eliminar Usuario",
            command=delete_user,
            fg_color="#f44336",
            hover_color="#da190b"
        ).pack(fill="x", pady=10)
    
    def open_file_dialog(self):
        if not self.current_file:
            messagebox.showwarning("Advertencia", "Seleccione un archivo primero")
            return
        
        self.select_file(self.current_file)
    
    def modify_file_dialog(self):
        if not self.current_file:
            messagebox.showwarning("Advertencia", "Seleccione un archivo primero")
            return
        
        file_info = self.system.get_file_info(self.current_file)
        if not file_info:
            messagebox.showerror("Error", "Archivo no encontrado")
            return
        
        from permission_manager import PermissionManager
        perm_manager = PermissionManager()
        
        if not perm_manager.can_write(file_info, self.current_user):
            messagebox.showerror("Error", "No tiene permisos de escritura para este archivo")
            return
        
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"✏️ Modificar Archivo: {self.current_file}")
        dialog.geometry("550x450")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(True, True)
        
        self.center_dialog(dialog, 550, 450)
        
        file_info, current_content = self.system.open_file(self.current_file, self.current_user)
        
        ctk.CTkLabel(dialog, text="Contenido actual:", font=ctk.CTkFont(weight="bold")).pack(pady=8)
        content_text = scrolledtext.ScrolledText(dialog, height=12, width=60)
        content_text.pack(pady=4, padx=15, fill="both", expand=True)
        content_text.insert(1.0, current_content)
        
        def modify_file():
            new_content = content_text.get(1.0, "end").strip()
            
            if self.system.modify_file(self.current_file, new_content, self.current_user):
                messagebox.showinfo("Éxito", "✅ Archivo modificado correctamente")
                self.update_file_list()
                self.select_file(self.current_file)
                dialog.destroy()
            else:
                messagebox.showerror("Error", "❌ No se pudo modificar el archivo")
        
        ctk.CTkButton(
            dialog, 
            text="💾 Guardar Cambios", 
            command=modify_file,
            fg_color="#4CAF50",
            hover_color="#45a049"
        ).pack(pady=8)
    
    def delete_file_dialog(self, filename=None):
        target_file = filename or self.current_file
        
        if not target_file:
            messagebox.showwarning("Advertencia", "Seleccione un archivo primero")
            return
        
        file_info = self.system.get_file_info(target_file)
        if not file_info:
            messagebox.showerror("Error", "Archivo no encontrado")
            return
        
        if file_info['owner'] != self.current_user:
            messagebox.showerror("Error", "❌ Solo el propietario puede eliminar el archivo")
            return
        
        result = messagebox.askyesno(
            "Confirmar Eliminación", 
            f"¿Está seguro de que desea mover '{target_file}' a la papelera?"
        )
        
        if result:
            if self.system.delete_file(target_file, self.current_user):
                messagebox.showinfo("Éxito", "🗑️ Archivo movido a la papelera")
                self.update_file_list()
                if target_file == self.current_file:
                    self.current_file = None
                    self.show_preview_message("Seleccione un archivo para ver su contenido")
                    self.hide_metadata()
                    self.preview_title.configure(text="Seleccione un archivo para ver la vista previa")
            else:
                messagebox.showerror("Error", "❌ No se pudo eliminar el archivo")
    
    def show_recycle_bin(self):
        recycle_files = self.system.list_recycle_bin()
        
        dialog = ctk.CTkToplevel(self)
        dialog.title("🗑️ Papelera de Reciclaje")
        dialog.geometry("650x450")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(True, True)
        
        self.center_dialog(dialog, 650, 450)
        
        if not recycle_files:
            ctk.CTkLabel(dialog, text="🗑️ La papelera está vacía", font=ctk.CTkFont(size=12)).pack(pady=40)
            return
        
        title_frame = ctk.CTkFrame(dialog)
        title_frame.pack(fill="x", padx=15, pady=8)
        
        ctk.CTkLabel(
            title_frame, 
            text=f"🗑️ Papelera de Reciclaje ({len(recycle_files)} archivos)",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack()
        
        list_frame = ctk.CTkScrollableFrame(dialog)
        list_frame.pack(fill="both", expand=True, padx=15, pady=8)
        
        for file_info in recycle_files:
            file_frame = ctk.CTkFrame(list_frame)
            file_frame.pack(fill="x", padx=4, pady=1)
            
            info_text = f"{file_info['filename']}\n🗓️ Eliminado: {file_info['deletion_date'][:19]} • 👤 {file_info['owner']}"
            
            file_label = ctk.CTkLabel(
                file_frame, 
                text=info_text, 
                anchor="w",
                justify="left"
            )
            file_label.pack(side="left", padx=8, pady=6, fill="x", expand=True)
            
            btn_frame = ctk.CTkFrame(file_frame, fg_color="transparent")
            btn_frame.pack(side="right", padx=4, pady=4)
            
            def recover_cmd(f=file_info['filename']):
                if self.system.recover_file(f, self.current_user):
                    messagebox.showinfo("Éxito", "✅ Archivo recuperado")
                    dialog.destroy()
                    self.update_file_list()
                    self.show_recycle_bin()
                else:
                    messagebox.showerror("Error", "❌ No se pudo recuperar el archivo")
            
            def delete_permanent_cmd(f=file_info['filename']):
                result = messagebox.askyesno(
                    "Eliminar Permanentemente",
                    f"¿Está seguro de que desea eliminar permanentemente '{f}'?\n\n⚠️ Esta acción no se puede deshacer.",
                    icon="warning"
                )
                if result:
                    if self.system.delete_file_permanently(f, self.current_user):
                        messagebox.showinfo("Éxito", "🗑️ Archivo eliminado permanentemente")
                        dialog.destroy()
                        self.update_file_list()
                        self.show_recycle_bin()
                    else:
                        messagebox.showerror("Error", "❌ No se pudo eliminar el archivo")
            
            recover_btn = ctk.CTkButton(
                btn_frame, 
                text="📤 Recuperar", 
                width=70,
                command=recover_cmd,
                fg_color="#4CAF50",
                hover_color="#45a049"
            )
            recover_btn.pack(side="left", padx=1)
            
            delete_btn = ctk.CTkButton(
                btn_frame,
                text="🔥 Eliminar",
                width=70,
                command=delete_permanent_cmd,
                fg_color="#f44336",
                hover_color="#da190b"
            )
            delete_btn.pack(side="left", padx=1)
    
    def create_backup_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("💾 Crear Backup del Sistema")
        dialog.geometry("450x350")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(True, True)
        
        self.center_dialog(dialog, 450, 350)
        
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        ctk.CTkLabel(
            main_frame,
            text="💾 Crear Backup del Sistema",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=15)
        
        info_text = (
            "Se creará un backup completo que incluye:\n"
            "• Tabla FAT con metadatos de archivos\n"
            "• Todos los bloques de datos\n"
            "• Archivos grandes\n"
            "• Información de usuarios y permisos"
        )
        
        info_label = ctk.CTkLabel(
            main_frame,
            text=info_text,
            font=ctk.CTkFont(size=11),
            justify="left"
        )
        info_label.pack(pady=8)
        
        ctk.CTkLabel(main_frame, text="Nombre del backup:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(15, 3))
        backup_name_entry = ctk.CTkEntry(main_frame, placeholder_text="Dejar vacío para nombre automático")
        backup_name_entry.pack(fill="x", pady=3)
        
        status_frame = ctk.CTkFrame(main_frame)
        status_frame.pack(fill="x", pady=15)
        
        status_label = ctk.CTkLabel(status_frame, text="", font=ctk.CTkFont(size=11))
        status_label.pack(pady=8)
        
        progress_bar = ctk.CTkProgressBar(status_frame)
        progress_bar.pack(fill="x", pady=4)
        progress_bar.set(0)
        progress_bar.pack_forget()
        
        def create_backup():
            backup_name = backup_name_entry.get().strip()
            if not backup_name:
                backup_name = None
            
            status_label.configure(text="⏳ Creando backup... Esto puede tomar unos momentos", text_color="blue")
            progress_bar.pack(fill="x", pady=4)
            progress_bar.set(0.3)
            dialog.update()
            
            def backup_thread():
                try:
                    success, message = self.system.create_backup(backup_name)
                    
                    if success:
                        self.after(0, lambda: progress_bar.set(1.0))
                        self.after(0, lambda: status_label.configure(text=f"✅ {message}", text_color="green"))
                        self.after(3000, dialog.destroy)
                        self.after(0, lambda: messagebox.showinfo("Backup Exitoso", message))
                    else:
                        self.after(0, lambda: status_label.configure(text=f"❌ {message}", text_color="red"))
                        self.after(0, lambda: progress_bar.pack_forget())
                        
                except Exception:
                    self.after(0, lambda: status_label.configure(text="❌ Error inesperado al crear el backup", text_color="red"))
                    self.after(0, lambda: progress_bar.pack_forget())
            
            threading.Thread(target=backup_thread, daemon=True).start()
        
        create_btn = ctk.CTkButton(
            main_frame,
            text="💾 Crear Backup",
            command=create_backup,
            height=40,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#673AB7",
            hover_color="#5E35B1"
        )
        create_btn.pack(fill="x", pady=8)
        
        ctk.CTkButton(
            main_frame,
            text="Cancelar",
            command=dialog.destroy,
            height=30,
            fg_color="transparent",
            border_width=2,
            text_color=("gray10", "#DCE4EE")
        ).pack(fill="x", pady=4)
    
    def restore_backup_dialog(self):
        backups = self.system.list_backups()
        
        dialog = ctk.CTkToplevel(self)
        dialog.title("📂 Restaurar Backup")
        dialog.geometry("550x450")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(True, True)
        
        self.center_dialog(dialog, 550, 450)
        
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        ctk.CTkLabel(
            main_frame,
            text="📂 Restaurar Backup del Sistema",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=15)
        
        if not backups:
            ctk.CTkLabel(
                main_frame,
                text="No hay backups disponibles.\nCrea un backup primero usando la opción '💾 Crear Backup'.",
                font=ctk.CTkFont(size=12),
                text_color="gray",
                justify="center"
            ).pack(expand=True)
            return
        
        warning_text = (
            "⚠️ ADVERTENCIA: Al restaurar un backup:\n"
            "• Todos los datos actuales serán reemplazados\n"
            "• Se creará un backup automático antes de restaurar\n"
            "• Esta acción no se puede deshacer"
        )
        
        warning_label = ctk.CTkLabel(
            main_frame,
            text=warning_text,
            font=ctk.CTkFont(size=11),
            text_color="orange",
            justify="left"
        )
        warning_label.pack(pady=8)
        
        list_frame = ctk.CTkScrollableFrame(main_frame)
        list_frame.pack(fill="both", expand=True, padx=8, pady=8)
        
        for backup in backups:
            backup_frame = ctk.CTkFrame(list_frame)
            backup_frame.pack(fill="x", padx=4, pady=2)
            
            size_mb = backup['size'] / (1024 * 1024)
            created_date = datetime.fromisoformat(backup['created']).strftime("%Y-%m-%d %H:%M:%S")
            info_text = f"{backup['name']}\n📏 {size_mb:.2f} MB • 🗓️ {created_date}"
            
            backup_label = ctk.CTkLabel(
                backup_frame, 
                text=info_text, 
                anchor="w", 
                justify="left",
                font=ctk.CTkFont(size=11)
            )
            backup_label.pack(side="left", padx=8, pady=6, fill="x", expand=True)
            
            btn_frame = ctk.CTkFrame(backup_frame, fg_color="transparent")
            btn_frame.pack(side="right", padx=4, pady=4)
            
            def create_restore_cmd(backup_path=backup['path'], backup_name=backup['name']):
                def restore_backup():
                    result = messagebox.askyesno(
                        "Confirmar Restauración",
                        f"¿Está seguro de que desea restaurar el backup?\n\n"
                        f"Backup: {backup_name}\n\n"
                        f"⚠️ Todos los datos actuales serán reemplazados.\n"
                        f"Se creará un backup automático antes de proceder.",
                        icon="warning"
                    )
                    if result:
                        progress_dialog = ctk.CTkToplevel(dialog)
                        progress_dialog.title("Restaurando Backup")
                        progress_dialog.geometry("350x180")
                        progress_dialog.transient(dialog)
                        progress_dialog.grab_set()
                        progress_dialog.resizable(False, False)
                        
                        self.center_dialog(progress_dialog, 350, 180)
                        
                        progress_frame = ctk.CTkFrame(progress_dialog)
                        progress_frame.pack(fill="both", expand=True, padx=15, pady=15)
                        
                        ctk.CTkLabel(
                            progress_frame,
                            text="🔄 Restaurando Backup",
                            font=ctk.CTkFont(size=14, weight="bold")
                        ).pack(pady=8)
                        
                        progress_label = ctk.CTkLabel(
                            progress_frame,
                            text="Restaurando datos del sistema...",
                            font=ctk.CTkFont(size=11)
                        )
                        progress_label.pack(pady=8)
                        
                        progress_bar = ctk.CTkProgressBar(progress_frame)
                        progress_bar.pack(fill="x", pady=8)
                        progress_bar.set(0.3)
                        
                        def restore_thread():
                            try:
                                success, message = self.system.restore_backup(backup_path)
                                
                                if success:
                                    self.after(0, lambda: progress_bar.set(1.0))
                                    self.after(0, lambda: progress_label.configure(text="✅ Backup restaurado exitosamente"))
                                    self.after(2000, progress_dialog.destroy)
                                    self.after(2000, dialog.destroy)
                                    self.after(2000, self.update_file_list)
                                    self.after(2000, lambda: messagebox.showinfo("Restauración Exitosa", message))
                                else:
                                    self.after(0, lambda: progress_label.configure(text=f"❌ Error: {message}"))
                                    self.after(0, lambda: progress_bar.pack_forget())
                                    
                            except Exception:
                                self.after(0, lambda: progress_label.configure(text="❌ Error inesperado al restaurar el backup"))
                                self.after(0, lambda: progress_bar.pack_forget())
                        
                        threading.Thread(target=restore_thread, daemon=True).start()
                
                restore_backup()
            
            def create_delete_cmd(backup_name=backup['name']):
                def delete_backup():
                    result = messagebox.askyesno(
                        "Eliminar Backup",
                        f"¿Está seguro de que desea eliminar el backup '{backup_name}'?",
                        icon="warning"
                    )
                    if result:
                        success, message = self.system.delete_backup(backup_name)
                        if success:
                            messagebox.showinfo("Backup Eliminado", message)
                            dialog.destroy()
                            self.restore_backup_dialog()
                        else:
                            messagebox.showerror("Error", message)
                
                delete_backup()
            
            restore_btn = ctk.CTkButton(
                btn_frame,
                text="🔄 Restaurar",
                width=70,
                command=create_restore_cmd,
                fg_color="#009688",
                hover_color="#00897B"
            )
            restore_btn.pack(side="left", padx=1)
            
            delete_btn = ctk.CTkButton(
                btn_frame,
                text="🗑️",
                width=35,
                command=create_delete_cmd,
                fg_color="#f44336",
                hover_color="#da190b"
            )
            delete_btn.pack(side="left", padx=1)
    
    def manage_permissions_dialog(self):
        if not self.current_file:
            messagebox.showwarning("Advertencia", "Seleccione un archivo primero")
            return
        
        file_info = self.system.get_file_info(self.current_file)
        if not file_info or file_info['owner'] != self.current_user:
            messagebox.showerror("Error", "❌ Solo el propietario puede gestionar permisos")
            return
        
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"🔐 Gestionar Permisos: {self.current_file}")
        dialog.geometry("450x350")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(True, True)
        
        self.center_dialog(dialog, 450, 350)
        
        current_frame = ctk.CTkFrame(dialog)
        current_frame.pack(fill="x", padx=15, pady=8)
        
        ctk.CTkLabel(current_frame, text="🔐 Permisos Actuales:", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        
        permissions_text = ""
        for user, perms in file_info['permissions'].items():
            permissions_text += f"• {user}: {', '.join(perms)}\n"
        
        perms_label = ctk.CTkLabel(current_frame, text=permissions_text, justify="left")
        perms_label.pack(anchor="w", pady=4)
        
        manage_frame = ctk.CTkFrame(dialog)
        manage_frame.pack(fill="x", padx=15, pady=8)
        
        ctk.CTkLabel(manage_frame, text="Usuario:").grid(row=0, column=0, padx=4, pady=4, sticky="w")
        user_entry = ctk.CTkEntry(manage_frame)
        user_entry.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        
        ctk.CTkLabel(manage_frame, text="Permiso:").grid(row=1, column=0, padx=4, pady=4, sticky="w")
        permission_var = ctk.StringVar(value="read")
        permission_combo = ctk.CTkComboBox(
            manage_frame, 
            values=["read", "write"],
            variable=permission_var
        )
        permission_combo.grid(row=1, column=1, padx=4, pady=4, sticky="ew")
        
        manage_frame.grid_columnconfigure(1, weight=1)
        
        def grant_permission():
            user = user_entry.get().strip()
            permission = permission_var.get()
            
            if not user:
                messagebox.showerror("Error", "❌ El usuario es requerido")
                return
            
            if self.system.grant_permission(self.current_file, self.current_user, user, permission):
                messagebox.showinfo("Éxito", "✅ Permiso concedido")
                dialog.destroy()
                self.select_file(self.current_file)
            else:
                messagebox.showerror("Error", "❌ No se pudo conceder el permiso")
        
        def revoke_permission():
            user = user_entry.get().strip()
            permission = permission_var.get()
            
            if not user:
                messagebox.showerror("Error", "❌ El usuario es requerido")
                return
            
            if self.system.revoke_permission(self.current_file, self.current_user, user, permission):
                messagebox.showinfo("Éxito", "✅ Permiso revocado")
                dialog.destroy()
                self.select_file(self.current_file)
            else:
                messagebox.showerror("Error", "❌ No se pudo revocar el permiso")
        
        btn_frame = ctk.CTkFrame(dialog)
        btn_frame.pack(pady=8)
        
        ctk.CTkButton(
            btn_frame, 
            text="➕ Conceder Permiso", 
            command=grant_permission,
            fg_color="#4CAF50",
            hover_color="#45a049"
        ).pack(side="left", padx=4)
        
        ctk.CTkButton(
            btn_frame, 
            text="➖ Revocar Permiso", 
            command=revoke_permission,
            fg_color="#f44336",
            hover_color="#da190b"
        ).pack(side="left", padx=4)
    
    def update_status(self, message):
        self.status_label.configure(text=message)
        self.after(5000, lambda: self.status_label.configure(text="✅ Sistema listo"))

    def center_dialog(self, dialog, width, height):
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (width // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')
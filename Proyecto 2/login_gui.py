import customtkinter as ctk
from tkinter import messagebox
from user_manager import UserManager

class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configuración de la ventana
        self.title("Sistema FAT - Login")
        self.geometry("400x500")
        self.resizable(False, False)
        
        # Centrar ventana
        self.center_window()
        
        # Inicializar gestor de usuarios
        self.user_manager = UserManager()
        
        # Variable para almacenar el usuario autenticado
        self.logged_in_user = None
        self.user_role = None
        
        # Crear interfaz
        self.create_widgets()
        
        # Hacer focus en el campo de usuario
        self.after(100, self.username_entry.focus)
    
    def center_window(self):
        """Centra la ventana en la pantalla"""
        self.update_idletasks()
        width = 400
        height = 500
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_widgets(self):
        """Crea los widgets de la interfaz de login"""
        # Frame principal
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        title_label = ctk.CTkLabel(
            main_frame,
            text="Sistema de Archivos FAT",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=40)
        
        # Subtítulo
        subtitle_label = ctk.CTkLabel(
            main_frame,
            text="Iniciar Sesión",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        subtitle_label.pack(pady=10)
        
        # Frame de formulario
        form_frame = ctk.CTkFrame(main_frame)
        form_frame.pack(fill="x", padx=40, pady=30)
        
        # Campo de usuario
        ctk.CTkLabel(form_frame, text="Usuario:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 5))
        self.username_entry = ctk.CTkEntry(form_frame, placeholder_text="Ingrese su usuario")
        self.username_entry.pack(fill="x", pady=5)
        self.username_entry.bind("<Return>", lambda e: self.password_entry.focus())
        
        # Campo de contraseña
        ctk.CTkLabel(form_frame, text="Contraseña:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 5))
        self.password_entry = ctk.CTkEntry(form_frame, placeholder_text="Ingrese su contraseña", show="•")
        self.password_entry.pack(fill="x", pady=5)
        self.password_entry.bind("<Return>", lambda e: self.login())
        
        # Botón de login
        self.login_button = ctk.CTkButton(
            form_frame,
            text="Iniciar Sesión",
            command=self.login,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.login_button.pack(fill="x", pady=20)
        
        # Separador
        separator = ctk.CTkFrame(form_frame, height=2, fg_color="gray30")
        separator.pack(fill="x", pady=20)
        
        # Botón de crear usuario
        self.create_user_button = ctk.CTkButton(
            form_frame,
            text="Crear Nuevo Usuario",
            command=self.show_create_user_dialog,
            height=35,
            fg_color="transparent",
            border_width=2,
            text_color=("gray10", "#DCE4EE")
        )
        self.create_user_button.pack(fill="x", pady=5)
        
        # Etiqueta de estado
        self.status_label = ctk.CTkLabel(
            form_frame,
            text="",
            text_color="red",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(pady=10)
        
        # Información de credenciales por defecto
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.pack(fill="x", padx=20, pady=10)
        
        info_label = ctk.CTkLabel(
            info_frame,
            text="Usuario demo: admin / admin123",
            text_color="gray",
            font=ctk.CTkFont(size=12)
        )
        info_label.pack(pady=10)
    
    def login(self):
        """Maneja el proceso de login"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username:
            self.show_status("Por favor ingrese su usuario", "red")
            self.username_entry.focus()
            return
        
        if not password:
            self.show_status("Por favor ingrese su contraseña", "red")
            self.password_entry.focus()
            return
        
        # Deshabilitar botón temporalmente
        self.login_button.configure(state="disabled")
        self.create_user_button.configure(state="disabled")
        
        # Autenticar usuario
        success, role = self.user_manager.authenticate(username, password)
        
        if success:
            self.logged_in_user = username
            self.user_role = role
            self.show_status(f"¡Bienvenido {username}!", "green")
            self.after(1000, self.open_main_app) 
        else:
            self.show_status("Usuario o contraseña incorrectos", "red")
            self.password_entry.delete(0, 'end')
            self.password_entry.focus()
        
        # Rehabilitar botones
        self.login_button.configure(state="normal")
        self.create_user_button.configure(state="normal")
    
    def show_create_user_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Crear Nuevo Usuario")
        dialog.geometry("400x500")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        # Centrar diálogo
        self.center_dialog(dialog, 400, 500)
        
        # Frame principal
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            main_frame,
            text="Crear Nuevo Usuario",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=20)
        
        # Campos del formulario
        form_frame = ctk.CTkFrame(main_frame)
        form_frame.pack(fill="x", padx=10, pady=10)
        
        # Usuario admin (para verificación)
        ctk.CTkLabel(form_frame, text="Usuario Admin:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 5))
        admin_user_entry = ctk.CTkEntry(form_frame, placeholder_text="Ingrese usuario admin")
        admin_user_entry.pack(fill="x", pady=5)
        
        ctk.CTkLabel(form_frame, text="Contraseña Admin:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 5))
        admin_pass_entry = ctk.CTkEntry(form_frame, placeholder_text="Ingrese contraseña admin", show="•")
        admin_pass_entry.pack(fill="x", pady=5)
        
        ctk.CTkLabel(form_frame, text="Nuevo Usuario:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 5))
        new_user_entry = ctk.CTkEntry(form_frame, placeholder_text="Ingrese nuevo usuario")
        new_user_entry.pack(fill="x", pady=5)
        
        ctk.CTkLabel(form_frame, text="Contraseña:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 5))
        new_pass_entry = ctk.CTkEntry(form_frame, placeholder_text="Ingrese nueva contraseña", show="•")
        new_pass_entry.pack(fill="x", pady=5)
        
        ctk.CTkLabel(form_frame, text="Confirmar Contraseña:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 5))
        confirm_pass_entry = ctk.CTkEntry(form_frame, placeholder_text="Confirme la contraseña", show="•")
        confirm_pass_entry.pack(fill="x", pady=5)
        
        # Rol del usuario
        ctk.CTkLabel(form_frame, text="Rol:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 5))
        role_var = ctk.StringVar(value="user")
        role_combo = ctk.CTkComboBox(
            form_frame,
            values=["user", "admin"],
            variable=role_var
        )
        role_combo.pack(fill="x", pady=5)
        
        # Etiqueta de estado
        status_label = ctk.CTkLabel(form_frame, text="", text_color="red", font=ctk.CTkFont(size=12))
        status_label.pack(pady=10)
        
        def create_user():
            admin_user = admin_user_entry.get().strip()
            admin_pass = admin_pass_entry.get().strip()
            new_user = new_user_entry.get().strip()
            new_pass = new_pass_entry.get().strip()
            confirm_pass = confirm_pass_entry.get().strip()
            role = role_var.get()
            
            # Validaciones
            if not all([admin_user, admin_pass, new_user, new_pass, confirm_pass]):
                status_label.configure(text="Todos los campos son requeridos", text_color="red")
                return
            
            if new_pass != confirm_pass:
                status_label.configure(text="Las contraseñas no coinciden", text_color="red")
                return
            
            # Crear usuario
            success, message = self.user_manager.create_user(new_user, new_pass, role, admin_user)
            
            if success:
                status_label.configure(text=message, text_color="green")
                dialog.after(2000, dialog.destroy)
            else:
                status_label.configure(text=message, text_color="red")
        
        ctk.CTkButton(
            form_frame,
            text="Crear Usuario",
            command=create_user
        ).pack(fill="x", pady=10)
    
    def center_dialog(self, dialog, width, height):
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (width // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')
    
    def show_status(self, message, color):
        self.status_label.configure(text=message, text_color=color)
    
    def open_main_app(self):
        try:
            from gui import FATFileSystemGUI
            
            # Cerrar ventana de login
            self.destroy()
            
            # Abrir aplicación principal
            app = FATFileSystemGUI(self.logged_in_user, self.user_role)
            app.mainloop()
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la aplicación principal: {str(e)}")
            self.destroy()
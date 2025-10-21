import customtkinter as ctk
import traceback

def main():
    try:
        # Configuración de la apariencia
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        # Abrir ventana de login
        from login_gui import LoginWindow
        login_app = LoginWindow()
        login_app.mainloop()
        
    except Exception as e:
        print(f"Error crítico: {e}")
        print(traceback.format_exc())
        input("Presione Enter para salir...")

if __name__ == "__main__":
    main()
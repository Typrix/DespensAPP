#--------- Configuración de resolución (PC) ---------#
from kivy.config import Config
Config.set("graphics", "height", "640")
Config.set("graphics", "width", "360")
Config.set("graphics", "resizable", "False")
#---------------------------------------------------#


#---------------------- APP ----------------------#
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDButton, MDButtonText, MDButtonIcon

class MainApp(MDApp):
    def build(self):

        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Green"

    def on_button_click(self):
        print("Boton presionado!")

    def cambiar_pantalla(self, name_option):

        self.root.current = name_option

    def cambiar_tema(self, valor_activo):
        self.theme_cls.theme_style = "Dark" if valor_activo else "Light"

#-------------------------------------------------#


#--------------- Bucle ejecución APP ---------------#
if __name__ == '__main__':
    MainApp().run()
#---------------------------------------------------#
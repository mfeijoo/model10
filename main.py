from kivymd.app import MDApp

class MyApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = 'Dark'
        self.title = 'Blue Physics v.10.0'
        self.icon = 'images/logoonlyspheretransparent.png'

    def callback(self):
        print('oido')

MyApp().run()
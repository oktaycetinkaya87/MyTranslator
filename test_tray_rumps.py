import rumps

class TestApp(rumps.App):
    @rumps.clicked("Hello")
    def hello(self, _):
        rumps.alert("Hello!")

if __name__ == "__main__":
    TestApp("Test", icon="assets/tray_icon.png").run()

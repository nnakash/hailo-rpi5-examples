import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

class RestaurantMenu(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Restaurant Menu")
        self.attributes('-fullscreen', True)  # Set the window to fullscreen
        
        self.create_widgets()

    def create_widgets(self):
        # Logo
        logo_image = Image.open("resources/feedme.png")
        logo_image = logo_image.resize((50, 50), Image.LANCZOS)  # Resize the logo
        self.logo = ImageTk.PhotoImage(logo_image)
        
        # Frame for logo and title
        self.header_frame = tk.Frame(self)
        self.header_frame.pack(pady=10, fill=tk.X)

        self.logo_label = tk.Label(self.header_frame, image=self.logo)
        self.logo_label.pack(side=tk.LEFT, padx=10)

        # Title
        self.title_label = tk.Label(self.header_frame, text="Restaurant Menu", font=("Arial", 24))
        self.title_label.pack(side=tk.LEFT, padx=10)

        # Search box
        self.search_var = tk.StringVar()
        self.search_box = ttk.Entry(self, textvariable=self.search_var)
        self.search_box.pack(pady=10, fill=tk.X, expand=True)
        self.search_box.bind('<KeyRelease>', self.filter_menu)

        # Menu list
        self.menu_frame = ttk.Frame(self)
        self.menu_frame.pack(fill=tk.BOTH, expand=True)

        self.menu_items = [
            'Pizza', 'Burger', 'Pasta', 'Salad', 'Sushi', 'Steak', 'Tacos', 'Sandwich'
        ]
        self.menu_buttons = []
        self.populate_menu()

    def populate_menu(self):
        for widget in self.menu_frame.winfo_children():
            widget.destroy()

        for item in self.menu_items:
            button = ttk.Button(self.menu_frame, text=item, command=lambda i=item: self.on_item_click(i))
            button.pack(fill=tk.X, pady=2)
            self.menu_buttons.append(button)

    def filter_menu(self, event):
        search_text = self.search_var.get().lower()
        for button in self.menu_buttons:
            if search_text in button.cget('text').lower():
                button.pack(fill=tk.X, pady=2)
            else:
                button.pack_forget()

    def on_item_click(self, item):
        print(f"{item} clicked")

if __name__ == "__main__":
    app = RestaurantMenu()
    app.mainloop()
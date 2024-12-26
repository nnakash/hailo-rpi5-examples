import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import json
import wave
import subprocess
import rpi_script
import os
import wav2mp4
import random

class RestaurantMenu(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Restaurant Menu")
        self.geometry("1920x1080")  # Set the window size to 1920x1080

        # Bind the F11 key to toggle fullscreen mode
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", self.exit_fullscreen)

        self.is_recording = False  # Initialize recording state
        self.ordered_items = {}  # Initialize dictionary to keep track of ordered items

        self.create_widgets()
        self.recorder = wav2mp4.Recorder()

        self.feeder, self.whisper = rpi_script.start_models()

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

        # Menu list
        self.menu_frame = ttk.Frame(self)
        self.menu_frame.pack(fill=tk.BOTH, expand=True)

        # Load menu items from JSON file
        with open("resources/burger_menu.json", "r") as file:
            self.menu_data = json.load(file)

        self.category_images = {
            "appetizers": ImageTk.PhotoImage(Image.open("resources/appetizers.png").resize((100, 100), Image.LANCZOS)),
            "burger": ImageTk.PhotoImage(Image.open("resources/burger.png").resize((100, 100), Image.LANCZOS)),
            "dessert": ImageTk.PhotoImage(Image.open("resources/desserts.png").resize((100, 100), Image.LANCZOS)),
            "drinks": ImageTk.PhotoImage(Image.open("resources/drinks.png").resize((100, 100), Image.LANCZOS))
        }

        self.show_categories()

        # Mic button images
        mic_image = Image.open("resources/mic.png")
        mic_image = mic_image.resize((100, 100), Image.LANCZOS)  # Resize the mic icon
        self.mic_icon = ImageTk.PhotoImage(mic_image)

        mic_pressed_image = Image.open("resources/mic_pressed.png")
        mic_pressed_image = mic_pressed_image.resize((100, 100), Image.LANCZOS)  # Resize the pressed mic icon
        self.mic_pressed_icon = ImageTk.PhotoImage(mic_pressed_image)

        self.mic_button = ttk.Button(self, image=self.mic_icon, command=self.record_audio)
        self.mic_button.place(relx=0.5, rely=0.0, anchor=tk.N, y=20)  # Position the button at the top center with some padding

    def show_categories(self):
        for widget in self.menu_frame.winfo_children():
            widget.destroy()

        col = 0
        for category in self.menu_data["menu"]:
            button = tk.Button(self.menu_frame, text=category["type"].capitalize(), font=("Arial", 18, "bold"), image=self.category_images[category["type"]], compound=tk.TOP, command=lambda c=category: self.show_items(c), width=250, height=250)
            button.grid(row=0, column=col, padx=10, pady=(20, 10))  # Add top padding to move buttons upward
            col += 1

        for i in range(col):
            self.menu_frame.grid_columnconfigure(i, weight=1)
        self.menu_frame.grid_rowconfigure(0, weight=1)

        checkout_button = tk.Button(self, text="Go to Checkout", font=("Arial", 18, "bold"), command=self.show_checkout)
        checkout_button.place(relx=1.0, rely=1.0, anchor=tk.SE, x=-20, y=-20)  # Position the button at the bottom right with some padding

    def show_items(self, category):
        self.current_category = category
        for widget in self.menu_frame.winfo_children():
            widget.destroy()

        back_button = tk.Button(self, text="Back", font=("Arial", 18, "bold"), command=self.show_categories)
        back_button.place(relx=0.0, rely=1.0, anchor=tk.SW, x=20, y=-20)  # Position the button at the bottom left with some padding

        col = 0
        for item in category["items"]:
            item_image_path = f"resources/{item['name']}.jpg"
            item_image = ImageTk.PhotoImage(Image.open(item_image_path).resize((100, 100), Image.LANCZOS))
            button = tk.Button(self.menu_frame, text=item["name"], font=("Arial", 14), image=item_image, compound=tk.TOP, command=lambda i=item: self.show_item_details(i), width=250, height=250)
            button.image = item_image  # Keep a reference to avoid garbage collection
            button.grid(row=1, column=col, padx=10, pady=(20, 10))  # Add top padding to move buttons upward
            col += 1

        for i in range(col):
            self.menu_frame.grid_columnconfigure(i, weight=1)
        self.menu_frame.grid_rowconfigure(1, weight=1)

    def show_item_details(self, item):
        for widget in self.menu_frame.winfo_children():
            widget.destroy()

        back_button = tk.Button(self, text="Back", font=("Arial", 18, "bold"), command=lambda: self.show_items(self.current_category))
        back_button.place(relx=0.0, rely=1.0, anchor=tk.SW, x=20, y=-20)  # Position the button at the bottom left with some padding

        item_label = tk.Label(self.menu_frame, text=item["name"], font=("Arial", 24))
        item_label.grid(row=1, column=0, columnspan=2, pady=10)

        item_image_path = f"resources/{item['name']}.jpg"
        item_image = ImageTk.PhotoImage(Image.open(item_image_path).resize((100, 100), Image.LANCZOS))
        item_image_label = tk.Label(self.menu_frame, image=item_image)
        item_image_label.image = item_image  # Keep a reference to avoid garbage collection
        item_image_label.grid(row=2, column=0, columnspan=2, pady=10)

        item_description = tk.Label(self.menu_frame, text=item["description"], font=("Arial", 14))
        item_description.grid(row=3, column=0, columnspan=2, pady=10)

        item_price = tk.Label(self.menu_frame, text=f"Price: ${item['price']:.2f}", font=("Arial", 18))
        item_price.grid(row=4, column=0, columnspan=2, pady=10)

        count_label = tk.Label(self.menu_frame, text="Count:", font=("Arial", 18))
        count_label.grid(row=5, column=0, pady=10)

        count_var = tk.IntVar(value=1)

        def increase_count():
            count_var.set(count_var.get() + 1)

        def decrease_count():
            if count_var.get() > 1:
                count_var.set(count_var.get() - 1)

        count_frame = tk.Frame(self.menu_frame)
        count_frame.grid(row=5, column=1, pady=10)

        decrease_button = tk.Button(count_frame, text="-", font=("Arial", 18), command=decrease_count)
        decrease_button.pack(side=tk.LEFT, padx=5)

        count_display = tk.Label(count_frame, textvariable=count_var, font=("Arial", 18))
        count_display.pack(side=tk.LEFT, padx=5)

        increase_button = tk.Button(count_frame, text="+", font=("Arial", 18), command=increase_count)
        increase_button.pack(side=tk.LEFT, padx=5)

        add_button = tk.Button(self.menu_frame, text="Add to Order", font=("Arial", 18, "bold"), command=lambda: self.add_to_order(item, count_var.get()))
        add_button.grid(row=6, column=0, columnspan=2, pady=10)

    def add_to_order(self, item, count):
        if count > 0:
            if item["name"] in self.ordered_items:
                self.ordered_items[item["name"]]["count"] += count
            else:
                self.ordered_items[item["name"]] = {"count": count, "price": item["price"], "options": []}
        self.show_categories()

    def show_checkout(self):
        for widget in self.menu_frame.winfo_children():
            widget.destroy()

        # back_button = tk.Button(self.menu_frame, text="Back", font=("Arial", 18, "bold"), command=self.show_categories)
        # back_button.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)

        if not self.ordered_items:
            label = tk.Label(self.menu_frame, text="No items ordered.", font=("Arial", 18))
            label.grid(row=1, column=0, columnspan=2, pady=10)
        else:
            total_price = 0
            row = 1
            for item_name, item_info in self.ordered_items.items():
                item_image_path = f"resources/{item_name}.jpg"
                item_image = ImageTk.PhotoImage(Image.open(item_image_path).resize((50, 50), Image.LANCZOS))
                item_frame = tk.Frame(self.menu_frame)
                item_frame.grid(row=row, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

                item_image_label = tk.Label(item_frame, image=item_image)
                item_image_label.image = item_image  # Keep a reference to avoid garbage collection
                item_image_label.pack(side=tk.LEFT, padx=5)

                item_label = tk.Label(item_frame, text=f"{item_name} x{item_info['count']} - ${item_info['price'] * item_info['count']:.2f}", font=("Arial", 14))
                item_label.pack(side=tk.LEFT, padx=5)

                if item_info["options"]:
                    options_label = tk.Label(item_frame, text=f"Options: {', '.join(item_info['options'])}", font=("Arial", 12))
                    options_label.pack(side=tk.LEFT, padx=5)

                # remove_button = tk.Button(item_frame, text="Remove", font=("Arial", 14), command=lambda name=item_name: self.remove_from_order(name))
                # remove_button.pack(side=tk.RIGHT, padx=5)

                total_price += item_info['price'] * item_info['count']
                row += 1

            total_label = tk.Label(self.menu_frame, text=f"Total Price: ${total_price:.2f}", font=("Arial", 18, "bold"))
            total_label.grid(row=row, column=0, columnspan=2, pady=10)

            checkout_button = tk.Button(self.menu_frame, text="Checkout", font=("Arial", 18, "bold"), command=self.checkout)
            checkout_button.grid(row=row+1, column=0, columnspan=2, pady=10)

    def checkout(self):
        order_number = random.randint(1000, 9999)
        thank_you_label = tk.Label(self.menu_frame, text=f"Thank you! Your order number is {order_number}", font=("Arial", 18, "bold"))
        thank_you_label.grid(row=0, column=0, columnspan=2, pady=10)

        self.update()
        self.after(1000, self.reset_order)

    def reset_order(self):
        self.ordered_items = {}
        self.show_categories()

    def on_item_click(self, item):
        self.current_category = item["category"]
        self.show_item_details(item)

    def toggle_fullscreen(self, event=None):
        is_fullscreen = self.attributes('-fullscreen')
        self.attributes('-fullscreen', not is_fullscreen)

    def exit_fullscreen(self, event=None):
        self.attributes('-fullscreen', False)

    def close_app(self, event=None):
        self.destroy()

    def record_audio(self):
        if self.is_recording:
            print("Stopping recording...")
            self.is_recording = False
            self.mic_button.config(image=self.mic_icon)
            self.recorder.stop()

            result = self.whisper.transcribe("output.mp4", language="English")
            prompt = result["text"]
            prompt = rpi_script.replace_number_words(prompt)

            parsed_order = rpi_script.parse_prompt(self.feeder, prompt)

            for full_item_name, count in parsed_order.items():
                item_name, *options = full_item_name.split(':')[0].strip().split(',')
                item_name = item_name.strip()
                options = ', '.join(option.strip() for option in options) if options else None

                if item_name in self.ordered_items:
                    self.ordered_items[item_name]["count"] += count
                    if options:
                        self.ordered_items[item_name]["options"].append(options)
                else:
                    # Find the item in the menu data to get the price
                    for category in self.menu_data["menu"]:
                        for item in category["items"]:
                            if item["name"] == item_name:
                                self.ordered_items[item_name] = {"count": count, "price": item["price"], "options": [options] if options else []}
                                break

            self.show_checkout()

        else:
            print("Starting recording...")
            self.is_recording = True
            self.mic_button.config(image=self.mic_pressed_icon)
            self.recorder.start()

if __name__ == "__main__":
    app = RestaurantMenu()
    app.mainloop()
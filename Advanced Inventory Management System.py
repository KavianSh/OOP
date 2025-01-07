import tkinter as tk
from tkinter import messagebox, filedialog
import csv
from collections import deque

class InventoryApp:
    def __init__(self):
        # Initialize the main window
        self.window = tk.Tk()
        self.window.title("Advanced Inventory Management System")

        # Initialize the inventory (list of dictionaries)
        self.inventory = []
        self.undo_stack = deque(maxlen=20)  # For undo functionality
        self.redo_stack = deque(maxlen=20)  # For redo functionality

        # Build the GUI
        self.setup_gui()

        # Start the main event loop
        self.window.mainloop()

    def setup_gui(self):
        """Set up the graphical user interface."""
        # Main Frame
        self.main_frame = tk.Frame(self.window)
        self.main_frame.pack(padx=10, pady=10)

        # Top Frame (Search Bar, Sorting, and Buttons)
        self.top_frame = tk.Frame(self.main_frame)
        self.top_frame.pack(pady=5)

        # Search Bar
        self.search_var = tk.StringVar()
        tk.Label(self.top_frame, text="Search:").pack(side="left", padx=5)
        self.search_entry = tk.Entry(self.top_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side="left", padx=5)
        self.search_var.trace("w", self.dynamic_search)  # Live filtering

        # Sorting Options
        tk.Label(self.top_frame, text="Sort By:").pack(side="left", padx=5)
        self.sort_var = tk.StringVar(value="Name")
        self.sort_menu = tk.OptionMenu(self.top_frame, self.sort_var, "Name", "Quantity", "Price", command=self.sort_inventory)
        self.sort_menu.pack(side="left", padx=5)

        # Buttons
        self.add_button = tk.Button(self.top_frame, text="Add Item", command=self.add_item_dialog)
        self.add_button.pack(side="left", padx=5)

        self.edit_button = tk.Button(self.top_frame, text="Edit Item", command=self.edit_item_dialog)
        self.edit_button.pack(side="left", padx=5)

        self.delete_button = tk.Button(self.top_frame, text="Delete Item", command=self.delete_item)
        self.delete_button.pack(side="left", padx=5)

        self.undo_button = tk.Button(self.top_frame, text="Undo", command=self.undo_action)
        self.undo_button.pack(side="left", padx=5)

        self.redo_button = tk.Button(self.top_frame, text="Redo", command=self.redo_action)
        self.redo_button.pack(side="left", padx=5)

        # Bottom Frame (Inventory List)
        self.bottom_frame = tk.Frame(self.main_frame)
        self.bottom_frame.pack(pady=10)

        # Scrollbar
        self.scrollbar = tk.Scrollbar(self.bottom_frame)
        self.scrollbar.pack(side="right", fill="y")

        # Inventory Listbox
        self.inventory_list = tk.Listbox(
            self.bottom_frame, height=15, width=70, yscrollcommand=self.scrollbar.set
        )
        self.inventory_list.pack(side="left", fill="both")
        self.scrollbar.config(command=self.inventory_list.yview)

        # Menu Bar
        self.create_menu()

    def create_menu(self):
        """Create the menu bar."""
        menu_bar = tk.Menu(self.window)
        self.window.config(menu=menu_bar)

        # File Menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Load Inventory", command=self.load_inventory)
        file_menu.add_command(label="Save Inventory", command=self.save_inventory)
        file_menu.add_separator()
        file_menu.add_command(label="Export to CSV", command=self.export_inventory)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.window.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)

    def dynamic_search(self, *args):
        """Dynamically filter the inventory list as the user types."""
        query = self.search_var.get().lower()
        self.inventory_list.delete(0, "end")

        for item in self.inventory:
            if query in item['name'].lower():
                self.inventory_list.insert("end", f"{item['name']} (Qty: {item['quantity']}, Price: ${item['price']})")

    def sort_inventory(self, sort_by):
        """Sort the inventory based on the selected attribute."""
        reverse = False
        if sort_by in ["Quantity", "Price"]:
            reverse = True

        self.inventory.sort(key=lambda x: x[sort_by.lower()], reverse=reverse)
        self.refresh_list()

    def add_item_dialog(self):
        """Open a dialog to add a new item."""
        self.open_item_dialog(title="Add New Item", save_callback=self.add_item)

    def edit_item_dialog(self):
        """Open a dialog to edit the selected item."""
        selected = self.inventory_list.curselection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an item to edit.")
            return

        index = selected[0]
        item = self.inventory[index]
        self.open_item_dialog(
            title="Edit Item",
            save_callback=lambda name, qty, price: self.edit_item(index, name, qty, price),
            item=item,
        )

    def open_item_dialog(self, title, save_callback, item=None):
        """Open a dialog to add or edit an item."""
        dialog = tk.Toplevel(self.window)
        dialog.title(title)

        # Item Name
        tk.Label(dialog, text="Item Name:").grid(row=0, column=0, padx=10, pady=5)
        name_var = tk.StringVar(value=item['name'] if item else "")
        tk.Entry(dialog, textvariable=name_var).grid(row=0, column=1, padx=10, pady=5)

        # Quantity
        tk.Label(dialog, text="Quantity:").grid(row=1, column=0, padx=10, pady=5)
        qty_var = tk.StringVar(value=item['quantity'] if item else "")
        tk.Entry(dialog, textvariable=qty_var).grid(row=1, column=1, padx=10, pady=5)

        # Price
        tk.Label(dialog, text="Price:").grid(row=2, column=0, padx=10, pady=5)
        price_var = tk.StringVar(value=item['price'] if item else "")
        tk.Entry(dialog, textvariable=price_var).grid(row=2, column=1, padx=10, pady=5)

        def save():
            try:
                name = name_var.get()
                qty = int(qty_var.get())
                price = float(price_var.get())
                save_callback(name, qty, price)
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Invalid Input", "Quantity must be an integer and Price a float!")

        tk.Button(dialog, text="Save", command=save).grid(row=3, columnspan=2, pady=10)

    def add_item(self, name, quantity, price):
        """Add a new item to the inventory."""
        self.inventory.append({'name': name, 'quantity': quantity, 'price': price})
        self.refresh_list()
        self.save_undo()

    def edit_item(self, index, name, quantity, price):
        """Edit an item in the inventory."""
        self.inventory[index] = {'name': name, 'quantity': quantity, 'price': price}
        self.refresh_list()
        self.save_undo()

    def delete_item(self):
        """Delete the selected item."""
        selected = self.inventory_list.curselection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an item to delete.")
            return

        index = selected[0]
        self.save_undo()
        del self.inventory[index]
        self.refresh_list()

    def undo_action(self):
        """Undo the last action."""
        if not self.undo_stack:
            messagebox.showinfo("Undo", "Nothing to undo.")
            return

        self.redo_stack.append(self.inventory.copy())
        self.inventory = self.undo_stack.pop()
        self.refresh_list()

    def redo_action(self):
        """Redo the last undone action."""
        if not self.redo_stack:
            messagebox.showinfo("Redo", "Nothing to redo.")
            return

        self.undo_stack.append(self.inventory.copy())
        self.inventory = self.redo_stack.pop()
        self.refresh_list()

    def save_undo(self):
        """Save the current inventory state for undo."""
        self.undo_stack.append(self.inventory.copy())

    def refresh_list(self):
        """Refresh the inventory listbox."""
        self.inventory_list.delete(0, "end")
        for item in self.inventory:
            self.inventory_list.insert("end", f"{item['name']} (Qty: {item['quantity']}, Price: ${item['price']})")

    def load_inventory(self):
        """Load inventory data from a CSV file."""
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return

        with open(file_path, newline="") as file:
            reader = csv.DictReader(file)
            self.inventory = [
                {'name': row['Name'], 'quantity': int(row['Quantity']), 'price': float(row['Price'])}
                for row in reader
            ]
        self.refresh_list()

    def save_inventory(self):
        """Save inventory data to a CSV file."""
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return

        with open(file_path, mode="w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=['Name', 'Quantity', 'Price'])
            writer.writeheader()
            writer.writerows(self.inventory)

    def export_inventory(self):
        """Export inventory to a CSV file."""
        self.save_inventory()

if __name__ == "__main__":
    InventoryApp()

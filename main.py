import sqlite3
import csv
from datetime import datetime
from tkinter import *
from tkinter import ttk, messagebox, filedialog

# Colors & Styles
PRIMARY = "#1e272e"
SIDEBAR = "#2f3640"
ACCENT = "#00d2d3"
BG_LIGHT = "#f1f2f6"

def init_db():
    conn = sqlite3.connect("inventory.db")
    c = conn.cursor()
    # Updated table with real management fields
    c.execute("""CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        brand_model TEXT,
        serial TEXT UNIQUE,
        specs TEXT,
        user TEXT,
        status TEXT,
        date_added TEXT
    )""")
    c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)")
    conn.commit()
    conn.close()

class AssetManager:
    def __init__(self, root, user):
        self.root = root
        self.user = user
        self.root.title("Device Management Entry")
        self.root.geometry("1200x700")
        self.selected_id = None

        # Data variables
        self.v_type = StringVar()
        self.v_model = StringVar()
        self.v_serial = StringVar()
        self.v_specs = StringVar()
        self.v_user = StringVar()
        self.v_status = StringVar()
        self.v_search = StringVar()

        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        # 1. SIDEBAR (The Management Tool)
        sidebar = Frame(self.root, bg=SIDEBAR, width=300)
        sidebar.pack(side=LEFT, fill=Y)
        sidebar.pack_propagate(False)

        Label(sidebar, text="DEVICE MANAGEMENT", font=("Arial", 12, "bold"), bg=SIDEBAR, fg=ACCENT).pack(pady=20)

        # Management Input Fields
        fields = [
            ("Category (Laptop/Monitor)", self.v_type),
            ("Brand & Model", self.v_model),
            ("Serial Number", self.v_serial),
            ("Specs (RAM/CPU/SSD)", self.v_specs),
            ("Current User", self.v_user)
        ]

        for lbl, var in fields:
            Label(sidebar, text=lbl, bg=SIDEBAR, fg="white", font=("Arial", 9)).pack(anchor=W, padx=20)
            Entry(sidebar, textvariable=var, font=("Arial", 10)).pack(fill=X, padx=20, pady=(2, 10))

        Label(sidebar, text="Inventory Status", bg=SIDEBAR, fg="white").pack(anchor=W, padx=20)
        self.cb_status = ttk.Combobox(sidebar, textvariable=self.v_status, state="readonly", 
                                      values=("New", "Deployed", "Maintenance", "Retired"))
        self.cb_status.pack(fill=X, padx=20, pady=5)
        self.cb_status.current(0)

        # Action Buttons
        Button(sidebar, text="+ ADD TO INVENTORY", bg="#10ac84", fg="white", font=("Arial", 10, "bold"), command=self.save_asset).pack(fill=X, padx=20, pady=20)
        Button(sidebar, text="Update Records", bg="#2e86de", fg="white", command=self.update_asset).pack(fill=X, padx=20, pady=5)
        Button(sidebar, text="Delete Entry", bg="#ee5253", fg="white", command=self.delete_asset).pack(fill=X, padx=20, pady=5)

        # 2. MAIN WORKSPACE
        work_area = Frame(self.root, bg=BG_LIGHT)
        work_area.pack(side=RIGHT, fill=BOTH, expand=True)

        # Header with Summary Metrics
        header = Frame(work_area, bg="white", height=80)
        header.pack(side=TOP, fill=X)
        Label(header, text="Management Overview", font=("Arial", 16, "bold"), bg="white").pack(side=LEFT, padx=30, pady=20)
        
        # Search & Report Bar
        tool_bar = Frame(work_area, bg=BG_LIGHT, pady=10)
        tool_bar.pack(fill=X, padx=30)
        Entry(tool_bar, textvariable=self.v_search, width=40).pack(side=LEFT, padx=5)
        Button(tool_bar, text="Search Inventory", command=self.search).pack(side=LEFT)
        Button(tool_bar, text="Export CSV Report", bg="#576574", fg="white", command=self.export).pack(side=RIGHT)

        # Management Table
        table_frame = Frame(work_area, bg="white", padx=10, pady=10)
        table_frame.pack(fill=BOTH, expand=True, padx=30, pady=(0, 30))

        cols = ("ID", "Category", "Brand/Model", "Serial", "Specs", "Assigned User", "Status", "Log Date")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.get_cursor)

    # Management Logic
    def load_data(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = sqlite3.connect("inventory.db")
        rows = conn.execute("SELECT * FROM assets").fetchall()
        for r in rows: self.tree.insert("", END, values=r)
        conn.close()

    def save_asset(self):
        if not self.v_serial.get(): 
            messagebox.showerror("Error", "Serial Number is required for management.")
            return
        
        dt = datetime.now().strftime("%Y-%m-%d")
        try:
            conn = sqlite3.connect("inventory.db")
            conn.execute("INSERT INTO assets (type, brand_model, serial, specs, user, status, date_added) VALUES (?,?,?,?,?,?,?)",
                        (self.v_type.get(), self.v_model.get(), self.v_serial.get(), self.v_specs.get(), self.v_user.get(), self.v_status.get(), dt))
            conn.commit(); conn.close()
            self.load_data(); self.clear()
        except sqlite3.IntegrityError:
            messagebox.showerror("Duplicate", "A device with this Serial already exists!")

    def update_asset(self):
        if not self.selected_id: return
        conn = sqlite3.connect("inventory.db")
        conn.execute("UPDATE assets SET type=?, brand_model=?, serial=?, specs=?, user=?, status=? WHERE id=?",
                    (self.v_type.get(), self.v_model.get(), self.v_serial.get(), self.v_specs.get(), self.v_user.get(), self.v_status.get(), self.selected_id))
        conn.commit(); conn.close()
        self.load_data(); messagebox.showinfo("Updated", "Asset data synchronized.")

    def delete_asset(self):
        if not self.selected_id: return
        conn = sqlite3.connect("inventory.db")
        conn.execute("DELETE FROM assets WHERE id=?", (self.selected_id,))
        conn.commit(); conn.close()
        self.load_data(); self.clear()

    def get_cursor(self, e):
        cursor_row = self.tree.focus()
        contents = self.tree.item(cursor_row)
        row = contents['values']
        if row:
            self.selected_id = row[0]
            self.v_type.set(row[1]); self.v_model.set(row[2])
            self.v_serial.set(row[3]); self.v_specs.set(row[4])
            self.v_user.set(row[5]); self.v_status.set(row[6])

    def search(self):
        q = self.v_search.get()
        conn = sqlite3.connect("inventory.db")
        rows = conn.execute("SELECT * FROM assets WHERE brand_model LIKE ? OR serial LIKE ? OR type LIKE ?", ('%'+q+'%', '%'+q+'%', '%'+q+'%')).fetchall()
        for i in self.tree.get_children(): self.tree.delete(i)
        for r in rows: self.tree.insert("", END, values=r)
        conn.close()

    def export(self):
        f = filedialog.asksaveasfilename(defaultextension=".csv")
        if f:
            conn = sqlite3.connect("inventory.db")
            data = conn.execute("SELECT * FROM assets").fetchall()
            with open(f, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["ID", "Category", "Model", "Serial", "Specs", "User", "Status", "Date Added"])
                writer.writerows(data)
            messagebox.showinfo("Report Generated", "Management CSV ready.")

    def clear(self):
        self.v_type.set(""); self.v_model.set(""); self.v_serial.set(""); self.v_specs.set(""); self.v_user.set(""); self.selected_id = None

if __name__ == "__main__":
    init_db()
    win = Tk()
    # Direct launch for management check
    app = AssetManager(win, "Manager")
    win.mainloop()
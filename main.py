import sqlite3
import csv
from datetime import datetime
from tkinter import *
from tkinter import ttk, messagebox, filedialog

# --- CONFIGURATION & COLORS ---
PRIMARY = "#2C3E50"  # Midnight Blue
ACCENT = "#1ABC9C"   # Modern Teal
BG_LIGHT = "#ECF0F1" # Soft Gray
SIDEBAR = "#34495E"  # Dark Slate

# --- 1. DATABASE LOGIC ---
def init_db():
    conn = sqlite3.connect("inventory.db")
    c = conn.cursor()
    # Assets Table
    c.execute("""CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT, brand_model TEXT, serial TEXT UNIQUE,
        specs TEXT, user TEXT, status TEXT, date_added TEXT
    )""")
    # Users Table
    c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)")
    conn.commit()
    conn.close()

# --- 2. REGISTRATION WINDOW ---
class RegisterWindow:
    def __init__(self):
        self.reg_win = Toplevel()
        self.reg_win.title("Create Profile")
        self.reg_win.geometry("350x300")
        self.reg_win.configure(bg=BG_LIGHT)

        Label(self.reg_win, text="USER REGISTRATION", font=("Arial", 12, "bold"), bg=BG_LIGHT).pack(pady=20)
        
        Label(self.reg_win, text="Username", bg=BG_LIGHT).pack()
        self.u_ent = Entry(self.reg_win, width=30)
        self.u_ent.pack(pady=5)

        Label(self.reg_win, text="Password", bg=BG_LIGHT).pack()
        self.p_ent = Entry(self.reg_win, show="*", width=30)
        self.p_ent.pack(pady=5)

        Button(self.reg_win, text="Register Profile", bg=ACCENT, fg="white", 
               command=self.save_user, width=20, pady=5).pack(pady=20)

    def save_user(self):
        u, p = self.u_ent.get(), self.p_ent.get()
        if not u or not p:
            messagebox.showerror("Error", "All fields required")
            return
        
        try:
            conn = sqlite3.connect("inventory.db")
            conn.execute("INSERT INTO users VALUES (?,?)", (u, p))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "Account created! You can now log in.")
            self.reg_win.destroy()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists!")

# --- 3. MAIN DASHBOARD ---
class AssetDashboard:
    def __init__(self, root, user):
        self.root = root
        self.root.title(f"ITAM Dashboard - {user}")
        self.root.geometry("1100x700")
        self.current_user = user
        self.selected_id = None

        # Data variables
        self.v_type = StringVar(); self.v_model = StringVar(); self.v_serial = StringVar()
        self.v_specs = StringVar(); self.v_user = StringVar(); self.v_status = StringVar()
        self.v_search = StringVar()

        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        # Sidebar for Entry
        side = Frame(self.root, bg=SIDEBAR, width=280)
        side.pack(side=LEFT, fill=Y)
        side.pack_propagate(False)

        Label(side, text="ADD ASSET", font=("Arial", 11, "bold"), bg=SIDEBAR, fg=ACCENT).pack(pady=20)

        fields = [("Category", self.v_type), ("Model", self.v_model), ("Serial", self.v_serial), 
                  ("Specs", self.v_specs), ("Assign User", self.v_user)]
        
        for lbl, var in fields:
            Label(side, text=lbl, bg=SIDEBAR, fg="white", font=("Arial", 9)).pack(anchor=W, padx=20)
            Entry(side, textvariable=var).pack(fill=X, padx=20, pady=(2, 8))

        Label(side, text="Status", bg=SIDEBAR, fg="white").pack(anchor=W, padx=20)
        self.cb = ttk.Combobox(side, textvariable=self.v_status, values=("New", "Deployed", "Maintenance", "Retired"))
        self.cb.pack(fill=X, padx=20); self.cb.current(0)

        Button(side, text="SAVE ASSET", bg=ACCENT, fg="white", font=("Arial", 10, "bold"), command=self.save).pack(fill=X, padx=20, pady=20)
        Button(side, text="Delete Selected", bg="#E74C3C", fg="white", command=self.delete).pack(fill=X, padx=20)
        Button(side, text="LOGOUT", bg="#95A5A6", command=self.logout).pack(side=BOTTOM, pady=20)

        # Right View
        view = Frame(self.root, bg=BG_LIGHT)
        view.pack(side=RIGHT, fill=BOTH, expand=True)

        header = Frame(view, bg="white", height=60); header.pack(fill=X)
        Label(header, text="Asset Inventory Logs", font=("Arial", 14, "bold"), bg="white").pack(side=LEFT, padx=20)
        
        tool = Frame(view, bg=BG_LIGHT, pady=10); tool.pack(fill=X, padx=20)
        Entry(tool, textvariable=self.v_search, width=30).pack(side=LEFT)
        Button(tool, text="Search", command=self.search).pack(side=LEFT, padx=5)
        Button(tool, text="Export CSV", bg="#34495E", fg="white", command=self.export).pack(side=RIGHT)

        table_frame = Frame(view, bg="white"); table_frame.pack(fill=BOTH, expand=True, padx=20, pady=(0, 20))
        cols = ("ID", "Type", "Model", "Serial", "Specs", "User", "Status", "Date")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        for col in cols: self.tree.heading(col, text=col); self.tree.column(col, width=100)
        self.tree.pack(fill=BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.get_selected)

    def load_data(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = sqlite3.connect("inventory.db")
        for r in conn.execute("SELECT * FROM assets").fetchall(): self.tree.insert("", END, values=r)
        conn.close()

    def save(self):
        dt = datetime.now().strftime("%Y-%m-%d")
        try:
            conn = sqlite3.connect("inventory.db")
            conn.execute("INSERT INTO assets (type, brand_model, serial, specs, user, status, date_added) VALUES (?,?,?,?,?,?,?)",
                        (self.v_type.get(), self.v_model.get(), self.v_serial.get(), self.v_specs.get(), self.v_user.get(), self.v_status.get(), dt))
            conn.commit(); conn.close(); self.load_data(); self.clear()
        except: messagebox.showerror("Err", "Serial number must be unique.")

    def delete(self):
        if not self.selected_id: return
        conn = sqlite3.connect("inventory.db")
        conn.execute("DELETE FROM assets WHERE id=?", (self.selected_id,))
        conn.commit(); conn.close(); self.load_data(); self.clear()

    def get_selected(self, e):
        row = self.tree.item(self.tree.focus())['values']
        if row:
            self.selected_id = row[0]
            self.v_type.set(row[1]); self.v_model.set(row[2]); self.v_serial.set(row[3])
            self.v_specs.set(row[4]); self.v_user.set(row[5]); self.v_status.set(row[6])

    def search(self):
        q = self.v_search.get()
        conn = sqlite3.connect("inventory.db")
        rows = conn.execute("SELECT * FROM assets WHERE serial LIKE ? OR brand_model LIKE ?", ('%'+q+'%', '%'+q+'%')).fetchall()
        for i in self.tree.get_children(): self.tree.delete(i)
        for r in rows: self.tree.insert("", END, values=r)
        conn.close()

    def export(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv")
        if path:
            conn = sqlite3.connect("inventory.db")
            data = conn.execute("SELECT * FROM assets").fetchall()
            with open(path, 'w', newline='') as f:
                csv.writer(f).writerow(["ID", "Type", "Model", "Serial", "Specs", "User", "Status", "Date"])
                csv.writer(f).writerows(data)
            messagebox.showinfo("Export", "CSV Saved!")

    def clear(self):
        self.v_type.set(""); self.v_model.set(""); self.v_serial.set(""); self.selected_id = None

    def logout(self):
        self.root.destroy()
        show_login_screen()

# --- 4. AUTHENTICATION (The Entry Gate) ---
def login_logic():
    u, p = user_ent.get(), pass_ent.get()
    conn = sqlite3.connect("inventory.db")
    res = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p)).fetchone()
    conn.close()
    if res or (u == "admin" and p == "1234"):
        login_win.destroy()
        root = Tk(); app = AssetDashboard(root, u); root.mainloop()
    else:
        messagebox.showerror("Error", "Invalid credentials")

def show_login_screen():
    global login_win, user_ent, pass_ent
    login_win = Tk()
    login_win.title("Manager Login")
    login_win.geometry("350x400")
    login_win.configure(bg=PRIMARY)

    Label(login_win, text="🔐 SYSTEM ACCESS", fg="white", bg=PRIMARY, font=("Arial", 14, "bold")).pack(pady=40)
    
    user_ent = Entry(login_win, width=25, justify=CENTER); user_ent.pack(pady=5); user_ent.insert(0, "admin")
    pass_ent = Entry(login_win, width=25, show="*", justify=CENTER); pass_ent.pack(pady=5); pass_ent.insert(0, "1234")

    Button(login_win, text="LOG IN", command=login_logic, bg=ACCENT, fg="white", width=20, pady=5).pack(pady=20)
    Button(login_win, text="Create Manager Account", borderwidth=0, bg=PRIMARY, fg="white", 
           cursor="hand2", command=lambda: RegisterWindow()).pack()

    login_win.mainloop()

if __name__ == "__main__":
    init_db()
    show_login_screen()
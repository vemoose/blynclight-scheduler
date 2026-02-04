import tkinter as tk
from tkinter import font as tkfont

class DesignSystem:
    # Premium SaaS Palette (Slate & Indigo)
    PRIMARY = "#6366F1"        # Indigo
    PRIMARY_HOVER = "#4F46E5"
    
    BG_WINDOW = "#F8FAFC"      # Slate 50
    BG_CARD = "#FFFFFF"        # White
    BORDER = "#E2E8F0"         # Slate 200
    
    TEXT_MAIN = "#1E293B"      # Slate 800
    TEXT_SECONDARY = "#64748B" # Slate 500
    
    SUCCESS = "#10B981"        # Emerald
    ERROR = "#EF4444"          # Red
    AWAY = "#3B82F6"           # Blue
    NEUTRAL = "#94A3B8"        # Slate 400
    
    RADIUS = 12
    
    def __init__(self):
        # We'll use standard font families that are always on Mac
        self.font_title = ("Inter", 18, "bold")
        self.font_h1 = ("Inter", 14, "bold")
        self.font_body = ("Inter", 12)
        self.font_caption = ("Inter", 11)
        self.font_bold = ("Inter", 12, "bold")

class ModernCard(tk.Frame):
    """A styled frame that looks like a SaaS card."""
    def __init__(self, master, title=None, **kwargs):
        super().__init__(master, bg=DesignSystem.BG_CARD, highlightthickness=1, highlightbackground=DesignSystem.BORDER, **kwargs)
        
        if title:
            self.header = tk.Frame(self, bg=DesignSystem.BG_CARD)
            self.header.pack(fill="x", padx=15, pady=(12, 8))
            
            tk.Label(
                self.header, text=title, font=("Inter", 13, "bold"), 
                bg=DesignSystem.BG_CARD, fg=DesignSystem.TEXT_MAIN
            ).pack(side="left")
            
            # Divider
            tk.Frame(self, bg=DesignSystem.BORDER, height=1).pack(fill="x")

        self.content_frame = tk.Frame(self, bg=DesignSystem.BG_CARD)
        self.content_frame.pack(fill="x", padx=20, pady=15)

class StyledButton(tk.Button):
    """A standard button styled with Indigo SaaS colors."""
    def __init__(self, master, text, variant="primary", command=None, **kwargs):
        if variant == "primary":
            bg = DesignSystem.PRIMARY
            fg = "white"
            active_bg = DesignSystem.PRIMARY_HOVER
        elif variant == "success":
            bg = DesignSystem.SUCCESS
            fg = "white"
            active_bg = "#059669"
        elif variant == "error":
            bg = DesignSystem.ERROR
            fg = "white"
            active_bg = "#DC2626"
        elif variant == "away":
            bg = DesignSystem.AWAY
            fg = "white"
            active_bg = "#2563EB"
        else: # Secondary/Neutral
            bg = "#F1F5F9"
            fg = DesignSystem.TEXT_MAIN
            active_bg = "#E2E8F0"
        
        super().__init__(
            master, text=text, command=command,
            bg=bg, fg=fg, activebackground=active_bg, activeforeground=fg,
            font=("Inter", 11, "bold"), relief="flat", borderwidth=0,
            padx=15, pady=8, cursor="hand2", **kwargs
        )
        
        # Mac specifics to make buttons look better
        self.bind("<Enter>", lambda e: self.config(bg=active_bg))
        self.bind("<Leave>", lambda e: self.config(bg=bg))

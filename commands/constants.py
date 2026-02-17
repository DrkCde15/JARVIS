class Colors:
    """Códigos ANSI para cores e estilos premium"""
    # Cores Básicas
    BLUE = '\033[38;5;39m'
    CYAN = '\033[38;5;51m'
    PURPLE = '\033[38;5;141m'
    MAGENTA = '\033[38;5;199m'
    PINK = '\033[38;5;213m'
    GRAY = '\033[38;5;240m'
    WHITE = '\033[97m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ORANGE = '\033[38;5;208m'
    
    # Estilos
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'
    HIDDEN = '\033[8m'
    
    # Efeitos Neon / Premium (TrueColor if supported, falling back to 256)
    NEON_CYAN = '\033[38;2;0;255;255m'
    NEON_GREEN = '\033[38;2;57;255;20m'
    NEON_PINK = '\033[38;2;255;20;147m'
    NEON_PURPLE = '\033[38;2;176;38;255m'
    GOLD = '\033[38;2;255;215;0m'
    
    # Reset
    RESET = '\033[0m'
    CLEAR_LINE = '\033[2K'
    
    # UI Helpers
    BAR = '┃'
    LINE_H = '━'
    CORNER_TL = '┏'
    CORNER_TR = '┓'
    CORNER_BL = '┗'
    CORNER_BR = '┛'
    T_TOP = '┳'
    T_BOTTOM = '┻'
    T_LEFT = '┣'
    T_RIGHT = '┫'
    CENTER = '╋'
    
    @staticmethod
    def gradient_text(text, start_rgb, end_rgb):
        """Gera um gradiente horizontal simples (simulado por caractere)"""
        # Se o terminal não suportar TrueColor, isso pode bugar, mas é um 'premium' touch
        chars = list(text)
        n = len(chars)
        if n <= 1: return text
        
        result = ""
        for i, char in enumerate(chars):
            r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * (i / (n - 1)))
            g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * (i / (n - 1)))
            b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * (i / (n - 1)))
            result += f"\033[38;2;{r};{g};{b}m{char}"
        return result + Colors.RESET

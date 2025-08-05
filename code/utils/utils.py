def get_color(color_name):
    colors = {
        "Black": (0, 0, 0),
        "Gray": (0.5, 0.5, 0.5),
        "White": (1, 1, 1),
        "Red": (1, 0, 0),
        "Blue": (0, 0, 1),
        "Green": (0, 1, 0)
    }
    return colors.get(color_name, (0.5, 0.5, 0.5))
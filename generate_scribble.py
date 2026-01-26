import random

def generate_scribble_svg():
    width = 300
    height = 50
    points = []
    
    # Start
    x = 0
    y = height / 2
    points.append((x, y))
    
    # Generate zig-zags
    steps = 40
    step_width = width / steps
    
    for i in range(steps):
        x += step_width
        # Randomize y between 0 and height
        # Bias towards center to ensure text coverage
        # But make it erratic
        y = random.randint(5, height - 5)
        
        # Add a little x jitter so it's not perfect grid
        x_jitter = x + random.randint(-2, 2)
        points.append((x_jitter, y))
        
    s = f"<svg viewBox='0 0 {width} {height}' xmlns='http://www.w3.org/2000/svg'>"
    
    # Create the path string
    d = f"M{points[0][0]},{points[0][1]}"
    for p in points[1:]:
        d += f" L{p[0]},{p[1]}"
        
    # Stroke attributes
    s += f"<path d='{d}' fill='none' stroke='#00f0ff' stroke-width='3' stroke-linecap='round' stroke-linejoin='round' />"
    
    # Add a second, slightly offset path for density
    points2 = [(p[0], height - p[1]) for p in points] # Invert y roughly
    d2 = f"M{points2[0][0]},{points2[0][1]}"
    for p in points2[1:]:
        d2 += f" L{p[0]},{p[1]}"
    
    s += f"<path d='{d2}' fill='none' stroke='#00f0ff' stroke-width='2' stroke-opacity='0.6' stroke-linecap='round' stroke-linejoin='round' />"
    
    s += "</svg>"
    
    print(s)

generate_scribble_svg()

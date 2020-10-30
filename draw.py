import pygame

def default_falloff(x):
    return min(max(1 - x**4, 0), 1)

def light(radius, colorf, colorb, steps=50, falloff=default_falloff):
    surf = pygame.Surface((radius*2, radius*2))
    surf.fill(colorb)
    for i in range(steps):
        imul = (i+1)/steps
        mul = falloff(imul)
        color = [0, 0, 0]
        for ci in range(3):
            color[ci] = round(colorf[ci]*imul + colorb[ci]*(1-imul))
        pygame.draw.circle(surf, color, (radius, radius), round(radius*0.7 + (radius*0.3-2)*mul))
    return surf

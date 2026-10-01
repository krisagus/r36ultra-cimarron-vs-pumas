import pygame
import os
import glob

def run_gallery(screen, joystick):
    WIDTH, HEIGHT = screen.get_width(), screen.get_height()
    font_title = pygame.font.Font(pygame.font.get_default_font(), 40)
    font_text = pygame.font.Font(pygame.font.get_default_font(), 25)
    
    image_paths = glob.glob("assets/*.png") + glob.glob("assets/*.jpg")
    image_paths.sort()
    
    if not image_paths:
        return
        
    current_idx = 0
    running = True
    clock = pygame.time.Clock()
    
    def load_img(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            img_w, img_h = img.get_size()
            max_w, max_h = WIDTH - 100, HEIGHT - 200
            ratio = min(max_w/max(1, img_w), max_h/max(1, img_h))
            if ratio < 1 or ratio > 2:
                new_w, new_h = int(img_w * ratio), int(img_h * ratio)
                if new_w > 0 and new_h > 0:
                    img = pygame.transform.scale(img, (new_w, new_h))
            return img
        except:
            return pygame.Surface((100, 100))
    
    current_img = load_img(image_paths[current_idx])
    
    while running:
        screen.fill((20, 25, 30))
        
        title_text = font_title.render("GALERIA DE ARTE (Revision)", True, (255, 215, 0))
        screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2, 30))
        
        name_text = font_text.render(f"[{current_idx+1}/{len(image_paths)}] {os.path.basename(image_paths[current_idx])}", True, (255, 255, 255))
        screen.blit(name_text, (WIDTH//2 - name_text.get_width()//2, HEIGHT - 100))
        
        inst_text = font_text.render("D-Pad L/R: Cambiar Imagen  |  B o ESC: Volver al Menu", True, (150, 150, 150))
        screen.blit(inst_text, (WIDTH//2 - inst_text.get_width()//2, HEIGHT - 50))
        
        img_rect = current_img.get_rect(center=(WIDTH//2, HEIGHT//2))
        screen.blit(current_img, img_rect)
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            nav_left, nav_right, exit_gal = False, False, False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT: nav_left = True
                if event.key == pygame.K_RIGHT: nav_right = True
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_b: exit_gal = True
                
            if event.type == pygame.JOYBUTTONDOWN:
                if joystick:
                    if joystick.get_button(0) or joystick.get_button(1): exit_gal = True
                    
            if event.type == pygame.JOYHATMOTION:
                if event.value[0] == -1: nav_left = True
                if event.value[0] == 1: nav_right = True
                
            if event.type == pygame.JOYAXISMOTION:
                if event.axis == 0:
                    if event.value < -0.5: nav_left = True
                    elif event.value > 0.5: nav_right = True
            
            if exit_gal:
                running = False
            elif nav_left:
                current_idx = (current_idx - 1) % len(image_paths)
                current_img = load_img(image_paths[current_idx])
                pygame.time.wait(150)
            elif nav_right:
                current_idx = (current_idx + 1) % len(image_paths)
                current_img = load_img(image_paths[current_idx])
                pygame.time.wait(150)
                
        clock.tick(30)

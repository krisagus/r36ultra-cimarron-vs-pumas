import pygame
import os
import random

sounds = {}

def load_sounds():
    if not sounds and pygame.mixer.get_init():
        try:
            sounds['hit'] = pygame.mixer.Sound("assets/hit.wav")
            sounds['shoot'] = pygame.mixer.Sound("assets/shoot.wav")
            sounds['jump'] = pygame.mixer.Sound("assets/jump.wav")
            sounds['block'] = pygame.mixer.Sound("assets/block.wav")
        except:
            pass

def play_sound(name):
    if name in sounds:
        sounds[name].play()

class Projectile:
    def __init__(self, x, y, facing_left, color, is_hook=False):
        self.rect = pygame.Rect(x, y, 40, 20)
        self.is_hook = is_hook
        self.speed = (25 if is_hook else 18) * (-1 if facing_left else 1)
        self.active = True
        self.color = color
        self.start_x = x

    def update(self, screen_width):
        self.rect.x += self.speed
        if self.rect.x < -100 or self.rect.x > screen_width + 100:
            self.active = False

    def draw(self, surface):
        if self.active:
            if self.is_hook:
                pygame.draw.line(surface, (200, 200, 200), (self.start_x, self.rect.y+10), (self.rect.centerx, self.rect.y+10), 3)
                pygame.draw.polygon(surface, (180, 180, 180), [(self.rect.x, self.rect.y), (self.rect.right, self.rect.y+10), (self.rect.x, self.rect.bottom)])
            else:
                pygame.draw.rect(surface, self.color, self.rect)
                pygame.draw.rect(surface, (255, 255, 255), (self.rect.x+10, self.rect.y+5, 20, 10))

class Fighter:
    def __init__(self, x, y, char_name, is_p1):
        load_sounds()
        self.char_name = char_name
        self.is_p1 = is_p1
        colors = {"Cimarron": (139, 69, 19), "Puma": (205, 170, 125), "Chiva": (200, 0, 0), "Profesor": (100, 80, 60), "Estudiante": (50, 50, 200)}
        self.color = colors.get(char_name, (100, 100, 100))
        self.image_right, self.image_left, self.image_evo_right, self.image_evo_left = None, None, None, None
        
        sprite_path = f"assets/{char_name.lower()}.png"
        if os.path.exists(sprite_path):
            try:
                img = pygame.image.load(sprite_path).convert_alpha()
                img = pygame.transform.scale(img, (250, 250))
                self.image_right = img
                self.image_left = pygame.transform.flip(img, True, False)
            except: pass
            
        sprite_evo_path = f"assets/{char_name.lower()}_evo.png"
        if os.path.exists(sprite_evo_path):
            try:
                img_evo = pygame.image.load(sprite_evo_path).convert_alpha()
                img_evo = pygame.transform.scale(img_evo, (280, 280))
                self.image_evo_right = img_evo
                self.image_evo_left = pygame.transform.flip(img_evo, True, False)
            except: pass

        # Cargar Sprite de Fatality específico
        self.fatality_img_right, self.fatality_img_left = None, None
        fatality_path = f"assets/{char_name.lower()}_fatality.png"
        if os.path.exists(fatality_path):
            try:
                img_f = pygame.image.load(fatality_path).convert_alpha()
                # Aumentamos un poco el tamaño para el impacto
                img_f = pygame.transform.scale(img_f, (320, 320)) 
                self.fatality_img_right = img_f
                self.fatality_img_left = pygame.transform.flip(img_f, True, False)
            except: pass

        self.rect = pygame.Rect(x, y, 100, 200)
        self.vel_y = 0; self.speed = 10; self.jump_power = -35; self.gravity = 2.5; self.hp = 100
        self.attacking = False; self.attack_cooldown = 0; self.action = 0; self.projectiles = []
        self.special_cooldown = 0; self.is_dizzy = False; self.dizzy_timer = 0; self.is_dead = False
        self.doing_fatality = False; self.fatality_timer = 0; self.facing_left = False
        self.shielding = False; self.blocking = False; self.is_evolved = False; self.dmg_mult = 1.0

        self.suplexing = None; self.suplexed_by = None; self.is_hooked = False; self.hook_timer = 0
        self.cannonball_active = False; self.cannonball_timer = 0

    def evolve(self):
        if not self.is_evolved:
            self.is_evolved = True; self.speed += 3; self.dmg_mult = 1.5; self.hp = min(100, self.hp + 30)
            play_sound('jump')

    def take_damage(self, amount, is_physical=False):
        if not self.doing_fatality:
            if is_physical and self.blocking:
                self.hp -= amount * 0.2; play_sound('block')
            else:
                self.hp -= amount
            if self.hp < 0: self.hp = 0

    def punch(self):
        self.attacking = True; self.action = 2; self.attack_cooldown = 20 

    def kick(self):
        self.attacking = True; self.action = 5; self.attack_cooldown = 35 

    def special_attack(self):
        self.action = 3; self.special_cooldown = 120; self.attacking = True; self.attack_cooldown = 40; play_sound('shoot')
        p_x = self.rect.left - 20 if self.facing_left else self.rect.right + 20
        self.projectiles.append(Projectile(p_x, self.rect.y + 50, self.facing_left, self.color))

    def throw_hook(self):
        self.action = 7; self.special_cooldown = 150; play_sound('shoot')
        p_x = self.rect.left - 20 if self.facing_left else self.rect.right + 20
        self.projectiles.append(Projectile(p_x, self.rect.y + 50, self.facing_left, self.color, is_hook=True))

    def start_suplex(self, target):
        self.suplexing = target; target.suplexed_by = self; self.vel_y = -40; play_sound('jump'); self.action = 8; self.attack_cooldown = 60

    def start_cannonball(self):
        self.cannonball_active = True; self.cannonball_timer = 20; self.special_cooldown = 180; self.action = 9; play_sound('jump')

    def move(self, screen_width, screen_height, floor_y, joystick, target, is_local=True, net_data=None, ai=False, finish_him_mode=False):
        if self.is_dead: return
        
        # Secuencia Cinematica de Fatality
        if self.doing_fatality:
            self.fatality_timer += 1
            if self.fatality_timer == 1:
                play_sound('jump')
            if self.fatality_timer == 35: # Punto de impacto
                play_sound('hit')
                play_sound('hit') # Doble para brutalidad
                target.take_damage(100, is_physical=True)
            if self.fatality_timer > 35:
                # Enemigo sale volando hacia atras
                target.vel_y = -15
                target.rect.x += -25 if self.facing_left else 25
                target.rect.y += target.vel_y
            return

        if self.suplexed_by: return

        dx, dy = 0, 0
        self.shielding = False; self.blocking = False
        
        transferred = []
        for p in self.projectiles:
            p.update(screen_width)
            if p.active and p.rect.colliderect(target.rect) and not target.is_dead:
                if p.is_hook:
                    if not target.shielding and not target.suplexing:
                        target.is_hooked = True; target.hook_timer = 15; target.facing_left = not self.facing_left; play_sound('hit')
                    p.active = False
                elif target.shielding:
                    p.speed *= -1; play_sound('block'); transferred.append(p)
                else:
                    dmg = 15 * self.dmg_mult
                    if target.blocking: dmg *= 0.5
                    target.take_damage(dmg, is_physical=False); play_sound('hit'); p.active = False
                    
        self.projectiles = [p for p in self.projectiles if p.active and p not in transferred]
        for p in transferred: target.projectiles.append(p)
        
        if self.special_cooldown > 0: self.special_cooldown -= 1
        if self.attack_cooldown > 0: self.attack_cooldown -= 1
        if self.is_dizzy:
            self.dizzy_timer -= 1
            if self.dizzy_timer <= 0 and not finish_him_mode: self.is_dizzy = False

        if is_local and self.hp > 0 and not self.is_dizzy and not self.suplexing and not self.cannonball_active and not self.is_hooked:
            if self.attack_cooldown == 0:
                key = pygame.key.get_pressed()
                jump_pressed, punch_pressed, kick_pressed, special_pressed = False, False, False, False
                is_down, is_forward = False, False
                
                if key[pygame.K_a]: dx = -self.speed; is_forward = not self.facing_left
                if key[pygame.K_d]: dx = self.speed; is_forward = self.facing_left
                if key[pygame.K_s]: is_down = True
                if key[pygame.K_w]: jump_pressed = True
                if key[pygame.K_SPACE] or key[pygame.K_j]: punch_pressed = True
                if key[pygame.K_k] or key[pygame.K_c]: kick_pressed = True
                if key[pygame.K_e]: special_pressed = True
                if key[pygame.K_q]: self.shielding = True
                if key[pygame.K_r]: self.blocking = True
                if key[pygame.K_t]: self.start_cannonball() 
                
                if joystick:
                    axis_x = joystick.get_axis(0); axis_y = joystick.get_axis(1)
                    hat = joystick.get_hat(0) if joystick.get_numhats() > 0 else (0,0)
                    if axis_x < -0.5 or hat[0] == -1: dx = -self.speed; is_forward = self.facing_left
                    if axis_x > 0.5 or hat[0] == 1: dx = self.speed; is_forward = not self.facing_left
                    if axis_y > 0.5 or hat[1] == -1: is_down = True
                    if joystick.get_button(0): jump_pressed = True 
                    if joystick.get_button(2): punch_pressed = True 
                    if joystick.get_button(1): kick_pressed = True 
                    if joystick.get_button(3): special_pressed = True 
                    if joystick.get_button(4) or joystick.get_button(6): self.blocking = True
                    if joystick.get_button(5) or joystick.get_button(7): self.shielding = True
                    if (joystick.get_button(4) and joystick.get_button(5)) and self.special_cooldown == 0:
                        self.start_cannonball(); punch_pressed = kick_pressed = special_pressed = False

                if finish_him_mode and special_pressed:
                    self.doing_fatality = True
                    self.fatality_timer = 0
                    return

                if ai and not finish_him_mode:
                    dist_x = target.rect.centerx - self.rect.centerx
                    if abs(dist_x) > 75: dx = self.speed if dist_x > 0 else -self.speed; is_forward = True
                    r = random.random()
                    if r < 0.04: punch_pressed = True
                    elif r < 0.06: kick_pressed = True
                    elif r < 0.08 and self.special_cooldown == 0: special_pressed = True
                    elif r < 0.09: self.blocking = True
                    elif r < 0.11 and self.special_cooldown == 0: self.start_cannonball()
                    elif r < 0.13 and self.special_cooldown == 0: is_down = True; special_pressed = True
                    if abs(dist_x) < 85 and r < 0.18: punch_pressed = True; is_forward = True 
                    if random.random() < 0.02 and self.rect.bottom >= floor_y: jump_pressed = True

                if self.shielding or self.blocking: dx = 0; punch_pressed = kick_pressed = special_pressed = False

                if jump_pressed and self.rect.bottom >= floor_y and not self.shielding and not self.blocking:
                    self.vel_y = self.jump_power; play_sound('jump')
                    
                if punch_pressed:
                    if is_forward and abs(target.rect.centerx - self.rect.centerx) < 90 and target.hp > 0 and not target.suplexing:
                        self.start_suplex(target)
                    else:
                        self.punch()
                elif kick_pressed: self.kick()
                elif special_pressed and self.special_cooldown == 0:
                    if is_down: self.throw_hook() 
                    else: self.special_attack()

        if self.cannonball_active:
            dx = 35 if not self.facing_left else -35
            self.cannonball_timer -= 1
            if self.rect.colliderect(target.rect) and not target.suplexed_by:
                target.take_damage(25 * self.dmg_mult, is_physical=True); play_sound('hit')
                target.rect.x += dx * 1.5; self.cannonball_active = False; self.vel_y = -20
            if self.cannonball_timer <= 0: self.cannonball_active = False

        if self.is_hooked:
            dx = 25 if self.facing_left else -25; self.hook_timer -= 1
            if self.hook_timer <= 0: self.is_hooked = False

        self.vel_y += self.gravity; dy += self.vel_y
        
        if self.suplexing:
            dx = 0; target.rect.centerx = self.rect.centerx; target.rect.bottom = self.rect.top + 20
            if self.rect.bottom + dy >= floor_y and self.vel_y > 0:
                dy = floor_y - self.rect.bottom; self.vel_y = 0; target.rect.bottom = floor_y
                target.take_damage(30 * self.dmg_mult, is_physical=True); play_sound('hit')
                target.is_dizzy = True; target.dizzy_timer = 40; self.suplexing.suplexed_by = None; self.suplexing = None; self.action = 0
        
        if self.rect.left + dx < 0: dx = -self.rect.left
        if self.rect.right + dx > screen_width: dx = screen_width - self.rect.right
        if self.rect.bottom + dy > floor_y and not self.suplexed_by: self.vel_y = 0; dy = floor_y - self.rect.bottom

        if not self.suplexing and not self.suplexed_by and not self.cannonball_active: self.facing_left = target.rect.centerx < self.rect.centerx
        self.rect.x += dx; self.rect.y += dy
        
        if self.rect.colliderect(target.rect) and not target.is_dizzy and not self.suplexing and not self.suplexed_by and not self.cannonball_active:
            if self.rect.centerx < target.rect.centerx: self.rect.x -= 3; target.rect.x += 3
            else: self.rect.x += 3; target.rect.x -= 3

        if self.attacking and self.action in [2, 5]:
            if (self.action == 2 and self.attack_cooldown == 10) or (self.action == 5 and self.attack_cooldown == 15):
                reach = 60 if self.action == 2 else 95; height = 40 if self.action == 2 else 60; y_offset = 30 if self.action == 2 else 100 
                hitbox_x = self.rect.centerx - reach if self.facing_left else self.rect.centerx
                hitbox = pygame.Rect(hitbox_x, self.rect.y + y_offset, reach, height)
                
                if hitbox.colliderect(target.rect) and not target.suplexed_by:
                    base_dmg = 5 if self.action == 2 else 12
                    target.take_damage(base_dmg * self.dmg_mult, is_physical=True)
                    if not target.blocking: play_sound('hit')
                    knockback = 10 if self.action == 2 else 25
                    if target.blocking: knockback //= 2
                    target.rect.x += -knockback if self.rect.centerx < target.rect.centerx else knockback

    def draw(self, surface):
        if self.is_dead and not self.doing_fatality:
            pygame.draw.rect(surface, (50, 0, 0), pygame.Rect(self.rect.x, self.rect.bottom - 40, 180, 40)); return

        # Logica Cinemática
        shake_x = 0
        if self.doing_fatality:
            # Oscurecer fondo
            dim = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 150))
            surface.blit(dim, (0,0))
            
            # Dibujar Muro FIAD Dinámico
            try:
                if not hasattr(self, 'prop_muro'):
                    self.prop_muro = pygame.image.load("assets/prop_muro.png").convert_alpha()
                # Posicionar muro detras del rival
                wall_x = self.rect.right + 50 if not self.facing_left else self.rect.left - 50 - self.prop_muro.get_width()
                if self.fatality_timer > 35: shake_x = random.randint(-15, 15) # CAMERA SHAKE IMPACTO
                surface.blit(self.prop_muro, (wall_x + shake_x, self.rect.bottom - self.prop_muro.get_height()))
            except: pass
            
        offset_x = random.randint(-8, 8) if (self.is_dizzy or self.is_hooked) else 0
        draw_rect = self.rect.copy(); draw_rect.x += offset_x + shake_x
        
        current_img_left = self.image_evo_left if (self.is_evolved and self.image_evo_left) else self.image_left
        current_img_right = self.image_evo_right if (self.is_evolved and self.image_evo_right) else self.image_right
        
        draw_rect.y -= (65 if self.is_evolved else 50) if current_img_right else 0
        if self.is_evolved: draw_rect.x -= 15
        
        img_to_draw = current_img_left if self.facing_left else current_img_right
        
        if self.doing_fatality and self.fatality_img_right:
            # Reemplazar con Sprite de Fatality
            if self.fatality_timer > 20:
                img_to_draw = self.fatality_img_left if self.facing_left else self.fatality_img_right
                # Ajustar tamaño gigante del sprite de impacto
                draw_rect.y -= 70
                draw_rect.x -= 35
                
        if self.suplexed_by and img_to_draw: img_to_draw = pygame.transform.flip(img_to_draw, False, True)
            
        if self.cannonball_active:
            s = pygame.Surface((draw_rect.width, draw_rect.height), pygame.SRCALPHA)
            pygame.draw.ellipse(s, (255, 200, 0, 150), s.get_rect()); surface.blit(s, draw_rect.topleft)

        if img_to_draw:
            if self.attacking and self.action in [2, 5]:
                push = (15 if self.action == 2 else 25) * (-1 if self.facing_left else 1); draw_rect.x += push
            if self.blocking:
                surface.blit(img_to_draw, draw_rect); s = pygame.Surface((img_to_draw.get_width(), img_to_draw.get_height()), pygame.SRCALPHA)
                s.fill((100, 100, 100, 100)); surface.blit(s, draw_rect, special_flags=pygame.BLEND_RGBA_MULT)
            else:
                surface.blit(img_to_draw, draw_rect)
        else:
            color = self.color
            if self.is_dizzy: color = (255, 100, 100)
            if self.doing_fatality: color = (255, 255, 255)
            if self.blocking: color = (100, 100, 100)
            pygame.draw.rect(surface, color, draw_rect)
            
        if self.shielding:
            shield_x = draw_rect.x - 40 if self.facing_left else draw_rect.right + 20
            shield_rect = pygame.Rect(shield_x, draw_rect.y - 20, 20, draw_rect.height + 40)
            s = pygame.Surface((shield_rect.width, shield_rect.height), pygame.SRCALPHA)
            pygame.draw.ellipse(s, (0, 255, 255, 180), s.get_rect()); surface.blit(s, shield_rect.topleft)

        if self.attacking and self.action in [2, 5] and self.attack_cooldown > 0:
            reach = 60 if self.action == 2 else 95; height = 40 if self.action == 2 else 60; y_offset = 30 if self.action == 2 else 100
            hitbox_x = self.rect.centerx - reach if self.facing_left else self.rect.centerx
            pygame.draw.rect(surface, (255, 255, 0) if self.action == 2 else (255, 100, 0), pygame.Rect(hitbox_x, self.rect.y + y_offset, reach, height))
        
        for p in self.projectiles: p.draw(surface)
        
        self.attacking = False
        if not self.shielding and not self.blocking and not self.suplexing and not self.cannonball_active:
            if self.action not in [0, 7] and self.attack_cooldown == 0 and self.special_cooldown < 110: self.action = 0

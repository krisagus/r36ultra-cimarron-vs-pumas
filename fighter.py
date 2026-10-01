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
    def __init__(self, x, y, facing_left, color):
        self.rect = pygame.Rect(x, y, 40, 20)
        self.speed = 18 if not facing_left else -18
        self.active = True
        self.color = color

    def update(self, screen_width):
        self.rect.x += self.speed
        if self.rect.x < -100 or self.rect.x > screen_width + 100:
            self.active = False

    def draw(self, surface):
        if self.active:
            pygame.draw.rect(surface, self.color, self.rect)
            pygame.draw.rect(surface, (255, 255, 255), (self.rect.x+10, self.rect.y+5, 20, 10))

class Fighter:
    def __init__(self, x, y, char_name, is_p1):
        load_sounds()
        self.char_name = char_name
        
        if char_name == "Cimarron": self.color = (139, 69, 19)
        elif char_name == "Puma": self.color = (205, 170, 125)
        elif char_name == "Tiburon": self.color = (100, 150, 200)
        elif char_name == "Zorro": self.color = (255, 140, 0)
        elif char_name == "Delfin": self.color = (150, 200, 255)
        elif char_name == "Aguila": self.color = (200, 150, 50)
        elif char_name == "Dragon": self.color = (255, 50, 50)
        elif char_name == "Halcon": self.color = (100, 100, 100)
        elif char_name == "Lobo": self.color = (255, 150, 0)
        elif char_name == "Venado": self.color = (150, 100, 50)
        elif char_name == "Perro": self.color = (120, 80, 50)
        elif char_name == "Cuervo": self.color = (40, 40, 40)
        elif char_name == "Caballo": self.color = (139, 69, 19)
        elif char_name == "Guepardo": self.color = (255, 204, 51)
        elif char_name == "Toro": self.color = (165, 42, 42)
        elif char_name == "Chiva": self.color = (200, 0, 0)
        elif char_name == "Profesor": self.color = (100, 80, 60)
        elif char_name == "Estudiante": self.color = (50, 50, 200)
        else: self.color = (100, 100, 100)

        self.image_right = None
        self.image_left = None
        self.image_evo_right = None
        self.image_evo_left = None
        
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

        self.rect = pygame.Rect(x, y, 100, 200)

        self.vel_y = 0
        self.speed = 10
        self.jump_power = -35
        self.gravity = 2.5
        self.hp = 100
        
        self.attacking = False
        self.attack_cooldown = 0
        self.action = 0
        self.projectiles = []
        self.special_cooldown = 0
        
        self.is_dizzy = False
        self.is_dead = False
        self.doing_fatality = False
        self.facing_left = False
        
        self.shielding = False
        self.blocking = False
        
        self.is_evolved = False
        self.dmg_mult = 1.0
        self.fatality_timer = 0

    def evolve(self):
        if not self.is_evolved:
            self.is_evolved = True
            self.speed += 3
            self.dmg_mult = 1.5
            self.hp = min(100, self.hp + 30)
            play_sound('jump')

    def take_damage(self, amount, is_physical=False):
        if not self.doing_fatality:
            if is_physical and self.blocking:
                self.hp -= amount * 0.2
                play_sound('block')
            else:
                self.hp -= amount
            if self.hp < 0: self.hp = 0

    def punch(self):
        self.attacking = True
        self.action = 2
        self.attack_cooldown = 20 

    def kick(self):
        self.attacking = True
        self.action = 5
        self.attack_cooldown = 35 

    def special_attack(self):
        self.action = 3
        self.special_cooldown = 120
        self.attacking = True
        self.attack_cooldown = 40
        play_sound('shoot')
        p_x = self.rect.left - 20 if self.facing_left else self.rect.right + 20
        self.projectiles.append(Projectile(p_x, self.rect.y + 50, self.facing_left, self.color))

    def move(self, screen_width, screen_height, floor_y, joystick, target, is_local=True, net_data=None, ai=False, finish_him_mode=False):
        if self.is_dead:
            return
            
        if self.doing_fatality:
            self.fatality_timer += 1
            if self.fatality_timer > 30:
                target.rect.y -= 45
                target.rect.x += random.randint(-15, 15)
            return

        dx, dy = 0, 0
        self.shielding = False
        self.blocking = False
        
        transferred = []
        for p in self.projectiles:
            p.update(screen_width)
            if p.active and p.rect.colliderect(target.rect) and not target.is_dead:
                if target.shielding:
                    p.speed *= -1
                    play_sound('block')
                    transferred.append(p)
                else:
                    dmg = 15 * self.dmg_mult
                    if target.blocking:
                        dmg *= 0.5
                    target.take_damage(dmg, is_physical=False)
                    play_sound('hit')
                    p.active = False
                    
        self.projectiles = [p for p in self.projectiles if p.active and p not in transferred]
        for p in transferred:
            target.projectiles.append(p)
        
        if self.special_cooldown > 0: self.special_cooldown -= 1
        if self.attack_cooldown > 0: self.attack_cooldown -= 1
        
        if is_local and self.hp > 0 and not self.is_dizzy:
            if self.attack_cooldown == 0:
                if ai:
                    if finish_him_mode and target.is_dizzy:
                        dist_x = target.rect.centerx - self.rect.centerx
                        if abs(dist_x) > 120:
                            dx = self.speed if dist_x > 0 else -self.speed
                        else:
                            self.special_attack()
                    else:
                        dist_x = target.rect.centerx - self.rect.centerx
                        incoming = [p for p in target.projectiles if abs(p.rect.x - self.rect.centerx) < 200]
                        if incoming and random.random() < 0.6:
                            self.shielding = True
                        else:
                            if abs(dist_x) > 250 and self.special_cooldown == 0:
                                self.special_attack()
                            elif abs(dist_x) > 100:
                                dx = self.speed if dist_x > 0 else -self.speed
                            else:
                                if random.random() < 0.5:
                                    self.punch()
                                else:
                                    self.kick()
                            if (target.rect.bottom < floor_y or random.random() < 0.02) and self.rect.bottom >= floor_y:
                                self.vel_y = self.jump_power
                                play_sound('jump')
                else:
                    key = pygame.key.get_pressed()
                    jump_pressed, punch_pressed, kick_pressed, special_pressed = False, False, False, False
                    
                    if key[pygame.K_a]: dx = -self.speed
                    if key[pygame.K_d]: dx = self.speed
                    if key[pygame.K_w]: jump_pressed = True
                    if key[pygame.K_SPACE] or key[pygame.K_j]: punch_pressed = True
                    if key[pygame.K_k] or key[pygame.K_c]: kick_pressed = True
                    if key[pygame.K_e]: special_pressed = True
                    if key[pygame.K_q]: self.shielding = True
                    if key[pygame.K_r]: self.blocking = True
                    
                    if joystick:
                        axis_x = joystick.get_axis(0)
                        hat = joystick.get_hat(0) if joystick.get_numhats() > 0 else (0,0)
                        if axis_x < -0.5 or hat[0] == -1: dx = -self.speed
                        if axis_x > 0.5 or hat[0] == 1: dx = self.speed
                        
                        if joystick.get_button(0): jump_pressed = True 
                        if joystick.get_button(2): punch_pressed = True 
                        if joystick.get_button(1): kick_pressed = True 
                        if joystick.get_button(3): special_pressed = True 
                        
                        if joystick.get_button(4) or joystick.get_button(6): 
                            self.blocking = True
                        if joystick.get_button(5) or joystick.get_button(7): 
                            self.shielding = True

                    if self.shielding or self.blocking:
                        dx = 0
                        punch_pressed = False
                        kick_pressed = False
                        special_pressed = False

                    if jump_pressed and self.rect.bottom >= floor_y and not self.shielding and not self.blocking:
                        self.vel_y = self.jump_power
                        play_sound('jump')
                    if punch_pressed:
                        self.punch()
                    elif kick_pressed:
                        self.kick()
                    elif special_pressed and self.special_cooldown == 0:
                        self.special_attack()
                        
            self.vel_y += self.gravity
            dy += self.vel_y
            
            if self.rect.left + dx < 0: dx = -self.rect.left
            if self.rect.right + dx > screen_width: dx = screen_width - self.rect.right
            if self.rect.bottom + dy > floor_y:
                self.vel_y = 0
                dy = floor_y - self.rect.bottom

            self.facing_left = target.rect.centerx < self.rect.centerx
            self.rect.x += dx
            self.rect.y += dy
            
            if self.rect.colliderect(target.rect) and not target.is_dizzy:
                if self.rect.centerx < target.rect.centerx:
                    self.rect.x -= 3
                    target.rect.x += 3
                else:
                    self.rect.x += 3
                    target.rect.x -= 3
            
        elif not is_local:
            if net_data:
                _, seq, nx, ny, nhp, nact, nfac = net_data
                self.rect.x = nx
                self.rect.y = ny
                self.hp = nhp
                self.facing_left = bool(nfac)
                if nact == 2 and self.attack_cooldown == 0: self.punch()
                elif nact == 5 and self.attack_cooldown == 0: self.kick()
                elif nact == 3 and self.special_cooldown == 0: self.special_attack()
                elif nact == 4: self.shielding = True
                elif nact == 6: self.blocking = True
                else: self.shielding, self.blocking = False, False
                self.action = nact

        if self.attacking and self.action in [2, 5]:
            if (self.action == 2 and self.attack_cooldown == 10) or (self.action == 5 and self.attack_cooldown == 15):
                reach = 60 if self.action == 2 else 95
                height = 40 if self.action == 2 else 60
                y_offset = 30 if self.action == 2 else 100 
                
                hitbox_x = self.rect.centerx - reach if self.facing_left else self.rect.centerx
                hitbox = pygame.Rect(hitbox_x, self.rect.y + y_offset, reach, height)
                
                if hitbox.colliderect(target.rect):
                    base_dmg = 5 if self.action == 2 else 12
                    target.take_damage(base_dmg * self.dmg_mult, is_physical=True)
                    if not target.blocking: play_sound('hit')
                    
                    knockback = 10 if self.action == 2 else 25
                    if target.blocking: knockback //= 2
                    target.rect.x += -knockback if self.rect.centerx < target.rect.centerx else knockback

    def draw(self, surface):
        if self.is_dead and not self.doing_fatality:
            dead_rect = pygame.Rect(self.rect.x, self.rect.bottom - 40, 180, 40)
            pygame.draw.rect(surface, (50, 0, 0), dead_rect)
            return

        offset_x = random.randint(-8, 8) if self.is_dizzy else 0
        draw_rect = self.rect.copy()
        draw_rect.x += offset_x
        
        current_img_left = self.image_evo_left if (self.is_evolved and self.image_evo_left) else self.image_left
        current_img_right = self.image_evo_right if (self.is_evolved and self.image_evo_right) else self.image_right
        
        draw_rect.y -= (65 if self.is_evolved else 50) if current_img_right else 0
        if self.is_evolved:
            draw_rect.x -= 15

        img_to_draw = current_img_left if self.facing_left else current_img_right
        
        if self.doing_fatality:
            if self.fatality_timer % 4 < 2:
                pygame.draw.circle(surface, (255,255,0), self.rect.center, 120 + self.fatality_timer*2, 10)
        
        if img_to_draw:
            if self.attacking:
                push = 0
                if self.action == 2: push = 15 if not self.facing_left else -15 
                if self.action == 5: push = 25 if not self.facing_left else -25 
                draw_rect.x += push
            
            if self.blocking:
                surface.blit(img_to_draw, draw_rect)
                s = pygame.Surface((img_to_draw.get_width(), img_to_draw.get_height()), pygame.SRCALPHA)
                s.fill((100, 100, 100, 100))
                surface.blit(s, draw_rect, special_flags=pygame.BLEND_RGBA_MULT)
            else:
                surface.blit(img_to_draw, draw_rect)
        else:
            color = (255, 100, 100) if self.is_dizzy else self.color
            if self.doing_fatality: color = (255, 255, 255)
            if self.blocking: color = (100, 100, 100)
            pygame.draw.rect(surface, color, draw_rect)
            
        if self.shielding:
            shield_x = draw_rect.x - 40 if self.facing_left else draw_rect.right + 20
            shield_rect = pygame.Rect(shield_x, draw_rect.y - 20, 20, draw_rect.height + 40)
            s = pygame.Surface((shield_rect.width, shield_rect.height), pygame.SRCALPHA)
            pygame.draw.ellipse(s, (0, 255, 255, 180), s.get_rect())
            surface.blit(s, shield_rect.topleft)

        if self.attacking and self.action in [2, 5] and self.attack_cooldown > 0:
            reach = 60 if self.action == 2 else 95
            height = 40 if self.action == 2 else 60
            y_offset = 30 if self.action == 2 else 100
            hitbox_x = self.rect.centerx - reach if self.facing_left else self.rect.centerx
            hitbox = pygame.Rect(hitbox_x, self.rect.y + y_offset, reach, height)
            
            hb_color = (255, 255, 0) if self.action == 2 else (255, 100, 0)
            pygame.draw.rect(surface, hb_color, hitbox)
        
        for p in self.projectiles:
            p.draw(surface)
        
        self.attacking = False
        if not self.shielding and not self.blocking:
            if self.action != 0 and self.attack_cooldown == 0 and self.special_cooldown < 110:
                self.action = 0
        elif self.shielding:
            self.action = 4
        elif self.blocking:
            self.action = 6

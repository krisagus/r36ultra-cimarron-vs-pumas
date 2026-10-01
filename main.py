import os
import sys
import random

try:
    os.environ['SDL_AUDIODRIVER'] = 'alsa'
    os.environ['SDL_NOMOUSE'] = '1'

    import pygame
    from fighter import Fighter
    from network_manager import NetworkManager
    from telemetry import CombatTelemetry

    pygame.display.init()
    pygame.font.init()
    pygame.joystick.init()
    
    try:
        pygame.mixer.pre_init(44100, -16, 2, 1024)
    pygame.mixer.init()
    except:
        pass

    WIDTH, HEIGHT = 720, 720
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
    pygame.display.set_caption("Cimarrón vs Pumas - KOF Mode")

    clock = pygame.time.Clock()
    FPS = 60
    FLOOR = 650
    BG_COLOR = (30, 30, 40)

    joystick = None
    if pygame.joystick.get_count() > 0:
        joystick = pygame.joystick.Joystick(0)
        joystick.init()

    font_title = pygame.font.Font(pygame.font.get_default_font(), 64)
    font_menu = pygame.font.Font(pygame.font.get_default_font(), 40)
    font_info = pygame.font.Font(pygame.font.get_default_font(), 30)
    font_small = pygame.font.Font(pygame.font.get_default_font(), 20)

    # Cargar fondos dinamicamente
    backgrounds = []
    if os.path.exists("assets"):
        bg_files = [f for f in os.listdir("assets") if f.startswith("bg_") and (f.endswith(".png") or f.endswith(".jpg"))]
        for bg_file in bg_files:
            bg_path = f"assets/{bg_file}"
            try:
                img = pygame.image.load(bg_path).convert()
                img = pygame.transform.scale(img, (WIDTH, HEIGHT))
                backgrounds.append(img)
            except:
                pass

    def play_intro(screen, clock):
        intro_dir = "assets/intro_frames"
        intro_audio = "assets/intro.wav"
        if not os.path.exists(intro_dir):
            return True

        frame_files = sorted([f for f in os.listdir(intro_dir) if f.lower().endswith((".jpg", ".jpeg", ".png"))])
        if not frame_files:
            return True

        audio_started = False
        if os.path.exists(intro_audio) and pygame.mixer.get_init():
            try:
                pygame.mixer.music.load(intro_audio)
                pygame.mixer.music.play()
                audio_started = True
            except Exception:
                pass

        intro_fps = 15
        intro_clock = pygame.time.Clock()

        for frame_file in frame_files:
            frame_path = os.path.join(intro_dir, frame_file)
            try:
                frame_img = pygame.image.load(frame_path).convert()
                frame_img = pygame.transform.scale(frame_img, (WIDTH, HEIGHT))
                screen.blit(frame_img, (0, 0))
                pygame.display.flip()
            except Exception:
                pass

            intro_clock.tick(intro_fps)

            skip = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if audio_started:
                        pygame.mixer.music.stop()
                    return False
                if event.type == pygame.KEYDOWN:
                    skip = True
                    break
                if event.type == pygame.JOYBUTTONDOWN:
                    skip = True
                    break

            if skip:
                break

        if audio_started:
            pygame.mixer.music.stop()
        pygame.event.clear()
        return True

    app_running = play_intro(screen, clock)

    while app_running:
        menu_options = ["1. Jugar vs CPU (3v3)", "2. Crear Partida", "3. Unirse a Partida", "4. Salir"]
        selected = 0
        in_menu = True
        game_mode = "CPU"
        
        while in_menu and app_running:
            if backgrounds:
                screen.blit(backgrounds[0], (0, 0))
                s = pygame.Surface((WIDTH, HEIGHT)); s.set_alpha(150); s.fill((0,0,0)); screen.blit(s, (0,0))
            else:
                screen.fill(BG_COLOR)

            title = font_title.render("CIMARRON VS PUMAS", True, (255,255,255))
            screen.blit(title, (WIDTH//2 - title.get_width()//2, 100))
            
            for i, option in enumerate(menu_options):
                color = (0, 255, 0) if i == selected else (150, 150, 150)
                text = font_menu.render(option, True, color)
                screen.blit(text, (WIDTH//2 - text.get_width()//2, 300 + i * 60))
                
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: app_running = False; in_menu = False
                
                nav_up, nav_down, nav_select = False, False, False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP: nav_up = True
                    if event.key == pygame.K_DOWN: nav_down = True
                    if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE: nav_select = True
                    if event.key == pygame.K_ESCAPE: app_running = False; in_menu = False
                if event.type == pygame.JOYHATMOTION:
                    if event.value[1] == 1: nav_up = True
                    elif event.value[1] == -1: nav_down = True
                if event.type == pygame.JOYAXISMOTION:
                    if event.axis == 1:
                        if event.value < -0.5: nav_up = True
                        elif event.value > 0.5: nav_down = True
                if event.type == pygame.JOYBUTTONDOWN:
                    if joystick.get_button(8) and joystick.get_button(9): app_running = False; in_menu = False
                    if joystick.get_button(0) or joystick.get_button(1): nav_select = True
                
                if nav_up: selected = (selected - 1) % len(menu_options); pygame.time.wait(150)
                if nav_down: selected = (selected + 1) % len(menu_options); pygame.time.wait(150)
                if nav_select:
                    if selected == 0: game_mode = "CPU"; in_menu = False
                    elif selected == 1: game_mode = "HOST"; in_menu = False
                    elif selected == 2: game_mode = "CLIENT"; in_menu = False
                    elif selected == 3: app_running = False; in_menu = False

        if not app_running: break

        characters_list = ["Cimarron", "Puma", "Tiburon", "Zorro", "Delfin", "Aguila", "Dragon", "Halcon", "Lobo", "Venado", "Perro", "Cuervo", "Caballo", "Guepardo", "Toro", "Chiva", "Profesor", "Estudiante"]
        p1_team = []
        p2_team = []
        p1_cursor = 0
        in_char_select = True

        while in_char_select and app_running:
            if backgrounds:
                screen.blit(backgrounds[1 % len(backgrounds)], (0, 0))
                s = pygame.Surface((WIDTH, HEIGHT)); s.set_alpha(150); s.fill((0,0,0)); screen.blit(s, (0,0))
            else:
                screen.fill(BG_COLOR)

            title = font_title.render("ARMA TU EQUIPO (3)", True, (255,255,255))
            screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
            
            p1_color = (0, 255, 0)
            p1_text = font_menu.render(f"Seleccionando: {characters_list[p1_cursor]}", True, p1_color)
            screen.blit(p1_text, (WIDTH//2 - p1_text.get_width()//2, 200))
            
            team1_text = font_info.render(f"J1 Team: {', '.join(p1_team)}", True, (0, 255, 0))
            screen.blit(team1_text, (50, 400))
            
            team2_text = font_info.render(f"J2 Team: {', '.join(p2_team)}", True, (255, 0, 0))
            screen.blit(team2_text, (50, 450))
            
            inst_text = font_info.render("<- Izq/Der -> | Boton A: Elegir", True, (200,200,200))
            screen.blit(inst_text, (WIDTH//2 - inst_text.get_width()//2, 600))
            
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: app_running = False; in_char_select = False
                
                nav_left, nav_right, nav_sel = False, False, False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a or event.key == pygame.K_LEFT: nav_left = True
                    if event.key == pygame.K_d or event.key == pygame.K_RIGHT: nav_right = True
                    if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN: nav_sel = True
                    if event.key == pygame.K_ESCAPE: app_running = False; in_char_select = False
                if event.type == pygame.JOYHATMOTION:
                    if event.value[0] == -1: nav_left = True
                    elif event.value[0] == 1: nav_right = True
                if event.type == pygame.JOYAXISMOTION:
                    if event.axis == 0:
                        if event.value < -0.5: nav_left = True
                        elif event.value > 0.5: nav_right = True
                if event.type == pygame.JOYBUTTONDOWN:
                    if joystick.get_button(8) and joystick.get_button(9): app_running = False; in_char_select = False
                    if joystick.get_button(0) or joystick.get_button(1): nav_sel = True
                
                if nav_left: p1_cursor = (p1_cursor - 1) % len(characters_list); pygame.time.wait(150)
                if nav_right: p1_cursor = (p1_cursor + 1) % len(characters_list); pygame.time.wait(150)
                
                if nav_sel:
                    if len(p1_team) < 3:
                        p1_team.append(characters_list[p1_cursor])
                    if len(p1_team) == 3 and game_mode == "CPU" and len(p2_team) < 3:
                        p2_team = [random.choice(characters_list) for _ in range(3)]
                    
            if len(p1_team) == 3 and len(p2_team) == 3:
                in_char_select = False

        if not app_running: break

        telemetry = CombatTelemetry()
        network = None
        if game_mode != "CPU":
            p2_team = ["Puma", "Tiburon", "Zorro"] if not p2_team else p2_team
            network = NetworkManager(is_host=(game_mode == "HOST"))

        p1_active_idx = 0
        p2_active_idx = 0
        
        if game_mode == "CLIENT":
            fighter1 = Fighter(200, FLOOR - 180, p2_team[0], True)
            fighter2 = Fighter(440, FLOOR - 180, p1_team[0], False)
        else:
            fighter1 = Fighter(200, FLOOR - 180, p1_team[0], True)
            fighter2 = Fighter(440, FLOOR - 180, p2_team[0], False)

        connected = (game_mode == "CPU")
        running = True
        
        finish_him_mode = False
        finish_him_timer = 300
        fatality_done = False
        match_over = False

        current_bg = random.choice(backgrounds) if backgrounds else None

        while running and app_running:
            clock.tick(FPS)
            
            if current_bg:
                screen.blit(current_bg, (0, 0))
            else:
                screen.fill(BG_COLOR)
                pygame.draw.rect(screen, (100, 100, 100), (0, FLOOR, WIDTH, HEIGHT - FLOOR))
                
            if fatality_done:
                s = pygame.Surface((WIDTH, HEIGHT)); s.set_alpha(120); s.fill((200,0,0)); screen.blit(s, (0,0))

            for event in pygame.event.get():
                if event.type == pygame.QUIT: app_running = False
                if event.type == pygame.JOYBUTTONDOWN:
                    if joystick.get_button(8) and joystick.get_button(9): running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: running = False

            if not connected and network:
                connected = network.discover_and_connect()
                text = font_info.render(f"Buscando Oponente UDP...", True, (255,255,255))
                screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2))
            else:
                net_data = None
                if network: net_data = network.receive_state()
                
                if fighter1.hp <= 0 and not match_over:
                    fighter2.evolve()
                    if p1_active_idx < 2:
                        p1_active_idx += 1
                        fighter1 = Fighter(200, FLOOR - 180, p1_team[p1_active_idx], True)
                    elif not finish_him_mode:
                        finish_him_mode = True
                        fighter1.is_dizzy = True
                
                if fighter2.hp <= 0 and not match_over:
                    fighter1.evolve()
                    if p2_active_idx < 2:
                        p2_active_idx += 1
                        fighter2 = Fighter(440, FLOOR - 180, p2_team[p2_active_idx], False)
                    elif not finish_him_mode:
                        finish_him_mode = True
                        fighter2.is_dizzy = True

                if finish_him_mode and not match_over:
                    finish_him_timer -= 1
                    if fighter1.doing_fatality or fighter2.doing_fatality:
                        fatality_done = True
                        match_over = True
                    elif finish_him_timer <= 0:
                        fighter1.is_dead = fighter1.is_dizzy
                        fighter2.is_dead = fighter2.is_dizzy
                        match_over = True
                
                if not match_over or fatality_done:
                    if game_mode == "CPU":
                        fighter1.move(WIDTH, HEIGHT, FLOOR, joystick, fighter2, is_local=True, ai=False, finish_him_mode=finish_him_mode)
                        fighter2.move(WIDTH, HEIGHT, FLOOR, None, fighter1, is_local=True, ai=True, finish_him_mode=finish_him_mode)
                    elif game_mode == "HOST":
                        fighter1.move(WIDTH, HEIGHT, FLOOR, joystick, fighter2, is_local=True, ai=False, finish_him_mode=finish_him_mode)
                        fighter2.move(WIDTH, HEIGHT, FLOOR, None, fighter1, is_local=False, net_data=net_data)
                    elif game_mode == "CLIENT":
                        fighter2.move(WIDTH, HEIGHT, FLOOR, joystick, fighter1, is_local=True, ai=False, finish_him_mode=finish_him_mode)
                        fighter1.move(WIDTH, HEIGHT, FLOOR, None, fighter2, is_local=False, net_data=net_data)
                
                fighter1.draw(screen)
                fighter2.draw(screen)

                bar_w = 300
                bar_h = 25
                p1_hp_ratio = max(0, fighter1.hp) / 100.0
                p2_hp_ratio = max(0, fighter2.hp) / 100.0
                
                p1_color = (0, 255, 0) if p1_hp_ratio > 0.5 else (255, 255, 0) if p1_hp_ratio > 0.2 else (255, 0, 0)
                p2_color = (0, 255, 0) if p2_hp_ratio > 0.5 else (255, 255, 0) if p2_hp_ratio > 0.2 else (255, 0, 0)

                pygame.draw.rect(screen, (255, 0, 0), (20, 20, bar_w, bar_h))
                pygame.draw.rect(screen, p1_color, (20, 20, bar_w * p1_hp_ratio, bar_h))
                pygame.draw.rect(screen, (255, 255, 255), (20, 20, bar_w, bar_h), 2)
                
                p1_status = " [EVO]" if fighter1.is_evolved else ""
                name1 = font_small.render(f"{p1_team[p1_active_idx]}{p1_status} ({3 - p1_active_idx})", True, (255, 255, 255))
                screen.blit(name1, (20, 50))

                p2_x = WIDTH - 20 - bar_w
                pygame.draw.rect(screen, (255, 0, 0), (p2_x, 20, bar_w, bar_h))
                pygame.draw.rect(screen, p2_color, (p2_x + (bar_w * (1 - p2_hp_ratio)), 20, bar_w * p2_hp_ratio, bar_h))
                pygame.draw.rect(screen, (255, 255, 255), (p2_x, 20, bar_w, bar_h), 2)
                
                p2_status = " [EVO]" if fighter2.is_evolved else ""
                name2 = font_small.render(f"{p2_team[p2_active_idx]}{p2_status} ({3 - p2_active_idx})", True, (255, 255, 255))
                screen.blit(name2, (WIDTH - 20 - name2.get_width(), 50))

                if finish_him_mode and not match_over:
                    text = font_title.render("¡ACABALO! (Boton Y)", True, (255, 0, 0))
                    screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - 50))
                    
                if match_over:
                    if fatality_done:
                        win_text = "¡FATALITY!"
                    else:
                        win_text = "¡GANADOR!"
                    text = font_title.render(win_text, True, (255, 255, 0))
                    screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2))
                    
                    inst = font_info.render("Presiona SELECT+START para volver", True, (255,255,255))
                    screen.blit(inst, (WIDTH//2 - inst.get_width()//2, HEIGHT//2 + 80))

            pygame.display.flip()

except Exception as e:
    pass

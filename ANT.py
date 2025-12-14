import pygame
import random
import math
import os 

# ====================================================
# A. KONSTANTA PYGAME
# ====================================================
LEBAR_LAYAR = 800
TINGGI_LAYAR = 600
FPS = 60

PUTIH = (255, 255, 255)
HITAM = (0, 0, 0)
HIJAU = (0, 255, 0) 
COKLAT = (139, 69, 19)
MERAH_DARAH = (180, 0, 0) 
KUNING = (255, 255, 0) 

# File gambar
BACKGROUND_IMAGE = "wooden_background.png" 
ANT_BIASA_IMAGE = "ant_biasa.png"
ANT_PRAJURIT_IMAGE = "ant_prajurit.png"
ANT_RATU_IMAGE = "ant_ratu.png"

# File untuk High Score
HIGHSCORE_FILE = "highscore.txt" 

# FILE SUARA
START_SOUND_FILE = "game_start.wav" 
SQUISH_SOUND_FILE = "ant_squish.wav" 

# ====================================================
# B. KELAS INDUK: Semut 
# ====================================================

class Semut(pygame.sprite.Sprite):
    
    def __init__(self, jenis, image_path, ukuran, kecepatan, x=0, y=0, health=1):
        super().__init__()
        
        # Atribut private/protected
        self.__posisi_x = x
        self.__posisi_y = y
        self.__kecepatan = kecepatan 
        self.__health = health
        
        # Atribut public
        self.jenis = jenis
        self.ukuran = ukuran
        
        try:
            original_image = pygame.image.load(image_path).convert_alpha()
            self.image = pygame.transform.scale(original_image, (ukuran, ukuran))
        except pygame.error:
            # Fallback jika gambar tidak ditemukan
            self.image = pygame.Surface([ukuran, ukuran])
            self.image.fill(COKLAT) 
            
        self.rect = self.image.get_rect()
        self.rect.x = self.__posisi_x
        self.rect.y = self.__posisi_y

    def get_posisi(self):
        return self.__posisi_x, self.__posisi_y

    def get_kecepatan(self):
        return self.__kecepatan

    def bergerak(self):
        self.__posisi_y += self.__kecepatan
        self.rect.y = self.__posisi_y

    def update(self):
        """Update untuk Semut Biasa hanya bergerak."""
        self.bergerak()
        return None # Secara default, tidak ada sinyal spawn

    def diserang(self, damage=1):
        self.__health -= damage
        if self.__health <= 0:
            self.kill()
            return True # Semut mati
        return False # Semut tidak mati


# ====================================================
# C. KELAS TURUNAN: SemutPrajurit
# ====================================================

class SemutPrajurit(Semut):
    def __init__(self, x, y):
        # Memanggil konstruktor kelas induk
        super().__init__(jenis="Prajurit", image_path=ANT_PRAJURIT_IMAGE, ukuran=53, kecepatan=2, x=x, y=y, health=2)
        self.arah_x = 1

    def bergerak(self):
        # Akses atribut protected/private dari induk 
        self._Semut__posisi_y += self._Semut__kecepatan
        
        # Gerakan zigzag sederhana
        if self._Semut__posisi_y % 15 < 7:
            self.arah_x = 1
        else:
            self.arah_x = -1
            
        self._Semut__posisi_x += self.arah_x * 0.5 
        
        self.rect.x = self._Semut__posisi_x
        self.rect.y = self._Semut__posisi_y
        
    def diserang(self, damage=1):
        # Override: Armor menahan serangan pertama
        if self._Semut__health > 1:
            print("[Prajurit] Armor menahan serangan!")
        return super().diserang(damage)


# ====================================================
# D. KELAS TURUNAN: SemutRatu
# ====================================================

class SemutRatu(Semut):
    def __init__(self, x, y):
        # Ratu lebih besar dan memiliki health lebih tinggi
        super().__init__(jenis="Ratu", image_path=ANT_RATU_IMAGE, ukuran=90, kecepatan=0.5, x=x, y=y, health=5)
        self.counter_spawn = 0
        
    def bergerak(self):
        self._Semut__posisi_y += self._Semut__kecepatan
        self.rect.y = self._Semut__posisi_y
        
    def update(self):
        """Override update: Selain bergerak, Ratu juga memicu sinyal spawn."""
        self.bergerak() # Lakukan pergerakan dasar
        
        self.counter_spawn += 1
        if self.counter_spawn % 120 == 0: # Spawn anak setiap 120 frame (~2 detik)
            return "SPAWN" 
        
        return None # Mengembalikan None jika tidak spawn


# ====================================================
# E. KELAS UTAMA: GameController
# ====================================================

class GameController:
    
    POIN_SELECTION = {
        "Biasa": 1.0, 
        "Prajurit": 3.0, 
        "Ratu": 10.0
    }
    
    def __init__(self):
        pygame.init()
        # Inisialisasi Mixer untuk Sound
        pygame.mixer.init() 
        
        self.layar = pygame.display.set_mode((LEBAR_LAYAR, TINGGI_LAYAR))
        pygame.display.set_caption("OOP Ant Killer Game (UAS PBO)")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        
        # --- STATUS GAME ---
        self.running = True
        self.game_over = False
        self.is_paused = True # Game dimulai dalam status paused/start screen
        
        # Inisialisasi awal
        self.all_sprites = pygame.sprite.Group()
        self.queue_spawn = []
        self.spawn_delay = 60 
        self.spawn_timer = 0
        self.score = 0
        self.lives = 5 
        
        self.high_score = self.load_high_score()
        
        # Memuat Suara
        self.start_sound = self.load_sound(START_SOUND_FILE)
        self.squish_sound = self.load_sound(SQUISH_SOUND_FILE)
        
        # Memuat Background
        try:
            self.background_image = pygame.image.load(BACKGROUND_IMAGE).convert()
            self.background_image = pygame.transform.scale(self.background_image, (LEBAR_LAYAR, TINGGI_LAYAR))
            print(f"Background berhasil dimuat: {BACKGROUND_IMAGE}")
        except pygame.error:
            print(f"Peringatan: Gagal memuat gambar background {BACKGROUND_IMAGE}. Menggunakan warna hijau solid.")
            self.background_image = pygame.Surface((LEBAR_LAYAR, TINGGI_LAYAR))
            self.background_image.fill(HIJAU)
        
        self.inisiasi_level()

    def load_sound(self, file_path):
        """Memuat file suara, menangani jika gagal."""
        if not os.path.exists(file_path):
            print(f"Peringatan: File suara tidak ditemukan: {file_path}")
            return None
        try:
            sound = pygame.mixer.Sound(file_path)
            # Volume disesuaikan agar tidak terlalu keras
            sound.set_volume(0.5) 
            return sound
        except pygame.error as e:
            print(f"Peringatan: Gagal memuat suara {file_path}. Error: {e}")
            return None
    
    def reset_game(self):
        """Meriset semua variabel game untuk memulai babak baru."""
        self.game_over = False
        self.is_paused = False # Game langsung dimulai setelah reset
        self.score = 0
        self.lives = 5
        self.all_sprites.empty() 
        self.queue_spawn = []
        self.spawn_timer = 0
        self.inisiasi_level()
        print("Game dimulai kembali.")
        
    def load_high_score(self):
        """Memuat high score dari file."""
        if not os.path.exists(HIGHSCORE_FILE):
            return 0
        try:
            with open(HIGHSCORE_FILE, "r") as f:
                return int(f.read())
        except (ValueError, IOError):
            print("Peringatan: File High Score rusak atau kosong.")
            return 0

    def save_high_score(self):
        """Menyimpan high score ke file."""
        try:
            with open(HIGHSCORE_FILE, "w") as f:
                f.write(str(int(self.high_score)))
        except IOError:
            print("Peringatan: Gagal menyimpan High Score.")

    def inisiasi_level(self):
        kecepatan_biasa = lambda: random.uniform(0.5, 1.5) 
        self.queue_spawn = [
            ("Biasa", random.randint(50, 150), 0, kecepatan_biasa()), 
            ("Prajurit", random.randint(250, 350), 0),
            ("Biasa", random.randint(650, 750), 0, kecepatan_biasa()),
            ("Ratu", random.randint(450, 550), 0),
            ("Biasa", random.randint(100, 200), 0, kecepatan_biasa()),
            ("Prajurit", random.randint(500, 600), 0),
        ]

    def spawn_semut(self, jenis, x, y, kecepatan_khusus=None):
        if jenis == "Prajurit":
            semut = SemutPrajurit(x=x, y=y)
        elif jenis == "Ratu":
            semut = SemutRatu(x=x, y=y)
        else:
            kecepatan = kecepatan_khusus if kecepatan_khusus is not None else random.uniform(0.5, 1.5)
            # Semut Biasa (menggunakan kelas induk Semut)
            semut = Semut(jenis="Biasa", image_path=ANT_BIASA_IMAGE, ukuran=38, kecepatan=kecepatan, x=x, y=y)
            
        self.all_sprites.add(semut)

    def spawn_semut_acak(self):
        jenis_semut = random.choice(["Biasa", "Prajurit"])
        x_pos = random.randint(50, LEBAR_LAYAR - 50)
        
        if jenis_semut == "Biasa":
            self.spawn_semut("Biasa", x=x_pos, y=0, kecepatan_khusus=random.uniform(0.5, 1.5))
        elif jenis_semut == "Prajurit":
            self.spawn_semut("Prajurit", x=x_pos, y=0)
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if self.is_paused and not self.game_over:
                        # Mulai game dari start screen
                        self.is_paused = False
                        print("Game dimulai!")
                        if self.start_sound:
                            self.start_sound.play()
                            
                    elif self.game_over:
                        # Mulai lagi game dari game over screen
                        self.reset_game()
                        if self.start_sound:
                            self.start_sound.play()
                        
            # MOUSE CLICK hanya diproses jika game tidak paused dan tidak game over
            if not self.is_paused and not self.game_over and event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                self.handle_click(pos)

    def handle_click(self, pos):
        x, y = pos
        # Iterasi salinan untuk menghindari error iterasi saat kill() dipanggil
        for semut in list(self.all_sprites): 
            if semut.rect.collidepoint(x, y): 
                is_dead = semut.diserang(damage=1) 
                
                if is_dead:
                    # Memainkan suara saat semut dibunuh
                    if self.squish_sound:
                        self.squish_sound.play()
                        
                    jenis_semut = semut.jenis
                    point_dasar = self.POIN_SELECTION.get(jenis_semut, 0)
                    self.score += point_dasar
                    print(f"Dibunuh: {jenis_semut}. Skor saat ini: {int(self.score)}")
                return # Hanya proses satu semut per klik

    def update_spawn_queue(self):
        # Mekanisme spawn dari queue
        if self.spawn_timer <= 0 and self.queue_spawn:
            data_semut = self.queue_spawn.pop(0) 
            jenis, x, y = data_semut[0], data_semut[1], data_semut[2]
            kecepatan = data_semut[3] if len(data_semut) > 3 else None

            self.spawn_semut(jenis, x, y, kecepatan)
            self.spawn_timer = self.spawn_delay 
        else:
            self.spawn_timer -= 1
            
        # Jika queue habis, lakukan spawn acak sesekali
        if not self.queue_spawn and len(self.all_sprites) < 5:
            if random.randint(1, 150) == 1: # Peluang kecil untuk spawn acak
                 self.spawn_semut_acak()


    def update_game(self):
        # Game logic hanya berjalan jika game tidak paused dan tidak game over
        if self.game_over or self.is_paused: 
            return

        self.update_spawn_queue() 
        
        semut_baru = []
        semut_yang_lolos = []

        # Mengganti self.all_sprites.update() dengan loop manual
        # untuk menangkap sinyal spawn dari SemutRatu.update()
        for semut in list(self.all_sprites):
            
            # Panggil update() pada setiap semut, menangkap sinyal spawn dari Ratu
            spawn_signal = semut.update() 
            
            # Cek jika semut lolos dari batas bawah layar
            if semut.get_posisi()[1] > TINGGI_LAYAR:
                semut_yang_lolos.append(semut)
            
            # Proses sinyal spawn dari Ratu
            if spawn_signal == "SPAWN":
                x, y = semut.get_posisi()
                kecepatan_anak = random.uniform(0.5, 1.5)
                # Spawn semut biasa di sekitar Ratu
                semut_baru.append(("Biasa", x + random.randint(-20, 20), y + 20, kecepatan_anak))

        # Proses Semut yang Lolos
        for semut in semut_yang_lolos:
            self.lives -= 1
            semut.kill()
            if self.lives <= 0:
                print("GAME OVER. Anda kehabisan nyawa.")
                
                # Cek High Score
                if self.score > self.high_score:
                    self.high_score = self.score
                    self.save_high_score()
                    print(f"!!! HIGH SCORE BARU: {int(self.high_score)} !!!")
                
                self.game_over = True 
                return

        # Spawn semut baru dari Ratu
        for data in semut_baru:
            jenis, x, y, kecepatan = data
            self.spawn_semut(jenis, x, y, kecepatan)
        

    def draw(self):
        self.layar.blit(self.background_image, (0, 0))
        
        # Semut hanya digambar jika game sedang berjalan
        if not self.is_paused and not self.game_over:
            self.all_sprites.draw(self.layar)
        
        # Tampilkan UI Score dan Lives
        teks_skor = self.font.render(f"Skor: {int(self.score)}", True, HITAM)
        self.layar.blit(teks_skor, (10, 10))
        
        teks_high_score = self.font.render(f"High Score: {int(self.high_score)}", True, HITAM)
        self.layar.blit(teks_high_score, (10, 40)) 
        
        teks_nyawa = self.font.render(f"Nyawa: {self.lives}", True, MERAH_DARAH)
        self.layar.blit(teks_nyawa, (LEBAR_LAYAR - 120, 10))
        
        # --- TAMPILAN START SCREEN ---
        if self.is_paused and not self.game_over:
             start_text = self.font.render("OOP ANT KILLER GAME", True, HITAM)
             rect_title = start_text.get_rect(center=(LEBAR_LAYAR // 2, TINGGI_LAYAR // 2 - 50))
             self.layar.blit(start_text, rect_title)
             
             start_text_prompt = self.font.render("TEKAN SPACE UNTUK MULAI", True, KUNING)
             rect_start = start_text_prompt.get_rect(center=(LEBAR_LAYAR // 2, TINGGI_LAYAR // 2))
             self.layar.blit(start_text_prompt, rect_start)
             
             
        # --- TAMPILAN GAME OVER ---
        elif self.game_over:
             game_over_text = self.font.render("GAME OVER", True, MERAH_DARAH)
             rect_go = game_over_text.get_rect(center=(LEBAR_LAYAR // 2, TINGGI_LAYAR // 2 - 30))
             self.layar.blit(game_over_text, rect_go)
             
             final_score_text = self.font.render(f"SKOR AKHIR: {int(self.score)}", True, HITAM)
             rect_fs = final_score_text.get_rect(center=(LEBAR_LAYAR // 2, TINGGI_LAYAR // 2 + 10))
             self.layar.blit(final_score_text, rect_fs)
             
             restart_text = self.font.render("Tekan SPACE untuk Mulai Lagi", True, KUNING)
             rect_restart = restart_text.get_rect(center=(LEBAR_LAYAR // 2, TINGGI_LAYAR // 2 + 60))
             self.layar.blit(restart_text, rect_restart)
        
        pygame.display.flip()

    def run(self):
        while self.running:
            self.clock.tick(FPS)
            self.handle_events()
            self.update_game()
            self.draw()
            
        pygame.quit()

if __name__ == "__main__":
    game = GameController()
    game.run()
import os
import winsound

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

class AudioAlert:
    """
    Handles triggering local audio alerts when drowsiness thresholds are breached.
    """
    def __init__(self, sound_path="assets/alert.wav"):
        self.sound_path = sound_path
        self.is_playing = False
        self.use_pygame = PYGAME_AVAILABLE and os.path.exists(sound_path)

        if self.use_pygame:
            pygame.mixer.init()
            self.sound = pygame.mixer.Sound(sound_path)

    def play(self):
        """Plays the alert sound if it's not already playing."""
        if not self.is_playing:
            self.is_playing = True
            if self.use_pygame:
                self.sound.play(loops=-1) # loop infinitely until stopped
            else:
                # Fallback to Windows beep: Frequency 2500Hz, Duration 1000ms
                # Beep is blocking, so we'll just do a single beep.
                winsound.Beep(2500, 1000)
                self.is_playing = False # Reset so it can be triggered again next frame

    def stop(self):
        """Stops the alert sound."""
        if self.is_playing and self.use_pygame:
            self.sound.stop()
        self.is_playing = False

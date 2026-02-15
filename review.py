import sys
import os
import pygame
import speech_recognition as sr
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from deep_translator import GoogleTranslator
import pyttsx3
from langdetect import detect
import pyperclip  # ✅ For paste support

# ---------------------------
# Paths Configuration
# ---------------------------
BASE_DIR = r"C:\Users\ragav\OneDrive\Desktop\smart_prod"
FONT_DIR = os.path.join(BASE_DIR, "fonts")

FONT_PATHS = {
    "en": None,
    "ta": os.path.join(FONT_DIR, "NotoSansTamil-VariableFont_wdth,wght.ttf"),
    "hi": os.path.join(FONT_DIR, "NotoSansDevanagari-VariableFont_wdth,wght.ttf"),
    "te": os.path.join(FONT_DIR, "NotoSansTelugu-VariableFont_wdth,wght.ttf"),
    "ml": os.path.join(FONT_DIR, "NotoSansMalayalam-VariableFont_wdth,wght.ttf"),
}

# ---------------------------
# Initialize libraries
# ---------------------------
pygame.init()
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Multilingual Product Review")

WHITE = (245, 245, 245)
BLACK = (10, 10, 10)
GREEN = (34, 177, 76)
RED = (200, 0, 0)
BLUE = (0, 102, 204)
GRAY = (60, 60, 60)

ui_font = pygame.font.Font(None, 28)
ui_font_big = pygame.font.Font(None, 40)

LANGS = {
    "1": ("English", "en-IN", "en"),
    "2": ("Tamil", "ta-IN", "ta"),
    "3": ("Hindi", "hi-IN", "hi"),
    "4": ("Telugu", "te-IN", "te"),
    "5": ("Malayalam", "ml-IN", "ml"),
}

engine = pyttsx3.init()
engine.setProperty("rate", 160)

nltk.download("vader_lexicon", quiet=True)
sia = SentimentIntensityAnalyzer()

# ---------------------------
# Font loader (always from fonts folder)
# ---------------------------
def load_lang_font(short_code, size):
    """
    Force loading from Noto fonts in ./fonts directory to correctly render Indic scripts.
    """
    path = FONT_PATHS.get(short_code)
    if path and os.path.exists(path):
        try:
            return pygame.font.Font(path, size)
        except Exception as e:
            print(f"[font] Error loading {path}: {e}")
    else:
        print(f"[font] Missing file for {short_code}: {path}")
    # fallback
    return pygame.font.Font(None, size)

LANG_FONTS = {}
for code in ["en", "ta", "hi", "te", "ml"]:
    LANG_FONTS[code] = {
        "normal": load_lang_font(code, 28),
        "large": load_lang_font(code, 40),
        "emoji": load_lang_font(code, 64),
    }

# ---------------------------
# Speech recognition
# ---------------------------
def record_and_recognize(recog_lang_code):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("[rec] Listening... speak now")
        r.adjust_for_ambient_noise(source, duration=0.4)
        audio = r.listen(source, timeout=8, phrase_time_limit=10)
    try:
        text = r.recognize_google(audio, language=recog_lang_code)
        print(f"[recog] success ({recog_lang_code}): {text!r}")
        return text
    except sr.UnknownValueError:
        print("[recog] Could not understand audio")
        return ""
    except sr.RequestError as e:
        print(f"[recog] API error: {e}")
        return ""

# ---------------------------
# Sentiment analysis
# ---------------------------
def get_sentiment_from_text(original_text):
    if not original_text.strip():
        return None, None, None
    try:
        translated = GoogleTranslator(source="auto", target="en").translate(original_text)
    except Exception as e:
        print("[translate] error:", e)
        translated = original_text
    scores = sia.polarity_scores(translated)
    compound = scores["compound"]
    if compound >= 0.05:
        label = "Positive"
    elif compound <= -0.05:
        label = "Negative"
    else:
        label = "Neutral"
    return translated, scores, label

# ---------------------------
# TTS
# ---------------------------
def speak_text(text):
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print("[tts] error:", e)

# ---------------------------
# UI helper
# ---------------------------
def draw_text_centered(font_obj, text, y, color=BLACK):
    if not text:
        return
    lines = str(text).split("\n")
    for i, line in enumerate(lines):
        surf = font_obj.render(line, True, color)
        screen.blit(surf, (WIDTH // 2 - surf.get_width() // 2, y + i * (surf.get_height() + 4)))

# ---------------------------
# Main
# ---------------------------
def main():
    stage = "menu"
    choice = None
    input_text = ""
    translated = ""
    scores = None
    label = None
    lang_font = LANG_FONTS["en"]["normal"]
    clock = pygame.time.Clock()

    while True:
        screen.fill(WHITE)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.KEYDOWN:
                if stage == "menu":
                    if ev.unicode in LANGS:
                        choice = ev.unicode
                        stage = "input_choice"

                elif stage == "input_choice":
                    if ev.unicode.lower() == "s":
                        lang_name, recog_code, short_code = LANGS[choice]
                        lang_font = LANG_FONTS.get(short_code, LANG_FONTS["en"])["normal"]
                        input_text = record_and_recognize(recog_code)
                        if not input_text:
                            input_text = ""
                            scores = None
                            label = None
                        else:
                            translated, scores, label = get_sentiment_from_text(input_text)
                            speak_text(f"Detected {label} review.")
                            stage = "result"

                    elif ev.unicode.lower() == "t":
                        input_text = ""
                        stage = "typing"

                elif stage == "typing":
                    # ✅ Paste support (Ctrl + V)
                    if ev.key == pygame.K_v and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                        clipboard_text = pyperclip.paste()
                        if clipboard_text:
                            input_text += clipboard_text

                    elif ev.key == pygame.K_RETURN:
                        translated, scores, label = get_sentiment_from_text(input_text)
                        if label:
                            speak_text(f"Detected {label} review.")
                        stage = "result"

                    elif ev.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    else:
                        input_text += ev.unicode

                elif stage == "result":
                    stage = "menu"

        # ---------- UI Draw ----------
        if stage == "menu":
            draw_text_centered(ui_font_big, "Choose language:", 60)
            y = 160
            for k in sorted(LANGS.keys()):
                draw_text_centered(ui_font, f"{k} - {LANGS[k][0]}", y)
                y += 40
            draw_text_centered(ui_font, "Press number (1-5)", 420, BLUE)
            draw_text_centered(ui_font, "After choosing, press S to Speak or T to Type", 460)

        elif stage == "input_choice":
            lang_name, recog_code, short_code = LANGS[choice]
            draw_text_centered(ui_font_big, f"Selected: {lang_name}", 60)
            draw_text_centered(ui_font, "Press 'S' to Speak OR 'T' to Type", 140)
            draw_text_centered(ui_font, "If Speak: please speak clearly, wait until listening ends", 200)

        elif stage == "typing":
            draw_text_centered(ui_font_big, "Type or Paste (Ctrl+V) your review below, then press Enter", 40)
            font_for_display = LANG_FONTS.get(LANGS[choice][2], LANG_FONTS["en"])["normal"]
            draw_text_centered(font_for_display, input_text, 200, BLUE)

        elif stage == "result":
            lang_short = LANGS[choice][2]
            font_for_display = LANG_FONTS.get(lang_short, LANG_FONTS["en"])["normal"]
            draw_text_centered(ui_font_big, f"Original ({LANGS[choice][0]}):", 20)
            draw_text_centered(font_for_display, input_text or "(no text recognized)", 70, BLACK)
            draw_text_centered(ui_font_big, "Translated (for sentiment):", 220)
            draw_text_centered(ui_font, translated or "(translation failed)", 260, BLACK)

            if scores:
                pos, neu, neg = scores["pos"], scores["neu"], scores["neg"]
                pygame.draw.rect(screen, GREEN, (220, 330, int(pos * 400), 36))
                pygame.draw.rect(screen, BLUE,  (220, 380, int(neu * 400), 36))
                pygame.draw.rect(screen, RED,   (220, 430, int(neg * 400), 36))
                draw_text_centered(ui_font, f"Positive: {pos*100:.1f}%", 330)
                draw_text_centered(ui_font, f"Neutral:  {neu*100:.1f}%", 380)
                draw_text_centered(ui_font, f"Negative: {neg*100:.1f}%", 430)
                draw_text_centered(ui_font_big, f"Result: {label}", 500)
            else:
                draw_text_centered(ui_font, "No sentiment available.", 350)

            draw_text_centered(ui_font, "Press any key to return to menu", 560, GRAY)

        pygame.display.flip()
        clock.tick(30)

if __name__ == "__main__":
    main()

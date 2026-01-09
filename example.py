#!/usr/bin/env python3
"""
Example usage of kokoro_announce library.

This script demonstrates how to use the library to generate multiple
TTS audio files with different voices, languages, and parameters.
"""

from pathlib import Path
from kokoro_announce import KokoroAnnouncer, KokoroSettings

def main():
    # Output folder - will be created if it doesn't exist
    output_folder = Path("generated_audio")
    output_folder.mkdir(exist_ok=True)
    
    # List of texts to synthesize with different parameters
    synthesis_tasks = [
        {"text": "Hello, this is a test of American English voice.", "voice": "af_heart", "lang": "a", "speed": 1.0, "sample_rate": 24000, "filename": "english_american.wav"},
        {"text": "Good afternoon, this is British English speaking.", "voice": "bm_lewis", "lang": "b", "speed": 0.9, "sample_rate": 24000, "filename": "english_british.wav"},
        {"text": "Hola, esto es una prueba en español.", "voice": "ef_dora", "lang": "e", "speed": 1.1, "sample_rate": 24000, "filename": "spanish_test.wav"},
        {"text": "Bonjour, ceci est un test en français.", "voice": "ff_siwis", "lang": "f", "speed": 1.0, "sample_rate": 24000, "filename": "french_test.wav"}
    ]
    
    print(f"[Info] Generating {len(synthesis_tasks)} audio files...")
    print(f"[Info] Output folder: {output_folder.absolute()}")
    print("-" * 50)
    
    # Generate each audio file
    for i, task in enumerate(synthesis_tasks, 1):
        try:
            # Create settings for this task
            settings = KokoroSettings(
                voice=task["voice"],
                lang_code=task["lang"],
                speed=task["speed"],
                sample_rate=task["sample_rate"]
            )
            
            # Create announcer with these settings
            announcer = KokoroAnnouncer(settings)
            
            # Generate output path
            output_path = output_folder / task["filename"]
            
            # Synthesize to file
            print(f"[Event] {i}/{len(synthesis_tasks)}: Generating '{task['filename']}'...")
            print(f"[Info] Text: {task['text'][:50]}{'...' if len(task['text']) > 50 else ''}")
            print(f"[Info] Voice: {task['voice']} (lang: {task['lang']}, speed: {task['speed']}, rate: {task['sample_rate']})")
            
            output_file = announcer.synthesize_to_file(task["text"], str(output_path))
            print(f"[Success] Generated: {output_file}")
                
        except Exception as e:
            print(f"[Error] Failed to generate '{task['filename']}': {e}")
        
        print()
    
    print("[Complete] Done! Check the generated_audio folder for your files.")

if __name__ == "__main__":
    main()
# main.py
# CLIP Runner for Name Reels Creator
# Logic lives in name_reel_maker.py

import sys
import os
from name_reel_maker import create_multiple_reels, cleanup_temp

def main():
    if len(sys.argv) < 2:
        print("\n🚀 Name Reels Creator")
        print("Usage: python3 main.py 'Name1, Name2' [optional_music.mp3]")
        print("Example: python3 main.py 'Vallarasu, Arjun' music.mp3\n")
        sys.exit(1)

    # Parse names from comma-separated string
    names = [n.strip() for n in sys.argv[1].split(",") if n.strip()]
    music = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"✨ Starting creation for {len(names)} name(s)...")
    
    try:
        results = create_multiple_reels(names, music)
        
        print(f"\n{'='*50}")
        print(f"✅ Finished! Created {len(results)}/{len(names)} reels.")
        for name, path in results:
            print(f"   → {name}: {path}")
        print(f"{'='*50}\n")
        
    except KeyboardInterrupt:
        print("\n⚠️ Process interrupted by user.")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
    finally:
        cleanup_temp()

if __name__ == "__main__":
    main()
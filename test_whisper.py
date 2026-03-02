import whisper

print("🎤 Whisper Transcription Test")
print("=" * 50)

# Load the AI model
print("\n⏳ Loading Whisper model...")
model = whisper.load_model("base")
print("✅ Model loaded!")

# Transcribe the audio file
print("\n🎯 Transcribing your audio file...")
print("   (This might take 30 seconds - 2 minutes)")
result = model.transcribe("TestAudio2.ogg")

# Display the full transcription
print("\n" + "=" * 50)
print("📝 FULL TRANSCRIPTION:")
print("=" * 50)
print(result["text"])

# Display timestamped segments
print("\n" + "=" * 50)
print("⏱️ TIMESTAMPED SEGMENTS:")
print("=" * 50)

for segment in result["segments"]:
    # Calculate timestamp in minutes:seconds format
    start_min = int(segment['start'] // 60)
    start_sec = int(segment['start'] % 60)
    end_min = int(segment['end'] // 60)
    end_sec = int(segment['end'] % 60)
    
    # Display timestamp and text
    print(f"\n[{start_min}:{start_sec:02d} - {end_min}:{end_sec:02d}]")
    print(f"  {segment['text']}")

print("\n" + "=" * 50)
print("✅ Transcription complete!")
print("=" * 50)
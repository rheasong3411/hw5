export function SpeechBubble({ text }: { text: string }) {
  return (
    <div className="speech-bubble">
      {text.slice(0, 125) || "Working through the ticket…"}
    </div>
  );
}

"""Support endpoints: ticket submission, ticket resolution, conversational chat."""
import logging
import re
import unicodedata

from fastapi import APIRouter, Header, HTTPException

from backend.app.schemas import (
    ChatRequest,
    ChatResponse,
    ResolveRequest,
    TicketCreate,
    TicketResponse,
)
from backend.app.ticket_store import (
    TICKETS_PATH,  # noqa: F401
    create_ticket,
    get_tickets,
    resolve_ticket,
)

support_router = APIRouter(prefix="/support", tags=["support"])
logger = logging.getLogger(__name__)


# ─── Text normalisation ───────────────────────────────────────────────────────

def _normalise(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[?!.,;:'\"]", "", text)
    return text


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text))


# ─── "More detail" intent detection ──────────────────────────────────────────
# When a user replies to a follow-up question saying "yes / tell me more / how"
# we need to detect that and serve the `detail` from the last bot turn.

_MORE_TRIGGERS = {
    "yes", "yeah", "yep", "yup", "sure", "ok", "okay", "go on", "go ahead",
    "please", "tell me more", "more info", "more information", "more details",
    "explain more", "elaborate", "more", "how", "how do i", "show me",
    "what do i do", "what should i do", "continue", "keep going", "and then",
    "next", "yes please", "i want to know more", "can you explain",
}

_NO_TRIGGERS = {
    "no", "nope", "nah", "not really", "no thanks", "im good", "i'm good",
    "thats fine", "that's fine", "got it", "i understand", "i get it",
    "never mind", "nevermind", "no need", "skip", "cancel",
}

def _is_more(norm: str) -> bool:
    return any(t in norm for t in _MORE_TRIGGERS) or norm in _MORE_TRIGGERS

def _is_no(norm: str) -> bool:
    return any(t in norm for t in _NO_TRIGGERS) or norm in _NO_TRIGGERS


# ─── Knowledge base (two-level: short reply + optional follow-up + detail) ───
#
# Each entry:
#   triggers    – trigger phrases (substring match on normalised message)
#   tokens      – bonus token keywords for fuzzy matching
#   reply       – SHORT first response (1-3 sentences max)
#   follow_up   – question the bot asks back (None = no follow-up)
#   suggestions – quick-reply button labels shown to the user
#   detail      – rich extended answer served when user says yes/more
#   escalate    – append ticket CTA to detail

_KB: list[dict] = [

    # ── GREETING ──────────────────────────────────────────────────────────────
    {
        "triggers": ["hello", "hi there", "hey there", "good morning", "good afternoon",
                     "good evening", "howdy", "greetings", "sup", "whats up", "hiya", "hey"],
        "tokens": ["hi", "hey", "morning", "evening", "hello"],
        "reply": "Hey there! 👋 I'm DeepScan's support assistant. What can I help you with today?",
        "follow_up": "Are you looking to analyze a video, or do you have a question about the platform?",
        "suggestions": ["How do I analyze a video?", "What is DeepScan?", "I have a problem"],
        "detail": None,
        "escalate": False,
    },

    # ── WHAT IS DEEPSCAN ──────────────────────────────────────────────────────
    {
        "triggers": ["what is deepscan", "what is this app", "what does this do",
                     "what does deepscan do", "purpose of this app", "about deepscan",
                     "explain deepscan", "tell me about deepscan"],
        "tokens": ["purpose", "about", "platform", "tool"],
        "reply": "DeepScan is an AI-powered deepfake detection platform. You upload an MP4 video and it tells you whether it's authentic or AI-generated — with a confidence score and a visual explanation.",
        "follow_up": "Want to know how it works under the hood, or would you rather jump straight into using it?",
        "suggestions": ["How does it work?", "How do I use it?", "What's a deepfake?"],
        "detail": (
            "**Here's the full picture:**\n\n"
            "🎥 Upload any MP4 (up to 100 MB)\n"
            "🧠 CNN+LSTM neural network analyzes each frame + temporal patterns\n"
            "📊 Get: **AUTHENTIC** or **DEEPFAKE** label, confidence %, and a Grad-CAM heatmap\n"
            "📁 Every result is saved to your **History** page\n"
            "📦 **Batch mode** — analyze up to 10 videos at once\n"
            "📈 **Stats page** — see your usage patterns and fake/real breakdown\n\n"
            "Built with MLOps best practices: MLflow tracking, Airflow pipelines, and Prometheus monitoring."
        ),
        "escalate": False,
    },

    # ── WHAT IS A DEEPFAKE ────────────────────────────────────────────────────
    {
        "triggers": ["what is a deepfake", "define deepfake", "deepfake meaning",
                     "what are deepfakes", "explain deepfake", "how are deepfakes made",
                     "face swap", "synthetic media", "ai generated video"],
        "tokens": ["deepfake", "fake", "synthetic", "manipulated", "swap"],
        "reply": "A deepfake is a video where AI has been used to manipulate someone's face or voice — most commonly swapping one person's face onto another's body.",
        "follow_up": "Would you like to know how DeepScan detects them?",
        "suggestions": ["Yes, how does detection work?", "How accurate is it?", "No thanks"],
        "detail": (
            "**How deepfakes are made and detected:**\n\n"
            "Deepfakes are created with GANs or diffusion models. They leave subtle artifacts — "
            "unnatural blending at hairlines, ear edges, and around the eyes.\n\n"
            "DeepScan's CNN+LSTM model is specifically trained to spot these artifacts:\n"
            "• **EfficientNet-B0** scans each frame for spatial anomalies\n"
            "• **LSTM** looks for unnatural motion patterns across frames\n"
            "• **Grad-CAM** then highlights *which regions* triggered the detection\n\n"
            "It works best on clear, front-facing videos with good lighting."
        ),
        "escalate": False,
    },

    # ── HOW TO USE ────────────────────────────────────────────────────────────
    {
        "triggers": ["how to use", "how do i use", "how to analyze", "how do i analyze",
                     "how to detect", "how to scan", "get started", "step by step",
                     "instructions", "guide me", "walk me through", "first time",
                     "never used before", "tutorial", "quickstart", "how do i begin"],
        "tokens": ["start", "use", "begin", "step", "tutorial", "guide", "first"],
        "reply": "It's simple! Go to **Analyze** in the nav bar, drag-and-drop your MP4 file, and hit analyze. Results appear in 5–30 seconds.",
        "follow_up": "Want the full step-by-step walkthrough, or do you have a specific question about the process?",
        "suggestions": ["Full walkthrough please", "What file formats work?", "How long does it take?"],
        "detail": (
            "**Step-by-step guide:**\n\n"
            "1. **Log in** — use `user` / `user123` (or `admin` / `admin123`)\n"
            "2. **Go to Analyze** — click it in the top nav bar\n"
            "3. **Upload your video** — drag-and-drop or click the upload zone. Must be MP4, under 100 MB\n"
            "4. **Wait for results** — the progress bar shows 4 stages (upload → preprocess → inference → Grad-CAM)\n"
            "5. **Read the result** — you get:\n"
            "   • AUTHENTIC or DEEPFAKE verdict\n"
            "   • Confidence score (0–100%)\n"
            "   • Grad-CAM heatmap showing which facial regions influenced the decision\n"
            "   • Options to download report, copy share link, adjust threshold, and submit feedback\n\n"
            "**Tip:** Use **Batch** mode to analyze up to 10 videos at once!"
        ),
        "escalate": False,
    },

    # ── FILE FORMAT ───────────────────────────────────────────────────────────
    {
        "triggers": ["what file", "file type", "file format", "file extension",
                     "accepted file", "supported file", "upload format",
                     "can i upload", "mp4", "avi", "mov", "mkv", "wmv",
                     "convert to mp4", "different format", "not mp4"],
        "tokens": ["mp4", "avi", "mov", "mkv", "format", "extension", "convert"],
        "reply": "DeepScan only accepts **MP4** files (up to 100 MB). AVI, MOV, MKV, and WMV aren't supported.",
        "follow_up": "Is your video in a different format? I can tell you how to convert it quickly.",
        "suggestions": ["Yes, how do I convert?", "My file is MP4 but still failing", "What about file size?"],
        "detail": (
            "**Converting to MP4 — three easy options:**\n\n"
            "🖥️ **HandBrake** (free, any OS)\n"
            "Open your file → select H.264 MP4 preset → Start Encode\n\n"
            "🎬 **VLC**\n"
            "Media → Convert/Save → select MP4 (H.264) → Start\n\n"
            "⌨️ **FFmpeg** (command line)\n"
            "```\nffmpeg -i input.avi output.mp4\n```\n\n"
            "🌐 **Online**: CloudConvert or FreeConvert — no install needed\n\n"
            "After converting, re-upload and it should work right away."
        ),
        "escalate": False,
    },

    # ── FILE SIZE ─────────────────────────────────────────────────────────────
    {
        "triggers": ["file size", "size limit", "how big", "how large", "max size",
                     "file too big", "too large", "large file", "100 mb",
                     "reduce file size", "compress video", "trim video"],
        "tokens": ["size", "limit", "large", "compress", "mb"],
        "reply": "The limit is **100 MB** per file. Most clips under 2 minutes at 720p are well within that.",
        "follow_up": "Is your video over 100 MB? I can walk you through how to reduce its size.",
        "suggestions": ["Yes, how do I reduce size?", "No, upload is still failing", "What formats are supported?"],
        "detail": (
            "**Ways to reduce video file size:**\n\n"
            "• **Trim it** — cut out unnecessary sections using Clideo or CapCut\n"
            "• **Lower resolution** — 720p is plenty for accurate detection\n"
            "• **Reduce bitrate** with FFmpeg:\n"
            "```\nffmpeg -i input.mp4 -b:v 1M output.mp4\n```\n"
            "• **HandBrake** — open file → lower the RF quality slider → encode\n\n"
            "**Tip:** Most deepfake artifacts appear in the first 30–60 seconds, so a short clip is often enough."
        ),
        "escalate": False,
    },

    # ── UPLOAD FAILING ────────────────────────────────────────────────────────
    {
        "triggers": ["upload failed", "upload error", "upload not working", "cant upload",
                     "cannot upload", "file not uploading", "upload problem",
                     "upload stuck", "nothing happens when i upload", "upload button not working",
                     "drag and drop not working"],
        "tokens": ["upload", "failed", "error", "stuck", "cant"],
        "reply": "Sorry to hear the upload isn't working. The most common causes are the wrong file format or file size over 100 MB.",
        "follow_up": "Can you tell me more — is there an error message on screen, or does it just do nothing?",
        "suggestions": ["There's an error message", "It just does nothing", "It's MP4 and under 100MB"],
        "detail": (
            "**Upload troubleshooting checklist:**\n\n"
            "1. ✅ File must be `.mp4` (not `.avi`, `.mov`, `.mkv`)\n"
            "2. ✅ File must be under **100 MB**\n"
            "3. ✅ Try **Chrome or Firefox** — some browsers handle file APIs differently\n"
            "4. ✅ Hard refresh: **Ctrl+Shift+R** (Windows) or **Cmd+Shift+R** (Mac)\n"
            "5. ✅ Check your internet connection\n"
            "6. ✅ If you see a 500 error, the backend may be down — this needs admin action\n\n"
            "If none of the above helps, please raise a support ticket with the exact error message."
        ),
        "escalate": True,
    },

    # ── PROCESSING TIME ───────────────────────────────────────────────────────
    {
        "triggers": ["how long does it take", "processing time", "how fast",
                     "takes too long", "taking forever", "very slow", "slow analysis",
                     "still loading", "still processing", "stuck on loading",
                     "progress bar stuck", "timeout", "timed out", "waiting too long"],
        "tokens": ["slow", "long", "time", "timeout", "loading", "wait", "stuck"],
        "reply": "Most videos analyze in **5–30 seconds**. Videos over 2 minutes can take up to 60 seconds.",
        "follow_up": "Is your analysis stuck right now, or are you just planning ahead?",
        "suggestions": ["It's stuck right now", "Just planning ahead", "How do I speed it up?"],
        "detail": (
            "**If analysis is stuck:**\n\n"
            "• Wait up to **90 seconds** — Grad-CAM generation can be slow on large videos\n"
            "• If the progress bar is frozen past 90s, **refresh** (Ctrl+R) and try again\n"
            "• Try a **shorter clip** (under 30 seconds) to confirm it's not file-specific\n"
            "• Check the pipeline status bar — if services show 🔴, the backend may be down\n\n"
            "**To speed up analysis:**\n"
            "• Use shorter clips — the LSTM only needs a few seconds to detect patterns\n"
            "• Lower the video resolution to 720p before uploading\n\n"
            "Persistent timeouts across multiple videos require admin attention."
        ),
        "escalate": True,
    },

    # ── PREDICTION RESULT ─────────────────────────────────────────────────────
    {
        "triggers": ["what does real mean", "what does fake mean", "what does authentic mean",
                     "what does the result mean", "how to read result", "interpret result",
                     "understand result", "result explanation", "what does it output",
                     "what is the verdict", "prediction mean"],
        "tokens": ["real", "fake", "verdict", "result", "prediction", "output", "mean"],
        "reply": "DeepScan gives you one of two verdicts: **AUTHENTIC** (no manipulation detected) or **DEEPFAKE** (AI-generated content found). Each comes with a confidence score.",
        "follow_up": "Want me to explain what the confidence score means, or how to handle a result you disagree with?",
        "suggestions": ["Explain confidence score", "The result seems wrong", "What is the heatmap?"],
        "detail": (
            "**Reading your result:**\n\n"
            "🟢 **AUTHENTIC** — model found no manipulation signals\n"
            "🔴 **DEEPFAKE** — model detected face-swap or AI-generation artifacts\n\n"
            "**Confidence score guide:**\n"
            "• 90–100% → Very high confidence, strong signal\n"
            "• 70–89% → High confidence, reliable\n"
            "• 55–69% → Moderate — treat with some caution\n"
            "• Near 50% → Uncertain — model saw mixed signals\n\n"
            "**Also check the Grad-CAM heatmap** — it shows which facial regions influenced the decision. "
            "Bright/red areas are what the model focused on."
        ),
        "escalate": False,
    },

    # ── WRONG PREDICTION ──────────────────────────────────────────────────────
    {
        "triggers": ["wrong prediction", "incorrect prediction", "bad result",
                     "false positive", "false negative", "wrong result", "incorrect result",
                     "disagree with result", "model is wrong", "prediction is wrong",
                     "it says fake but its real", "it says real but its fake",
                     "misclassified", "the result seems wrong", "i think its wrong"],
        "tokens": ["wrong", "incorrect", "false", "bad", "disagree", "misclassified"],
        "reply": "The model isn't perfect — it can make mistakes, especially when confidence is near 50%. Your feedback is really valuable for improving it.",
        "follow_up": "Did you already try adjusting the threshold slider on the result card?",
        "suggestions": ["What's the threshold slider?", "How do I submit feedback?", "It's consistently wrong"],
        "detail": (
            "**What you can do about a wrong prediction:**\n\n"
            "1. **Submit feedback** — click 'Was this correct?' → Yes/No on the result card. "
            "This sends labeled data back for future model training.\n\n"
            "2. **Adjust the threshold slider** — drag it on the result card to re-evaluate the verdict "
            "at a different cutoff (default 50%). Lower = catch more deepfakes; higher = fewer false positives.\n\n"
            "3. **Check the confidence** — if it's near 50%, the model was genuinely uncertain. "
            "These borderline cases are the hardest.\n\n"
            "4. **Test a different clip** — try a longer or cleaner segment from the same video.\n\n"
            "For systematic errors on specific video types, please raise a support ticket with examples."
        ),
        "escalate": True,
    },

    # ── CONFIDENCE SCORE ──────────────────────────────────────────────────────
    {
        "triggers": ["confidence score", "what is confidence", "confidence percentage",
                     "how confident", "confidence level", "low confidence", "high confidence",
                     "50 percent", "near 50", "borderline", "can i trust the result",
                     "how sure is the model"],
        "tokens": ["confidence", "score", "percent", "certain", "sure", "trust"],
        "reply": "The confidence score shows how certain the model is — **above 75%** is reliable, **near 50%** means the model was genuinely unsure.",
        "follow_up": "Is your confidence score high or low? I can help you decide what to do next.",
        "suggestions": ["Score is near 50%", "Score is high but result seems wrong", "How do I improve accuracy?"],
        "detail": (
            "**Full confidence score guide:**\n\n"
            "• **90–100%** — Very high. Strong manipulation or authenticity signal.\n"
            "• **75–89%** — High. Result is reliable for most purposes.\n"
            "• **55–74%** — Moderate. Treat with some caution.\n"
            "• **50–54%** — Low. Mixed signals — outcome is uncertain.\n\n"
            "**When confidence is low (~50%):**\n"
            "• Try the **threshold slider** to re-evaluate at a different cutoff\n"
            "• Upload a longer or higher-quality clip\n"
            "• Submit feedback so the model learns from this edge case\n"
            "• Check the **Grad-CAM heatmap** — low confidence often means the model spotted some "
            "but not enough artifacts to be sure"
        ),
        "escalate": False,
    },

    # ── GRAD-CAM ──────────────────────────────────────────────────────────────
    {
        "triggers": ["gradcam", "grad cam", "grad-cam", "heatmap", "heat map",
                     "saliency map", "visualization", "highlighted regions",
                     "what is the heatmap", "red areas", "bright areas",
                     "model explainability", "explainability", "why did it say fake",
                     "why did it say real", "how did the model decide", "what did the model look at"],
        "tokens": ["heatmap", "gradcam", "region", "highlight", "explain", "overlay"],
        "reply": "The Grad-CAM heatmap shows *why* the model made its decision — brighter/redder regions are what it focused on most.",
        "follow_up": "Want to know what to look for in the heatmap, or why a specific region was highlighted?",
        "suggestions": ["What regions indicate a deepfake?", "How do I read the colors?", "My heatmap looks weird"],
        "detail": (
            "**How to read the Grad-CAM heatmap:**\n\n"
            "🔴 **Red/bright areas** → high influence on the prediction\n"
            "🔵 **Blue/dark areas** → low influence\n\n"
            "**What to look for in deepfakes:**\n"
            "The model typically highlights:\n"
            "• Eye edges and corners — common blending artifacts\n"
            "• Mouth / jaw transition — where face-swap tools leave seams\n"
            "• Hairline boundaries — hard to synthesize perfectly\n"
            "• Ear areas — often poorly generated\n\n"
            "**For authentic videos:**\n"
            "Highlights tend to be on natural high-motion or high-texture areas — "
            "these don't indicate manipulation.\n\n"
            "Think of it as the model pointing at evidence, not absolute proof. "
            "Always read it alongside the confidence score."
        ),
        "escalate": False,
    },

    # ── MODEL / HOW IT WORKS ──────────────────────────────────────────────────
    {
        "triggers": ["how does the model work", "what model is used", "model architecture",
                     "what algorithm", "cnn lstm", "efficientnet", "neural network",
                     "how was it trained", "model accuracy", "model performance",
                     "under the hood", "technical details", "how accurate is it"],
        "tokens": ["model", "cnn", "lstm", "neural", "algorithm", "trained", "accuracy"],
        "reply": "DeepScan uses a **CNN+LSTM** architecture — EfficientNet-B0 reads each frame, and an LSTM finds patterns across the sequence of frames.",
        "follow_up": "Want the full technical breakdown, or are you more interested in accuracy and limitations?",
        "suggestions": ["Full technical details", "How accurate is it?", "What are its limitations?"],
        "detail": (
            "**Technical architecture:**\n\n"
            "🏗️ **EfficientNet-B0 (CNN)** — extracts spatial features from each video frame. "
            "Trained to spot subtle face-swap artifacts.\n\n"
            "⏱️ **LSTM** — processes the frame sequence to catch temporal inconsistencies "
            "(unnatural eye movement, expression transitions, lighting changes).\n\n"
            "🎨 **Grad-CAM** — applied post-inference to show which regions activated most strongly.\n\n"
            "📊 **Training:** SDFVD dataset, tracked with MLflow, deployed via Docker.\n\n"
            "**Best accuracy conditions:**\n"
            "✅ Front-facing face, clear lighting, 720p+, 5–60 second clips\n"
            "❌ Blurry/occluded faces, extreme angles, heavy compression, very short clips\n\n"
            "Visit the **Model Card** page in the nav bar for full specs and known limitations."
        ),
        "escalate": False,
    },

    # ── BATCH UPLOAD ──────────────────────────────────────────────────────────
    {
        "triggers": ["batch upload", "batch mode", "batch processing", "upload multiple",
                     "multiple videos", "many videos", "bulk upload", "upload at once",
                     "analyze multiple", "can i upload more than one", "10 videos"],
        "tokens": ["batch", "multiple", "bulk", "several", "many"],
        "reply": "Yes! The **Batch** page lets you analyze up to **10 MP4 videos at once** — each processed independently.",
        "follow_up": "Want to know how to use it, or are you hitting an issue with a batch?",
        "suggestions": ["How do I use batch mode?", "My batch isn't working", "Are results saved?"],
        "detail": (
            "**Using Batch mode:**\n\n"
            "1. Click **Batch** in the top nav bar\n"
            "2. Click 'Choose MP4 files…' and select up to 10 files\n"
            "3. Click **Analyze All**\n"
            "4. A results table appears with per-file: verdict, confidence, latency, and any errors\n\n"
            "**Things to know:**\n"
            "• Each file still has the 100 MB limit\n"
            "• Files process sequentially — larger batches take longer\n"
            "• All successful results are saved to your **History** page\n"
            "• If one file fails, the others still process normally — check the Error column\n\n"
            "If all files fail with the same error, the backend may need restarting."
        ),
        "escalate": False,
    },

    # ── HISTORY ───────────────────────────────────────────────────────────────
    {
        "triggers": ["history page", "prediction history", "past results", "previous results",
                     "my history", "view history", "history not showing", "history empty",
                     "no history", "history missing", "old results gone"],
        "tokens": ["history", "past", "previous", "saved", "old"],
        "reply": "The **History** page shows your last 50 analyses with a confidence trend chart. Click 'History' in the nav bar.",
        "follow_up": "Is your history showing correctly, or is it appearing empty?",
        "suggestions": ["It's empty even after analyzing", "How does the trend chart work?", "Can I delete history?"],
        "detail": (
            "**If history appears empty:**\n\n"
            "• Make sure you're logged in as the **same user** who ran the analyses\n"
            "• Analyses run as 'anonymous' (not logged in properly) won't appear\n"
            "• History is per-user and capped at **50 most recent records**\n\n"
            "**The sparkline chart** shows your confidence scores over time — "
            "🔴 dots = deepfake verdicts, 🟢 dots = authentic verdicts. "
            "It appears once you have 2+ records.\n\n"
            "**Deleting history:** Not available via the UI in the current version. "
            "Contact an admin if you need records cleared."
        ),
        "escalate": False,
    },

    # ── STATS ─────────────────────────────────────────────────────────────────
    {
        "triggers": ["stats page", "statistics", "my stats", "usage stats", "personal stats",
                     "how many videos analyzed", "total analyses", "stats not showing",
                     "donut chart", "average confidence", "average latency"],
        "tokens": ["stats", "statistics", "total", "average", "kpi"],
        "reply": "The **Stats** page shows your personal usage summary — total analyses, fake/real ratio, average confidence, and more.",
        "follow_up": "Are you looking to understand a specific stat, or is the page not loading correctly?",
        "suggestions": ["What do the stats mean?", "Page isn't loading", "How are stats calculated?"],
        "detail": (
            "**Stats page breakdown:**\n\n"
            "• **Total analyses** — all videos you've analyzed (up to 50 stored)\n"
            "• **This week** — analyses in the last 7 days\n"
            "• **Avg confidence** — mean confidence score across all your results\n"
            "• **Avg latency** — mean inference time in milliseconds\n"
            "• **Last analysis** — how long ago your most recent analysis was\n\n"
            "🍩 **Donut chart** — shows your fake vs. authentic split visually\n\n"
            "Stats are calculated from your last 50 saved records. "
            "If the page is empty, you haven't run any analyses yet — head to the **Analyze** page!"
        ),
        "escalate": False,
    },

    # ── PRIVACY ───────────────────────────────────────────────────────────────
    {
        "triggers": ["is my video stored", "do you save my video", "data privacy",
                     "privacy", "gdpr", "is it secure", "who can see my video",
                     "delete my data", "personal data", "sensitive data"],
        "tokens": ["privacy", "store", "save", "data", "secure", "delete", "gdpr"],
        "reply": "Your video is **never saved to disk**. It's processed entirely in memory and discarded immediately after analysis.",
        "follow_up": "Do you have a specific data concern — for example, GDPR deletion or compliance requirements?",
        "suggestions": ["What data IS saved?", "I need data deleted", "Is the connection secure?"],
        "detail": (
            "**What DeepScan stores:**\n\n"
            "✅ Saved (per-user):\n"
            "• Prediction result (label + confidence)\n"
            "• Filename, timestamp, inference latency\n"
            "• Feedback you submit\n\n"
            "❌ Never saved:\n"
            "• Your actual video file\n"
            "• Raw video frames\n"
            "• Any biometric data\n\n"
            "For GDPR deletion requests or compliance needs, please raise a support ticket — "
            "an admin can delete your records from the history store."
        ),
        "escalate": False,
    },

    # ── LOGIN ─────────────────────────────────────────────────────────────────
    {
        "triggers": ["how to login", "login credentials", "forgot password",
                     "wrong password", "cant login", "cannot login", "locked out",
                     "login failed", "invalid credentials", "login error",
                     "how do i sign in", "what is the password"],
        "tokens": ["login", "password", "credential", "sign", "access", "locked"],
        "reply": "Demo credentials: `user` / `user123` for standard access, `admin` / `admin123` for admin access.",
        "follow_up": "Are you locked out with those credentials, or do you need admin-level access for something specific?",
        "suggestions": ["Still can't login", "What can admins do?", "How do I change my password?"],
        "detail": (
            "**Login details:**\n\n"
            "👤 Standard user: `user` / `user123`\n"
            "🔑 Administrator: `admin` / `admin123`\n\n"
            "**Admin access unlocks:**\n"
            "• Pipeline Dashboard (Airflow, MLflow, Prometheus/Grafana)\n"
            "• Admin panel\n"
            "• Support ticket management\n\n"
            "**If credentials still don't work:**\n"
            "Someone may have changed the defaults. Please raise a support ticket and an admin will reset them."
        ),
        "escalate": True,
    },

    # ── SUPPORT TICKET ────────────────────────────────────────────────────────
    {
        "triggers": ["raise a ticket", "raise ticket", "open ticket", "submit ticket",
                     "report issue", "report a bug", "contact support", "need support",
                     "how to raise ticket", "file a ticket", "support ticket"],
        "tokens": ["ticket", "raise", "report", "submit", "bug", "issue"],
        "reply": "Go to the **Help** page → click **'Report an Issue'** → fill in a subject and description → submit.",
        "follow_up": "Would you like tips on what details to include so the admin can help you faster?",
        "suggestions": ["Yes, what details should I include?", "I already submitted, what's next?", "No thanks"],
        "detail": (
            "**Writing an effective support ticket:**\n\n"
            "Include these for the fastest resolution:\n\n"
            "1. **Subject** — short summary (e.g. 'Upload fails on MP4 files')\n"
            "2. **What happened** — exact steps you took\n"
            "3. **What you expected** — what should have happened\n"
            "4. **Error message** — copy the exact text if any\n"
            "5. **File details** — format, size, duration of the video if relevant\n"
            "6. **Browser** — Chrome/Firefox/Safari and OS\n\n"
            "The more detail you provide, the faster an admin can diagnose and resolve the issue."
        ),
        "escalate": False,
    },

    # ── FEEDBACK ──────────────────────────────────────────────────────────────
    {
        "triggers": ["how to give feedback", "submit feedback", "feedback button",
                     "was this correct", "provide feedback", "help train the model",
                     "improve the model", "where is feedback"],
        "tokens": ["feedback", "correct", "label", "improve", "train"],
        "reply": "After every analysis, the result card shows **'Was this prediction correct?'** — click Yes or No to send feedback.",
        "follow_up": "Is the feedback button not visible, or were you wondering how it affects the model?",
        "suggestions": ["How does feedback improve the model?", "The button isn't showing", "No, I found it"],
        "detail": (
            "**How feedback works:**\n\n"
            "When you click Yes or No:\n"
            "• Your response is logged as a ground-truth label\n"
            "• It's stored in the feedback JSONL log\n"
            "• During the next training run (triggered via Airflow), this data is used to retrain the model\n\n"
            "**Why it matters:**\n"
            "Edge cases — low-quality videos, unusual lighting, novel deepfake techniques — "
            "are exactly where the model needs the most help. Your labeled examples make it smarter over time.\n\n"
            "Even a single 'No, this was wrong' helps the model learn from its mistakes!"
        ),
        "escalate": False,
    },

    # ── DOWNLOAD / SHARE ──────────────────────────────────────────────────────
    {
        "triggers": ["download report", "export result", "save result", "share result",
                     "copy link", "share link", "permalink", "how to share", "how to download",
                     "get analysis report", "json report", "export json"],
        "tokens": ["download", "export", "share", "report", "link", "json"],
        "reply": "After analysis you get two options: **Download Report** (JSON file with full details) and **Copy Link** (shareable URL encoding the result).",
        "follow_up": "Are you trying to share with someone, or save the full report including the heatmap?",
        "suggestions": ["Share with someone", "Save full report with heatmap", "What's in the JSON?"],
        "detail": (
            "**Download Report** exports a JSON file containing:\n"
            "• Prediction verdict + confidence\n"
            "• Threshold used, inference latency, frames analyzed\n"
            "• MLflow run ID\n"
            "• Grad-CAM heatmap (base64 encoded)\n\n"
            "**Copy Link** generates a URL that encodes the result in the hash:\n"
            "• Anyone with the link sees the same result instantly\n"
            "• The heatmap is NOT included in the link (too large for a URL)\n"
            "• Use Download Report if you need to share the heatmap too\n\n"
            "Both buttons are at the bottom of the result card after analysis."
        ),
        "escalate": False,
    },

    # ── THRESHOLD SLIDER ──────────────────────────────────────────────────────
    {
        "triggers": ["threshold", "threshold slider", "confidence threshold",
                     "adjust threshold", "what is threshold", "slider on result",
                     "move the slider", "set threshold"],
        "tokens": ["threshold", "slider", "cutoff", "adjust"],
        "reply": "The threshold slider on the result card lets you re-evaluate the verdict at a different confidence cutoff — without re-running the analysis.",
        "follow_up": "Would you like to know when to use a higher vs. lower threshold?",
        "suggestions": ["When should I adjust it?", "What's the default?", "Does it re-analyze the video?"],
        "detail": (
            "**How the threshold slider works:**\n\n"
            "• Default cutoff: **50%** — above = DEEPFAKE, below = AUTHENTIC\n"
            "• The slider changes this cutoff on the fly (no re-analysis needed)\n\n"
            "**When to adjust:**\n"
            "• **Lower threshold (e.g. 30%)** — catch more deepfakes. Trade-off: more false positives\n"
            "• **Higher threshold (e.g. 70%)** — fewer false alarms. Trade-off: may miss subtle fakes\n\n"
            "The change is **client-side only** — it does not affect your saved history or feedback. "
            "Use it to explore sensitivity, then submit feedback with the correct label."
        ),
        "escalate": False,
    },

    # ── DARK / LIGHT MODE ─────────────────────────────────────────────────────
    {
        "triggers": ["dark mode", "light mode", "theme", "toggle theme", "switch theme",
                     "night mode", "color scheme"],
        "tokens": ["dark", "light", "mode", "theme"],
        "reply": "Click the **☀/🌙 icon** in the top-right of the nav bar to toggle between dark and light mode. Your preference is saved.",
        "follow_up": None,
        "suggestions": None,
        "detail": None,
        "escalate": False,
    },

    # ── PIPELINE / ADMIN ──────────────────────────────────────────────────────
    {
        "triggers": ["pipeline dashboard", "airflow", "mlflow", "prometheus", "grafana",
                     "admin panel", "monitoring dashboard", "dag status", "training pipeline",
                     "experiment tracking", "mlops dashboard"],
        "tokens": ["pipeline", "airflow", "mlflow", "prometheus", "grafana", "admin", "dashboard"],
        "reply": "The **Pipeline Dashboard** is for admins. Log in as `admin` and click **Pipeline** in the nav bar.",
        "follow_up": "Are you an admin trying to access it, or looking to understand what it shows?",
        "suggestions": ["I'm an admin, it's not loading", "What does it show?", "How do I restart services?"],
        "detail": (
            "**Pipeline Dashboard contains:**\n\n"
            "📡 **Pipeline Status** — live health of Airflow, MLflow, and the backend API\n"
            "🔄 **Airflow DAGs** — view and trigger data ingestion + model training pipelines\n"
            "🧪 **MLflow experiments** — compare training runs, metrics, and model versions\n"
            "📊 **Prometheus/Grafana** — live request counts, latency histograms, drift scores\n\n"
            "**If services show offline (🔴):**\n"
            "```\ndocker compose up -d\n```\n"
            "Run this in the project directory to restart all containers."
        ),
        "escalate": False,
    },

    # ── APP CRASH / NOT WORKING ───────────────────────────────────────────────
    {
        "triggers": ["app not working", "app crashed", "page not loading", "blank page",
                     "error 500", "500 error", "internal server error", "503",
                     "connection refused", "cannot connect", "not responding",
                     "site down", "backend error", "server error"],
        "tokens": ["crash", "error", "broken", "down", "500", "503", "server"],
        "reply": "Sorry to hear something's broken! Let's figure out what's happening.",
        "follow_up": "What exactly do you see — a specific error code, a blank page, or something else?",
        "suggestions": ["Error 500 / server error", "Blank or white page", "Analysis runs but gives no result"],
        "detail": (
            "**Troubleshooting steps:**\n\n"
            "**Step 1 — Hard refresh**\n"
            "Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)\n\n"
            "**Step 2 — Try a different browser**\n"
            "Chrome or Firefox recommended\n\n"
            "**Step 3 — Check the pipeline status bar**\n"
            "On the Analyze page — if services show 🔴, the backend is down\n\n"
            "**Step 4 — Backend restart (admin)**\n"
            "```\ndocker compose up -d\n```\n\n"
            "**Step 5 — Raise a ticket**\n"
            "If none of the above works, submit a support ticket with the exact error message."
        ),
        "escalate": True,
    },

    # ── THANK YOU ─────────────────────────────────────────────────────────────
    {
        "triggers": ["thank you", "thanks", "thank u", "thx", "ty", "cheers",
                     "appreciated", "great help", "very helpful", "you helped",
                     "that helped", "perfect thanks", "awesome thanks"],
        "tokens": ["thank", "thanks", "helpful"],
        "reply": "You're welcome! 😊 Feel free to ask anything else.",
        "follow_up": "Is there anything else I can help you with?",
        "suggestions": ["How do I analyze a video?", "Raise a support ticket", "No, I'm all set!"],
        "detail": None,
        "escalate": False,
    },

    # ── GOODBYE ───────────────────────────────────────────────────────────────
    {
        "triggers": ["goodbye", "bye", "see you", "see ya", "cya", "ttyl",
                     "no im good", "no im all set", "im good", "all set",
                     "no need", "no thanks", "thats all", "thats it"],
        "tokens": ["bye", "goodbye", "later", "done"],
        "reply": "Goodbye! 👋 Come back anytime. If anything breaks or a question pops up, I'm right here.",
        "follow_up": None,
        "suggestions": None,
        "detail": None,
        "escalate": False,
    },

    # ── OK / UNDERSTOOD ───────────────────────────────────────────────────────
    {
        "triggers": ["ok", "okay", "got it", "understood", "i see", "makes sense",
                     "i understand", "alright", "sounds good", "great", "perfect",
                     "awesome", "cool", "nice", "excellent"],
        "tokens": ["ok", "okay", "understand"],
        "reply": "Great! 👍 Let me know if you need anything else.",
        "follow_up": None,
        "suggestions": ["Analyze a video", "Check my history", "Raise a ticket"],
        "detail": None,
        "escalate": False,
    },
]

# ─── Escalation suffix ────────────────────────────────────────────────────────

_ESCALATE_SUFFIX = (
    "\n\n💬 If this doesn't resolve it, **raise a support ticket** on the Help page "
    "('Report an Issue') with as much detail as possible — our team will investigate."
)

# ─── Rotating fallbacks ───────────────────────────────────────────────────────

_FALLBACKS = [
    {
        "reply": "Hmm, I'm not sure I have a specific answer for that.",
        "follow_up": "Could you rephrase it, or pick one of these common topics?",
        "suggestions": ["How do I upload a video?", "My result seems wrong", "Raise a support ticket"],
        "detail": None,
    },
    {
        "reply": "That's a bit outside what I can answer directly — it might need admin attention.",
        "follow_up": "Would you like to raise a support ticket so a human expert can look into it?",
        "suggestions": ["Yes, how do I raise a ticket?", "Try a different question", "What can you help with?"],
        "detail": None,
    },
    {
        "reply": "I don't have enough information to answer that accurately right now.",
        "follow_up": "Want me to point you to the right resource?",
        "suggestions": ["Model Card page", "Pipeline Dashboard", "Raise a support ticket"],
        "detail": None,
    },
]
_fallback_idx = 0


# ─── Matching engine ──────────────────────────────────────────────────────────

def _find_entry(norm: str) -> dict | None:
    """Return best matching KB entry or None."""
    msg_tokens = _tokens(norm)

    # Tier 1: trigger phrase substring match
    for entry in _KB:
        if any(t in norm for t in entry["triggers"]):
            return entry

    # Tier 2: token overlap (≥2 shared tokens)
    best_score, best_entry = 0, None
    for entry in _KB:
        kb_text = " ".join(entry["triggers"]) + " " + " ".join(entry.get("tokens") or [])
        overlap = len(msg_tokens & _tokens(kb_text))
        if overlap > best_score:
            best_score, best_entry = overlap, entry
    if best_score >= 2:
        return best_entry

    return None


def _rule_based_reply(message: str, last_detail: str | None, last_escalate: bool) -> ChatResponse:
    """
    Conversational matching:
    1. If message is a "yes/more" to the previous follow-up → serve last_detail
    2. If message is a "no" → acknowledge and prompt for another topic
    3. Otherwise → find matching KB entry and return short reply + follow_up
    """
    global _fallback_idx
    norm = _normalise(message)

    # ── User said "yes/more" ──────────────────────────────────────────────────
    if last_detail and _is_more(norm):
        suffix = _ESCALATE_SUFFIX if last_escalate else ""
        return ChatResponse(
            reply=last_detail + suffix,
            follow_up="Does that answer your question?",
            suggestions=["Yes, thanks!", "I have another question", "Raise a support ticket"],
            detail=None,
        )

    # ── User said "no/skip" ───────────────────────────────────────────────────
    if last_detail and _is_no(norm):
        return ChatResponse(
            reply="No problem! What else can I help you with?",
            follow_up=None,
            suggestions=["How do I analyze a video?", "My result seems wrong", "Raise a support ticket"],
            detail=None,
        )

    # ── Normal intent matching ────────────────────────────────────────────────
    entry = _find_entry(norm)
    if entry:
        detail = entry.get("detail")
        if entry.get("escalate") and detail:
            detail = detail + _ESCALATE_SUFFIX
        return ChatResponse(
            reply=entry["reply"],
            follow_up=entry.get("follow_up"),
            suggestions=entry.get("suggestions"),
            detail=detail,
        )

    # ── Fallback ──────────────────────────────────────────────────────────────
    fb = _FALLBACKS[_fallback_idx % len(_FALLBACKS)]
    _fallback_idx += 1
    return ChatResponse(
        reply=fb["reply"],
        follow_up=fb["follow_up"],
        suggestions=fb["suggestions"],
        detail=None,
    )


# ─── HTTP endpoints ───────────────────────────────────────────────────────────

@support_router.post("/tickets", response_model=TicketResponse, status_code=201)
def submit_ticket(
    body: TicketCreate,
    x_username: str = Header(default="anonymous"),
):
    ticket = create_ticket(x_username, body.subject, body.description)
    logger.info("ticket_created", extra={"ticket_id": ticket["id"], "username": x_username})
    return ticket


@support_router.get("/tickets", response_model=list[TicketResponse])
def list_tickets(
    x_role: str = Header(default="user"),
    x_username: str = Header(default="anonymous"),
):
    if x_role == "admin":
        return get_tickets()
    return get_tickets(username=x_username)


@support_router.patch("/tickets/{ticket_id}/resolve", response_model=TicketResponse)
def resolve_ticket_endpoint(
    ticket_id: str,
    body: ResolveRequest,
    x_role: str = Header(default="user"),
):
    if x_role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    updated = resolve_ticket(ticket_id, body.resolution)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    logger.info("ticket_resolved", extra={"ticket_id": ticket_id})
    return updated


@support_router.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest):
    """Conversational support chat — stateless backend, conversation state on client."""
    # Client sends last_detail and last_escalate as optional context
    last_detail: str | None = getattr(body, "last_detail", None)
    last_escalate: bool = getattr(body, "last_escalate", False)
    return _rule_based_reply(body.message, last_detail, last_escalate)

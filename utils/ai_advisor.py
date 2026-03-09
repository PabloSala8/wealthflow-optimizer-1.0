import json
import difflib
from typing import Dict, List, Optional
import config

_chat_sessions = {}  # session_id -> ChatSession


def _get_gemini_client():
    if not config.AI_ENABLED or not config.GEMINI_API_KEY or config.GEMINI_API_KEY == "your_key_here":
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=config.GEMINI_API_KEY)
        return genai.GenerativeModel(config.GEMINI_MODEL)
    except Exception:
        return None


def chat_with_advisor(message: str, session_id: str, report_context: Dict) -> str:
    client = _get_gemini_client()
    if not client:
        return "AI advisor is currently unavailable. Please enable AI and add a valid API key."

    try:
        import google.generativeai as genai

        if session_id not in _chat_sessions:
            context_str = (
                f"You are a fiduciary financial advisor assistant. The user has just received a portfolio audit. "
                f"Here is their report data:\n\n"
                f"- Current broker: {report_context.get('current_broker_name', 'Unknown')}\n"
                f"- Total AUM: ${report_context.get('aum', 0):,.2f}\n"
                f"- Health score: {report_context.get('health_score', 'N/A')}/100 ({report_context.get('health_band', '')})\n"
                f"- Total cash in sweep: ${report_context.get('total_cash', 0):,.2f}\n"
                f"- Annual sweep opportunity loss vs best broker: ${report_context.get('sweep_loss', 0):,.2f}\n"
                f"- Best alternative broker: {report_context.get('best_broker_name', 'N/A')}\n"
                f"- Estimated annual savings by switching: ${report_context.get('annual_savings', 0):,.2f}\n"
                f"- Break-even months: {report_context.get('breakeven_months', 'N/A')}\n"
                f"- Flagged mutual funds: {', '.join(report_context.get('mutual_fund_flags', [])) or 'None'}\n\n"
                f"Answer the user's questions clearly and concisely. Be honest about limitations. "
                f"Never recommend specific securities. Keep answers under 150 words unless a detailed explanation is needed."
            )
            model = genai.GenerativeModel(
                config.GEMINI_MODEL,
                system_instruction=context_str,
            )
            _chat_sessions[session_id] = model.start_chat(history=[])

        chat = _chat_sessions[session_id]
        response = chat.send_message(message)
        return response.text.strip()
    except Exception as e:
        return f"Sorry, I couldn't process that. Please try again. ({str(e)})"


def map_headers_with_ai(raw_headers: List[str], sample_row: Dict) -> Dict[str, Optional[str]]:
    canonical = config.CANONICAL_FIELDS
    client = _get_gemini_client()
    if client:
        try:
            prompt = (
                f"You are a data normalization assistant. Map these raw CSV headers to canonical field names.\n\n"
                f"Canonical fields: {json.dumps(canonical)}\n\n"
                f"Raw headers: {json.dumps(raw_headers)}\n\n"
                f"Sample row: {json.dumps(sample_row)}\n\n"
                f"Return ONLY a valid JSON object where keys are raw headers and values are canonical field names "
                f"(or null if no match). Example: {{\"Mkt_Val\": \"market_value\", \"XYZ\": null}}"
            )
            response = client.generate_content(prompt)
            text = response.text.strip()
            # Strip markdown code fences if present
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            mapping = json.loads(text.strip())
            return mapping
        except Exception:
            pass
    # Fallback: fuzzy matching
    mapping = {}
    for raw in raw_headers:
        matches = difflib.get_close_matches(raw.lower().replace("_", ""),
                                             [c.replace("_", "") for c in canonical],
                                             n=1, cutoff=0.6)
        if matches:
            idx = [c.replace("_", "") for c in canonical].index(matches[0])
            mapping[raw] = canonical[idx]
        else:
            mapping[raw] = None
    return mapping


def generate_executive_summary(
    aum: float,
    health_score: int,
    health_band: str,
    sweep_loss_annual: float,
    sweep_bps: float,
    best_broker_name: str,
    annual_savings: float,
    acats_breakeven_months: float,
    current_broker_name: str,
) -> str:
    client = _get_gemini_client()
    if client:
        try:
            prompt = (
                f"You are a fiduciary financial advisor providing a plain-language audit summary. "
                f"Write exactly 3 paragraphs (~300 words total) in plain prose. No markdown, no bullet points, no headers.\n\n"
                f"Portfolio facts:\n"
                f"- Total AUM: ${aum:,.2f}\n"
                f"- Health Score: {health_score}/100 ({health_band})\n"
                f"- Current broker: {current_broker_name}\n"
                f"- Annual cash sweep opportunity loss: ${sweep_loss_annual:,.2f} ({sweep_bps:.0f} basis points)\n"
                f"- Best alternative broker: {best_broker_name}\n"
                f"- Estimated annual savings by switching: ${annual_savings:,.2f}\n"
                f"- Break-even months after ACATS transfer: {acats_breakeven_months}\n\n"
                f"Paragraph 1: Summarize current portfolio health and the main drag on returns.\n"
                f"Paragraph 2: Explain the specific fee leakage and what the best alternative offers.\n"
                f"Paragraph 3: Give a clear action recommendation with urgency framing."
            )
            response = client.generate_content(prompt)
            return response.text.strip()
        except Exception:
            pass
    # Fallback template
    breakeven_str = f"{acats_breakeven_months:.1f} months" if acats_breakeven_months != float("inf") else "N/A (no exit fee)"
    return (
        f"Your portfolio of ${aum:,.2f} has received a health score of {health_score}/100, "
        f"placing it in the '{health_band}' band. This assessment reflects the cumulative drag "
        f"of broker fees and suboptimal cash sweep rates currently eroding your returns at {current_broker_name}. "
        f"While your equity positions are well-diversified, the uninvested cash sitting in the sweep account "
        f"is a primary source of preventable yield loss.\n\n"
        f"The analysis identified an annual cash sweep opportunity loss of ${sweep_loss_annual:,.2f} "
        f"({sweep_bps:.0f} basis points), meaning your idle cash is earning far below what top-tier "
        f"brokers currently offer. {best_broker_name} stands out as the optimal alternative, offering "
        f"terms that could generate an estimated ${annual_savings:,.2f} in additional annual value — "
        f"without requiring any changes to your investment strategy or holdings.\n\n"
        f"Switching brokers via ACATS transfer is straightforward and typically completes within 5-7 "
        f"business days. Given the potential savings, the break-even point on any transfer costs is "
        f"approximately {breakeven_str}. Every month of inaction represents continued fee leakage. "
        f"We recommend initiating the transfer process promptly to begin capturing these recoverable gains."
    )

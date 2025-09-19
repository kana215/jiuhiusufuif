
import os
import re
import json
import datetime as dt
from typing import List, Dict, Optional
import requests

def _parse_relative_date(phrase: str, base: dt.date) -> Optional[str]:
    """
    Very simple parser for phrases like "this Friday", "next Monday".
    Returns ISO yyyy-mm-dd or None.
    """
    phrase = phrase.lower().strip()
    weekdays = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
    today_wd = base.weekday()
    # handle "this X" and "next X"
    for idx, wd in enumerate(weekdays):
        if f"this {wd}" in phrase:
            delta = (idx - today_wd) % 7
            target = base + dt.timedelta(days=delta if delta != 0 else 0)
            return target.isoformat()
        if f"next {wd}" in phrase:
            delta = ((idx - today_wd) % 7) + 7
            target = base + dt.timedelta(days=delta)
            return target.isoformat()
    return None

def extract_tasks_from_text(text: str) -> List[Dict]:
    """
    Naive rule-based extraction: lines beginning with verbs or bullets become tasks.
    You can replace with an LLM call if desired.
    """
    lines = [l.strip() for l in re.split(r'[\n\r]+', text) if l.strip()]
    tasks = []
    base_date = dt.date.today()
    for line in lines:
        # bullet or imperative-looking sentence
        if re.match(r"^(-|\*|\d+\.)\s+", line) or re.match(r"^(do|fix|create|update|prepare|write|сделать|исправить|создать|подготовить|написать)\b", line, re.I):
            # detect due
            due = _parse_relative_date(line, base_date)
            tasks.append({
                "summary": re.sub(r"^(-|\*|\d+\.)\s+", "", line)[:120],
                "description": line,
                "due_date": due
            })
    # fallback: if nothing matched, create a single task from the whole text (too naive, but safe)
    if not tasks and text:
        tasks.append({"summary": text[:120], "description": text})
    return tasks

def guess_assignee(text: str) -> Optional[str]:
    # naive name guesser; adapt to your team
    m = re.search(r"\b(Aisulu|Samat|Айсулу|Самат)\b", text, re.I)
    return m.group(0) if m else None

class JiraClient:
    def __init__(self, base_url: str, email: str, api_token: str, project_key: str):
        assert base_url and email and api_token and project_key, "Missing Jira credentials"
        self.base_url = base_url.rstrip("/")
        self.auth = (email, api_token)
        self.project_key = project_key

    def create_issue(self, summary: str, description: str = "", duedate: Optional[str] = None) -> dict:
        url = f"{self.base_url}/rest/api/3/issue"
        payload = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": "Task"}
            }
        }
        if duedate:
            payload["fields"]["duedate"] = duedate
        r = requests.post(url, auth=self.auth, json=payload, headers={"Accept":"application/json","Content-Type":"application/json"})
        if r.status_code >= 300:
            raise RuntimeError(f"Jira create_issue failed: {r.status_code} {r.text}")
        return r.json()

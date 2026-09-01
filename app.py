"""
Ace of Sales — Infrastructure Sales Assistant · Streamlit UI
IBM Storage Sales Project Centre
"""

from __future__ import annotations
import copy
import io
import json
import re
import sys
import random
from datetime import date, datetime, timedelta
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as _components

sys.path.insert(0, str(Path(__file__).parent))

from app.parsers.econfig_parser import parse_project, parse_project_csv_only
from app.parsers.scale_parser import parse_scale_project
from app.parsers.bid_parser import parse_bid_docx
from app.generators.exec_summary import generate_exec_summary
from app.generators.rfp_generator import generate_rfp
from app.generators.special_bid_generator import generate_special_bid
from app.generators.scale_exec_summary import generate_scale_exec_summary
from app.generators.scale_rfp_generator import generate_scale_rfp
from app.generators.scale_special_bid_generator import generate_scale_special_bid
from app.generators.bid_justification import generate_bj, ollama_status
from app.parsers.san_parser import parse_san_csv, has_san_switches
from app.knowledge.product_db import get_model_info, get_docs, get_san_switch_info
from app.generators.san_rfp_generator import generate_san_rfp

# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Ace of Sales", page_icon="♠",
                   layout="wide", initial_sidebar_state="collapsed")

# ─────────────────────────────────────────────────────────────────────────────
# CSS  — IBM.com light palette  (ibm.com/products/flashsystem)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:ital,wght@0,300;0,400;0,600;1,300&family=IBM+Plex+Mono:wght@400;600&display=swap');

:root {
  --white:       #ffffff;
  --gray-10:     #f4f4f4;
  --gray-20:     #e8e8e8;
  --gray-30:     #c6c6c6;
  --gray-50:     #8d8d8d;
  --gray-70:     #525252;
  --gray-100:    #161616;
  --blue-60:     #0f62fe;
  --blue-70:     #0353e9;
  --blue-80:     #002d9c;
  --blue-text:   #4589ff;
  --green-50:    #24a148;
  --yellow-30:   #f1c21b;
  --red-60:      #da1e28;
  --teal-60:     #0072c3;
}

/* ── Reset & font ──────────────────────────────────────────────────────── */
html, body, [class*="css"] {
  font-family: 'IBM Plex Sans', 'Helvetica Neue', Arial, sans-serif !important;
  -webkit-font-smoothing: antialiased;
}

/* ── App shell — pure white ────────────────────────────────────────────── */
.stApp                       { background: var(--white) !important; }
.main .block-container       { background: var(--white) !important;
                               padding-top: 0 !important;
                               padding-left: 0 !important;
                               padding-right: 0 !important;
                               max-width: 100% !important; }

/* ── Hide default Streamlit chrome — including top gap ─────────────────── */
#MainMenu, footer, header    { visibility: hidden; height: 0 !important; }
[data-testid="stSidebar"]    { display: none; }
[data-testid="stHeader"]     { display: none !important; height: 0 !important; }
[data-testid="stToolbar"]    { display: none !important; height: 0 !important; }
[data-testid="stDecoration"] { display: none !important; height: 0 !important; }
[data-testid="stStatusWidget"] { display: none !important; }

/* Zero out every top padding that Streamlit injects */
.stApp > header                          { height: 0 !important; min-height: 0 !important; }
.stAppViewBlockContainer                 { padding-top: 0 !important; margin-top: 0 !important; }
.stMainBlockContainer                    { padding-top: 0 !important; }
.main .block-container                   { padding-top: 0 !important; margin-top: 0 !important; }
div[data-testid="stAppViewContainer"]    { padding-top: 0 !important; margin-top: 0 !important; }
div[data-testid="stAppViewContainer"] > section               { padding-top: 0 !important; }
div[data-testid="stAppViewContainer"] > section:first-child   { padding-top: 0 !important; }
/* Streamlit 1.35+ wrapper */
div[class*="appview-container"]          { padding-top: 0 !important; }
div[class*="block-container"]            { padding-top: 0 !important; }

/* ── Typography ─────────────────────────────────────────────────────────── */
h1 { font-size: 42px !important; font-weight: 300 !important;
     color: var(--gray-100) !important; line-height: 1.2 !important;
     letter-spacing: -0.01em !important; margin: 0 0 8px !important; }
h2 { font-size: 11px !important; font-weight: 600 !important;
     color: var(--gray-70) !important; text-transform: uppercase !important;
     letter-spacing: 0.12em !important; border: none !important;
     margin: 0 0 16px !important; padding: 0 !important; }
h3 { font-size: 20px !important; font-weight: 400 !important;
     color: var(--gray-100) !important; margin: 0 0 8px !important; }
p, li { color: var(--gray-100) !important; font-size: 16px !important; line-height: 1.6 !important; }

/* ── Top nav bar ────────────────────────────────────────────────────────── */
.ibm-nav {
  background: var(--gray-100);
  padding: 0 40px;
  height: 56px;
  width: 100%;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: fixed; top: 0; left: 0; right: 0; z-index: 9999;
  margin-top: 0 !important;
}
/* Push content below fixed nav */
.ibm-nav-spacer { height: 56px; }
/* Left side: brand + page links grouped together */
.ibm-nav-left {
  display: flex; align-items: center; gap: 0;
}
.ibm-nav-brand {
  font-size: 15px; font-weight: 600; color: #ffffff;
  letter-spacing: 0.01em; font-family: 'IBM Plex Sans', sans-serif;
  white-space: nowrap; padding-right: 8px;
}
/* "Bolt" suffix — white, same weight as IBM */
.ibm-nav-brand span { color: #ffffff; margin-left: 6px; font-weight: 600; }
/* separator between brand and page links */
.ibm-nav-sep {
  width: 1px; height: 20px; background: #525252;
  margin: 0 8px; flex-shrink: 0;
}
.ibm-nav-links { display: flex; gap: 0; align-items: center; }
.ibm-nav-link {
  font-size: 14px; color: #c6c6c6; padding: 0 16px; height: 56px;
  display: flex; align-items: center; cursor: pointer;
  font-family: 'IBM Plex Sans', sans-serif; text-decoration: none;
  white-space: nowrap;
}
.ibm-nav-link:hover { background: #393939; color: #ffffff; }
.ibm-nav-link.active { color: #ffffff; border-bottom: 2px solid var(--blue-60); }
.ibm-nav-link-muted { color: #6f6f6f !important; font-style: italic; cursor: default; }
.ibm-nav-link-muted:hover { background: transparent !important; color: #6f6f6f !important; }
.ibm-nav-doc-group {
  display: flex; align-items: center; gap: 0;
  border-left: 1px solid #393939; margin-left: 8px; padding-left: 8px;
}
.ibm-nav-doc-label {
  font-size: 11px; color: #8d8d8d; padding: 0 10px 0 4px;
  font-family: 'IBM Plex Sans', sans-serif; white-space: nowrap;
  letter-spacing: 0.02em;
}

/* ── Nav responsive — small MacBook (≤ 1280px) ──────────────────────────── */
@media (max-width: 1280px) {
  .ibm-nav { padding: 0 16px; }
  .ibm-nav-link { font-size: 13px; padding: 0 12px; }
  .ibm-nav-doc-label { display: none; }
  .ibm-nav-doc-group { margin-left: 4px; padding-left: 4px; }
}
@media (max-width: 1024px) {
  .ibm-nav { padding: 0 12px; height: auto; min-height: 56px; flex-wrap: wrap; }
  .ibm-nav-left { flex-wrap: wrap; }
  .ibm-nav-links { flex-wrap: wrap; }
  .ibm-nav-link { font-size: 12px; padding: 0 10px; height: 44px; }
  .ibm-nav-brand { font-size: 13px; }
  .ibm-nav-doc-group { display: none; }
}

/* ── Hero band ──────────────────────────────────────────────────────────── */
.ibm-hero {
  background: var(--gray-10);
  padding: 48px 40px 40px;
  border-bottom: 1px solid var(--gray-20);
}
.ibm-hero-eyebrow {
  font-size: 12px; font-weight: 600; color: var(--blue-text);
  text-transform: uppercase; letter-spacing: 0.1em;
  margin: 0 0 12px; font-family: 'IBM Plex Sans', sans-serif;
}
.ibm-hero h1 { font-size: 36px !important; font-weight: 300 !important;
               color: var(--gray-100) !important; margin: 0 0 12px !important; }
.ibm-hero-sub { font-size: 16px; color: var(--gray-70);
                max-width: 640px; line-height: 1.6;
                font-family: 'IBM Plex Sans', sans-serif; }
.ibm-hero-steps {
  display: flex; align-items: stretch; justify-content: center;
  gap: 0; margin-top: 28px; flex-wrap: wrap;
}
.ibm-hero-step {
  display: flex; align-items: center; gap: 16px;
  background: var(--white); border: 1px solid var(--gray-20);
  border-radius: 4px; padding: 18px 24px;
  flex: 1; min-width: 210px; max-width: 300px;
}
.ibm-hero-step-num {
  width: 36px; height: 36px; border-radius: 50%;
  background: var(--blue-60); color: #fff;
  font-size: 16px; font-weight: 600;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.ibm-hero-step-title { font-size: 14px; font-weight: 600; color: var(--gray-100); margin-bottom: 3px; }
.ibm-hero-step-sub   { font-size: 11.5px; color: var(--gray-70); line-height: 1.45; }
.ibm-hero-step-arrow {
  font-size: 22px; color: var(--gray-30);
  padding: 0 12px; flex-shrink: 0; align-self: center;
}

/* ── Step indicator ─────────────────────────────────────────────────────── */
.ibm-steps {
  display: flex; align-items: center; gap: 0;
  padding: 20px 40px; background: var(--white);
  border-bottom: 1px solid var(--gray-20);
}
.ibm-step {
  display: flex; align-items: center; gap: 10px;
  font-size: 13px; color: var(--gray-50);
  font-family: 'IBM Plex Sans', sans-serif;
  padding: 8px 16px 8px 0;
}
.ibm-step.active  { color: var(--gray-100); }
.ibm-step.done    { color: var(--green-50); }
.ibm-step-num {
  width: 24px; height: 24px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 600; flex-shrink: 0;
  background: var(--gray-20); color: var(--gray-70);
}
.ibm-step.active .ibm-step-num { background: var(--blue-60); color: #fff; }
.ibm-step.done   .ibm-step-num { background: var(--green-50); color: #fff; }
.ibm-step-sep { color: var(--gray-30); margin: 0 4px; font-size: 18px; }

/* ── Page content wrapper ───────────────────────────────────────────────── */
.ibm-content { padding: 0 40px 60px; max-width: 1200px; }

/* ── Section label ───────────────────────────────────────────────────────── */
.ibm-section-label {
  font-size: 11px; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.1em; color: var(--gray-50);
  border-bottom: 2px solid var(--blue-60);
  padding-bottom: 8px; margin: 32px 0 20px;
  font-family: 'IBM Plex Sans', sans-serif;
}

/* ── White card / tile ──────────────────────────────────────────────────── */
.ibm-card {
  background: var(--white); border: 1px solid var(--gray-20);
  padding: 24px; margin-bottom: 1px;
}
.ibm-card-title {
  font-size: 14px; font-weight: 600; color: var(--gray-100);
  margin-bottom: 4px; font-family: 'IBM Plex Sans', sans-serif;
}
.ibm-card-body {
  font-size: 13px; color: var(--gray-70); line-height: 1.55;
  font-family: 'IBM Plex Sans', sans-serif;
}

/* ── Feature tile (welcome) ─────────────────────────────────────────────── */
.ibm-feature {
  background: var(--white); border: 1px solid var(--gray-20);
  border-top: 3px solid var(--blue-60);
  padding: 24px 24px 28px;
  display: flex;
  flex-direction: column;
  min-height: 220px;
  box-sizing: border-box;
}
.ibm-feature-icon  { font-size: 28px; margin-bottom: 14px; display: block; }
.ibm-feature-title { font-size: 18px; font-weight: 400; color: var(--gray-100); margin-bottom: 10px; font-family: 'IBM Plex Sans', sans-serif; }
.ibm-feature-body  { font-size: 14px; color: var(--gray-70); line-height: 1.6; font-family: 'IBM Plex Sans', sans-serif; flex: 1; }

/* ── Tags ────────────────────────────────────────────────────────────────── */
.ibm-tag {
  display: inline-block; padding: 3px 10px; font-size: 11px;
  font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em;
  margin-top: 16px; font-family: 'IBM Plex Sans', sans-serif;
}
.ibm-tag-blue { background: var(--blue-60); color: #fff; }
.ibm-tag-gray { background: var(--gray-20); color: var(--gray-70); }

/* ── Notifications ──────────────────────────────────────────────────────── */
.ibm-notif {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 12px 16px; font-size: 13px; line-height: 1.5;
  color: var(--gray-100); margin: 8px 0;
  font-family: 'IBM Plex Sans', sans-serif;
}
.ibm-notif-info    { background: #edf5ff; border-left: 3px solid var(--blue-60); }
.ibm-notif-ok      { background: #defbe6; border-left: 3px solid var(--green-50); }
.ibm-notif-warn    { background: #fdf6dd; border-left: 3px solid var(--yellow-30); }
.ibm-notif b       { font-weight: 600; }

/* ── Metric tiles (custom HTML .ibm-metric) ─────────────────────────────── */
.ibm-metric-row {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 6px;
  margin-bottom: 4px;
}
.ibm-metric {
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-top: 3px solid #0f62fe;
  padding: 10px 10px 12px;
  min-height: 72px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
}
.ibm-metric-label {
  font-size: 9px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #525252;
  line-height: 1.3;
  margin-bottom: 7px;
  font-family: 'IBM Plex Sans', sans-serif;
}
.ibm-metric-value {
  font-size: 14px;
  font-weight: 500;
  color: #161616;
  font-family: 'IBM Plex Mono', monospace;
  line-height: 1.3;
  word-break: break-word;
  overflow-wrap: break-word;
}
.ibm-metric-delta {
  font-size: 10px;
  color: #525252;
  margin-top: 5px;
  font-family: 'IBM Plex Sans', sans-serif;
}

/* ── Buttons ─────────────────────────────────────────────────────────────── */
/* Primary — solid blue */
button[data-testid="baseButton-primary"],
.stButton > button[kind="primary"],
[data-testid="stBaseButton-primary"] {
  background: linear-gradient(135deg, #0f62fe 0%, #0043ce 100%) !important;
  color: #ffffff !important;
  border: none !important;
  border-radius: 4px !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  letter-spacing: 0.02em !important;
  padding: 12px 28px !important;
  height: auto !important;
  box-shadow: 0 1px 3px rgba(15,98,254,0.3) !important;
  transition: box-shadow 120ms ease, background 120ms ease !important;
}
/* Force white text on every child element inside primary button */
button[data-testid="baseButton-primary"] *,
.stButton > button[kind="primary"] *,
[data-testid="stBaseButton-primary"] *,
button[data-testid="baseButton-primary"] p,
button[data-testid="baseButton-primary"] div,
button[data-testid="baseButton-primary"] span {
  color: #ffffff !important;
}
button[data-testid="baseButton-primary"]:hover,
.stButton > button[kind="primary"]:hover {
  background: linear-gradient(135deg, #0353e9 0%, #002d9c 100%) !important;
  color: #ffffff !important;
  box-shadow: 0 4px 12px rgba(15,98,254,0.4) !important;
}
button[data-testid="baseButton-primary"]:hover *,
.stButton > button[kind="primary"]:hover * { color: #ffffff !important; }
button[data-testid="baseButton-primary"]:active,
.stButton > button[kind="primary"]:active {
  background: #002d9c !important;
  color: #ffffff !important;
  box-shadow: none !important;
}
button[data-testid="baseButton-primary"]:active * { color: #ffffff !important; }

/* Secondary — ghost outline */
button[data-testid="baseButton-secondary"],
button[data-testid="stBaseButton-secondary"],
.stButton > button:not([kind="primary"]) {
  background: transparent !important;
  color: var(--blue-text) !important;
  border: 1.5px solid var(--blue-60) !important;
  border-radius: 4px !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  padding: 10px 28px !important;
  transition: background 100ms ease !important;
}
button[data-testid="baseButton-secondary"] *,
button[data-testid="stBaseButton-secondary"] *,
button[data-testid="baseButton-secondary"] p,
button[data-testid="stBaseButton-secondary"] p,
.stButton > button:not([kind="primary"]) *,
.stButton > button:not([kind="primary"]) p {
  color: var(--blue-text) !important;
}
.stButton > button:not([kind="primary"]):hover,
button[data-testid="stBaseButton-secondary"]:hover {
  background: #edf5ff !important;
  color: var(--blue-text) !important;
}
/* Disabled buttons — always legible */
button[disabled],
button:disabled,
.stButton > button[disabled],
.stButton > button:disabled {
  background: var(--gray-20) !important;
  color: var(--gray-70) !important;
  border-color: var(--gray-30) !important;
  opacity: 0.7 !important;
}
button[disabled] *,
button:disabled *,
.stButton > button[disabled] *,
.stButton > button:disabled * {
  color: var(--gray-70) !important;
}
/* Download button — same as primary */
.stDownloadButton > button,
div[data-testid="stDownloadButton"] > button {
  background: linear-gradient(135deg, #0f62fe 0%, #0043ce 100%) !important;
  color: #ffffff !important;
  border: none !important;
  border-radius: 4px !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  padding: 12px 28px !important;
  width: 100% !important;
  box-shadow: 0 1px 3px rgba(15,98,254,0.3) !important;
}
.stDownloadButton > button *,
div[data-testid="stDownloadButton"] > button * { color: #ffffff !important; }
.stDownloadButton > button:hover {
  background: linear-gradient(135deg, #0353e9 0%, #002d9c 100%) !important;
  color: #ffffff !important;
  box-shadow: 0 4px 12px rgba(15,98,254,0.4) !important;
}

/* ── Multiselect — tags ──────────────────────────────────────────────────── */
[data-baseweb="tag"] {
  background: #0f62fe !important;
  border-radius: 2px !important;
}
[data-baseweb="tag"] *,
[data-baseweb="tag"] span {
  color: #ffffff !important;
}

/* ── Multiselect / Selectbox — dropdown popover (rendered as body portal) ── */
/* Streamlit mounts the dropdown outside .stApp — needs body-level selectors  */
body [data-baseweb="popover"],
body [data-baseweb="menu"],
body ul[role="listbox"] {
  background: #ffffff !important;
  border: 1px solid #e8e8e8 !important;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12) !important;
}
body [role="option"] {
  background: #ffffff !important;
  color: #161616 !important;
}
body [role="option"]:hover,
body [role="option"][aria-selected="true"] {
  background: #edf5ff !important;
  color: #161616 !important;
}
/* All text nodes inside the portal */
body [data-baseweb="popover"] *,
body [data-baseweb="menu"] *,
body ul[role="listbox"] * {
  color: #161616 !important;
  background-color: transparent !important;
}
/* Restore hover highlight */
body [role="option"]:hover *,
body [role="option"][aria-selected="true"] * {
  color: #161616 !important;
  background-color: transparent !important;
}
/* Divider line inside dropdown */
body [data-baseweb="popover"] hr,
body [data-baseweb="menu"] hr {
  border-color: #e8e8e8 !important;
}

/* ── Datepicker calendar popup (body portal) ────────────────────────────── */
/* Nuclear reset — Baseweb sets black bg on out-of-month rows/cells         */
body [data-baseweb="calendar"],
body [data-baseweb="datepicker"],
body [data-baseweb="calendar"] *,
body [data-baseweb="datepicker"] * {
  background: #ffffff !important;
  background-color: #ffffff !important;
  color: #161616 !important;
  box-sizing: border-box !important;
}
/* Calendar outer wrapper */
body [data-baseweb="calendar"] {
  box-shadow: 0 4px 16px rgba(0,0,0,0.14) !important;
  border: 1px solid #e8e8e8 !important;
  border-radius: 4px !important;
  padding: 8px !important;
}
/* Header month/year selects */
body [data-baseweb="calendar"] [data-baseweb="select"],
body [data-baseweb="calendar"] [data-baseweb="select"] * {
  background: #ffffff !important;
  color: #161616 !important;
}
/* All grid rows and cells — white */
body [data-baseweb="calendar"] [role="grid"],
body [data-baseweb="calendar"] [role="row"],
body [data-baseweb="calendar"] [role="gridcell"],
body [data-baseweb="calendar"] [role="columnheader"] {
  background: #ffffff !important;
  background-color: #ffffff !important;
  color: #161616 !important;
}
/* Individual day buttons */
body [data-baseweb="calendar"] button {
  background: transparent !important;
  background-color: transparent !important;
  color: #161616 !important;
  border-radius: 50% !important;
}
/* Hover */
body [data-baseweb="calendar"] [role="gridcell"] button:hover {
  background: #edf5ff !important;
  color: #0f62fe !important;
}
/* Selected day */
body [data-baseweb="calendar"] [aria-selected="true"] button {
  background: #0f62fe !important;
  background-color: #0f62fe !important;
  color: #ffffff !important;
}
/* Today */
body [data-baseweb="calendar"] [data-today="true"] button {
  border: 2px solid #0f62fe !important;
  color: #0f62fe !important;
  background: transparent !important;
}
/* Disabled / out-of-month days */
body [data-baseweb="calendar"] [aria-disabled="true"],
body [data-baseweb="calendar"] [aria-disabled="true"] *,
body [data-baseweb="calendar"] button[disabled],
body [data-baseweb="calendar"] button:disabled {
  background: #ffffff !important;
  background-color: #ffffff !important;
  color: #c6c6c6 !important;
}
/* Navigation arrows */
body [data-baseweb="calendar"] [data-baseweb="button"],
body [data-baseweb="calendar"] [data-baseweb="button"] * {
  background: transparent !important;
  color: #161616 !important;
}

/* ── Nav page-switch buttons — hidden trigger row ───────────────────────── */
/* Collapsed to zero height — navigation is handled by HTML nav links above. */
[data-testid="stHorizontalBlock"]:has([aria-label="🏢  Sales Centre"]) {
  height: 0 !important;
  min-height: 0 !important;
  overflow: hidden !important;
  margin: 0 !important;
  padding: 0 !important;
  visibility: hidden !important;
}
/* ── Custom tab bar ──────────────────────────────────────────────────────── */
/* Streamlit sets aria-label on buttons = button label text.                 */
/* Target the stHorizontalBlock containing our tab buttons via :has()        */
/* :has() works in all modern browsers (Chrome 105+, Firefox 121+, Safari 15.4+) */
/* Tab bar anchor — triggered by any of the 6 tab buttons */
[data-testid="stHorizontalBlock"]:has([aria-label="📋  Executive Summary"]) {
  background: #f4f4f4 !important;
  border-top: 1px solid #e8e8e8 !important;
  border-bottom: 1px solid #e8e8e8 !important;
  padding: 8px 12px !important;
  margin: 0 -40px !important;
  gap: 6px !important;
  align-items: stretch !important;
}
[data-testid="stHorizontalBlock"]:has([aria-label="📋  Executive Summary"]) > [data-testid="stColumn"] {
  padding: 0 3px !important;
  min-width: 0 !important;
}

/* ── Inactive tab buttons ─────────────────────────────────────────────────── */
[data-testid="stHorizontalBlock"]:has([aria-label="📋  Executive Summary"]) [data-testid="stBaseButton-secondary"] {
  background: transparent !important;
  border: 1px solid transparent !important;
  border-radius: 4px !important;
  color: #525252 !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  height: 42px !important;
  width: 100% !important;
  box-shadow: none !important;
  padding: 10px 8px !important;
}
[data-testid="stHorizontalBlock"]:has([aria-label="📋  Executive Summary"]) [data-testid="stBaseButton-secondary"] * {
  color: #525252 !important;
}
[data-testid="stHorizontalBlock"]:has([aria-label="📋  Executive Summary"]) [data-testid="stBaseButton-secondary"]:hover {
  background: #e0e0e0 !important;
  color: #161616 !important;
}
[data-testid="stHorizontalBlock"]:has([aria-label="📋  Executive Summary"]) [data-testid="stBaseButton-secondary"]:hover * { color: #161616 !important; }

/* ── Active tab button (primary) ─────────────────────────────────────────── */
[data-testid="stHorizontalBlock"]:has([aria-label="📋  Executive Summary"]) [data-testid="stBaseButton-primary"] {
  background: #ffffff !important;
  border: 1px solid #e8e8e8 !important;
  border-left: 3px solid #0f62fe !important;
  border-radius: 4px !important;
  color: #161616 !important;
  font-size: 13px !important;
  font-weight: 600 !important;
  height: 42px !important;
  width: 100% !important;
  box-shadow: 0 1px 4px rgba(0,0,0,.10) !important;
  padding: 10px 9px !important;
}
[data-testid="stHorizontalBlock"]:has([aria-label="📋  Executive Summary"]) [data-testid="stBaseButton-primary"] * { color: #161616 !important; }

/* ── DataFrames & tables ────────────────────────────────────────────────── */
[data-testid="stDataFrame"] { border: 1px solid var(--gray-20) !important; border-radius: 0 !important; }
[data-testid="stDataFrame"] th {
  background: var(--gray-10) !important; color: var(--gray-100) !important;
  font-size: 11px !important; font-weight: 600 !important;
  text-transform: uppercase !important; letter-spacing: 0.08em !important;
  border-bottom: 1px solid var(--gray-30) !important; padding: 10px 12px !important;
}
[data-testid="stDataFrame"] td {
  font-size: 13px !important; color: var(--gray-100) !important;
  border-bottom: 1px solid var(--gray-20) !important;
  padding: 8px 12px !important; background: var(--white) !important;
}
table { font-size: 13px !important; border-collapse: collapse !important; width: 100% !important; }
thead tr th {
  background: var(--gray-10) !important; color: var(--gray-100) !important;
  font-size: 11px !important; font-weight: 600 !important;
  text-transform: uppercase !important; letter-spacing: 0.08em !important;
  padding: 10px 12px !important; border-bottom: 1px solid var(--gray-30) !important;
  text-align: left !important;
}
tbody tr td {
  padding: 10px 12px !important; border-bottom: 1px solid var(--gray-20) !important;
  color: var(--gray-100) !important; background: var(--white) !important;
}
tbody tr:nth-child(even) td { background: var(--gray-10) !important; }
tbody tr:hover td { background: #edf5ff !important; }

/* ── Inputs ──────────────────────────────────────────────────────────────── */
.stTextInput input, .stNumberInput input, .stTextArea textarea {
  border: 1px solid var(--gray-30) !important;
  border-bottom: 2px solid var(--gray-50) !important;
  border-radius: 3px !important;
  background: var(--gray-10) !important;
  color: var(--gray-100) !important;
  font-size: 14px !important;
  padding: 10px 12px !important;
  box-shadow: none !important;
  transition: border-color 120ms ease, background 120ms ease !important;
}
.stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
  border: 1px solid var(--blue-60) !important;
  border-bottom: 2px solid var(--blue-60) !important;
  background: #ffffff !important;
  outline: none !important;
  box-shadow: 0 0 0 2px rgba(15,98,254,.15) !important;
}
.stTextInput input:hover, .stNumberInput input:hover, .stTextArea textarea:hover {
  border-color: var(--gray-70) !important;
  background: #ffffff !important;
}
/* Date input */
[data-testid="stDateInput"] input {
  border: 1px solid var(--gray-30) !important;
  border-bottom: 2px solid var(--gray-50) !important;
  border-radius: 3px !important;
  background: var(--gray-10) !important;
  color: var(--gray-100) !important;
  font-size: 14px !important;
  padding: 10px 12px !important;
  box-shadow: none !important;
}
[data-testid="stDateInput"] input:focus {
  border: 1px solid var(--blue-60) !important;
  border-bottom: 2px solid var(--blue-60) !important;
  background: #ffffff !important;
  outline: none !important;
}
/* Selectbox — nuke dark background at every nesting level */
[data-baseweb="select"] div,
[data-baseweb="select"] > div:first-child {
  background: var(--gray-10) !important;
  border-radius: 3px !important;
}
[data-baseweb="select"] > div:first-child:hover,
[data-baseweb="select"] > div:first-child:hover div {
  background: #ffffff !important;
}
/* value + placeholder text — keep readable */
[data-baseweb="select"] span,
[data-baseweb="select"] [data-baseweb="select-value-container"],
[data-baseweb="select"] [data-baseweb="select-value-container"] * {
  color: var(--gray-100) !important;
  background: transparent !important;
}
/* dropdown arrow icon */
[data-baseweb="select"] svg {
  fill: var(--gray-70) !important;
}
/* keep dropdown LIST (portal) white — it's outside the select container */
body [data-baseweb="popover"] [data-baseweb="menu"] div,
body [data-baseweb="popover"] [data-baseweb="menu"] ul {
  background: #ffffff !important;
}
/* do NOT touch calendar internals */
body [data-baseweb="calendar"] [data-baseweb="select"] div,
body [data-baseweb="datepicker"] [data-baseweb="select"] div {
  background: #ffffff !important;
}
/* labels */
.stTextInput label, .stNumberInput label, .stTextArea label, .stSlider label,
.stSelectbox label, .stFileUploader label,
[data-testid="stDateInput"] label {
  color: var(--gray-70) !important; font-size: 12px !important;
  font-weight: 600 !important; text-transform: uppercase !important;
  letter-spacing: 0.06em !important;
}

/* ── File uploader ───────────────────────────────────────────────────────── */
[data-testid="stFileUploader"] {
  background: var(--gray-10) !important;
  border: 1px dashed var(--gray-50) !important;
  border-radius: 0 !important;
  padding: 16px 16px 12px 16px !important;
  margin-bottom: 8px !important;
  min-height: 180px !important;
  display: flex !important;
  flex-direction: column !important;
}
[data-testid="stFileUploader"]:hover { border-color: var(--blue-60) !important; }
[data-testid="stFileUploaderDropzone"] {
  flex: 1 !important;
  min-height: 110px !important;
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  justify-content: center !important;
  padding: 12px 12px !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] p,
[data-testid="stFileUploaderDropzoneInstructions"] p *,
[data-testid="stFileUploaderDropzone"] p,
[data-testid="stFileUploaderDropzone"] p *,
[data-testid="stFileUploaderDropzone"] span,
[data-testid="stFileUploaderDropzone"] small,
[data-testid="stFileUploaderDropzone"] div {
  color: #6f6f6f !important;
  font-size: 13px !important;
}
[data-testid="stFileUploader"] * {
  color: #6f6f6f !important;
}
[data-testid="stFileUploader"] button,
[data-testid="stFileUploader"] button * {
  color: #4589ff !important;
}
/* upload step badge */
.upload-step-badge {
  display: block !important;
  width: 100% !important;
  box-sizing: border-box !important;
  font-size: 13px !important;
  font-weight: 700 !important;
  letter-spacing: 0.04em !important;
  text-transform: uppercase !important;
  padding: 7px 14px !important;
  border-radius: 2px !important;
  margin-bottom: 0 !important;
  text-align: left !important;
  transition: background .2s, color .2s, border-color .2s;
}
.upload-step-badge.required {
  background: #dde9ff !important;
  color: #4589ff !important;
  border: 1.5px solid #4589ff88 !important;
}
.upload-step-badge.optional {
  background: #e8e8e8 !important;
  color: #525252 !important;
  border: 1.5px solid #c6c6c6 !important;
}
/* Uploaded state — green background */
.upload-step-badge.uploaded {
  background: #defbe6 !important;
  color: #198038 !important;
  border: 1.5px solid #24a148 !important;
}
.upload-step-num {
  font-size: 11px !important;
  font-weight: 600 !important;
  color: #8d8d8d !important;
  text-transform: uppercase !important;
  letter-spacing: 0.08em !important;
  margin-bottom: 3px !important;
}
.upload-step-num.uploaded {
  color: #198038 !important;
}

/* ── Slider ──────────────────────────────────────────────────────────────── */
[data-baseweb="slider"] [role="slider"] { background: var(--blue-60) !important; }

/* ── Divider ─────────────────────────────────────────────────────────────── */
hr { border: none !important; border-top: 1px solid var(--gray-20) !important; margin: 24px 0 !important; }

/* ── Alerts ──────────────────────────────────────────────────────────────── */
[data-testid="stAlert"] { border-radius: 0 !important; border-left-width: 3px !important; font-size: 13px !important; }

/* ── Expander ────────────────────────────────────────────────────────────── */
[data-testid="stExpander"] summary {
  background: var(--gray-10) !important; border: 1px solid var(--gray-20) !important;
  border-radius: 0 !important; color: var(--gray-100) !important;
  font-size: 13px !important; font-weight: 600 !important; padding: 10px 14px !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def notif(kind: str, text: str) -> str:
    icon = {"info": "ℹ️", "ok": "✅", "warn": "⚠️"}[kind]
    cls  = {"info": "ibm-notif-info", "ok": "ibm-notif-ok", "warn": "ibm-notif-warn"}[kind]
    return f'<div class="ibm-notif {cls}">{icon}&nbsp; {text}</div>'

def section(label: str) -> None:
    st.markdown(f'<div class="ibm-section-label">{label}</div>', unsafe_allow_html=True)

def pad(content_fn):
    """Wrap content in 40px horizontal padding."""
    _, col, _ = st.columns([0.04, 0.92, 0.04])
    with col:
        content_fn()


# ─────────────────────────────────────────────────────────────────────────────
# Constants — channel / people lists
# ─────────────────────────────────────────────────────────────────────────────
DISTRIBUTORS = ["— wybierz —", "Arrow Electronics", "Arrow ECS Baltic", "TD Synnex"]

IBM_SALES_REPS = [
    "— wybierz —",
    "Adam Karaszewski",
    "Artur Król",
    "Bartosz Pizon",
    "Daniel Kudyba",
    "Dawid Dołowy",
    "Dominik Dabrowski",
    "Jacek Goździk",
    "Józef Angelus",
    "Łukasz Pikur",
    "Łukasz Stolarczyk",
    "Łukasz Winiarski",
    "Maryia Shulhach",
    "Mirosław Pura",
    "Piotr Sękowski",
]

COMPETITORS_STORAGE = [
    "Pure Storage FlashArray",
    "Dell EMC PowerStore",
    "NetApp AFF",
    "HPE Alletra / Nimble",
    "Hitachi VSP",
    "Huawei OceanStor",
    "Other (describe below)",
]

COMPETITORS_SAN = [
    "Cisco MDS (Nexus)",
    "HPE SN Switch (OEM Brocade)",
    "Dell PowerSwitch FC (OEM Brocade)",
    "Arista / other FC vendor",
    "Other (describe below)",
]

# Powody extended bid validity (> 30 dni od dziś)
EXTENDED_VALIDITY_REASONS: list[tuple[str, str]] = [
    ("",                          "— select reason —"),
    ("client_rfp_requires",       "Client RFP / tender specifies extended validity period"),
    ("procurement_cycle_long",    "Client procurement / approval cycle exceeds 30 days"),
    ("budget_approval_pending",   "Client budget approval pending beyond standard window"),
    ("multi_year_framework",      "Multi-year framework agreement negotiation in progress"),
    ("complex_technical_review",  "Complex technical evaluation / PoC extending timeline"),
    ("public_sector_regulation",  "Public sector / government regulation requires longer validity"),
    ("partner_request",           "Partner / reseller formally requested extended validity"),
    ("other",                     "Other — specify in Special Bid questionnaire"),
]

# Predefiniowane scenariusze deal-type — klucz → (label UI, opis techniczny, słowa kluczowe RFP)
DEAL_TYPES: list[tuple[str,str,str]] = [
    ("— wybierz —",
     "— wybierz —",
     ""),
    ("san_refresh",
     "Refresh of SAN infrastructure for critical workloads",
     "Fibre Channel SAN fabric refresh replacing end-of-support b-type switches, "
     "requiring non-disruptive migration, 32/64 Gbps port density, and IBM Storage Expert Care support"),
    ("new_database",
     "New storage for critical database workloads",
     "high-performance all-flash storage for critical database workloads (Oracle, SAP HANA, MS SQL), "
     "requiring low latency, high IOPS, and enterprise data protection"),
    ("vmware_cloud",
     "Storage for VMware & hybrid cloud",
     "shared all-flash storage for VMware vSphere / vSAN environments with hybrid cloud connectivity, "
     "requiring high availability, thin provisioning, and Storage Virtualize integration"),
    ("ai_gpu",
     "Fast storage for AI / GPU containerised workloads",
     "high-throughput all-flash storage for AI training and inference workloads running on GPU clusters "
     "in OpenShift / Kubernetes, requiring NVMe-oF connectivity and >10 GB/s sequential throughput"),
    ("backup_dr",
     "Storage for backup / disaster recovery",
     "scalable all-flash storage for backup and DR workloads, requiring high effective capacity "
     "through data reduction, Safeguarded Copy, and Global Mirror replication"),
    ("consolidation",
     "Storage consolidation / migration from legacy",
     "storage consolidation replacing legacy HDD/hybrid arrays with all-flash, "
     "requiring seamless data migration, IBM Storage Insights, and virtualisation of third-party storage"),
    ("file_nas",
     "Unified block + file / NAS workloads",
     "unified all-flash storage for mixed block and file (NFS/SMB) workloads, "
     "requiring IBM Spectrum Scale or native file services integration"),
]

# Warianty tekstów dla Sekcja A — Deal Background / Scenario
# Każdy deal type ma kilka wersji, żeby rotować i uniknąć powtarzalności
# Format: { deal_key: [ "wariant 1", "wariant 2", ... ] }
# Użyj {client}, {mname}, {usable}, {raid}, {sup_name} jako placeholder
_BACKGROUND_VARIANTS: dict[str, list[str]] = {
    "new_database": [
        # NEW DEAL — database platform replacement
        "Deal type: New deal — primary storage replacement for mission-critical database workloads. "
        "{client} is replacing end-of-life SAN infrastructure that can no longer meet the IOPS and "
        "latency SLAs of Oracle RAC and SAP HANA. The procurement team issued a formal RFP with mandatory "
        "requirements: sub-1 ms response times at peak load, NVMe all-flash architecture, {usable:.0f} TiB "
        "usable capacity ({raid}), and synchronous replication for zero-RPO DR. "
        "IBM {mname} with FlashCore Module 5 (FCM5) was shortlisted on the basis of performance benchmarks "
        "and AI-powered inline ransomware detection — a differentiating capability not available in competing "
        "proposals. Support: {sup_name}. "
        "IBM has no existing footprint at this account; failure to win means losing the initial IBM deployment "
        "to a competitor, with all follow-on expansion orders going to the incumbent by default.",

        # EXPANSION — growing transaction volumes
        "Deal type: Capacity expansion — transaction volume growth forcing storage upgrade. "
        "{client} has confirmed that their current HDD/hybrid storage cannot sustain growing "
        "transaction volumes for Oracle EBS and MS SQL Server analytical workloads. A capacity and "
        "performance audit identified a bottleneck at peak load: current latency exceeds 4 ms against "
        "an SLA of <1 ms. The RFP mandates an NVMe all-flash array with >500K IOPS, {usable:.0f} TiB "
        "usable ({raid}), and 24×7 enterprise support. "
        "IBM {mname} with {sup_name} fulfils all mandatory criteria. "
        "This is a net-new IBM storage installation; the requested Special Bid pricing is required to "
        "match the competitive price band established by shortlisted vendors during the evaluation.",

        # COMPETITIVE RFP — two-DC replication
        "Deal type: New deal — competitive RFP for dual-site database storage with zero-RPO replication. "
        "{client} issued a formal RFP for primary storage serving SAP HANA scale-out and Oracle Database "
        "across two data centres. Technical mandatory requirements include: sustained sub-1 ms latency at "
        "peak IOPS, synchronous Global Mirror replication, {usable:.0f} TiB usable ({raid}), and a single "
        "support contract covering both sites. IBM {mname} (FCM5, AI ransomware detection) meets all "
        "criteria and differentiates from competing bids. "
        "Failure to secure this deal at the right price will result in Pure Storage or Dell EMC becoming "
        "the strategic storage supplier for this account for the next 5+ years.",
    ],
    "vmware_cloud": [
        # CONSOLIDATION — legacy SAN islands
        "Deal type: New deal — VMware environment consolidation, replacing 3 legacy SAN islands. "
        "{client} is consolidating three end-of-life SAN systems into a single shared all-flash platform "
        "supporting 800+ VMware vSphere VMs across two sites. The RFP requires native vSphere/vCenter "
        "integration (VAAI/VASA), thin provisioning, Storage Policy-Based Management (SPBM), and optional "
        "IBM Storage Virtualize for non-disruptive migration from third-party arrays. "
        "IBM {mname} ({usable:.0f} TiB, {raid}) with {sup_name} meets all technical requirements. "
        "Competing vendors (Pure Storage, NetApp AFF) are offering aggressive migration incentives and "
        "Evergreen-type subscription pricing. The requested exception discount is required to remain "
        "competitive on a total-cost-of-ownership basis over the 5-year contract period.",

        # VSPHERE REFRESH — post-VMware Broadcom pricing change
        "Deal type: New deal — VMware storage refresh driven by Broadcom licensing cost review. "
        "Following the Broadcom acquisition of VMware and significant vSphere licence cost increases, "
        "{client} initiated a storage platform review to reduce vSAN complexity and overall VMware TCO. "
        "The RFP mandates an NVMe all-flash array compatible with VMware vSphere 8.0 and OpenShift "
        "Virtualization as a potential alternative hypervisor. IBM {mname} provides native VAAI/VASA "
        "integration, {usable:.0f} TiB usable ({raid}), and a validated Red Hat OpenShift migration path. "
        "Exception pricing is required to win against HPE Alletra 9000 and Dell PowerStore, both of "
        "which submitted proposals 10–15% below IBM list price.",

        # PRIMARY STORAGE MODERNISATION — end-of-life SAN replacement
        "Deal type: New deal — primary storage modernisation, replacing end-of-life SAN infrastructure. "
        "{client} initiated a formal storage refresh programme to replace ageing SAN arrays that can no "
        "longer meet the IOPS and latency SLAs required by virtualised workloads running on VMware vSphere. "
        "The RFP mandates NVMe all-flash performance, {usable:.0f} TiB usable ({raid}), native VAAI/VASA "
        "integration, and a single enterprise support contract. IBM {mname} with IBM Storage Insights "
        "provides proactive capacity and performance management without additional cost. "
        "{sup_name} support is included. "
        "Competing vendors are offering aggressive pricing; the requested exception discount is required "
        "to position IBM as the most cost-effective all-flash platform for this on-premises refresh.",
    ],
    "ai_gpu": [
        # NEW AI PLATFORM — LLM training
        "Deal type: New deal — primary storage for GPU AI/ML training cluster (net-new IBM deployment). "
        "{client} is building a GPU compute cluster for large-language-model (LLM) training and inference, "
        "requiring storage that can sustain >10 GB/s sequential throughput per GPU node group with "
        "NVMe-oF over RoCE/InfiniBand for NVIDIA DGX/HGX systems running OpenShift / Kubernetes. "
        "IBM {mname} ({usable:.0f} TiB, {raid}) with FCM5 inline ransomware protection satisfies all "
        "mandatory I/O requirements. "
        "This is a strategically important net-new deployment: IBM has no existing footprint at this "
        "account, and winning establishes IBM as the AI storage supplier for expected follow-on GPU "
        "cluster expansions planned for H2. Special Bid pricing is required to beat Pure Storage "
        "FlashBlade//S and VAST Data proposals submitted below IBM list.",

        # POST-POC — preferred vendor
        "Deal type: Preferred vendor selection — post-PoC procurement following successful IBM trial. "
        "Following a 6-week proof-of-concept for AI/ML inference workloads, {client} selected IBM {mname} "
        "as their preferred all-flash platform based on demonstrated throughput and latency results. "
        "The formal RFP covers {usable:.0f} TiB usable ({raid}), NVMe-oF connectivity, and deep "
        "integration with Red Hat OpenShift AI. {sup_name} covers 24×7 support SLA. "
        "Although IBM is the preferred vendor, the procurement committee requires a price within "
        "the budget ceiling validated during the PoC business case — exception pricing is required "
        "to convert the technical win into a commercial win before a competing vendor re-enters the bid.",

        # LARGE-SCALE TRAINING — parallel I/O
        "Deal type: New deal — AI training infrastructure, parallel I/O from 64+ GPU nodes. "
        "A formal AI infrastructure RFP by {client} requires a storage platform capable of sustaining "
        "parallel read I/O simultaneously from 64+ GPU nodes during distributed model training. "
        "IBM {mname} delivers the required throughput profile with {usable:.0f} TiB usable capacity "
        "({raid}) and built-in inline data reduction to maximise effective capacity for large model "
        "checkpoints. This is IBM's first opportunity in the customer's AI infrastructure programme; "
        "the requested discount brings the net price in line with cloud-native storage offerings "
        "(AWS FSx for Lustre, Azure NetApp Files) evaluated as alternatives during the RFP process.",
    ],
    "backup_dr": [
        # RANSOMWARE RECOVERY — new Safeguarded Copy deployment
        "Deal type: New deal — air-gapped backup and ransomware recovery platform. "
        "{client} completed a cybersecurity audit following an industry-wide ransomware alert and "
        "identified a critical gap: no immutable, air-gapped copy of Tier-1 production data. "
        "The RFP mandates: immutable snapshots (Safeguarded Copy), Global Mirror synchronous replication, "
        ">3:1 effective data reduction, and {usable:.0f} TiB ({raid}) usable capacity. "
        "IBM {mname} with FCM5 delivers hardware-level ransomware detection and Safeguarded Copy — "
        "capabilities unavailable in Dell EMC Data Domain and Commvault HyperScale X proposals. "
        "{sup_name} ensures 4-hour hardware response SLA. Special Bid pricing is required to close "
        "within the security budget approved by the board.",

        # POST-INCIDENT — recovery infrastructure rebuild
        "Deal type: Urgent new deal — backup infrastructure rebuild following ransomware incident. "
        "{client} suffered a ransomware attack that encrypted production storage and backup targets "
        "simultaneously. The emergency RFP requires an isolated backup platform with Safeguarded Copy, "
        "automated recovery testing, and FCM5 AI-powered detection of anomalous write patterns. "
        "IBM {mname} ({usable:.0f} TiB usable, {raid}) is the only shortlisted solution combining "
        "hardware-level threat detection with immutable copy management. "
        "{sup_name} provides 24×7 critical response. Exception pricing is required to fit within the "
        "emergency budget envelope approved by the board; failure to win means the customer will "
        "deploy a competitor solution as the permanent cyber-resilience platform.",

        # BC/DR — RPO/RTO mandate
        "Deal type: New deal — business continuity platform, RPO/RTO compliance mandate. "
        "A business continuity audit at {client} identified that the existing backup chain cannot "
        "meet the RPO < 15 min and RTO < 1 h SLAs mandated by new regulatory requirements (DORA / NIS2). "
        "The RFP covers Global Mirror and Safeguarded Copy on IBM {mname} ({usable:.0f} TiB, {raid}) "
        "as the compliant DR platform. Competing proposals from Zerto/HPE include multi-year software "
        "bundles at aggressive pricing. The requested exception discount is required to position IBM "
        "as the most cost-effective path to regulatory compliance.",
    ],
    "consolidation": [
        # EOL REFRESH — multiple legacy arrays
        "Deal type: New deal — storage consolidation, decommissioning 4 end-of-life arrays. "
        "{client} is decommissioning four end-of-life HDD/hybrid arrays (HPE 3PAR, EMC VNX) as part "
        "of a planned data-centre refresh. The RFP requires non-disruptive Live Data Migration from all "
        "incumbent arrays, IBM Storage Insights integration for unified management, and a consolidated "
        "{usable:.0f} TiB ({raid}) all-flash target platform. "
        "IBM {mname} with Storage Virtualize enables migration from third-party arrays without downtime — "
        "a key differentiator versus HPE Alletra, which requires disruptive migration for non-HPE arrays. "
        "{sup_name} provides post-migration 24×7 support. Special Bid pricing is required to justify "
        "the total project investment versus a competitor's migration incentive programme.",

        # TCO-DRIVEN CONSOLIDATION
        "Deal type: New deal — all-flash consolidation, 40% TCO reduction mandate. "
        "{client} launched a strategic cost-reduction programme targeting 40% storage TCO savings over "
        "3 years. An independent TCO analysis confirmed that consolidating 6 HDD arrays onto IBM {mname} "
        "({usable:.0f} TiB, {raid}) delivers: 65% rack-space reduction, 55% power and cooling savings, "
        "and elimination of 4 separate support contracts. {sup_name} replaces all existing per-array "
        "maintenance agreements. Exception pricing is required to match Pure Storage Evergreen//One "
        "subscription-model TCO projections submitted by a competing vendor as the primary alternative.",

        # MIGRATION + EXPANSION
        "Deal type: New deal — infrastructure modernisation, migration and capacity expansion. "
        "A data-centre footprint reduction mandate at {client} requires replacing multiple legacy storage "
        "silos with a single IBM {mname} ({usable:.0f} TiB, {raid}). The migration scope covers "
        "petabytes of production data from incumbent arrays without service interruption, using IBM "
        "Storage Virtualize Live Data Migration. Post-migration, IBM Storage Insights provides proactive "
        "capacity and performance management across the consolidated platform. "
        "Exception pricing is requested to offset the migration project costs and remain competitive "
        "against Dell EMC's migration incentive programme, which includes free professional services.",
    ],
    "file_nas": [
        # UNIFIED NAS — VDI + file sharing
        "Deal type: New deal — unified block and file platform for VDI and unstructured data. "
        "{client} is deploying a new unified storage platform to serve mixed NFS/SMB workloads for "
        "3,000 virtualised desktops (VDI) and a centralised file-sharing environment replacing "
        "end-of-life Windows File Server clusters. The RFP mandates: native NAS protocols (NFSv4.1, "
        "SMB 3.1.1), scale-out capacity to {usable:.0f} TiB ({raid}), inline deduplication and "
        "compression, and S3-compatible object access for archival tiers. "
        "IBM {mname} with IBM Spectrum Scale integration meets all protocol and scalability requirements. "
        "{sup_name} covers 24×7 SLA. Exception pricing is required to compete with NetApp AFF and "
        "Qumulo all-flash NAS proposals that are priced 12–18% below IBM list.",

        # VDI EXPANSION
        "Deal type: Capacity expansion — VDI scale-out, growing from 1,500 to 4,500 seats. "
        "Following a successful IBM storage deployment for the initial VDI rollout, {client} is "
        "expanding from 1,500 to 4,500 virtual desktop seats and requires additional all-flash capacity. "
        "The expansion RFP covers {usable:.0f} TiB usable ({raid}) with native SMB 3.1.1 and NFSv4.1, "
        "and is evaluated on a price-per-desktop metric. IBM {mname} delivers the required IOPS/TiB "
        "density. Competing vendors have submitted proposals using the existing IBM deployment as a "
        "benchmark, pricing aggressively to displace IBM in the expansion. Special Bid pricing is "
        "required to retain the account and protect the existing IBM footprint.",

        # MEDIA + COLLABORATION
        "Deal type: New deal — media asset storage and collaboration platform consolidation. "
        "A media production and collaboration workload consolidation project at {client} requires "
        "scalable NAS storage with high-throughput sequential I/O for video editing (4K/8K streams) "
        "and S3-compatible object access for long-term archive. IBM {mname} ({usable:.0f} TiB, {raid}) "
        "with IBM Spectrum Scale delivers unified block, file, and object from a single platform, "
        "eliminating the need for separate media asset management storage. "
        "{sup_name} ensures business continuity. The requested exception discount aligns the net price "
        "with competing pure-NAS proposals (Dell EMC PowerScale, Qumulo) that include bundled "
        "media workflow software at no additional cost.",
    ],
    "san_refresh": [
        # Competitive FC SAN refresh
        "Deal type: SAN infrastructure refresh — end-of-support Fibre Channel fabric replacement. "
        "{client} is operating Brocade b-type SAN switches that have reached or are approaching "
        "end-of-support. The customer requires a non-disruptive migration path to 32/64 Gbps FC, "
        "ensuring continued compatibility with existing FlashSystem / DS8000 storage. "
        "IBM {mname} (Brocade OEM) provides native ISL trunking, FICON support, and direct integration "
        "with IBM Storage Expert Care. "
        "Special Bid pricing is required to match Cisco MDS competitive proposals, which have been "
        "submitted at significantly below list price for this refresh opportunity.",

        # Greenfield SAN — no prior IBM FC footprint
        "Deal type: Net-new SAN fabric deployment — greenfield Fibre Channel connectivity. "
        "{client} is deploying an all-flash storage infrastructure ({mname}) and requires a "
        "dedicated FC SAN fabric to connect host servers to storage. The customer evaluated Cisco MDS "
        "and HPE SN switches; IBM b-type SAN switches were selected for native IBM stack integration "
        "and single-vendor support. "
        "Exception pricing is required to align the total solution cost (FlashSystem + SAN) with "
        "competing all-in-one proposals from Dell and HPE.",

        # SAN consolidation / upgrade — 16G to 64G
        "Deal type: SAN upgrade — Fibre Channel speed uplift from 16 Gb to 32/64 Gb. "
        "{client} is consolidating SAN fabrics across multiple data centres and upgrading "
        "to 64 Gbps FC to support NVMe-oF workloads and eliminate I/O bottlenecks. "
        "IBM {mname} with {sup_name} support was selected after a formal evaluation; "
        "the requested discount is required to remain competitive against Cisco MDS 9300 series, "
        "which has been aggressively priced in this account.",
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# Projects folder
# ─────────────────────────────────────────────────────────────────────────────
PROJECTS_DIR = Path("projects")
PROJECTS_DIR.mkdir(exist_ok=True)

_SAVEABLE_KEYS = [
    "client_name", "seller_name", "deal_type", "due_date", "discount_pct",
    "bid_distributor", "bid_sales_rep", "bid_reseller",
    "bid_competitors_sel", "bid_incumbent", "bid_incumbent_model",
    "bid_opportunity_ctx", "bid_background", "bid_business_just",
    "bid_deal_history", "bid_client_budget", "bid_ref_sbo_c",
    "bid_validity_reason",
]

def _save_project(name: str) -> Path:
    """Save session metadata (not binary files) to JSON."""
    def _json_default(obj):
        if hasattr(obj, "isoformat"):   # date / datetime
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

    payload = {k: st.session_state.get(k) for k in _SAVEABLE_KEYS}
    payload["project_data"] = {
        k: v for k, v in st.session_state.get("project_data", {}).items()
        if isinstance(v, (str, int, float, bool, list, dict, type(None)))
    }
    payload["saved_at"] = date.today().isoformat()
    slug = re.sub(r"[^\w]", "_", name.strip()) or "project"
    path = PROJECTS_DIR / f"{slug}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    return path

def _load_project(path: Path) -> None:
    """Restore session state from saved JSON."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    for k in _SAVEABLE_KEYS:
        if k in payload:
            st.session_state[k] = payload[k]
    if "project_data" in payload and payload["project_data"]:
        st.session_state["project_data"]   = payload["project_data"]
        st.session_state["project_loaded"] = True

def _list_saved_projects():
    return sorted(PROJECTS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)


# ─────────────────────────────────────────────────────────────────────────────
# Session state defaults
# ─────────────────────────────────────────────────────────────────────────────
_SESSION_DEFAULTS: dict = {
    "nav_page": "sales",             # "sales" | "bj"
    "product_line": "flashsystem",   # "flashsystem" | "scale" | "fusion" | "power"
    "project_loaded": False, "project_data": {},
    "client_name": "", "seller_name": "",
    "deal_type": DEAL_TYPES[0][0],   # key string e.g. "new_database"
    "due_date": date.today() + timedelta(days=30),
    "discount_pct": 60.0, "disc_slider": 60.0, "disc_num": 60.0, "iops_manual": 0,
    "num_systems": 1, "eu_margin_pct": 15.0,
    "active_tab": "exec",
    # Exec Summary
    "exec_bytes": None, "exec_filename": "",
    "exec_lang": "en",
    # RFP
    "rfp_bytes": None, "rfp_filename": "",
    "rfp_iops_manual": 0,
    "rfp_lang": "en",
    # Special Bid
    "bid_bytes": None, "bid_filename": "",
    "bid_distributor": DISTRIBUTORS[0],
    "bid_sales_rep": IBM_SALES_REPS[0],
    "bid_reseller": "",
    "bid_competitors_sel": [],
    "bid_incumbent": "",
    "bid_incumbent_model": "",
    "bid_opportunity_ctx": "",
    "bid_background": "",
    "bid_business_just": "",
    "bid_deal_history": "",
    "bid_client_budget": "",
    "bid_ref_sbo_c": "",
    "bid_validity_reason": "",
}

def _reset_session() -> None:
    """Clear all project & form state, restoring defaults. Called on logo click or new config."""
    # Keys to preserve across reset
    _keep = {"nav_page", "product_line", "exec_lang", "rfp_lang"}
    for k, v in _SESSION_DEFAULTS.items():
        if k not in _keep:
            st.session_state[k] = v
    # Also clear derived/input widget shadow keys that Streamlit caches
    for _shadow in [
        "num_systems_input", "disc_num", "disc_slider", "mep_input", "mep_text_input",
        "due_date_input", "eu_margin_pct_input", "bid_budget_text",
        "_prev_deal_type_for_bg", "_bj_prev_sig",
        "sel_deal_type",   # selectbox widget key — must be cleared so index picks up new deal_type
    ]:
        st.session_state.pop(_shadow, None)
    # Clear all bg-variant index keys
    for k in list(st.session_state.keys()):
        if k.startswith("_bg_variant_idx_"):
            del st.session_state[k]

# Apply defaults on first load
for k, v in _SESSION_DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Handle ?reset=1 query param (triggered by logo link)
if st.query_params.get("reset") == "1":
    _reset_session()
    st.query_params.clear()
    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# NAV BAR
# ─────────────────────────────────────────────────────────────────────────────
# Build Documentation links for the currently loaded model (if any)
_nav_model_code = (st.session_state.get("project_data") or {}).get("model_code", "")
_nav_model_info = get_model_info(_nav_model_code) if _nav_model_code else {}
_nav_short      = _nav_model_info.get("short", "")
_nav_name       = _nav_model_info.get("name", "")
_nav_docs       = get_docs(_nav_short) if _nav_short else {}
_nav_docs_url   = _nav_docs.get("docs_url", "")
_nav_sm_url     = _nav_docs.get("sales_manual_url", "")

# SAN switches docs — collect unique switch models from loaded project
_nav_san_switches = (st.session_state.get("project_data") or {}).get("san_switches", [])
_nav_san_seen: set[str] = set()
_nav_san_links_html = ""
for _nssw in _nav_san_switches:
    _ns_short = _nssw.get("switch_short", "")
    if _ns_short and _ns_short not in _nav_san_seen:
        _nav_san_seen.add(_ns_short)
        _ns_docs = get_docs(_ns_short)
        _ns_docs_url = _ns_docs.get("docs_url", "")
        _ns_sm_url   = _ns_docs.get("sales_manual_url", "")
        if _ns_docs_url or _ns_sm_url:
            _nav_san_links_html += f'<span class="ibm-nav-doc-label">Docs for {_ns_short}</span>'
            if _ns_docs_url:
                _nav_san_links_html += f'<a class="ibm-nav-link" href="{_ns_docs_url}" target="_blank" rel="noopener">IBM Docs ↗</a>'
            if _ns_sm_url:
                _nav_san_links_html += f'<a class="ibm-nav-link" href="{_ns_sm_url}" target="_blank" rel="noopener">Sales Manual ↗</a>'

if _nav_docs_url or _nav_san_links_html:
    _doc_links = '<div class="ibm-nav-doc-group">'
    if _nav_docs_url:
        # Build short label: "FS7600" from "IBM FlashSystem 7600", "SAN64B-7" already short
        _nav_short_label = _nav_short if _nav_short else _nav_name
        _doc_links += (
            f'<span class="ibm-nav-doc-label">Docs for {_nav_short_label}</span>'
            f'<a class="ibm-nav-link" href="{_nav_docs_url}" target="_blank" rel="noopener">IBM Docs ↗</a>'
            f'<a class="ibm-nav-link" href="{_nav_sm_url}" target="_blank" rel="noopener">Sales Manual ↗</a>'
        )
    _doc_links += _nav_san_links_html
    _doc_links += '</div>'
else:
    _doc_links = '<a class="ibm-nav-link ibm-nav-link-muted" href="#">Documentation — load a config first</a>'

_tools_links = (
    f'<div class="ibm-nav-doc-group">'
    f'<span class="ibm-nav-doc-label">IBM Tools</span>'
    f'<a class="ibm-nav-link" href="https://www.ibm.com/services/econfigcloud/" target="_blank" rel="noopener">IBM e-config ↗</a>'
    f'<a class="ibm-nav-link" href="https://www.ibm.com/tools/storage-modeller/" target="_blank" rel="noopener">Storage Modeller ↗</a>'
    f'</div>'
)

# ── Query-param routing — ?p=bj / ?p=sales ──────────────────────────────────
_qp = st.query_params.get("p", "")
if _qp in ("sales", "bj"):
    st.session_state["nav_page"] = _qp
_nav_page = st.session_state.get("nav_page", "sales")

# ── Nav bar — all links in pure HTML, routing via ?p= query params ───────────
_nav_sales_cls = "ibm-nav-link active" if _nav_page == "sales" else "ibm-nav-link"
_nav_bj_cls    = "ibm-nav-link active" if _nav_page == "bj"    else "ibm-nav-link"

st.markdown(
    f'<div class="ibm-nav">'
    f'  <div class="ibm-nav-left">'
    f'    <a class="ibm-nav-brand" href="?reset=1" style="text-decoration:none;cursor:pointer" title="New configuration — reset app">IBM <span>Ace of Sales</span></a>'
    f'    <div class="ibm-nav-sep"></div>'
    f'    <div class="ibm-nav-links">'
    f'      <a class="{_nav_sales_cls}" href="?p=sales">Sales Centre</a>'
    f'      <a class="{_nav_bj_cls}"    href="?p=bj">Bid Justification</a>'
    f'    </div>'
    f'  </div>'
    f'  <div class="ibm-nav-links">'
    f'    {_tools_links}'
    f'    {_doc_links}'
    f'  </div>'
    f'</div>'
    f'<div class="ibm-nav-spacer"></div>',
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE ROUTER  — must come before any page-specific rendering
# ─────────────────────────────────────────────────────────────────────────────
if _nav_page == "bj":
    # =========================================================================
    # PAGE — BID JUSTIFICATION
    # =========================================================================
    _, bj_main, _ = st.columns([0.04, 0.92, 0.04])
    with bj_main:
        st.markdown("""
<div class="ibm-hero">
  <div class="ibm-hero-eyebrow">IBM Storage</div>
  <h1 class="ibm-hero">Bid Justification Generator</h1>
  <div class="ibm-hero-sub">
    Fill in the fields below to generate a ready-to-submit Business Justification
    for an IBM Hardware Special Bid pricing request.
  </div>
</div>
""", unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        _bj_left, _bj_right = st.columns([1, 1], gap="large")

        with _bj_left:
            # ── BP Price + Currency (always visible) ──────────────────────
            section("BP Price")
            _curr_opts = ["EUR", "USD", "PLN"]
            if "bj_currency" not in st.session_state:
                st.session_state["bj_currency"] = "EUR"

            _bj_price_col, _bj_curr_col = st.columns([3, 1], gap="small")
            with _bj_curr_col:
                _bj_curr = st.radio(
                    "Currency",
                    options=_curr_opts,
                    index=_curr_opts.index(st.session_state.get("bj_currency", "EUR")),
                    key="bj_currency_radio",
                )
                st.session_state["bj_currency"] = _bj_curr
            with _bj_price_col:
                _bj_bp_price = st.number_input(
                    f"BP Price ({_bj_curr})",
                    min_value=0.0,
                    value=float(st.session_state.get("bj_bp_price", 0.0)),
                    step=1000.0,
                    format="%.2f",
                    key="bj_bp_price_input",
                )
                st.session_state["bj_bp_price"] = _bj_bp_price

            # ── Optional DOCX upload (pre-fills BP price) ─────────────────
            with st.expander("⬆  Pre-fill from Special Bid DOCX *(optional)*", expanded=True):
                _bid_file = st.file_uploader(
                    "Special Bid DOCX",
                    type=["docx"],
                    key="bj_bid_upload",
                    help="Upload the filled-in HW Special Bid Pricing Request DOCX",
                    label_visibility="collapsed",
                )
                if _bid_file:
                    try:
                        _bid_data = parse_bid_docx(io.BytesIO(_bid_file.read()))
                        st.session_state["bj_bid_data"] = _bid_data
                        # sync currency + price from doc if file changed
                        if st.session_state.get("_bj_last_file") != _bid_file.name:
                            _doc_curr = _bid_data.get("currency", "EUR").upper()
                            if _doc_curr in _curr_opts:
                                st.session_state["bj_currency"] = _doc_curr
                            st.session_state["bj_bp_price"] = float(_bid_data.get("net_price", 0.0))
                            st.session_state["_bj_last_file"] = _bid_file.name
                            st.rerun()
                        st.markdown(notif("ok", "DOCX parsed successfully."), unsafe_allow_html=True)
                        if _bid_data["parse_warnings"]:
                            for _w in _bid_data["parse_warnings"]:
                                st.markdown(notif("warn", _w), unsafe_allow_html=True)
                        _bid_data_disp = _bid_data
                        st.dataframe({
                            "Field": ["Client", "Model", "List Price", "Net Price", "Discount"],
                            "Value": [
                                _bid_data_disp.get("client_name", "—"),
                                _bid_data_disp.get("model_name", "—"),
                                f"{_bid_data_disp.get('list_price', 0):,.2f} {_bid_data_disp.get('currency','EUR')}",
                                f"{_bid_data_disp.get('net_price', 0):,.2f} {_bid_data_disp.get('currency','EUR')}",
                                f"{_bid_data_disp.get('discount_pct', 0):.1f}%",
                            ],
                        }, hide_index=True, use_container_width=True)
                    except Exception as _e:
                        st.error(f"Parse error: {_e}")

        with _bj_right:
            section("Context")

            _bj_ct_col, _bj_cust_col, _bj_val_col = st.columns(3, gap="small")
            with _bj_ct_col:
                _bj_client_type = st.radio(
                    "Tender type",
                    options=["Private sector", "Public sector"],
                    index=0,
                    horizontal=False,
                    key="bj_client_type",
                )
                _bj_client_type_key = "public" if "Public" in _bj_client_type else "private"
            with _bj_cust_col:
                _bj_cust_status = st.radio(
                    "Customer status",
                    options=["New customer", "Existing customer"],
                    index=0,
                    horizontal=False,
                    key="bj_cust_status",
                )
            with _bj_val_col:
                _bj_validity_type = st.radio(
                    "Bid validity",
                    options=["Standard (30 days)", "Extended (>30 days)"],
                    index=0,
                    horizontal=False,
                    key="bj_validity_type",
                )
                _bj_is_extended = (_bj_validity_type == "Extended (>30 days)")
                if _bj_is_extended:
                    _bj_validity_days = st.number_input(
                        "Days",
                        min_value=31, max_value=365,
                        value=int(st.session_state.get("bj_validity_days", 60)),
                        step=1,
                        key="bj_validity_days_input",
                        label_visibility="visible",
                    )
                    st.session_state["bj_validity_days"] = _bj_validity_days
                else:
                    _bj_validity_days = 30

            # ── Extended validity reason (shown only when extended) ───────
            if _bj_is_extended:
                _bj_vr_opts  = [r[1] for r in EXTENDED_VALIDITY_REASONS]
                _bj_vr_keys  = [r[0] for r in EXTENDED_VALIDITY_REASONS]
                _bj_vr_cur   = st.session_state.get("bj_validity_reason_key", "")
                _bj_vr_idx   = (_bj_vr_keys.index(_bj_vr_cur)
                                if _bj_vr_cur in _bj_vr_keys else 0)
                _bj_vr_sel = st.selectbox(
                    "Reason for extended validity",
                    options=_bj_vr_opts,
                    index=_bj_vr_idx,
                    key="bj_validity_reason_sel",
                )
                _bj_validity_reason = _bj_vr_sel
                st.session_state["bj_validity_reason_key"] = _bj_vr_keys[
                    _bj_vr_opts.index(_bj_vr_sel)
                ]
            else:
                _bj_validity_reason = ""

            st.markdown(
                '<div style="font-size:12px;font-weight:600;text-transform:uppercase;'
                'letter-spacing:.06em;color:var(--gray-70);margin:8px 0 4px">Competition</div>',
                unsafe_allow_html=True,
            )
            _bj_competitors = st.multiselect(
                "Competition",
                options=COMPETITORS_STORAGE,
                default=st.session_state.get("bj_competitors", []),
                key="bj_competitors_ms",
                label_visibility="collapsed",
            )

            _bj_ref_sbo = st.text_input(
                "Ref. SBO  *(optional)*",
                value=st.session_state.get("bj_ref_sbo", ""),
                placeholder="e.g. SBO-2024-12345",
                key="bj_ref_sbo_input",
                help="Reference SBO number — will be included in the Business Justification",
            )
            st.session_state["bj_ref_sbo"] = _bj_ref_sbo

            _bj_extra = st.text_area(
                "Additional info *(optional)*",
                value=st.session_state.get("bj_extra", ""),
                placeholder=(
                    "e.g. Customer is a strategic IBM account. "
                    "Competing offer includes 5-year service bundle. "
                    "Tender deadline is 30 Jun."
                ),
                height=80,
                key="bj_extra_input",
            )
            st.session_state["bj_extra"] = _bj_extra

        # ── Generate button ───────────────────────────────────────────────
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        _bj_gc1, _bj_gc2, _bj_gc3 = st.columns([1, 2, 1])
        with _bj_gc2:
            _gen_clicked = st.button(
                "Generate Business Justification →",
                type="primary",
                use_container_width=True,
                key="btn_gen_bj",
            )

        if _gen_clicked:
            # ── Deterministic 5-line template ─────────────────────────────
            _bp_curr   = st.session_state.get("bj_currency", "EUR")
            _bp_amount = float(st.session_state.get("bj_bp_price", 0.0))
            _bp_fmt    = f"{_bp_amount:,.0f} {_bp_curr}"
            _ref_sbo   = st.session_state.get("bj_ref_sbo", "").strip()
            _comp_list = _bj_competitors
            _comp_str  = ", ".join(_comp_list) if _comp_list else "key competing vendors"
            _is_new    = "New" in _bj_cust_status
            _is_pub    = "Public" in _bj_client_type
            _is_ext    = _bj_is_extended

            # Line 1 — BP price
            _line1 = f"I approve total BP price: {_bp_fmt}."

            # Line 2 — Bid validity
            if _is_ext:
                _vr = st.session_state.get("bj_extra", "")  # reuse var below
                _vr = _bj_validity_reason.strip() if _bj_validity_reason.strip() and _bj_validity_reason != "— select reason —" else ""
                _line2 = (
                    f"Bid validity: extended ({_bj_validity_days} days)"
                    + (f" — {_vr}." if _vr else ".")
                )
            else:
                _line2 = "Bid validity: standard (30 days)."

            # Line 3 — Customer + tender type + discount justification
            _tender = "public tender" if _is_pub else "private tender"
            if _is_new:
                _line3 = (
                    f"New client for IBM — {_tender} — "
                    "therefore we need to get a very aggressive discount."
                )
            else:
                _line3 = (
                    f"Existing IBM client, threatened by entry of a competing vendor "
                    f"({_comp_str}) — {_tender} — "
                    "therefore we need to get a very aggressive discount."
                )

            # Line 2b — Reference SBO (only if provided) — placed right after BP price
            _line_sbo = f"Reference SBO nr {_ref_sbo}." if _ref_sbo else ""

            # Line 4 — Competition
            _line4 = f"We compete with {_comp_str}."

            # Line 6 — Additional info (only if provided)
            _extra = st.session_state.get("bj_extra", "").strip()
            _line6 = _extra if _extra else ""

            _bj_lines = [_line1]
            if _line_sbo:
                _bj_lines.append(_line_sbo)
            _bj_lines += [_line2, _line3, _line4]
            if _line6:
                _bj_lines.append(_line6)

            st.session_state["bj_result"] = "\n".join(_bj_lines)
            # ──────────────────────────────────────────────────────────────

        # ── Result ────────────────────────────────────────────────────────
        _bj_result = st.session_state.get("bj_result", "")
        if _bj_result:
            section("Business Justification")

            # Render each numbered line as a separate row in a styled card
            _bj_lines_disp = _bj_result.split("\n")
            _rows_html = "".join(
                f'<div style="padding:6px 0;border-bottom:1px solid #e0e0e0;'
                f'{"font-weight:600;" if i == 0 else ""}">'
                f'<span style="color:#0f62fe;font-weight:700;margin-right:8px">{i+1}.</span>'
                f'{line}</div>'
                for i, line in enumerate(_bj_lines_disp) if line.strip()
            )
            st.markdown(
                f'<div style="background:#f4f4f4;border-left:4px solid #0f62fe;'
                f'padding:12px 20px;font-size:13px;line-height:1.7;color:#161616;'
                f'font-family:\'IBM Plex Sans\',sans-serif;margin:8px 0 8px;'
                f'border-radius:2px">{_rows_html}</div>',
                unsafe_allow_html=True,
            )

            # Action buttons row
            _bj_r1, _bj_r2, _bj_r3 = st.columns([1, 1, 4], gap="small")
            with _bj_r1:
                if st.button("✕  Clear", key="btn_regen_bj", use_container_width=True):
                    st.session_state.pop("bj_result", None)
                    st.rerun()
            with _bj_r2:
                # Copy button via JS clipboard API injected into an iframe
                _escaped = _bj_result.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
                _components.html(
                    f"""<button onclick="navigator.clipboard.writeText(`{_escaped}`).then(()=>{{
                            this.textContent='✓  Copied!';
                            this.style.background='#24a148';
                            setTimeout(()=>{{this.textContent='📋  Copy';this.style.background='#0f62fe';}},1800);
                        }})"
                        style="width:100%;height:38px;background:#0f62fe;color:#fff;border:none;
                               border-radius:4px;font-size:13px;font-weight:500;cursor:pointer;
                               font-family:'IBM Plex Sans',sans-serif;letter-spacing:.02em">
                        📋  Copy
                    </button>""",
                    height=44,
                )

    st.stop()  # don't render Sales Centre on BJ page

# ─────────────────────────────────────────────────────────────────────────────
# SALES CENTRE — steps + hero + main content
# ─────────────────────────────────────────────────────────────────────────────

# Workflow step indicator
loaded = st.session_state["project_loaded"]
step1_done = loaded
step2_done = loaded and bool(st.session_state["client_name"])
step3_done = bool(st.session_state["exec_bytes"])

def step_cls(done, active):
    if done:   return "done"
    if active: return "active"
    return ""

st.markdown("""
<div class="ibm-hero">
  <div class="ibm-hero-eyebrow">IBM Storage · Sales Automation</div>
  <h1 class="ibm-hero">Ace of Sales — Infrastructure Sales Assistant</h1>
  <div class="ibm-hero-steps">
    <div class="ibm-hero-step">
      <span class="ibm-hero-step-num">1</span>
      <div>
        <div class="ibm-hero-step-title">Upload e-config CSV</div>
        <div class="ibm-hero-step-sub">FlashSystem · SAN b-type · Storage Scale</div>
      </div>
    </div>
    <div class="ibm-hero-step-arrow">→</div>
    <div class="ibm-hero-step">
      <span class="ibm-hero-step-num">2</span>
      <div>
        <div class="ibm-hero-step-title">Add Project Details</div>
        <div class="ibm-hero-step-sub">Client · deal type · discount</div>
      </div>
    </div>
    <div class="ibm-hero-step-arrow">→</div>
    <div class="ibm-hero-step">
      <span class="ibm-hero-step-num">3</span>
      <div>
        <div class="ibm-hero-step-title">Generate Documents</div>
        <div class="ibm-hero-step-sub">Exec Summary · RFP/RFI · Special Bid</div>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

_, main, _ = st.columns([0.04, 0.92, 0.04])

with main:

    # =========================================================================
    # PRODUCT LINE SELECTOR
    # =========================================================================
    _LINE_OPTIONS = {
        "flashsystem": ("⚡", "FlashSystem + SAN", "All-NVMe block storage (FS5600 · FS7600 · FS9600 · …) + SAN b-type switches"),
        "scale":       ("🗂️", "Storage Scale",     "Parallel file storage for AI & HPC (Scale 3500 · 6000)"),
        "fusion":      ("☁️", "Storage Fusion",    "Coming soon — hybrid cloud storage orchestration"),
        "power":       ("🖥️", "Power Server",      "Coming soon — IBM Power10 compute"),
    }

    st.markdown("""
<style>
.pl-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-bottom:16px; }
.pl-card {
    border:2px solid var(--gray-20); border-radius:6px; padding:14px 12px;
    cursor:pointer; text-align:center; background:var(--white);
    transition:border-color .15s, background .15s;
}
.pl-card.active  { border-color:var(--blue-60); background:#f0f5ff; }
.pl-card.soon    { opacity:.5; cursor:default; }
.pl-card .pl-icon { font-size:22px; margin-bottom:4px; }
.pl-card .pl-name { font-weight:600; font-size:13px; color:var(--gray-100); }
.pl-card .pl-sub  { font-size:11px; color:var(--gray-70); margin-top:2px; }
</style>
""", unsafe_allow_html=True)

    _pl_cols = st.columns(4, gap="small")
    for _pl_key, (_pl_icon, _pl_name, _pl_sub) in _LINE_OPTIONS.items():
        _pl_is_active = (st.session_state["product_line"] == _pl_key)
        _pl_coming    = _pl_key in ("fusion", "power")
        _pl_col_idx   = list(_LINE_OPTIONS.keys()).index(_pl_key)
        with _pl_cols[_pl_col_idx]:
            _pl_btn_type = "primary" if _pl_is_active else "secondary"
            _pl_label    = f"{_pl_icon} {_pl_name}" + (" *(soon)*" if _pl_coming else "")
            if st.button(_pl_label, key=f"pl_btn_{_pl_key}",
                         use_container_width=True,
                         type=_pl_btn_type,
                         disabled=_pl_coming):
                if st.session_state["product_line"] != _pl_key:
                    # reset parse state on line switch
                    st.session_state["product_line"]   = _pl_key
                    st.session_state["project_loaded"] = False
                    st.session_state["project_data"]   = {}
                    st.session_state["exec_bytes"]     = None
                    st.session_state["rfp_bytes"]      = None
                    st.session_state["bid_bytes"]      = None
                    st.rerun()

    _pl_cur = st.session_state["product_line"]
    _pl_icon_cur, _pl_name_cur, _pl_desc_cur = _LINE_OPTIONS[_pl_cur]
    st.markdown(
        f'<div style="font-size:12px;color:var(--gray-70);margin-bottom:4px">'
        f'Selected: <b>{_pl_name_cur}</b> — {_pl_desc_cur}</div>',
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # =========================================================================
    # STEP 1 — Upload & Parse
    # =========================================================================
    section("Step 1 — Upload Configuration Files")

    _is_scale = (st.session_state["product_line"] == "scale")
    _badge_wrap = (
        "margin-bottom:-8px !important;"
        "padding-bottom:0 !important;"
    )

    # Helper: build badge HTML — green when file already uploaded
    def _upload_badge(step_label: str, badge_text: str, base_cls: str, file_obj) -> str:
        done = file_obj is not None
        num_cls   = "upload-step-num uploaded"   if done else "upload-step-num"
        badge_cls = f"upload-step-badge uploaded" if done else f"upload-step-badge {base_cls}"
        prefix    = "✓ &nbsp;" if done else ""
        return (
            f'<div style="{_badge_wrap}">'
            f'<div class="{num_cls}">{step_label}</div>'
            f'<div class="{badge_cls}">{prefix}{badge_text}</div>'
            f'</div>'
        )

    if _is_scale:
        # Scale: 2 files — CSV + single combined Capacity & Performance XLSX
        u1, u2 = st.columns([1, 1], gap="large")
        with u1:
            csv_file = st.file_uploader(
                "Upload e-config CSV",
                type=["csv"], key="scale_csv_upload",
                help="IBM e-config Cloud → Export CSV (multi-system ESS file)",
                label_visibility="collapsed",
            )
            st.markdown(
                _upload_badge("Step 1 of 2", "Upload e-config CSV",
                              "required", csv_file),
                unsafe_allow_html=True,
            )
        with u2:
            capacity_file = st.file_uploader(
                "StorM Capacity & Performance Report",
                type=["xlsx"], key="scale_capacity_upload",
                help="ESS Storage Modeller combined Capacity & Performance report",
                label_visibility="collapsed",
            )
            st.markdown(
                _upload_badge("Step 2 of 2", "StorM Capacity &amp; Performance Report",
                              "required", capacity_file),
                unsafe_allow_html=True,
            )
        perf_file = None  # included in capacity XLSX for Scale
    else:
        # FlashSystem: CSV required + 2 optional XLSX
        u1, u2, u3 = st.columns([1, 1, 1], gap="large")
        with u1:
            csv_file = st.file_uploader(
                "Upload e-config CSV",
                type=["csv"], key="fs_csv_upload",
                help="IBM e-config Cloud → Export CSV",
                label_visibility="collapsed",
            )
            st.markdown(
                _upload_badge("Required", "Upload e-config CSV",
                              "required", csv_file),
                unsafe_allow_html=True,
            )
        with u2:
            capacity_file = st.file_uploader(
                "StorM Capacity Report",
                type=["xlsx"], key="fs_capacity_upload",
                help="Adds exact usable capacity, RAID type, cache. Not required for Special Bid.",
                label_visibility="collapsed",
            )
            st.markdown(
                _upload_badge("Optional", "StorM Capacity Report",
                              "optional", capacity_file),
                unsafe_allow_html=True,
            )
        with u3:
            perf_file = st.file_uploader(
                "StorM Performance Report",
                type=["xlsx"], key="fs_perf_upload",
                help="Adds IOPS/latency data for Exec Summary and RFP. Not required for Special Bid.",
                label_visibility="collapsed",
            )
            st.markdown(
                _upload_badge("Optional", "StorM Performance Report",
                              "optional", perf_file),
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # CSV-only mode notice
    _csv_only_mode = (csv_file is not None and capacity_file is None and not _is_scale)
    if _csv_only_mode:
        st.markdown(
            notif("info",
                  "⚡ <b>CSV-only mode</b> — capacity will be estimated from drive configuration. "
                  "Sufficient for <b>Special Bid</b> generation. "
                  "Add Storage Modeller XLSX for Exec Summary and RFP (exact capacity + performance data)."),
            unsafe_allow_html=True,
        )

    pc1, pc2, pc3 = st.columns([1, 2, 1])
    with pc2:
        parse_clicked = st.button(
            "Parse Files →", type="primary", use_container_width=True,
            disabled=(csv_file is None),
        )

    if parse_clicked:
        # Reset all project-specific state before loading new config
        _reset_session()
        with st.spinner("Parsing configuration files…"):
            try:
                _csv_buf  = io.BytesIO(csv_file.read())   # type: ignore[union-attr]
                if st.session_state["product_line"] == "scale":
                    _cap_buf  = io.BytesIO(capacity_file.read())  # type: ignore[union-attr]
                    _perf_buf = io.BytesIO(perf_file.read()) if perf_file else None
                    project = parse_scale_project(
                        _csv_buf, _cap_buf,
                        performance_xlsx_source=_perf_buf,
                    )
                    # Auto deal type for Scale — sync selectbox widget key too
                    _scale_dt_label = next((d[1] for d in DEAL_TYPES if d[0] == "ai_gpu"), "ai_gpu")
                    st.session_state["deal_type"]     = "ai_gpu"
                    st.session_state["sel_deal_type"] = _scale_dt_label
                else:
                    # FlashSystem + SAN path
                    # Always try to parse SAN switches from the CSV
                    _csv_buf.seek(0)
                    _san_switches = parse_san_csv(_csv_buf)
                    _csv_buf.seek(0)

                    if capacity_file is not None:
                        _cap_buf  = io.BytesIO(capacity_file.read())
                        _perf_buf = io.BytesIO(perf_file.read()) if perf_file else None
                        project = parse_project(
                            _csv_buf, _cap_buf,
                            performance_xlsx_source=_perf_buf,
                        )
                    else:
                        # CSV-only path — no XLSX available
                        project = parse_project_csv_only(_csv_buf)

                    # Attach SAN switch data (may be empty list if no switches)
                    project["san_switches"] = _san_switches

                    # ── Auto-set deal type based on what was loaded ─────────────────
                    _only_san = bool(_san_switches) and not bool(project.get("model_code", ""))
                    def _set_deal_type(key: str) -> None:
                        """Set both the state key and the selectbox widget key."""
                        label = next((d[1] for d in DEAL_TYPES if d[0] == key), key)
                        st.session_state["deal_type"]    = key
                        st.session_state["sel_deal_type"] = label  # drives selectbox
                    if _only_san:
                        _set_deal_type("san_refresh")
                    else:
                        _set_deal_type("vmware_cloud")

                    # ── Auto-set num_systems from SAN switch qty ────────────────────
                    # For SAN-only: num_systems = total qty of all switches
                    # For FS+SAN: keep num_systems = 1 (FS-based)
                    if _only_san and _san_switches:
                        _total_sw_qty = sum(sw.get("qty", 1) for sw in _san_switches)
                        if _total_sw_qty > 1:
                            st.session_state["num_systems"] = _total_sw_qty
                            st.session_state["num_systems_input"] = _total_sw_qty

                st.session_state["project_data"]   = project
                st.session_state["project_loaded"] = True
                st.rerun()
            except Exception as e:
                st.error(f"Parse error: {e}")
                st.exception(e)

    # show file-status hints
    if not csv_file:
        st.markdown(notif("info", "Upload your <b>e-config CSV</b> to begin."), unsafe_allow_html=True)
    elif not capacity_file and not _is_scale and not loaded:
        st.markdown(
            notif("info",
                  "CSV uploaded. Click <b>Parse Files</b> to continue with CSV-only mode "
                  "(Special Bid), or also upload Storage Modeller XLSX for full mode."),
            unsafe_allow_html=True,
        )
    elif not loaded:
        st.markdown(notif("info", "Files ready — click <b>Parse Files</b>."), unsafe_allow_html=True)
    else:
        _csv_only_flag = st.session_state.get("project_data", {}).get("_csv_only", False)
        _parsed_note = (
            "Parsed in <b>CSV-only mode</b> — capacity estimated from drives. "
            "Exec Summary and RFP require Storage Modeller XLSX."
            if _csv_only_flag else "Files parsed successfully. Continue below."
        )
        st.markdown(notif("ok" if not _csv_only_flag else "info", _parsed_note), unsafe_allow_html=True)

    # =========================================================================
    # STEP 2 — Project Details  (always visible, greyed-out when not loaded)
    # =========================================================================
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    section("Step 2 — Project Details")

    pd1, pd2, pd3 = st.columns([1, 1, 1], gap="large")

    with pd1:
        st.session_state["client_name"] = st.text_input(
            "Client / End-User Name",
            value=st.session_state["client_name"],
            placeholder="e.g. Acme Bank S.A.",
            disabled=not loaded,
        )
        _rep_opts = IBM_SALES_REPS
        _rep_idx  = (_rep_opts.index(st.session_state["seller_name"])
                     if st.session_state["seller_name"] in _rep_opts else 0)
        st.session_state["seller_name"] = st.selectbox(
            "Sales Representative",
            options=_rep_opts,
            index=_rep_idx,
            disabled=not loaded,
            key="sel_seller_step2",
        )

    with pd2:
        _dt_keys   = [d[0] for d in DEAL_TYPES]
        _dt_labels = [d[1] for d in DEAL_TYPES]
        _dt_idx    = (_dt_keys.index(st.session_state["deal_type"])
                      if st.session_state["deal_type"] in _dt_keys else 0)
        st.session_state["deal_type"] = _dt_keys[
            _dt_labels.index(
                st.selectbox(
                    "Deal Type / Workload Scenario",
                    options=_dt_labels,
                    index=_dt_idx,
                    disabled=not loaded,
                    key="sel_deal_type",
                    help="Selecting a scenario auto-fills texts in Special Bid and Executive Summary",
                )
            )
        ]
        _cur_dt_key = st.session_state["deal_type"]
        _cur_dt_desc = next((d[2] for d in DEAL_TYPES if d[0] == _cur_dt_key), "")
        if loaded and _cur_dt_desc:
            st.markdown(
                f'<div style="font-size:11px;color:var(--gray-70);line-height:1.45;'
                f'border-left:2px solid var(--blue-60);padding:4px 8px;margin:6px 0 10px;'
                f'background:#edf5ff">{_cur_dt_desc}</div>',
                unsafe_allow_html=True,
            )
        # Normalise due_date to a date object before setting the key
        _dd_raw = st.session_state["due_date"]
        if isinstance(_dd_raw, str) and _dd_raw:
            try:
                _dd_raw = datetime.strptime(_dd_raw, "%d %b %Y").date()
            except ValueError:
                _dd_raw = None
        if "due_date_input" not in st.session_state:
            st.session_state["due_date_input"] = _dd_raw
        st.date_input(
            "Bid / RFP Due Date",
            min_value=date.today(),
            format="DD/MM/YYYY",
            disabled=not loaded,
            help="Data zostanie wstawiona do Opportunity Context i tytułu oferty",
            key="due_date_input",
        )
        st.session_state["due_date"] = st.session_state["due_date_input"]
        _dd = st.session_state["due_date"]
        if loaded and _dd:
            _dd_str = _dd.strftime("%d %b %Y") if hasattr(_dd, "strftime") else str(_dd)
            _days_ahead = (_dd - date.today()).days if hasattr(_dd, "strftime") else 0
            if _days_ahead > 30:
                _validity_days = _days_ahead
                st.markdown(
                    notif(
                        "warn",
                        f"Due date <b>{_dd_str}</b> is <b>{_validity_days} days</b> from today — "
                        f"exceeds the standard 30-day bid validity. "
                        f"Provide a reason below; it will be included in the Special Bid questionnaire."
                    ),
                    unsafe_allow_html=True,
                )
                _vr_labels = [r[1] for r in EXTENDED_VALIDITY_REASONS]
                _vr_keys   = [r[0] for r in EXTENDED_VALIDITY_REASONS]
                _vr_cur    = st.session_state["bid_validity_reason"]
                _vr_idx    = (_vr_keys.index(_vr_cur) if _vr_cur in _vr_keys else 0)
                _vr_sel = st.selectbox(
                    "Extended validity reason",
                    options=_vr_labels,
                    index=_vr_idx,
                    disabled=not loaded,
                    key="sel_validity_reason",
                    help="Required when bid validity exceeds 30 days — sent to IBM pricers",
                )
                st.session_state["bid_validity_reason"] = (
                    _vr_keys[_vr_labels.index(_vr_sel)]
                )
                if not st.session_state["bid_validity_reason"]:
                    st.markdown(
                        notif("warn", "Select a reason to justify the extended validity period."),
                        unsafe_allow_html=True,
                    )
            else:
                st.markdown(
                    notif("info", f"Due date <b>{_dd_str}</b> will appear in all generated documents."),
                    unsafe_allow_html=True,
                )

    with pd3:
        # ── Price basis ───────────────────────────────────────────────────────
        _proj_pd3  = st.session_state.get("project_data") or {}
        _lp_pd3    = (
            _proj_pd3.get("list_price_hw", 0)
            + _proj_pd3.get("list_price_sw", 0)
            + _proj_pd3.get("list_price_support", 0)
        ) if loaded else 0.0
        _ship_pd3  = _proj_pd3.get("shipping", 0) if loaded else 0.0
        _nsys_pd3  = int(st.session_state.get("num_systems", 1))
        _curr_pd3  = _proj_pd3.get("currency", "EUR") if loaded else "EUR"

        # Detect config type for MEP labelling
        _pd3_san_switches = _proj_pd3.get("san_switches", []) if loaded else []
        _pd3_has_fs       = bool(_proj_pd3.get("model_code", "")) if loaded else False
        _pd3_san_only     = bool(_pd3_san_switches) and not _pd3_has_fs
        _pd3_fs_and_san   = _pd3_has_fs and bool(_pd3_san_switches)

        # Pre-compute SAN EU price for display (read-only, same discount_pct)
        _pd3_san_eu = 0.0
        if loaded and _pd3_san_switches:
            _d_pd3 = float(st.session_state.get("discount_pct", 60.0))
            for _sw_p in _pd3_san_switches:
                _sw_p_lp  = (_sw_p.get("list_price_hw", 0)
                           + _sw_p.get("list_price_sw", 0)
                           + _sw_p.get("list_price_support", 0))
                _sw_p_qty = _sw_p.get("qty", 1)
                _sw_p_sh  = _sw_p.get("shipping", 0.0)
                _pd3_san_eu += _sw_p_lp * _sw_p_qty * (1 - _d_pd3 / 100) + _sw_p_sh * _sw_p_qty

        # ── Callback helpers ─────────────────────────────────────────────────
        def _eu_from_disc(disc):
            """EU price = (lp × (1-d) + ship) × n   [discount applied directly to list → EU]"""
            if _lp_pd3 <= 0:
                return 0.0
            return round((_lp_pd3 * (1 - disc / 100) + _ship_pd3) * _nsys_pd3, 0)

        def _disc_from_eu(eu):
            """disc = (1 - (eu/n - ship) / lp) × 100"""
            if _lp_pd3 <= 0 or _nsys_pd3 <= 0:
                return st.session_state["discount_pct"]
            d = (1.0 - (eu / _nsys_pd3 - _ship_pd3) / _lp_pd3) * 100.0
            return round(max(5.0, min(95.0, d)), 1)

        def _on_disc_change():
            d   = float(st.session_state["disc_num"])
            m   = float(st.session_state.get("eu_margin_pct", 0.0))
            st.session_state["discount_pct"] = d
            # MEP = EU price = list × (1-d) + ship
            new_mep = _eu_from_disc(d)
            st.session_state["mep_input"]      = new_mep
            st.session_state["mep_text_input"] = f"{int(new_mep):,}".replace(",", " ")

        def _on_mep_change():
            mep = float(st.session_state["mep_input"])
            # MEP IS the EU price — derive discount from it directly
            d   = _disc_from_eu(mep)
            st.session_state["discount_pct"] = d
            st.session_state["disc_num"]     = d
            st.session_state["mep_input"]    = mep

        # ── Init / first-load ────────────────────────────────────────────────
        if "disc_num" not in st.session_state:
            st.session_state["disc_num"] = float(st.session_state["discount_pct"])
        # Init MEP = EU price from current discount
        _mep_from_disc = _eu_from_disc(st.session_state["discount_pct"])
        if "mep_input" not in st.session_state or (loaded and _mep_from_disc > 0 and st.session_state.get("mep_input", 0) == 0):
            st.session_state["mep_input"] = _mep_from_disc
            st.session_state["mep_text_input"] = f"{int(_mep_from_disc):,}".replace(",", " ")

        # Notif bar
        disc = float(st.session_state["discount_pct"])
        if loaded:
            if disc > 65:
                st.markdown(notif("warn", f"<b>{disc:.1f}%</b> — Special Bid questionnaire required."), unsafe_allow_html=True)
            elif disc > 60:
                st.markdown(notif("info", f"<b>{disc:.1f}%</b> — above standard 60% baseline."), unsafe_allow_html=True)
            else:
                st.markdown(notif("ok",   f"<b>{disc:.1f}%</b> — within standard baseline."), unsafe_allow_html=True)

        # MEP field — text input with currency formatting
        def _on_mep_text_change():
            raw = st.session_state.get("mep_text_input", "")
            cleaned = re.sub(r"[^\d.]", "", raw.replace(" ", "").replace(",", ""))
            try:
                val = float(cleaned) if cleaned else 0.0
            except ValueError:
                return
            st.session_state["mep_input"] = val
            _on_mep_change()
            # reformat display with thousand separators
            st.session_state["mep_text_input"] = f"{int(val):,}".replace(",", " ")

        _mep_display = f"{int(st.session_state.get('mep_input', 0)):,}".replace(",", " ")
        # MEP field label adapts to config type
        _mep_label = (
            f"Requested MEP — SAN ({_curr_pd3})"     if _pd3_san_only else
            f"Requested MEP — FlashSystem ({_curr_pd3})" if _pd3_fs_and_san else
            f"Requested MEP ({_curr_pd3})"
        )
        st.text_input(
            _mep_label,
            value=_mep_display,
            disabled=not loaded,
            help="Enter the requested MEP — Discount (%) updates automatically.",
            key="mep_text_input",
            on_change=_on_mep_text_change,
            placeholder="0",
        )

        # For FS+SAN: show SAN EU price read-only below FS MEP
        if loaded and _pd3_fs_and_san and _pd3_san_eu > 0:
            st.markdown(
                f'<div style="font-size:11px;color:var(--gray-70);margin:2px 0 6px;'
                f'border-left:3px solid var(--blue-60);padding:4px 8px;background:#f0f5ff;">'
                f'<b>SAN EU Price:</b> '
                f'<span style="font-weight:600;color:var(--gray-100)">'
                f'{_pd3_san_eu:,.0f} {_curr_pd3}</span>'
                f'&nbsp;·&nbsp;{sum(sw.get("qty",1) for sw in _pd3_san_switches)}× switch(es)'
                f'&nbsp;·&nbsp;same {float(st.session_state.get("discount_pct",60)):.1f}% discount'
                f'</div>',
                unsafe_allow_html=True,
            )

        # ── Systems / Discount / EU Margin — inside pd3, below MEP ──────────
        st.markdown(
            '<div style="font-size:11px;color:var(--gray-70);margin:8px 0 2px">Price adjustments</div>',
            unsafe_allow_html=True,
        )
        _ns_col2, _disc_col2, _em_col2 = st.columns(3, gap="small")

        with _ns_col2:
            if "num_systems_input" not in st.session_state:
                st.session_state["num_systems_input"] = int(st.session_state["num_systems"])

            def _on_systems_change():
                n = int(st.session_state["num_systems_input"])
                st.session_state["num_systems"] = n
                _proj_s  = st.session_state.get("project_data") or {}
                _lp_s    = (_proj_s.get("list_price_hw", 0)
                          + _proj_s.get("list_price_sw", 0)
                          + _proj_s.get("list_price_support", 0))
                _ship_s  = _proj_s.get("shipping", 0)
                d = float(st.session_state["discount_pct"])
                new_mep = round((_lp_s * (1 - d / 100) + _ship_s) * n, 0)
                st.session_state["mep_input"]      = new_mep
                st.session_state["mep_text_input"] = f"{int(new_mep):,}".replace(",", " ")

            st.number_input(
                "Systems",
                min_value=1, max_value=99,
                step=1,
                disabled=not loaded,
                help="Multiplies total price. When > 1, a note is added to the Exec Summary.",
                key="num_systems_input",
                on_change=_on_systems_change,
            )
            st.session_state["num_systems"] = st.session_state["num_systems_input"]

        with _disc_col2:
            st.number_input(
                "Discount (%)",
                min_value=5.0, max_value=95.0,
                step=0.5,
                format="%.1f",
                disabled=not loaded,
                key="disc_num",
                on_change=_on_disc_change,
            )

        with _em_col2:
            if "eu_margin_pct_input" not in st.session_state:
                st.session_state["eu_margin_pct_input"] = float(st.session_state["eu_margin_pct"])

            def _on_margin_change():
                m = float(st.session_state["eu_margin_pct_input"])
                st.session_state["eu_margin_pct"] = m
                # EU price = list*(1-d)+ship stays fixed when margin changes;
                # margin only affects how BP is split from EU — no need to update MEP

            st.number_input(
                "EU Margin (%)",
                min_value=0.0, max_value=100.0,
                step=0.5,
                format="%.1f",
                disabled=not loaded,
                help="Partner margin deducted from EU price to get BP price.",
                key="eu_margin_pct_input",
                on_change=_on_margin_change,
            )
            st.session_state["eu_margin_pct"] = st.session_state["eu_margin_pct_input"]

    # =========================================================================
    # STEP 3 — only shown after parsing
    # =========================================================================
    if not loaded:
        st.markdown("<br>", unsafe_allow_html=True)

        # Welcome feature tiles
        section("What You Can Generate")
        wc1, wc2, wc3 = st.columns(3, gap="large")
        tiles = [
            ("📋", "Executive Summary",
             "Professional DOCX with IBM branding, product photo, full technical specification and pricing. Valid 30 days.",
             "ibm-tag-blue", "Available"),
            ("📝", "Technical RFP / RFI",
             "Requirements table (18 rows) with your exact config values — capacity, RAID, ports, cache, support SLA.",
             "ibm-tag-blue", "Available"),
            ("💼", "Special Bid Request",
             "Pre-filled HW Special Bid questionnaire (sections A/B/C). Pricing auto-calculated. ~40% less manual work.",
             "ibm-tag-blue", "Available"),
        ]
        for col, (icon, title, body, tag_cls, tag_txt) in zip([wc1, wc2, wc3], tiles):
            with col:
                st.markdown(f"""
<div class="ibm-feature">
  <span class="ibm-feature-icon">{icon}</span>
  <div class="ibm-feature-title">{title}</div>
  <div class="ibm-feature-body">{body}</div>
  <span class="ibm-tag {tag_cls}">{tag_txt}</span>
</div>""", unsafe_allow_html=True)
        st.stop()

    # ── Project is loaded — show metrics + generators ─────────────────────
    project      = st.session_state["project_data"]
    model_code   = project.get("model_code", "")
    model_info   = get_model_info(model_code)
    client_name  = st.session_state["client_name"]
    seller_name  = st.session_state["seller_name"]
    discount_pct = st.session_state["discount_pct"]
    deal_type    = st.session_state["deal_type"]
    _dd_raw      = st.session_state["due_date"]
    due_date     = _dd_raw.strftime("%d %b %Y") if hasattr(_dd_raw, "strftime") else (str(_dd_raw) if _dd_raw else "")

    # Resolve deal-type description for use in auto-generated texts
    _dt_map      = {d[0]: (d[1], d[2]) for d in DEAL_TYPES}
    _deal_label, _deal_desc = _dt_map.get(deal_type, ("", ""))

    # ── Drive label (reused in metrics + Special Bid hints) ──────────────
    _drive_raw   = project.get("drive_type", "FCM5")
    _dm          = re.match(r"([\d.]+)\s*TB\s+Flash\w+\s+Module\s+(\d+)", _drive_raw, re.IGNORECASE)
    _drive_short = f"{_dm.group(1)} TB FCM{_dm.group(2)}" if _dm else _drive_raw

    # ── SAN switches from parsed project data ────────────────────────────
    _san_switches = project.get("san_switches", [])
    _has_san      = bool(_san_switches)
    _has_fs       = bool(project.get("model_code", ""))

    # ── Metrics strip — pure HTML grid, equal height guaranteed ──────────
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if _has_fs and _has_san:
        section("Configuration at a Glance — FlashSystem")
    elif _has_san and not _has_fs:
        section("Configuration at a Glance — SAN")
    else:
        section("Configuration at a Glance")

    _drive_qty  = project.get("drives_count", 0)
    _drive_disp = re.match(r"([\d.]+)\s*TB", _drive_raw)
    iops_sub1   = project.get("perf_iops_max_sub1ms", 0)
    lat_sub1    = project.get("perf_latency_at_max_sub1ms", 0.0)
    bw_sub1     = project.get("perf_bandwidth_sub1ms", 0.0)
    _num_sys    = int(st.session_state.get("num_systems", 1))
    _eu_margin  = float(st.session_state.get("eu_margin_pct", 15.0))
    lp          = (project.get("list_price_hw",0)
                 + project.get("list_price_sw",0)
                 + project.get("list_price_support",0))
    _shipping   = project.get("shipping", 0)
    # EU price = list × (1 - discount%) + shipping  [discount applied to list → EU directly]
    _eu         = float(st.session_state.get("mep_input") or
                        (lp * (1 - discount_pct / 100) + _shipping) * _num_sys)
    # BP = EU × (1 - margin%)
    _bp         = _eu * (1 - _eu_margin / 100) if _eu_margin > 0 else _eu
    _curr       = project.get("currency", "EUR")
    _sup_info    = project.get("support_info") or {}
    _sup_name    = _sup_info.get("name", "—")
    _sup_years   = _sup_info.get("years", "—")
    _sup_fix     = _sup_info.get("fix_time_hours", "")
    _sup_fix_str = f"· {_sup_fix}" if _sup_fix else ""

    def _tile(label, value, delta=""):
        d = f'<div class="ibm-metric-delta">{delta}</div>' if delta else ""
        return (f'<div class="ibm-metric">'
                f'<div class="ibm-metric-label">{label}</div>'
                f'<div class="ibm-metric-value">{value}</div>'
                f'{d}</div>')

    _is_scale_view = (st.session_state.get("product_line") == "scale")

    if _is_scale_view:
        # ── Storage Scale kafelki ─────────────────────────────────────────
        _sc_data_nodes  = project.get("num_data_nodes", 1) or 1
        _sc_proto_nodes = project.get("num_protocol_nodes", 0)
        _sc_cache_lbl   = project.get("cache_label", "")
        _sc_cache_gb    = project.get("cache_gb", 0)
        _sc_ib_n        = project.get("ib_adapters", 0)
        _sc_ib_desc     = project.get("ib_adapter_desc", "IB NDR adapter")
        _sc_bw_r        = project.get("throughput_read_gbs",  0.0)
        _sc_bw_w        = project.get("throughput_write_gbs", 0.0)
        _sc_bw_r_gibs   = project.get("throughput_read_gibs",  0.0)
        _sc_bw_w_gibs   = project.get("throughput_write_gibs", 0.0)
        _sc_has_hdd     = project.get("has_hdd_shelf", False)
        _sc_hdd_raw_tb  = project.get("hdd_raw_tb",  0.0)
        _sc_hdd_raw_tib = project.get("hdd_raw_tib", 0.0)
        _sc_hdd_type    = project.get("hdd_drive_type", "")
        _sc_hdd_cnt     = project.get("hdd_drives_count", 0)
        _sc_labs_qty    = project.get("expert_labs_qty", 0)
        _sc_labs_price  = project.get("expert_labs_price", 0.0)
        _sc_labs_desc   = project.get("expert_labs_desc", "")

        # Utility node summary for tile
        # Protocol Node qty comes from SYSTEM SUMMARY "System Quantity" line
        _sc_util = project.get("utility_nodes", [])
        if _sc_util:
            _sc_util_parts = []
            for u in _sc_util:
                _u_qty = u["qty"]
                # Override Protocol Node qty with value from SYSTEM SUMMARY
                if "Protocol" in u["type"] and _sc_proto_nodes > 0:
                    _u_qty = _sc_proto_nodes
                _sc_util_parts.append(
                    f"{_u_qty} × {u['type'].replace('Protocol Node','Protocol').replace('Management Server','Mgmt')}"
                )
            _sc_util_str = " + ".join(_sc_util_parts)
            _sc_util_detail = ", ".join(
                f"{u['qty']} × {u['mtm']}" + (f" ({u['memory']})" if u["memory"] else "")
                for u in _sc_util
            )
        else:
            _sc_util_str    = (f"{_sc_proto_nodes} × Protocol" if _sc_proto_nodes else "—")
            _sc_util_detail = ""

        # Drive label for Scale — NVMe drives only (HDD shown in separate tile)
        _sc_nvme_qty  = project.get("drives_per_node", 0) or _drive_qty
        _sc_drive_lbl = (f"{_sc_nvme_qty} × {_drive_disp.group(1)} TB NVMe"
                         if _drive_disp else f"{_sc_nvme_qty} × {_drive_raw}")

        # Model tile — show short name (ESS3500) + MTM
        _sc_model_short = model_info.get("short", model_info.get("name", model_code))
        _sc_model_name  = model_info.get("name", model_code)

        # HDD shelf tile
        _hdd_tile = ""
        if _sc_has_hdd and _sc_hdd_cnt:
            _hdd_cnt_str  = f"{_sc_hdd_cnt} × {_sc_hdd_type.split(' ')[0]} HDD" if _sc_hdd_type else f"{_sc_hdd_cnt} × HDD"
            _hdd_cap_str  = f"{_sc_hdd_raw_tib:.1f} TiB" if _sc_hdd_raw_tib else "—"
            _hdd_cap_sub  = f"{_sc_hdd_raw_tb:.0f} TB raw · 4U102 shelf"
            _hdd_tile     = _tile("HDD Shelf Capacity", _hdd_cap_str, _hdd_cap_sub)

        # Expert Labs tile
        _labs_tile = ""
        if _sc_labs_qty:
            _labs_val  = f"{_sc_labs_qty} × Project Unit"
            _labs_sub  = f"{_sc_labs_price:,.0f} {_curr} · Onsite" if _sc_labs_price else "Onsite"
            _labs_tile = _tile("Expert Labs", _labs_val, _labs_sub)

        st.markdown(
            '<div class="ibm-metric-row">'
            + _tile("Model",
                    _sc_model_short,
                    f"{_sc_data_nodes} data node(s) · {_sc_model_name} · {model_code}")
            + _tile("NVMe Drives",
                    _sc_drive_lbl,
                    project.get("drive_type", "—"))
            + _tile("Raw",
                    f"{project.get('raw_tib',0):.1f} TiB",
                    f"{project.get('raw_tb',0):.1f} TB")
            + _tile("Usable",
                    f"{project.get('usable_tib',0):.1f} TiB",
                    f"{project.get('usable_tb',0):.1f} TB · {project.get('raid_type','Erasure Code')}")
            + _hdd_tile
            + _tile("Cache (data node)",
                    f"{_sc_cache_gb} GB" if _sc_cache_gb else "—",
                    _sc_cache_lbl or "DDR4")
            + _tile("Protocol Node",
                    _sc_util_str,
                    _sc_util_detail)
            + _tile("IB Adapters",
                    f"{_sc_ib_n} × adapter" if _sc_ib_n else "—",
                    _sc_ib_desc[:40] if _sc_ib_desc else "")
            + _tile("Support", _sup_name,
                    f"{_sup_years} yr{' ' + _sup_fix_str if _sup_fix_str else ''}" if _sup_years != "—" else "—")
            + _labs_tile
            + _tile("Max Read Bandwidth",
                    f"{_sc_bw_r:.2f} GB/s" if _sc_bw_r else "—",
                    f"{_sc_bw_r_gibs:.2f} GiB/s" if _sc_bw_r else "upload modeller file")
            + _tile("Max Write Bandwidth",
                    f"{_sc_bw_w:.2f} GB/s" if _sc_bw_w else "—",
                    f"{_sc_bw_w_gibs:.2f} GiB/s" if _sc_bw_w else "")
            + _tile("BP Price", f"{_bp:,.0f} {_curr}",
                    f"{_num_sys} × system" if _num_sys > 1 else "")
            + _tile("End User Price", f"{_eu:,.0f} {_curr}",
                    "= Requested MEP")
            + '</div>',
            unsafe_allow_html=True,
        )
    elif _has_fs:
        # ── FlashSystem kafelki ───────────────────────────────────────────
        _is_hybrid    = project.get("is_hybrid", False)
        _drive_lbl    = (f"{_drive_qty} × {_drive_disp.group(1)} TB FCM"
                         if _drive_disp else f"{_drive_qty} × {_drive_raw}")
        _drive_tile_lbl = "FCM Drives" if _is_hybrid else "Drives"
        _eff_tib      = project.get("effective_tib", 0.0)
        _eff_tb       = project.get("effective_tb", 0.0)
        _comp_pct     = project.get("compression_pct", 0.0)
        _dedup_pct    = project.get("dedup_pct", 0.0)
        # Correct ratio formula: X% savings → ratio = 1 / (1 - X/100)
        # e.g. 50% compression → 2:1, 67% → 3:1
        # Combined savings are additive (capped at 99% to avoid div/0)
        _dr_savings   = min(_comp_pct + _dedup_pct, 99.0) / 100.0
        _dr_ratio     = (1.0 / (1.0 - _dr_savings)) if _dr_savings > 0 else 1.0
        _dr_str       = f"{_dr_ratio:.2f}:1"
        _dr_detail    = f"Compr {_comp_pct:.0f}% · Dedup {_dedup_pct:.0f}%"

        # HDD tier — only when hdd_drives_count > 0 (guards against is_hybrid=True with no actual HDD data)
        _hdd_cnt     = project.get("hdd_drives_count", 0)
        _has_hdd     = _is_hybrid and _hdd_cnt > 0
        _hdd_tile_fs = ""
        if _has_hdd:
            _hdd_dt       = project.get("hdd_drive_type", "")
            _hdd_raw_tib  = project.get("hdd_raw_tib",  0.0)
            _hdd_raw_tb   = project.get("hdd_raw_tb",   0.0)
            _hdd_use_tib  = project.get("hdd_usable_tib", 0.0)
            _hdd_use_tb   = project.get("hdd_usable_tb",  0.0)
            _hdd_enc      = project.get("hdd_enclosure", "")
            _hdd_cap_m    = re.match(r"([\d.]+\s*TB)", _hdd_dt)
            _hdd_drv_lbl  = (f"{_hdd_cnt} × {_hdd_cap_m.group(1)} NL-SAS"
                             if _hdd_cap_m and _hdd_cnt else f"{_hdd_cnt} × HDD")
            _hdd_raw_str  = f"{_hdd_raw_tib:.1f} TiB" if _hdd_raw_tib else "—"
            _hdd_tile_fs  = (_tile("HDD Drives",  _hdd_drv_lbl, _hdd_dt[:35] if _hdd_dt else "")
                           + _tile("HDD Raw",     _hdd_raw_str, f"{_hdd_raw_tb:.1f} TB")
                           + _tile("HDD Usable",  f"{_hdd_use_tib:.1f} TiB" if _hdd_use_tib else "—",
                                                  f"{_hdd_use_tb:.1f} TB · DRAID6"))

        _raw_lbl    = "Full Raw Space"              if _has_hdd else "Raw"
        _usable_lbl = "Full Usable Space (SSD+HDD)" if _has_hdd else "Usable"
        _raw_sub    = f"{project.get('raw_tb',0):.1f} TB · SSD + HDD" if _has_hdd else f"{project.get('raw_tb',0):.1f} TB"
        _use_sub    = f"{project.get('usable_tb',0):.1f} TB · {project.get('raid_type','DRAID6')}"

        st.markdown(
            '<div class="ibm-metric-row">'
            + _tile("Model", model_info.get("short", model_code),
                    model_info.get("name", model_code))
            + _tile(_drive_tile_lbl, _drive_lbl, _drive_short)
            + _tile(_raw_lbl,    f"{project.get('raw_tib',0):.1f} TiB", _raw_sub)
            + _tile(_usable_lbl, f"{project.get('usable_tib',0):.1f} TiB", _use_sub)
            + _hdd_tile_fs
            + _tile("Effective", f"{_eff_tib:.1f} TiB" if _eff_tib else "—",
                                 f"{_eff_tb:.1f} TB" if _eff_tb else "upload capacity file")
            + (""  if _has_hdd else
               _tile("Data Reduction", _dr_str if (_comp_pct or _dedup_pct) else "—",
                     _dr_detail if (_comp_pct or _dedup_pct) else ""))
            + _tile("Cache", f"{project.get('cache_gb', 0)} GB" if project.get('cache_gb') else "—",
                    "per I/O group")
            + _tile("Support", _sup_name,
                    f"{_sup_years} yr{' ' + _sup_fix_str if _sup_fix_str else ''}" if _sup_years != "—" else "—")
            + _tile("Workload IOPS &lt;1ms",
                    f"{iops_sub1:,}" if iops_sub1 else "—",
                    f"{lat_sub1:.3f} ms" if iops_sub1 else "upload perf file")
            + _tile("Bandwidth &lt;1ms",
                    f"{bw_sub1:,.0f} MiB/s" if bw_sub1 else "—",
                    f"at {iops_sub1:,} IOPS" if bw_sub1 else "")
            + _tile("BP Price", f"{_bp:,.0f} {_curr}",
                    f"{_num_sys} × system" if _num_sys > 1 else "")
            + _tile("End User Price", f"{_eu:,.0f} {_curr}",
                    "= Requested MEP")
            + '</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── SAN Configuration at a Glance (only when SAN switches are present) ─
    if _has_san:
        if _has_fs:
            section("Configuration at a Glance — SAN")
        # build one tile per unique switch model, grouped by model_code
        # collect switches — deduplicate by model_code, sum qty
        _san_grouped: dict[str, dict] = {}
        for _sw in _san_switches:
            _k = _sw["model_code"]
            if _k not in _san_grouped:
                _san_grouped[_k] = dict(_sw)
            else:
                _san_grouped[_k]["qty"] += _sw["qty"]
                # accumulate price
                for _pf in ("list_price_hw", "list_price_sw", "list_price_support",
                            "list_price_total", "shipping"):
                    _san_grouped[_k][_pf] = (
                        _san_grouped[_k].get(_pf, 0.0) + _sw.get(_pf, 0.0)
                    )

        for _sw_data in _san_grouped.values():
            _sw_qty          = _sw_data.get("qty", 1)
            _sw_name         = _sw_data.get("switch_short", _sw_data.get("model_code", ""))
            _sw_model        = _sw_data.get("model_code", "")
            _sw_brocade      = _sw_data.get("brocade_model", "")
            _sw_exhaust      = _sw_data.get("exhaust", "")
            _sw_exhaust_str  = f" · {_sw_exhaust} exhaust" if _sw_exhaust else ""
            _sw_form         = _sw_data.get("form_factor", "")
            _sw_max_ports    = _sw_data.get("max_ports", 0)
            _sw_active_ports = _sw_data.get("active_ports", 0)
            _sw_speed        = _sw_data.get("port_speed_gbps", 0)
            _sw_sup_info     = _sw_data.get("support_info") or {}
            _sw_sup_name     = _sw_sup_info.get("name", "—")
            _sw_sup_yrs      = _sw_sup_info.get("years", "—")
            _sw_sup_fix      = _sw_sup_info.get("fix_time_hours", "")
            _sw_sup_fix_str  = f" · {_sw_sup_fix}" if _sw_sup_fix else ""
            _sw_lp_hw        = _sw_data.get("list_price_hw", 0.0)
            _sw_lp_sup       = _sw_data.get("list_price_support", 0.0)
            _sw_lp_sw        = _sw_data.get("list_price_sw", 0.0)
            _sw_ship         = _sw_data.get("shipping", 0.0)
            _sw_curr         = _sw_data.get("currency", _curr)
            # For SAN-only: honour num_systems as additional multiplier so the
            # price tiles update when the user edits "Systems" in Step 2.
            # _sw_qty already reflects the qty from the parsed config (e.g. 2× SAN64B-7);
            # num_systems acts as a further "how many of this config" multiplier.
            _sw_ns_mult      = _num_sys if not _has_fs else 1
            _sw_lp_total     = (_sw_lp_hw + _sw_lp_sup + _sw_lp_sw) * _sw_qty * _sw_ns_mult
            _sw_eu           = _sw_lp_total * (1 - discount_pct / 100) + _sw_ship * _sw_qty * _sw_ns_mult
            _sw_bp           = _sw_eu * (1 - float(st.session_state.get("eu_margin_pct", 15.0)) / 100)

            # SANnav licenses tile
            _sw_sannav       = _sw_data.get("sannav_licenses", [])
            _sw_sannav_tile  = ""
            if _sw_sannav:
                _sv_names = []
                for _sv in _sw_sannav:
                    _sv_yrs  = _sv.get("years", 0)
                    _sv_desc = _sv.get("description", "")
                    _sv_short = _sv_desc.replace("IBM SANnav ", "")
                    _sv_yrs_s = f" ({_sv_yrs}Y)" if _sv_yrs else ""
                    _sv_qty   = _sv.get("qty", 1) if "qty" in _sv else 1
                    _sv_label = f"{_sv_qty}× {_sv_short}{_sv_yrs_s}" if _sv_qty > 1 else f"{_sv_short}{_sv_yrs_s}"
                    _sv_names.append(_sv_label)
                _sw_sannav_tile = _tile("SANnav Software",
                                        _sv_names[0] if len(_sv_names) == 1 else f"{len(_sv_names)} licenses",
                                        " · ".join(_sv_names) if len(_sv_names) > 1 else "")

            # Optics tiles — separate LW and SW/cable
            _sw_lw_qty      = _sw_data.get("lw_optics_qty", 0)
            _sw_swc_qty     = _sw_data.get("sw_optics_qty", 0)
            _sw_lw_tile     = ""
            _sw_swc_tile    = ""
            if _sw_lw_qty:
                _sw_lw_tile  = _tile("LW Optics (SFP)",
                                     f"{_sw_lw_qty} × LW SFP",
                                     "long-wave · 10 km · single-mode")
            if _sw_swc_qty:
                _sw_swc_tile = _tile("SW Cables / SFP",
                                     f"{_sw_swc_qty} × OM3 LC",
                                     "short-wave · multimode · ≤10 m")

            # Qty prefix for tile labels
            _qty_pfx = f"{_sw_qty} × " if _sw_qty > 1 else ""
            # Brocade model — own tile
            _sw_brocade_tile = ""
            if _sw_brocade:
                _sw_brocade_tile = _tile("OEM Platform",
                                         _sw_brocade,
                                         "IBM OEM — Brocade / Broadcom")

            st.markdown(
                '<div class="ibm-metric-row">'
                + _tile("Switch Model",
                        f"{_qty_pfx}{_sw_name}",
                        f"{_sw_model}{_sw_exhaust_str} · {_sw_form}")
                + _sw_brocade_tile
                + _tile("Active / Max Ports",
                        f"{_sw_active_ports} / {_sw_max_ports}",
                        f"port speed: {_sw_speed} Gbps FC")
                + _sw_lw_tile
                + _sw_swc_tile
                + _sw_sannav_tile
                + _tile("Support", _sw_sup_name,
                        f"{_sw_sup_yrs} yr{_sw_sup_fix_str}" if _sw_sup_yrs != "—" else "—")
                + _tile("Switch BP Price", f"{_sw_bp:,.0f} {_sw_curr}",
                        f"{_sw_qty * _sw_ns_mult} × switch" if _sw_qty * _sw_ns_mult > 1 else "")
                + _tile("Switch EU Price", f"{_sw_eu:,.0f} {_sw_curr}",
                        "= Requested MEP (switch only)" if not _has_fs else "switch total")
                + '</div>',
                unsafe_allow_html=True,
            )
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Data Profile + Settings — collapsed expanders under metrics ────────
    _pd_col, _st_col = st.columns(2, gap="large")
    with _pd_col:
        with st.expander("📊  Data Profile (workload + storage)", expanded=False):
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
            d1, d2 = st.columns(2, gap="large")
            with d1:
                section("Hardware")
                st.dataframe({"Parameter": [
                    "Model","Product Name","Firmware","I/O Groups","Enclosures",
                    "Drives","Drive Type","Drive Feature","Cache (GB)","FC Ports","Encryption","Cables",
                ], "Value": [
                    project.get("model_code","—"), model_info.get("name","—"),
                    project.get("product_version","—"), project.get("io_groups","—"),
                    project.get("enclosures","—"), project.get("drives_count","—"),
                    project.get("drive_type","—"), project.get("drive_feature","—"),
                    project.get("cache_gb","—"), project.get("fc_ports","—"),
                    "Yes" if project.get("encryption") else "No", project.get("cable_qty","—"),
                ]}, hide_index=True, use_container_width=True)

                section("Capacity")
                st.dataframe({"Parameter": [
                    "Raw (TB)","Raw (TiB)","Usable (TB)","Usable (TiB)",
                    "Effective (TB)","Effective (TiB)","Recommended Max (TiB)",
                    "RAID Type","Rebuild Areas","Pool",
                ], "Value": [
                    f"{project.get('raw_tb',0):.2f}",     f"{project.get('raw_tib',0):.2f}",
                    f"{project.get('usable_tb',0):.2f}",   f"{project.get('usable_tib',0):.2f}",
                    f"{project.get('effective_tb',0):.2f}", f"{project.get('effective_tib',0):.2f}",
                    f"{project.get('recommended_max_tib',0):.0f}",
                    project.get("raid_type","—"), project.get("rebuild_areas","—"), project.get("pool_type","—"),
                ]}, hide_index=True, use_container_width=True)

            with d2:
                section("Performance")
                if project.get("perf_iops_total"):
                    _pd_iops_sub1 = project.get("perf_iops_max_sub1ms", 0)
                    _pd_lat_sub1  = project.get("perf_latency_at_max_sub1ms", 0.0)
                    st.dataframe({"Parameter": [
                        "★ Max IOPS below 1 ms latency",
                        "  Latency at max sub-1ms IOPS",
                        "Workload IOPS (configured)",
                        "  Workload latency",
                        "Read IOPS","Write IOPS","Read %",
                        "Block Size (KiB)","Throughput (MiB/s)","Cache Hit %",
                    ], "Value": [
                        f"{_pd_iops_sub1:,}" if _pd_iops_sub1 else "—",
                        f"{_pd_lat_sub1:.3f} ms" if _pd_lat_sub1 else "—",
                        f"{project.get('perf_iops_total',0):,}",
                        f"{project.get('perf_latency_ms',0):.3f} ms",
                        f"{project.get('perf_iops_read',0):,}",
                        f"{project.get('perf_iops_write',0):,}",
                        f"{project.get('perf_read_pct',0):.0f}%",
                        project.get("perf_transfer_size_kib","—"),
                        f"{project.get('perf_throughput_mib',0):,.1f} MiB/s",
                        f"{project.get('perf_cache_hit_pct',0):.1f}%",
                    ]}, hide_index=True, use_container_width=True)
                else:
                    st.markdown(notif("warn","No performance file uploaded."), unsafe_allow_html=True)

                section("Pricing")
                _pd_curr = project.get("currency","EUR")
                st.dataframe({"Parameter": [
                    "Currency","Price File","Config ID",
                    f"List HW ({_pd_curr})", f"List Support ({_pd_curr})",
                    f"List SW ({_pd_curr})", f"Shipping ({_pd_curr})",
                ], "Value": [
                    _pd_curr, project.get("price_file_date","—"), project.get("config_id","—"),
                    f"{project.get('list_price_hw',0):,.2f}",
                    f"{project.get('list_price_support',0):,.2f}",
                    f"{project.get('list_price_sw',0):,.2f}",
                    f"{project.get('shipping',0):,.2f}",
                ]}, hide_index=True, use_container_width=True)

                section("Environment")
                st.dataframe({"Parameter": [
                    "Rack Units","Power Typical (kW)","Power Max (kW)","Cooling (BTU/h)"
                ], "Value": [
                    project.get("rack_units","—"),
                    f"{project.get('power_kw_typical',0):.3f}",
                    f"{project.get('power_kw_max',0):.3f}",
                    f"{project.get('cooling_btu',0):,.0f}",
                ]}, hide_index=True, use_container_width=True)

    with _st_col:
        with st.expander("⚙️  Settings & Overrides", expanded=False):
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
            s1c, s2c = st.columns(2, gap="large")
            with s1c:
                section("Document Settings")
                st.markdown(notif("info","Language: <b>English</b> — Polish option coming soon."), unsafe_allow_html=True)
                _st_img = model_info.get("image","N/A")
                st.markdown(f"""
| Asset | Path |
|---|---|
| IBM Logo | `app/assets/logos/IBM_logo.svg` |
| Product image | `app/assets/images/{_st_img}` |
""")

                section("Manual Data Override")
                st.markdown(
                    '<div style="font-size:12px;color:var(--gray-70);margin-bottom:8px">'
                    'Correct values parsed from files if needed (cache, FC ports, IOPS).</div>',
                    unsafe_allow_html=True,
                )
                _ov1, _ov2 = st.columns(2)
                with _ov1:
                    _cache_ov = st.number_input(
                        "Cache (GB) override",
                        min_value=0, max_value=4096,
                        value=int(project.get("cache_gb", 0)),
                        step=64, key="ov_cache",
                    )
                    _fc_ov = st.number_input(
                        "FC Ports override",
                        min_value=0, max_value=64,
                        value=int(project.get("fc_ports", 0)),
                        step=2, key="ov_fc",
                    )
                with _ov2:
                    _iops_ov = st.number_input(
                        "IOPS override",
                        min_value=0, max_value=10_000_000,
                        value=int(project.get("perf_iops_total", 0)),
                        step=10_000, key="ov_iops",
                    )
                    _enc_ov = st.checkbox(
                        "Encryption enabled",
                        value=bool(project.get("encryption", True)),
                        key="ov_enc",
                    )
                if st.button("Apply Overrides →", type="primary", key="btn_apply_ov"):
                    project["cache_gb"]        = _cache_ov
                    project["fc_ports"]        = _fc_ov
                    project["perf_iops_total"] = _iops_ov
                    project["encryption"]      = _enc_ov
                    st.session_state["project_data"] = project
                    st.markdown(notif("ok", "Overrides applied. Re-generate documents to use new values."),
                                unsafe_allow_html=True)

            with s2c:
                section("Debug — Raw JSON")
                with st.expander("Show parsed project data"):
                    safe = {k: v for k, v in project.items()
                            if isinstance(v, (str,int,float,bool,list,dict,type(None)))}
                    st.json(safe)

                section("Extreme Discount Warning")
                if discount_pct >= 75:
                    st.markdown(notif("warn",
                        f"<b>{discount_pct:.1f}%</b> discount is an extreme deviation "
                        f"({discount_pct - 60:.1f} pp above baseline). "
                        "Ensure full business justification is documented in Special Bid tab."),
                        unsafe_allow_html=True)
                else:
                    st.markdown(notif("ok", "Discount within acceptable range (< 75%)."),
                                unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Custom tab bar (Streamlit buttons inside .ibm-tabbar wrapper) ────
    _TABS_MAIN = [
        ("exec",     "📋  Executive Summary"),
        ("rfp",      "📝  RFP / RFI"),
        ("bid",      "💼  Special Bid"),
        ("projects", "🗂️  Projects"),
    ]
    _at = st.session_state["active_tab"]

    # ── Primary tab bar (4 main outputs) ──────────────────────────────────
    st.markdown('<div class="ibm-tabbar-row">', unsafe_allow_html=True)
    _tab_cols = st.columns(len(_TABS_MAIN))
    for _col, (_key, _label) in zip(_tab_cols, _TABS_MAIN):
        with _col:
            _is_active = (_at == _key)
            if st.button(_label, key=f"tab_btn_{_key}",
                         use_container_width=True,
                         type="primary" if _is_active else "secondary"):
                st.session_state["active_tab"] = _key
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    _at = st.session_state["active_tab"]

    # =====================================================================
    # TAB — Executive Summary
    # =====================================================================
    if _at == "exec":
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

        t1_left, t1_right = st.columns([1, 1], gap="large")

        with t1_left:
            _exec_san_only = bool(project.get("san_switches")) and not bool(project.get("model_code", ""))
            iops_manual = 0
            if not _exec_san_only:
                section("Performance Data")
                iops_from_file = project.get("perf_iops_total", 0)
                iops_sub1      = project.get("perf_iops_max_sub1ms", 0)
                lat_sub1       = project.get("perf_latency_at_max_sub1ms", 0.0)
                if not iops_from_file:
                    st.markdown(notif("warn", "No performance file — enter IOPS manually."), unsafe_allow_html=True)
                    iops_manual = st.number_input(
                        "IOPS (manual entry)",
                        min_value=0, max_value=10_000_000,
                        value=st.session_state["iops_manual"], step=10_000,
                    )
                    st.session_state["iops_manual"] = iops_manual
                else:
                    sub1_str = f" &nbsp;|&nbsp; Max below 1 ms: <b>{iops_sub1:,} IOPS @ {lat_sub1:.3f} ms</b>" if iops_sub1 else ""
                    st.markdown(
                        notif("ok", f"Workload: <b>{iops_from_file:,} IOPS</b> · {project.get('perf_latency_ms',0):.3f} ms{sub1_str}"),
                        unsafe_allow_html=True,
                    )

            section("Pricing Preview")
            list_hw   = project.get("list_price_hw", 0)
            list_sw   = project.get("list_price_sw", 0)
            list_sup  = project.get("list_price_support", 0)
            ship      = project.get("shipping", 0)
            d         = discount_pct / 100
            curr      = project.get("currency", "EUR")
            n_sys     = int(st.session_state.get("num_systems", 1))
            eu_margin = float(st.session_state.get("eu_margin_pct", 15.0))
            m         = 1 - eu_margin / 100
            # EU = list × (1-d), BP = EU × (1-margin)
            eu_hw     = list_hw*(1-d) * n_sys
            eu_sw     = list_sw*(1-d) * n_sys
            eu_sup    = list_sup*(1-d) * n_sys
            eu_ship   = ship * n_sys
            eu_tot    = eu_hw + eu_sw + eu_sup + eu_ship
            bp_hw     = eu_hw  * m
            bp_sw     = eu_sw  * m
            bp_sup    = eu_sup * m
            bp_ship   = eu_ship          # shipping passes through without margin
            bp_tot    = bp_hw + bp_sw + bp_sup + bp_ship
            list_tot  = (list_hw+list_sw+list_sup+ship) * n_sys

            st.dataframe({
                "Category": ["Hardware", "Support", "Software", "Shipping", "TOTAL"],
                f"List ({curr})": [
                    f"{list_hw*n_sys:,.2f}", f"{list_sup*n_sys:,.2f}", f"{list_sw*n_sys:,.2f}",
                    f"{ship*n_sys:,.2f}", f"{list_tot:,.2f}",
                ],
                f"EU Price @ {discount_pct:.0f}% ({curr})": [
                    f"{eu_hw:,.2f}", f"{eu_sup:,.2f}",
                    f"{eu_sw:,.2f}", f"{eu_ship:,.2f}", f"{eu_tot:,.2f}",
                ],
                f"BP Price (EU×{1-eu_margin/100:.2f}) ({curr})": [
                    f"{bp_hw:,.2f}", f"{bp_sup:,.2f}",
                    f"{bp_sw:,.2f}", f"{bp_ship:,.2f}", f"{bp_tot:,.2f}",
                ],
            }, hide_index=True, use_container_width=True)
            _sys_label = f"{n_sys} × {model_info.get('short', model_code)}" if n_sys > 1 else model_info.get('short', model_code)
            if n_sys > 1:
                st.markdown(notif("info", f"End User Price covers <b>{n_sys} systems</b> ({_sys_label}) combined."), unsafe_allow_html=True)
            else:
                st.markdown(notif("info", f"End User Price for <b>1 system</b> ({_sys_label})."), unsafe_allow_html=True)

            valid_date = (date.today() + timedelta(days=30)).strftime("%d %b %Y")
            st.markdown(notif("info", f"Offer valid until <b>{valid_date}</b> (30 days from today)."), unsafe_allow_html=True)

        with t1_right:
            section("Detected Support Package")
            sup  = project.get("support_info") or {}
            _fix_time_val = (
                sup.get("fix_time_hours") or "Yes — committed fix-time"
                if sup.get("fix_time") else "No fix-time SLA"
            )
            st.markdown(f"""
| Parameter | Value |
|---|---|
| Package | {sup.get('name','Not detected')} |
| Level | {sup.get('level','—')} |
| Coverage | {sup.get('coverage','—')} |
| Fix-time SLA | {_fix_time_val} |
| Duration | {sup.get('years','—')} year(s) |
""")

            missing = []
            if not client_name: missing.append("Client name")
            if not seller_name: missing.append("Sales representative")
            if missing:
                st.markdown(notif("warn", "Fill in " + ", ".join(missing) + " in Step 2 above."), unsafe_allow_html=True)

            section("Generate")
            _exec_lang_opts = {"English": "en", "Polski": "pl"}
            _exec_lang_cur  = st.session_state["exec_lang"]
            _exec_lang_lbl  = next(k for k, v in _exec_lang_opts.items() if v == _exec_lang_cur)
            _exec_lang_sel  = st.radio(
                "Document language",
                options=list(_exec_lang_opts.keys()),
                index=list(_exec_lang_opts.keys()).index(_exec_lang_lbl),
                horizontal=True,
                key="radio_exec_lang",
            )
            st.session_state["exec_lang"] = _exec_lang_opts[_exec_lang_sel]

            if st.button("Generate Executive Summary DOCX →", type="primary", use_container_width=True):
                with st.spinner("Generating…"):
                    try:
                        _gen_fn = (generate_scale_exec_summary
                                   if st.session_state["product_line"] == "scale"
                                   else generate_exec_summary)
                        _gen_kwargs = dict(
                            project=project,
                            client_name=client_name,
                            seller_name=seller_name,
                            discount_pct=discount_pct,
                            lang=st.session_state["exec_lang"],
                            num_systems=int(st.session_state.get("num_systems", 1)),
                            eu_margin_pct=float(st.session_state.get("eu_margin_pct", 15.0)),
                        )
                        if st.session_state["product_line"] != "scale":
                            _gen_kwargs["iops_override"] = iops_manual if iops_manual > 0 else None
                        docx_bytes = _gen_fn(**_gen_kwargs)
                        slug = re.sub(r"[^\w]", "_", client_name) if client_name else "Client"
                        _lang_sfx = "_PL" if st.session_state["exec_lang"] == "pl" else ""
                        fname = f"ExecSummary_{model_info.get('short',model_code)}_{slug}_{date.today():%Y%m%d}{_lang_sfx}.docx"
                        st.session_state["exec_bytes"]    = docx_bytes
                        st.session_state["exec_filename"] = fname
                        st.markdown(notif("ok", f"Ready: <b>{fname}</b>"), unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Error: {e}")
                        st.exception(e)

            if st.session_state["exec_bytes"]:
                st.download_button(
                    "⬇  Download .docx",
                    data=st.session_state["exec_bytes"],
                    file_name=st.session_state["exec_filename"],
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                )


    # =====================================================================
    # =====================================================================
    # TAB — RFP / RFI
    # =====================================================================
    if _at == "rfp":
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        r1_left, r1_right = st.columns([1, 1], gap="large")

        with r1_left:
            section("RFP Information")
            _rfp_san_only = bool(project.get("san_switches")) and not bool(project.get("model_code", ""))
            rfp_iops_manual    = 0
            rfp_iops_from_file = 0   # initialise; set below for non-SAN configs
            if not _rfp_san_only:
                rfp_iops_from_file = project.get("perf_iops_total", 0)
                rfp_iops_sub1      = project.get("perf_iops_max_sub1ms", 0)
                rfp_lat_sub1       = project.get("perf_latency_at_max_sub1ms", 0.0)
                if rfp_iops_from_file:
                    rfp_iops_val = rfp_iops_sub1 or rfp_iops_from_file
                    st.markdown(
                        notif("ok", f"Performance from file: <b>{rfp_iops_val:,} IOPS</b>"
                              + (f" @ {rfp_lat_sub1:.3f} ms (max sub-1ms)" if rfp_iops_sub1 else "")),
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(notif("warn", "No performance file — enter IOPS manually."), unsafe_allow_html=True)
                    rfp_iops_manual = st.number_input(
                        "IOPS (manual entry)",
                        min_value=0, max_value=10_000_000,
                        value=st.session_state.get("rfp_iops_manual", 0), step=10_000,
                    )
                    st.session_state["rfp_iops_manual"] = rfp_iops_manual

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            sup = project.get("support_info") or {}
            # For SAN-only, try to get support from first switch
            if _rfp_san_only and not sup:
                sup = (project.get("san_switches") or [{}])[0].get("support_info") or {}
            _rfp_fix = sup.get("fix_time_hours") if sup.get("fix_time") else None
            st.markdown(notif("info",
                f"Support: <b>{sup.get('name','—')}</b> · "
                f"{sup.get('coverage','—')} · "
                f"{('fix-time: ' + _rfp_fix) if _rfp_fix else 'no fix-time'} · "
                f"{sup.get('years','—')} yr"
            ), unsafe_allow_html=True)

        with r1_right:
            section("Generate RFP")
            _rfp_lang_opts = {"English": "en", "Polski": "pl"}
            _rfp_lang_cur  = st.session_state["rfp_lang"]
            _rfp_lang_lbl  = next(k for k, v in _rfp_lang_opts.items() if v == _rfp_lang_cur)
            _rfp_lang_sel  = st.radio(
                "Document language",
                options=list(_rfp_lang_opts.keys()),
                index=list(_rfp_lang_opts.keys()).index(_rfp_lang_lbl),
                horizontal=True,
                key="radio_rfp_lang",
            )
            st.session_state["rfp_lang"] = _rfp_lang_opts[_rfp_lang_sel]

            missing_rfp = []
            if not client_name: missing_rfp.append("Client name")
            if missing_rfp:
                st.markdown(notif("warn", "Fill in " + ", ".join(missing_rfp) + " in Step 2."), unsafe_allow_html=True)

            _rfp_label = (
                "Generate SAN RFP / Specification (.docx) →"
                if _rfp_san_only else
                "Generate RFP / RFI (.docx) →"
            )
            if st.button(_rfp_label, type="primary", use_container_width=True, key="btn_rfp"):
                with st.spinner("Generating RFP…"):
                    try:
                        slug = re.sub(r"[^\w]", "_", client_name) if client_name else "Client"
                        _rfp_sfx = "_PL" if st.session_state["rfp_lang"] == "pl" else ""
                        if _rfp_san_only:
                            # SAN-only → dedicated SAN RFP
                            rfp_bytes = generate_san_rfp(
                                project=project,
                                client_name=client_name,
                                seller_name=seller_name,
                                lang=st.session_state["rfp_lang"],
                            )
                            _san_short = (project.get("san_switches") or [{}])[0].get("switch_short", "SAN")
                            rfp_fname = f"RFP_SAN_{_san_short}_{slug}_{date.today():%Y%m%d}{_rfp_sfx}.docx"
                        else:
                            # FlashSystem / Scale RFP
                            rfp_iops_used = rfp_iops_manual if not rfp_iops_from_file else 0
                            _rfp_fn = (generate_scale_rfp
                                       if st.session_state["product_line"] == "scale"
                                       else generate_rfp)
                            rfp_bytes = _rfp_fn(
                                project=project,
                                client_name=client_name,
                                seller_name=seller_name,
                                iops_override=rfp_iops_used if rfp_iops_used > 0 else None,
                                lang=st.session_state["rfp_lang"],
                                num_systems=int(st.session_state.get("num_systems", 1)),
                            )
                            rfp_fname = f"RFP_{model_info.get('short', model_code)}_{slug}_{date.today():%Y%m%d}{_rfp_sfx}.docx"
                            # FS+SAN: append SAN section as a second document merged inline
                            if project.get("san_switches"):
                                from docx import Document as _Doc2
                                from docx.enum.text import WD_BREAK
                                # Generate standalone SAN spec
                                san_rfp_bytes = generate_san_rfp(
                                    project=project,
                                    client_name=client_name,
                                    seller_name=seller_name,
                                    lang=st.session_state["rfp_lang"],
                                )
                                # Merge: open FS doc, append SAN doc paragraphs + tables
                                fs_doc  = _Doc2(io.BytesIO(rfp_bytes))
                                san_doc = _Doc2(io.BytesIO(san_rfp_bytes))
                                # Add page-break divider before SAN section
                                _break_p = fs_doc.add_paragraph()
                                _break_r = _break_p.add_run()
                                _break_r.add_break(WD_BREAK.PAGE)
                                # Copy all body elements from san_doc into fs_doc
                                for _elem in san_doc.element.body:
                                    fs_doc.element.body.append(copy.deepcopy(_elem))
                                _merged_buf = io.BytesIO()
                                fs_doc.save(_merged_buf)
                                rfp_bytes = _merged_buf.getvalue()
                                rfp_fname = f"RFP_{model_info.get('short', model_code)}_SAN_{slug}_{date.today():%Y%m%d}{_rfp_sfx}.docx"
                        st.session_state["rfp_bytes"]    = rfp_bytes
                        st.session_state["rfp_filename"] = rfp_fname
                        st.markdown(notif("ok", f"Ready: <b>{rfp_fname}</b>"), unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Error: {e}")
                        st.exception(e)

            if st.session_state["rfp_bytes"]:
                st.download_button(
                    "⬇  Download RFP .docx",
                    data=st.session_state["rfp_bytes"],
                    file_name=st.session_state["rfp_filename"],
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                    key="dl_rfp",
                )

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        # Configuration Requirements Preview — adapt for SAN-only
        section("Configuration Requirements Preview")
        if _rfp_san_only:
            _san_preview = []
            for _sw in (project.get("san_switches") or []):
                _sw_qty  = _sw.get("qty", 1)
                _sw_name = _sw.get("switch_short", _sw.get("model_code", "—"))
                _sw_act  = _sw.get("active_ports", 0)
                _sw_max  = _sw.get("max_ports", 0)
                _sw_spd  = _sw.get("port_speed_gbps", 32)
                _sw_sup2 = (_sw.get("support_info") or {})
                _sw_lw   = _sw.get("lw_optics_qty", 0)
                _sw_swc  = _sw.get("sw_optics_qty", 0)
                _san_preview += [
                    ("Switch model",   f"{_sw_qty}× {_sw_name}"),
                    ("Active / max ports", f"{_sw_act} / {_sw_max}"),
                    ("Port speed",     f"{_sw_spd} Gbps FC"),
                    ("LW optics",      f"{_sw_lw}× SFP+ LW" if _sw_lw else "—"),
                    ("SW cables",      f"{_sw_swc}× OM3 cable" if _sw_swc else "—"),
                    ("Support",        f"{_sw_sup2.get('name','—')} · {_sw_sup2.get('coverage','—')} · {_sw_sup2.get('years','—')} yr"),
                ]
            st.dataframe(
                {"Parameter": [r[0] for r in _san_preview], "Value": [r[1] for r in _san_preview]},
                hide_index=True, use_container_width=True,
            )
        else:
            rfp_rows = [
                ("Enclosure",      f"{model_info.get('form_factor','1U')} · {project.get('io_groups','2')} I/O Groups · {project.get('enclosures','1')} enclosure(s)"),
                ("Raw capacity",   f"{project.get('raw_tib',0):.2f} TiB / {project.get('raw_tb',0):.2f} TB"),
                ("Usable capacity",f"{project.get('usable_tib',0):.2f} TiB / {project.get('usable_tb',0):.2f} TB  [{project.get('raid_type','RAID 6')}]"),
                ("Drives",         f"{project.get('drives_count',0)} × {project.get('drive_label', project.get('drive_type','FCM5'))}"),
                ("Cache",          f"{project.get('cache_gb',256)} GB"),
                ("FC ports",       f"{project.get('fc_ports',8)} × 32 Gb/s"),
                ("Encryption",     "Yes" if project.get("encryption") else "Required"),
                ("Support",        f"{sup.get('name','—')} · {sup.get('coverage','—')} · {sup.get('years','—')} years"),
            ]
            if project.get("san_switches"):
                rfp_rows.append(("SAN switches", "; ".join(
                    f"{s.get('qty',1)}× {s.get('switch_short', s.get('model_code',''))}"
                    for s in project.get("san_switches", [])
                )))
            st.dataframe(
                {"Parameter": [r[0] for r in rfp_rows], "Value": [r[1] for r in rfp_rows]},
                hide_index=True, use_container_width=True,
            )

    # =====================================================================
    # =====================================================================
    # TAB — Special Bid
    # =====================================================================
    if _at == "bid":
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

        # ── Pricing data (shared across columns) ─────────────────────────
        list_hw2  = project.get("list_price_hw", 0)
        list_sw2  = project.get("list_price_sw", 0)
        list_sup2 = project.get("list_price_support", 0)
        ship2     = project.get("shipping", 0)
        d2        = discount_pct / 100
        curr2     = project.get("currency", "EUR")
        net2      = list_hw2*(1-d2) + list_sw2*(1-d2) + list_sup2*(1-d2) + ship2
        list_tot2 = list_hw2 + list_sw2 + list_sup2 + ship2
        dev_from_60 = discount_pct - 60.0

        # ── Build auto-suggested texts (computed once, user can override) ─
        _mname     = model_info.get("name", model_code)
        _drives    = project.get("drives_count", 0)
        _dshort    = _drive_short  # reuse from metrics block above
        _usable    = project.get("usable_tib", 0.0)
        _raw       = project.get("raw_tib", 0.0)
        _raid      = project.get("raid_type", "RAID 6")
        _cache     = project.get("cache_gb", 256)
        _sup       = project.get("support_info") or {}
        _sup_name  = _sup.get("name", "Expert Care")
        _iops_sub1 = project.get("perf_iops_max_sub1ms", 0)

        _due_str  = f"Bid submission due: {due_date}." if due_date else "Bid submission date TBD."
        _deal_str = f" Workload scenario: {_deal_label}." if _deal_label and _deal_label != "— wybierz —" else ""

        _is_scale_bid = (st.session_state.get("product_line") == "scale")
        _is_san_only  = bool(project.get("san_switches")) and not bool(project.get("model_code", ""))
        _san_switches_bid = project.get("san_switches", [])

        if _is_scale_bid:
            # ── Scale-specific opportunity context ───────────────────────
            _sc_bw_r   = project.get("throughput_read_gbs", 0.0)
            _sc_bw_w   = project.get("throughput_write_gbs", 0.0)
            _sc_ib_n   = project.get("ib_adapters", 0)
            _sc_ib_d   = project.get("ib_adapter_desc", "CX-7 VPI 200GbE/NDR200")
            _sc_nodes  = project.get("num_data_nodes", 1) or 1
            _sc_util   = project.get("utility_nodes", [])
            _sc_util_s = (", ".join(
                f"{u['qty']} × {u['type']} ({u['mtm']})" for u in _sc_util
            ) if _sc_util else "")
            _bw_str    = (f", max sequential throughput {_sc_bw_r:.2f} GB/s read / "
                          f"{_sc_bw_w:.2f} GB/s write" if _sc_bw_r else "")
            _ib_str    = (f", {_sc_ib_n} × {_sc_ib_d} network adapters" if _sc_ib_n else "")
            _util_str  = (f", utility nodes: {_sc_util_s}" if _sc_util_s else "")
            _hint_opportunity = (
                f"Net-new IBM parallel file storage deployment opportunity for "
                f"{client_name or '[Client]'} — delivery of {_mname} with "
                f"{_sc_nodes} data node(s), {_drives} × {_dshort} NVMe SSD drives, "
                f"{_raw:.1f} TiB raw / {_usable:.1f} TiB usable ({_raid})"
                f"{_bw_str}{_ib_str}{_util_str}. "
                f"Support: {_sup_name}.{_deal_str} "
                f"Currently in the RFP response stage. {_due_str}"
            )
        elif _is_san_only:
            # ── SAN-only opportunity context ─────────────────────────────
            _san_lines = []
            for _sw in _san_switches_bid:
                _sw_qty  = _sw.get("qty", 1)
                _sw_name = _sw.get("switch_name", _sw.get("switch_short", "SAN Switch"))
                _sw_act  = _sw.get("active_ports", 0)
                _sw_max  = _sw.get("max_ports", 0)
                _sw_sup  = (_sw.get("support_info") or {}).get("name", "Expert Care")
                _sw_spd  = _sw.get("port_speed_gbps", 32)
                _san_lines.append(
                    f"{_sw_qty}× {_sw_name} ({_sw_act}/{_sw_max} ports active, {_sw_spd} Gbps FC)"
                )
            _san_summary = "; ".join(_san_lines) if _san_lines else "IBM b-type SAN switches"
            _hint_opportunity = (
                f"IBM Fibre Channel SAN fabric opportunity for {client_name or '[Client]'} — "
                f"delivery of {_san_summary}. "
                f"Support: {_sup_name}.{_deal_str} "
                f"Currently in the RFP response stage. {_due_str}"
            )
        else:
            # ── FlashSystem opportunity context ──────────────────────────
            _fc = project.get("fc_ports", 8)
            _san_addon = ""
            if _san_switches_bid:
                _sw0 = _san_switches_bid[0]
                _san_addon = (
                    f" SAN fabric: {_sw0.get('qty', 1)}× {_sw0.get('switch_name', 'SAN Switch')} "
                    f"({_sw0.get('active_ports', 0)} active ports)."
                )
            _hint_opportunity = (
                f"Net-new IBM storage deployment opportunity for {client_name or '[Client]'} — "
                f"delivery of {_mname} with {_drives}× {_dshort} drives, "
                f"{_raw:.1f} TiB raw / {_usable:.1f} TiB usable ({_raid}), "
                f"{_cache} GB cache, {_fc} FC 32Gb/s ports"
                + (f", up to {_iops_sub1:,} IOPS below 1 ms latency" if _iops_sub1 else "")
                + f". Support: {_sup_name}.{_san_addon}{_deal_str} "
                f"Currently in the RFP response stage. {_due_str}"
            )

        # Collect competitors — SAN uses different list
        _bj_comp_list  = st.session_state.get("bid_competitors_sel", [])
        _bj_incumbent  = st.session_state.get("bid_incumbent", "")
        _bj_inc_model  = st.session_state.get("bid_incumbent_model", "")
        _bj_budget     = st.session_state.get("bid_client_budget", "")
        _bj_comp_str   = ", ".join(_bj_comp_list) if _bj_comp_list else (
            "leading parallel file storage vendors" if _is_scale_bid
            else ("Cisco MDS, HPE SN switches" if _is_san_only else "leading all-flash vendors")
        )

        # Select background text variant based on deal_type
        _bg_variants = _BACKGROUND_VARIANTS.get(deal_type, [])
        if _bg_variants and not _is_scale_bid:
            # deterministic per session+deal_type to avoid rerun changes
            _bg_seed_key = f"_bg_variant_idx_{deal_type}"
            if _bg_seed_key not in st.session_state:
                st.session_state[_bg_seed_key] = random.randint(0, len(_bg_variants) - 1)
            _bg_idx = st.session_state[_bg_seed_key] % len(_bg_variants)
            _hint_background = _bg_variants[_bg_idx].format(
                client=client_name or "[Client]",
                mname=_mname if not _is_san_only else (
                    _san_switches_bid[0].get("switch_name", "IBM SAN Switch") if _san_switches_bid else "IBM SAN Switch"
                ),
                usable=_usable,
                raid=_raid,
                sup_name=_sup_name,
            )
            # Replace hardcoded competitor names with user selection
            if _bj_comp_list:
                _hint_background = re.sub(
                    r"(Special Bid pricing is (?:required|requested|needed|necessary)|"
                    r"Exception pricing is (?:required|requested|needed|necessary)|"
                    r"The requested (?:exception discount|discount) is (?:required|necessary))"
                    r"([^.]+?)"
                    r"(Pure Storage|Dell EMC|NetApp|HPE|Hitachi|Huawei|VAST Data|Qumulo|Commvault|Veritas|Zerto|"
                    r"Cisco MDS|HPE SN|Arista)"
                    r"([^.]*\.)",
                    lambda m: f"{m.group(1)}{m.group(2)}{_bj_comp_str}.",
                    _hint_background,
                )
        elif _is_scale_bid:
            # ── Scale-specific deal background ───────────────────────────
            _sc_bw_r2  = project.get("throughput_read_gbs", 0.0)
            _bw_req    = (f"sequential throughput exceeding {_sc_bw_r2:.0f} GB/s read" if _sc_bw_r2 else "high-throughput sequential I/O")
            _hint_background = (
                f"This is a competitive parallel file storage RFP for {client_name or '[Client]'}, "
                f"requiring exception pricing to remain competitive against {_bj_comp_str}. "
                + (f"Use case: {_deal_desc} " if _deal_desc else
                   "The customer is evaluating solutions for AI training, large-scale analytics, or HPC workloads. ")
                + f"Key technical requirements: min. {_usable:.0f} TiB usable ({_raid}), "
                f"{_bw_req}, POSIX-compliant parallel file system with GPFS/Scale protocol support, "
                f"24×7 enterprise support. "
                f"IBM {_mname} meets all requirements and is listed on the NVIDIA-Certified Storage Systems list, "
                f"validating its readiness for GPU-accelerated AI/ML workloads — "
                f"a key differentiator against competing solutions from {_bj_comp_str}."
            )
        else:
            _hint_background = (
                f"This is a competitive storage RFP for {client_name or '[Client]'}, "
                f"requiring exception pricing to remain competitive against {_bj_comp_str}. "
                + (f"Use case: {_deal_desc} " if _deal_desc else
                   "The customer is evaluating solutions to [replace incumbent / expand capacity / migrate workloads]. ")
                + f"Key technical requirements: min. {_usable:.0f} TiB usable, {_raid}, "
                f"24×7 enterprise support, NVMe all-flash architecture. "
                f"IBM {_mname} meets all requirements while delivering AI-powered ransomware detection "
                f"via FlashCore Module 5 — a differentiating capability unavailable in {_bj_comp_str} solutions."
            )

        _dev_str = (f"representing a {dev_from_60:.1f}-point deviation above the 60% baseline" if dev_from_60 > 0 else "within the standard 60% baseline")

        _bj_inc_str    = (f"Incumbent: {_bj_incumbent}" + (f" ({_bj_inc_model})" if _bj_inc_model else "") + ". " if _bj_incumbent else "")
        _bj_budget_str = (f"Client's approximate budget: {_bj_budget} {curr2}. " if _bj_budget else "")

        if _is_scale_bid:
            _hint_business_just = (
                f"Requested BP price: {net2:,.0f} {curr2} (IBM list: {list_tot2:,.0f} {curr2}) — "
                f"discount {discount_pct:.1f}%, {_dev_str}.\n\n"
                + (f"Client's approximate budget: {_bj_budget} {curr2}.\n" if _bj_budget else "")
                + (f"Incumbent: {_bj_incumbent}" + (f" ({_bj_inc_model})" if _bj_inc_model else "") + ".\n" if _bj_incumbent else "")
                + f"\nJustification: The requested discount level is required to be competitive against "
                f"{_bj_comp_str}, who are expected to submit proposals significantly below IBM list price "
                f"for this account. IBM list pricing is not competitive in the HPC/AI parallel file storage "
                f"segment without exception support — vendors in this space ({_bj_comp_str}) routinely "
                f"price 50–60% below published list to secure initial deployments.\n\n"
                f"IBM {_mname} justifies the investment through: (1) NVIDIA-Certified Storage Systems "
                f"listing — independently validated for GPU-accelerated AI/ML workloads; "
                f"(2) GPFS-based parallel file system (IBM Storage Scale) with linear bandwidth scalability "
                f"and POSIX compliance — required for MPI/OpenMPI workloads; "
                f"(3) CX-7 VPI 200GbE/NDR200 fabric connectivity delivering deterministic low-latency I/O "
                f"to GPU nodes — capabilities not available in competing proposals.\n\n"
                f"Failure to approve this discount will result in loss of the opportunity to {_bj_comp_str}. "
                f"Winning this deal establishes IBM as the strategic AI storage supplier at this account "
                f"with significant follow-on expansion potential."
            )
        elif _is_san_only:
            # ── SAN-specific business justification ──────────────────────
            _san_total_ports = sum(
                sw.get("active_ports", 0) * sw.get("qty", 1) for sw in _san_switches_bid
            )
            _san_max_ports = sum(
                sw.get("max_ports", 0) * sw.get("qty", 1) for sw in _san_switches_bid
            )
            _san_model_names = ", ".join(
                f"{sw.get('qty', 1)}× {sw.get('switch_name', 'SAN Switch')}"
                for sw in _san_switches_bid
            ) if _san_switches_bid else "IBM b-type SAN switches"
            _hint_business_just = (
                f"Requested BP price: {net2:,.0f} {curr2} (IBM list: {list_tot2:,.0f} {curr2}) — "
                f"discount {discount_pct:.1f}%, {_dev_str}.\n\n"
                + (f"Client's approximate budget: {_bj_budget} {curr2}.\n" if _bj_budget else "")
                + (f"Incumbent: {_bj_incumbent}" + (f" ({_bj_inc_model})" if _bj_inc_model else "") + ".\n" if _bj_incumbent else "")
                + f"\nJustification: The requested discount is necessary to compete against {_bj_comp_str}, "
                f"which {'are' if ',' in _bj_comp_str else 'is'} expected to submit proposals significantly "
                f"below IBM list price for this SAN infrastructure refresh.\n\n"
                f"Configuration: {_san_model_names} — {_san_total_ports} active FC ports "
                f"({_san_max_ports} max) with IBM Storage Expert Care support.\n\n"
                f"IBM b-type SAN switches (Brocade OEM) justify the investment through: "
                f"(1) Native IBM stack integration — single-vendor support with IBM FlashSystem and DS8000, "
                f"eliminating cross-vendor support boundary issues; "
                f"(2) Gen 7 / Gen 8 Fibre Channel technology — 64 Gbps FC and NVMe-oF readiness "
                f"for next-generation storage connectivity; "
                f"(3) IBM Storage Expert Care — 4-hour hardware response SLA with proactive monitoring "
                f"through IBM Storage Insights, unavailable in Cisco MDS or HPE proposals.\n\n"
                f"Failure to approve this discount will result in loss of the SAN refresh opportunity "
                f"to {_bj_comp_str}. IBM SAN presence in this account is a prerequisite for future "
                f"FlashSystem storage expansion opportunities."
            )
        else:
            _hint_business_just = (
                f"Requested BP price: {net2:,.0f} {curr2} (IBM list: {list_tot2:,.0f} {curr2}) — "
                f"discount {discount_pct:.1f}%, {_dev_str}.\n\n"
                + (f"Client's approximate budget: {_bj_budget} {curr2}.\n" if _bj_budget else "")
                + (f"Incumbent: {_bj_incumbent}" + (f" ({_bj_inc_model})" if _bj_inc_model else "") + ".\n" if _bj_incumbent else "")
                + f"\nJustification: The requested discount level is required to match the competitive "
                f"price band established during the RFP process. {_bj_comp_str} "
                f"{'have' if ',' in _bj_comp_str else 'has'} submitted or are expected to submit "
                f"proposals priced below IBM list — IBM cannot win this deal at list pricing.\n\n"
                f"IBM {_mname} differentiates on three commercially relevant dimensions: "
                f"(1) FlashCore Module 5 (FCM5) — hardware-level inline AI ransomware detection, "
                f"providing a security layer unavailable in {_bj_comp_str} solutions and directly "
                f"addressing customer cybersecurity requirements without additional software cost; "
                f"(2) Distributed RAID 6 with >2 TB/h rebuild speed — minimising data exposure during "
                f"drive failure, a critical SLA requirement for Tier-1 production workloads; "
                f"(3) IBM Storage Insights — proactive AI-driven capacity and performance management "
                f"included at no additional cost, reducing customer operational overhead.\n\n"
                f"Approving the requested exception discount secures the initial IBM deployment and "
                f"prevents {_bj_comp_str} from establishing the incumbent position. "
                f"All follow-on capacity expansions will default to the incumbent vendor."
            )

        # ─────────────────────────────────────────────────────────────────
        # ROW 1: Channel info (left) + Section A fields (right)
        # ─────────────────────────────────────────────────────────────────
        sb1, sb2 = st.columns([1, 1], gap="large")

        with sb1:
            # ── Channel / tier table ──────────────────────────────────────
            section("Sales Channel")

            bid_dist_idx = (DISTRIBUTORS.index(st.session_state["bid_distributor"])
                            if st.session_state["bid_distributor"] in DISTRIBUTORS else 0)
            st.session_state["bid_distributor"] = st.selectbox(
                "Tier 1 Distributor",
                options=DISTRIBUTORS,
                index=bid_dist_idx,
                disabled=not loaded,
                key="sel_distributor",
            )

            # Auto-sync: jeśli Step 2 ma wybranego represetanta, użyj go jako default
            _step2_rep = st.session_state.get("seller_name", "")
            _bid_rep_cur = st.session_state["bid_sales_rep"]
            if (loaded and _step2_rep and _step2_rep != IBM_SALES_REPS[0]
                    and _bid_rep_cur == IBM_SALES_REPS[0]):
                st.session_state["bid_sales_rep"] = _step2_rep
                _bid_rep_cur = _step2_rep
            bid_rep_idx = (IBM_SALES_REPS.index(_bid_rep_cur)
                           if _bid_rep_cur in IBM_SALES_REPS else 0)
            st.session_state["bid_sales_rep"] = st.selectbox(
                "IBM Sales Representative",
                options=IBM_SALES_REPS,
                index=bid_rep_idx,
                disabled=not loaded,
                key="sel_salesrep",
                help="Auto-populated from Step 2 — can be changed independently",
            )

            st.session_state["bid_reseller"] = st.text_input(
                "Tier 2 Reseller",
                value=st.session_state["bid_reseller"],
                placeholder="Reseller company name",
                disabled=not loaded,
            )
            # End user comes from client_name (Step 2)
            st.markdown(
                f'<div style="font-size:12px;font-weight:600;text-transform:uppercase;'
                f'letter-spacing:.06em;color:var(--gray-70);margin-top:8px">End User</div>'
                f'<div style="font-size:14px;color:var(--gray-100);padding:8px 0 4px;'
                f'border-bottom:1px solid var(--gray-20)">'
                f'{client_name or "<i style=\'color:var(--gray-50)\'>fill in Step 2</i>"}</div>',
                unsafe_allow_html=True,
            )

            # ── Pricing summary ───────────────────────────────────────────
            section("Pricing Summary (auto)")
            st.dataframe({
                "Category": ["Hardware (List)", "Support (List)", "Software (List)", "Shipping", "NET Total"],
                f"List ({curr2})": [
                    f"{list_hw2:,.2f}", f"{list_sup2:,.2f}", f"{list_sw2:,.2f}",
                    f"{ship2:,.2f}", f"{list_tot2:,.2f}",
                ],
                f"Net @ {discount_pct:.0f}%": [
                    f"{list_hw2*(1-d2):,.2f}", f"{list_sup2*(1-d2):,.2f}",
                    f"{list_sw2*(1-d2):,.2f}", f"{ship2:,.2f}", f"{net2:,.2f}",
                ],
            }, hide_index=True, use_container_width=True)

            if discount_pct > 65:
                st.markdown(notif("warn",
                    f"Discount <b>{discount_pct:.1f}%</b> — Special Bid required "
                    f"(<b>{dev_from_60:.1f} pp</b> above the 60% baseline)."),
                    unsafe_allow_html=True)
            else:
                st.markdown(notif("ok",
                    f"Discount <b>{discount_pct:.1f}%</b> — within standard 60% baseline."),
                    unsafe_allow_html=True)

        with sb2:
            # ── Section A — Opportunity Context ──────────────────────────
            section("Section A — Opportunity Context")
            st.markdown(
                '<div style="font-size:11px;color:var(--gray-70);margin-bottom:4px">'
                '💡 Describe the solution, deal scope and sales stage. '
                'Pre-filled text below — edit as needed.</div>',
                unsafe_allow_html=True,
            )
            if not st.session_state["bid_opportunity_ctx"] and loaded:
                st.session_state["bid_opportunity_ctx"] = _hint_opportunity
            st.session_state["bid_opportunity_ctx"] = st.text_area(
                "Opportunity Context",
                value=st.session_state["bid_opportunity_ctx"],
                height=130, disabled=not loaded,
                label_visibility="collapsed",
            )

            # ── Section A — Deal Background ───────────────────────────────
            section("Section A — Deal Background / Scenario")
            # Gdy deal_type się zmienia, wyczyść poprzedni tekst i przypisz nowy wariant
            _prev_dt_key = "_prev_deal_type_for_bg"
            if st.session_state.get(_prev_dt_key) != deal_type:
                st.session_state["bid_background"] = ""
                # Reset background text when deal_type changes
                _bg_seed_key2 = f"_bg_variant_idx_{deal_type}"
                _bg_variants2 = _BACKGROUND_VARIANTS.get(deal_type, [])
                if _bg_variants2:
                    st.session_state[_bg_seed_key2] = random.randint(0, len(_bg_variants2) - 1)
                st.session_state[_prev_dt_key] = deal_type
            _bg_hint_label_cols = st.columns([4, 1])
            with _bg_hint_label_cols[0]:
                st.markdown(
                    '<div style="font-size:11px;color:var(--gray-70);margin-bottom:4px">'
                    '💡 Text matched to the selected scenario — edit as needed.</div>',
                    unsafe_allow_html=True,
                )
            with _bg_hint_label_cols[1]:
                if loaded and st.button("↺ New variant", key="btn_regen_bg",
                                        help="Rotate to the next text variant for this scenario",
                                        use_container_width=True):
                    _bg_seed_key3 = f"_bg_variant_idx_{deal_type}"
                    _bg_vars3 = _BACKGROUND_VARIANTS.get(deal_type, [])
                    if _bg_vars3:
                        _cur3 = st.session_state.get(_bg_seed_key3, 0)
                        st.session_state[_bg_seed_key3] = (_cur3 + 1) % len(_bg_vars3)
                    st.session_state["bid_background"] = ""
                    st.rerun()
            if not st.session_state["bid_background"] and loaded:
                st.session_state["bid_background"] = _hint_background
            st.session_state["bid_background"] = st.text_area(
                "Deal Background",
                value=st.session_state["bid_background"],
                height=130, disabled=not loaded,
                label_visibility="collapsed",
            )

        # ─────────────────────────────────────────────────────────────────
        # ROW 2: Competitive Positioning (B) + Business Justification + History
        # ─────────────────────────────────────────────────────────────────
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        sb3, sb4 = st.columns([1, 1], gap="large")

        with sb3:
            section("Section B — Competitive Positioning")
            st.markdown(
                '<div style="font-size:11px;color:var(--gray-70);margin-bottom:6px">'
                '💡 Select the main competitors and fill in incumbent details.</div>',
                unsafe_allow_html=True,
            )
            # Custom label with required asterisk
            st.markdown(
                '<div style="font-size:12px;font-weight:600;text-transform:uppercase;'
                'letter-spacing:.06em;color:var(--gray-70);margin-bottom:4px">'
                'Key competitors&nbsp;<span style="color:#da1e28;font-size:13px">*</span></div>',
                unsafe_allow_html=True,
            )
            # Use SAN competitor list for SAN-only deals
            _bid_comp_options = (
                COMPETITORS_SAN if _is_san_only else COMPETITORS_STORAGE
            )
            # Auto-clear competitor selection if it contains storage-specific items when switching to SAN
            _san_comp_names = {c for c in COMPETITORS_SAN}
            _storage_comp_names = {c for c in COMPETITORS_STORAGE}
            _cur_sel = st.session_state["bid_competitors_sel"]
            if _is_san_only and any(c in _storage_comp_names - _san_comp_names for c in _cur_sel):
                st.session_state["bid_competitors_sel"] = []
                _cur_sel = []
            st.session_state["bid_competitors_sel"] = st.multiselect(
                "Key competitors",
                options=_bid_comp_options,
                default=[c for c in _cur_sel if c in _bid_comp_options],
                disabled=not loaded,
                key="ms_competitors",
                label_visibility="collapsed",
            )

            c_inc1, c_inc2 = st.columns(2)
            with c_inc1:
                st.session_state["bid_incumbent"] = st.text_input(
                    "Incumbent vendor  *(optional)*",
                    value=st.session_state["bid_incumbent"],
                    placeholder="e.g. Pure Storage, HPE 3PAR",
                    disabled=not loaded,
                )
            with c_inc2:
                st.session_state["bid_incumbent_model"] = st.text_input(
                    "Incumbent model  *(optional)*",
                    value=st.session_state["bid_incumbent_model"],
                    placeholder="e.g. FA//C60, 3PAR 8400",
                    disabled=not loaded,
                )

            # Auto-build competitor hint text
            _comp_list = st.session_state["bid_competitors_sel"]
            _incumbent = st.session_state["bid_incumbent"]
            _inc_model = st.session_state["bid_incumbent_model"]
            if _comp_list or _incumbent:
                _comp_str = ", ".join(_comp_list) if _comp_list else "not specified"
                if _is_san_only:
                    _hint_comp = (
                        f"This is a competitive SAN fabric refresh opportunity. "
                        + (f"Incumbent vendor: {_incumbent}" + (f" ({_inc_model})" if _inc_model else "") + ". " if _incumbent else "")
                        + f"Key competitors: {_comp_str}. "
                        f"Competing SAN proposals are expected to be priced below IBM list, "
                        f"targeting the {net2:,.0f} {curr2} range. "
                        f"IBM b-type SAN switches differentiate through native IBM stack integration, "
                        f"64 Gbps FC and NVMe-oF readiness, and IBM Storage Expert Care support. "
                        f"Source: [client feedback / partner insight / RFP documentation]."
                    )
                else:
                    _hint_comp = (
                        f"This is a competitive all-flash storage opportunity. "
                        + (f"Incumbent vendor: {_incumbent}" + (f" ({_inc_model})" if _inc_model else "") + ". " if _incumbent else "")
                        + f"Key competitors: {_comp_str}. "
                        f"Competing solutions are expected to be priced lower than IBM list price, "
                        f"targeting the {net2:,.0f} {curr2} range. "
                        f"IBM {_mname} differentiates through: AI-powered ransomware detection "
                        f"(FlashCore Module 5), Distributed RAID 6 with >2 TB/h rebuild, "
                        f"and IBM Storage Insights for proactive management. "
                        f"Source: [client feedback / partner insight / RFP documentation]."
                    )
                st.markdown(
                    f'<div style="background:#edf5ff;border-left:3px solid var(--blue-60);'
                    f'padding:10px 14px;font-size:12px;color:var(--gray-100);margin-top:8px;'
                    f'line-height:1.55">'
                    f'<b>Suggested text for Section B:</b><br><br>'
                    f'{_hint_comp}</div>',
                    unsafe_allow_html=True,
                )

        with sb4:
            section("Section A — Business Justification")

            # Pole budżetu klienta — formatowanie z separatorami tysięcy
            def _on_budget_change():
                raw = st.session_state.get("bid_budget_text", "")
                cleaned = re.sub(r"[^\d.]", "", raw.replace(" ", "").replace(",", ""))
                try:
                    val = int(float(cleaned)) if cleaned else 0
                except ValueError:
                    return
                formatted = f"{val:,}".replace(",", " ")
                st.session_state["bid_client_budget"] = formatted
                st.session_state["bid_budget_text"] = formatted

            _budget_display = st.session_state.get("bid_client_budget", "")
            st.text_input(
                f"Client's Approx. Budget ({curr2})",
                value=_budget_display,
                placeholder=f"e.g. {int(net2):,}".replace(",", " "),
                disabled=not loaded,
                help="Enter the client's approximate budget — included in the Business Justification text",
                key="bid_budget_text",
                on_change=_on_budget_change,
            )

            # Reset BJ gdy zmienią się konkurenci, incumbent lub budżet
            _bj_sig = (
                tuple(sorted(st.session_state.get("bid_competitors_sel", []))),
                st.session_state.get("bid_incumbent", ""),
                st.session_state.get("bid_client_budget", ""),
            )
            if st.session_state.get("_bj_prev_sig") != _bj_sig:
                st.session_state["_bj_prev_sig"] = _bj_sig
                st.session_state["bid_business_just"] = ""   # wymuś regenerację

            st.markdown(
                '<div style="font-size:11px;color:var(--gray-70);margin-bottom:4px">'
                '💡 Auto-generated from pricing data, selected competitors and budget — edit as needed.</div>',
                unsafe_allow_html=True,
            )
            if not st.session_state["bid_business_just"] and loaded:
                st.session_state["bid_business_just"] = _hint_business_just
            st.session_state["bid_business_just"] = st.text_area(
                "Business Justification",
                value=st.session_state["bid_business_just"],
                height=160, disabled=not loaded,
                label_visibility="collapsed",
            )

            section("Section C — Prior Bid / Deal History (optional)")
            _sbo_c1, _sbo_c2 = st.columns([1, 1], gap="small")
            with _sbo_c1:
                st.session_state["bid_ref_sbo_c"] = st.text_input(
                    "Reference SBO  *(optional)*",
                    value=st.session_state["bid_ref_sbo_c"],
                    placeholder="e.g. SBO-2025-12345",
                    disabled=not loaded,
                    key="bid_ref_sbo_c_input",
                )
            st.session_state["bid_deal_history"] = st.text_area(
                "Deal History",
                value=st.session_state["bid_deal_history"],
                placeholder=(
                    "No previous related bids.\n"
                    "Or: Bid #XXXXX from [year] — [short description]."
                ),
                height=80, disabled=not loaded,
                label_visibility="collapsed",
            )

        # ─────────────────────────────────────────────────────────────────
        # Generate button
        # ─────────────────────────────────────────────────────────────────
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        bc1, bc2, bc3 = st.columns([1, 2, 1])
        with bc2:
            _bid_dist_val  = st.session_state["bid_distributor"]
            _bid_rep_val   = st.session_state["bid_sales_rep"]
            _missing_bid   = []
            if _bid_dist_val == DISTRIBUTORS[0]: _missing_bid.append("Distributor")
            if _bid_rep_val  == IBM_SALES_REPS[0]: _missing_bid.append("IBM Sales Rep")
            if not client_name: _missing_bid.append("End User (Step 2)")
            if not st.session_state["bid_competitors_sel"]: _missing_bid.append("Key competitors ✱")
            if _missing_bid:
                st.markdown(
                    notif("warn", "Please fill in required fields: <b>" + ", ".join(_missing_bid) + "</b>"),
                    unsafe_allow_html=True,
                )

            if st.button("Generate Special Bid Questionnaire →", type="primary",
                         use_container_width=True, key="btn_bid"):
                with st.spinner("Generating…"):
                    try:
                        # Build competitor info string from selections + manual text
                        _comp_info_final = ""
                        if st.session_state["bid_competitors_sel"] or st.session_state["bid_incumbent"]:
                            _c = st.session_state["bid_competitors_sel"]
                            _i = st.session_state["bid_incumbent"]
                            _im = st.session_state["bid_incumbent_model"]
                            _comp_info_final = (
                                ("Incumbent: " + _i + (_im and f" ({_im})" or "") + ". " if _i else "")
                                + ("Competitors: " + ", ".join(_c) + "." if _c else "")
                            )

                        _eff_rep = (_bid_rep_val if _bid_rep_val != IBM_SALES_REPS[0]
                                    else seller_name)

                        _vr_key = st.session_state.get("bid_validity_reason", "")
                        _vr_label = next(
                            (r[1] for r in EXTENDED_VALIDITY_REASONS if r[0] == _vr_key),
                            "",
                        )
                        _dd_raw2 = st.session_state["due_date"]
                        _days_fwd = (_dd_raw2 - date.today()).days if hasattr(_dd_raw2, "strftime") else 0
                        _bid_fn = (generate_scale_special_bid
                                   if st.session_state["product_line"] == "scale"
                                   else generate_special_bid)
                        bid_bytes = _bid_fn(
                            project=project,
                            client_name=client_name,
                            seller_name=_eff_rep,
                            distributor_name=(_bid_dist_val if _bid_dist_val != DISTRIBUTORS[0]
                                              else ""),
                            reseller_name=st.session_state["bid_reseller"],
                            discount_pct=discount_pct,
                            opportunity_context=st.session_state["bid_opportunity_ctx"],
                            deal_background=st.session_state["bid_background"],
                            competitor_info=_comp_info_final,
                            deal_history=(
                                (f"Reference SBO: {st.session_state['bid_ref_sbo_c']}\n" if st.session_state.get("bid_ref_sbo_c") else "")
                                + (st.session_state["bid_deal_history"] or "")
                            ).strip() or None,
                            business_justification=st.session_state["bid_business_just"],
                            extended_validity_days=_days_fwd if _days_fwd > 30 else 0,
                            extended_validity_reason=_vr_label,
                            num_systems=int(st.session_state.get("num_systems", 1)),
                            eu_margin_pct=float(st.session_state.get("eu_margin_pct", 15.0)),
                        )
                        slug = re.sub(r"[^\w]", "_", client_name) if client_name else "Client"
                        bid_fname = f"SpecialBid_{model_info.get('short', model_code)}_{slug}_{date.today():%Y%m%d}.docx"
                        st.session_state["bid_bytes"]    = bid_bytes
                        st.session_state["bid_filename"] = bid_fname
                        st.markdown(notif("ok", f"Ready: <b>{bid_fname}</b>"), unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Error: {e}")
                        st.exception(e)

        if st.session_state["bid_bytes"]:
            bd1, bd2, bd3 = st.columns([1, 2, 1])
            with bd2:
                st.download_button(
                    "⬇  Download Special Bid .docx",
                    data=st.session_state["bid_bytes"],
                    file_name=st.session_state["bid_filename"],
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                    key="dl_bid",
                )

    # =====================================================================
    # =====================================================================
    # TAB — Projects & Settings
    # =====================================================================
    if _at == "projects":
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

        # ── Projects (save / load) ────────────────────────────────────────
        pr1, pr2 = st.columns([1, 1], gap="large")

        with pr1:
            section("Save Current Project")
            _save_name = st.text_input(
                "Project name",
                value=client_name or "",
                placeholder="e.g. Acme_Bank_FS5600",
                key="proj_save_name",
                disabled=not loaded,
            )
            if st.button("💾  Save Project", type="primary",
                         use_container_width=True, key="btn_save_proj",
                         disabled=(not loaded)):
                if _save_name.strip():
                    _p = _save_project(_save_name)
                    st.markdown(notif("ok", f"Saved: <b>{_p.name}</b>"), unsafe_allow_html=True)
                else:
                    st.markdown(notif("warn", "Enter a project name first."), unsafe_allow_html=True)

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            st.markdown(notif("info",
                "Saves client name, discount, channel info, opportunity texts "
                "and all parsed configuration data — <b>not</b> the original CSV/XLSX files."),
                unsafe_allow_html=True)

        with pr2:
            section("Load Saved Project")
            _saved = _list_saved_projects()
            if not _saved:
                st.markdown(notif("info", "No saved projects yet — save one first."),
                            unsafe_allow_html=True)
            else:
                _proj_names = {p.stem: p for p in _saved}
                _proj_labels = list(_proj_names.keys())
                _sel_proj = st.selectbox(
                    "Select project",
                    options=_proj_labels,
                    key="sel_load_proj",
                )
                if _sel_proj:
                    _sel_path = _proj_names[_sel_proj]
                    try:
                        _meta = json.loads(_sel_path.read_text(encoding="utf-8"))
                        _saved_at = _meta.get("saved_at", "—")
                        _saved_client = _meta.get("client_name", "—")
                        _saved_disc = _meta.get("discount_pct", "—")
                        _saved_model = (_meta.get("project_data") or {}).get("model_code", "—")
                        st.markdown(f"""
| Field | Value |
|---|---|
| Client | {_saved_client} |
| Model | {_saved_model} |
| Discount | {_saved_disc}% |
| Saved | {_saved_at} |
""")
                    except Exception:
                        pass
                    if st.button("📂  Load Project", type="primary",
                                 use_container_width=True, key="btn_load_proj"):
                        _load_project(_sel_path)
                        st.markdown(notif("ok", f"Loaded: <b>{_sel_proj}</b>. Documents tab is ready."),
                                    unsafe_allow_html=True)
                        st.rerun()

                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                section("Delete Saved Project")
                _del_names = [p.stem for p in _saved]
                _del_sel = st.selectbox("Select to delete", _del_names, key="sel_del_proj")
                if st.button("🗑  Delete", key="btn_del_proj"):
                    _dp = _proj_names.get(_del_sel)
                    if _dp and _dp.exists():
                        _dp.unlink()
                        st.markdown(notif("ok", f"Deleted <b>{_del_sel}</b>."),
                                    unsafe_allow_html=True)
                        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.ibm-footer {
  background: var(--gray-10);
  border-top: 1px solid var(--gray-20);
  padding: 32px 40px;
  margin-top: 48px;
}
.ibm-footer-row {
  display: flex; align-items: flex-start;
  justify-content: space-between; gap: 40px;
  flex-wrap: wrap;
}
.ibm-footer-brand {
  font-size: 13px; font-weight: 600; color: var(--gray-100);
  margin-bottom: 6px; font-family: 'IBM Plex Sans', sans-serif;
}
.ibm-footer-brand span { color: var(--blue-text); font-weight: 300; }
.ibm-footer-sub {
  font-size: 12px; color: var(--gray-50);
  font-family: 'IBM Plex Sans', sans-serif; line-height: 1.5;
}
.ibm-footer-col { flex: 1; min-width: 180px; }
.ibm-footer-col-title {
  font-size: 11px; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.08em; color: var(--gray-70);
  margin-bottom: 10px; font-family: 'IBM Plex Sans', sans-serif;
}
.ibm-footer-item {
  display: flex; align-items: center; gap: 8px;
  font-size: 13px; color: var(--gray-70);
  margin-bottom: 8px; font-family: 'IBM Plex Sans', sans-serif;
}
.ibm-footer-item .ibm-tag { margin-top: 0; padding: 2px 7px; font-size: 10px; }
.ibm-footer-copy {
  margin-top: 24px; padding-top: 16px; border-top: 1px solid var(--gray-20);
  font-size: 11px; color: var(--gray-50);
  font-family: 'IBM Plex Sans', sans-serif;
}
</style>
<div class="ibm-footer">
  <div class="ibm-footer-row">
    <div class="ibm-footer-col" style="flex:1.4">
      <div class="ibm-footer-brand">Ace <span>of Sales</span></div>
      <div class="ibm-footer-sub">
        IBM Storage Sales Project Centre<br>
        Automates Executive Summary, RFP/RFI, and Special Bid documents<br>
        from IBM e-config and Storage Modeller exports.
      </div>
    </div>
    <div class="ibm-footer-col">
      <div class="ibm-footer-col-title">Roadmap</div>
      <div class="ibm-footer-item">
        📋 &nbsp;Executive Summary
        <span class="ibm-tag ibm-tag-blue">Live</span>
      </div>
      <div class="ibm-footer-item">
        📝 &nbsp;Technical RFP / RFI
        <span class="ibm-tag ibm-tag-blue">Live</span>
      </div>
      <div class="ibm-footer-item">
        💼 &nbsp;Special Bid Request
        <span class="ibm-tag ibm-tag-blue">Live</span>
      </div>
      <div class="ibm-footer-item">
        🇵🇱 &nbsp;Polish Language
        <span class="ibm-tag ibm-tag-blue">Live</span>
      </div>
    </div>
    <div class="ibm-footer-col">
      <div class="ibm-footer-col-title">Supported Inputs</div>
      <div class="ibm-footer-item">📄 &nbsp;IBM e-config Cloud CSV</div>
      <div class="ibm-footer-item">📊 &nbsp;Storage Modeller Capacity XLSX</div>
      <div class="ibm-footer-item">📊 &nbsp;Storage Modeller Performance XLSX</div>
    </div>
  </div>
  <div class="ibm-footer-copy">
    IBM, FlashSystem, and FlashCore are trademarks of International Business Machines Corporation.
    Prices shown are list prices from IBM e-config and do not constitute a binding offer.
  </div>
</div>
""", unsafe_allow_html=True)

"""Build an IEEE-style two-column PDF of the ShopSense report with ReportLab.

Content mirrors report/shopsense_report.tex.
Usage: python build_report_pdf.py <report_dir>
"""
import sys
from pathlib import Path

from PIL import Image as PILImage
from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (BaseDocTemplate, Frame, FrameBreak, Image, KeepTogether,
                                NextPageTemplate, PageTemplate, Paragraph, Spacer, Table,
                                TableStyle)

REPORT = Path(sys.argv[1])
FIG = REPORT / "figures"
OUT = REPORT / "ShopSense_AI_Report.pdf"

PAGE_W, PAGE_H = A4
MARGIN_X, MARGIN_TOP, MARGIN_BOTTOM = 16 * mm, 18 * mm, 20 * mm
GAP = 6 * mm
COL_W = (PAGE_W - 2 * MARGIN_X - GAP) / 2
TITLE_H = 74 * mm

# ---------------------------------------------------------------- styles
base = dict(fontName="Times-Roman", fontSize=9.6, leading=11.6)
body = ParagraphStyle("body", alignment=TA_JUSTIFY, firstLineIndent=10, spaceAfter=2, **base)
body_noindent = ParagraphStyle("body0", parent=body, firstLineIndent=0)
title = ParagraphStyle("title", fontName="Times-Roman", fontSize=20, leading=24,
                       alignment=TA_CENTER, spaceAfter=10)
author = ParagraphStyle("author", fontName="Times-Roman", fontSize=9.5, leading=11.5,
                        alignment=TA_CENTER)
abstract = ParagraphStyle("abstract", fontName="Times-Bold", fontSize=8.8, leading=10.6,
                          alignment=TA_JUSTIFY, spaceAfter=6)
h1 = ParagraphStyle("h1", fontName="Times-Roman", fontSize=9.6, leading=12, alignment=TA_CENTER,
                    spaceBefore=8, spaceAfter=4)
h2 = ParagraphStyle("h2", fontName="Times-Italic", fontSize=9.6, leading=12, alignment=TA_LEFT,
                    spaceBefore=5, spaceAfter=2)
caption = ParagraphStyle("caption", fontName="Times-Roman", fontSize=8, leading=9.6,
                         alignment=TA_JUSTIFY, spaceBefore=3, spaceAfter=8)
tcaption = ParagraphStyle("tcaption", fontName="Times-Roman", fontSize=8, leading=9.6,
                          alignment=TA_CENTER, spaceBefore=6, spaceAfter=3)
cell = ParagraphStyle("cell", fontName="Times-Roman", fontSize=8, leading=9.4)
cellb = ParagraphStyle("cellb", parent=cell, fontName="Times-Bold")
equation = ParagraphStyle("eq", fontName="Times-Italic", fontSize=9.6, leading=13,
                          alignment=TA_CENTER, spaceBefore=3, spaceAfter=3)
listitem = ParagraphStyle("li", parent=body, firstLineIndent=0, leftIndent=12, bulletIndent=2)
ref = ParagraphStyle("ref", fontName="Times-Roman", fontSize=8, leading=9.6,
                     alignment=TA_JUSTIFY, leftIndent=14, firstLineIndent=-14, spaceAfter=2)

ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI"]
counters = {"sec": 0, "sub": 0, "fig": 0, "tab": 0}
story = []


def P(text, style=body):
    story.append(Paragraph(text, style))


def section(name, numbered=True):
    counters["sub"] = 0
    if numbered:
        label = f"{ROMAN[counters['sec']]}. {name.upper()}"
        counters["sec"] += 1
    else:
        label = name.upper()
    story.append(Paragraph(label, h1))


def subsection(name):
    letter = chr(ord("A") + counters["sub"])
    counters["sub"] += 1
    story.append(Paragraph(f"{letter}. {name}", h2))


def figure(filename, text, width_frac=1.0):
    counters["fig"] += 1
    path = FIG / filename
    w, h = PILImage.open(path).size
    width = COL_W * width_frac
    img = Image(str(path), width=width, height=width * h / w)
    img.hAlign = "CENTER"
    story.append(KeepTogether([
        Spacer(1, 3), img,
        Paragraph(f"Fig. {counters['fig']}. {text}", caption)]))


def table(title_text, rows, col_widths):
    counters["tab"] += 1
    data = [[Paragraph(str(c), cellb if r == 0 else cell) for c in row]
            for r, row in enumerate(rows)]
    t = Table(data, colWidths=col_widths, hAlign="CENTER")
    t.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 0.8, colors.black),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
        ("LINEBELOW", (0, -1), (-1, -1), 0.8, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(KeepTogether([
        Paragraph(f"TABLE {ROMAN[counters['tab'] - 1]}<br/>{title_text.upper()}", tcaption),
        t, Spacer(1, 6)]))


def architecture_diagram():
    w, h = COL_W, 150
    d = Drawing(w, h)
    blue, violet, grey = colors.HexColor("#EEF2FF"), colors.HexColor("#F3E8FF"), colors.HexColor("#F1F5F9")

    def box(x, y, bw, bh, lines, fill):
        d.add(Rect(x, y, bw, bh, rx=3, ry=3, fillColor=fill, strokeColor=colors.HexColor("#334155"),
                   strokeWidth=0.6))
        for i, line in enumerate(lines):
            d.add(String(x + bw / 2, y + bh / 2 + (len(lines) - 1) * 4.5 - i * 9 - 2.5, line,
                         fontName="Times-Roman", fontSize=7.4, textAnchor="middle"))

    def arrow(x1, y1, x2, y2, both=False, dashed=False):
        line = Line(x1, y1, x2, y2, strokeColor=colors.HexColor("#334155"), strokeWidth=0.7)
        if dashed:
            line.strokeDashArray = [2, 2]
        d.add(line)
        import math
        ang = math.atan2(y2 - y1, x2 - x1)
        for (px, py, a) in ([(x2, y2, ang)] + ([(x1, y1, ang + math.pi)] if both else [])):
            d.add(Polygon([px, py, px - 5 * math.cos(a - 0.4), py - 5 * math.sin(a - 0.4),
                           px - 5 * math.cos(a + 0.4), py - 5 * math.sin(a + 0.4)],
                          fillColor=colors.HexColor("#334155"), strokeWidth=0))

    cx = w / 2
    box(cx - 52, 118, 104, 28, ["React frontend", "(survey, chat widget)"], blue)
    box(cx - 58, 70, 116, 28, ["Flask backend / gateway", "(auth, products, survey)"], blue)
    box(2, 74, 58, 20, ["PostgreSQL"], grey)
    box(4, 8, 70, 34, ["Content-based", "+ SVD"], violet)
    box(cx - 35, 8, 70, 34, ["NCF + hybrid", "(PyTorch)"], violet)
    box(w - 84, 8, 80, 34, ["NLP service", "(search, sentiment,", "chatbot)"], violet)
    arrow(cx, 117, cx, 99, both=True)
    d.add(String(cx + 4, 106, "REST", fontName="Times-Italic", fontSize=6.5))
    arrow(cx - 30, 69, 40, 43)
    arrow(cx, 69, cx, 43)
    arrow(cx + 30, 69, w - 44, 43)
    arrow(61, 84, cx - 59, 84, both=True)
    arrow(cx + 53, 132, w - 22, 43, dashed=True)
    d.add(String(w - 40, 104, "WebSocket", fontName="Times-Italic", fontSize=6.5))
    counters["fig"] += 1
    story.append(KeepTogether([d, Paragraph(
        f"Fig. {counters['fig']}. High-level architecture. The chatbot uses a WebSocket directly "
        "to the NLP service; everything else goes through the backend gateway.", caption)]))


# ---------------------------------------------------------------- page templates
def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Times-Roman", 8)
    canvas.drawCentredString(PAGE_W / 2, 10 * mm, str(doc.page))
    canvas.restoreState()


col_h_first = PAGE_H - MARGIN_TOP - MARGIN_BOTTOM - TITLE_H
col_h = PAGE_H - MARGIN_TOP - MARGIN_BOTTOM
first = PageTemplate(id="first", onPage=footer, frames=[
    Frame(MARGIN_X, PAGE_H - MARGIN_TOP - TITLE_H, PAGE_W - 2 * MARGIN_X, TITLE_H, id="title",
          leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0),
    Frame(MARGIN_X, MARGIN_BOTTOM, COL_W, col_h_first, id="c1", leftPadding=0, rightPadding=0,
          topPadding=0, bottomPadding=0),
    Frame(MARGIN_X + COL_W + GAP, MARGIN_BOTTOM, COL_W, col_h_first, id="c2", leftPadding=0,
          rightPadding=0, topPadding=0, bottomPadding=0),
])
later = PageTemplate(id="later", onPage=footer, frames=[
    Frame(MARGIN_X, MARGIN_BOTTOM, COL_W, col_h, id="l1", leftPadding=0, rightPadding=0,
          topPadding=0, bottomPadding=0),
    Frame(MARGIN_X + COL_W + GAP, MARGIN_BOTTOM, COL_W, col_h, id="l2", leftPadding=0,
          rightPadding=0, topPadding=0, bottomPadding=0),
])
doc = BaseDocTemplate(str(OUT), pagesize=A4, pageTemplates=[first, later],
                      title="ShopSense AI: A Student-Focused Shopping Platform",
                      author="Aanchal Yadav, Riya Aryan, Susmita, Sneha",
                      subject="Hybrid recommendations, semantic search and review intelligence")

# ---------------------------------------------------------------- title block
P("ShopSense AI: A Student-Focused Shopping Platform with Hybrid Recommendations, "
  "Semantic Search and Review Intelligence", title)
authors = [("Aanchal Yadav"), ("Riya Aryan"), ("Susmita"), ("Sneha")]
aff = ("<i>Dept. of Computer Science and Engineering</i><br/><i>[College Name]</i><br/>[City], India")
t = Table([[Paragraph(f"{name}<br/>{aff}", author) for name in authors]],
          colWidths=[(PAGE_W - 2 * MARGIN_X) / 4] * 4)
t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
story.append(t)
story.append(NextPageTemplate("later"))
story.append(FrameBreak())

# ---------------------------------------------------------------- abstract
P("<i>Abstract</i>—Students buying things for college (a first laptop, a calculator for an "
  "engineering exam, a kettle for the hostel room) often know what they need but not what the "
  "product is called. Typical e-commerce search expects exact keywords, and new users get generic "
  "suggestions because the site knows nothing about them yet. We built ShopSense AI, a web "
  "platform for this audience that combines several recommendation approaches with natural "
  "language processing. Four models contribute recommendations: a content-based model using "
  "TF-IDF with fuzzy, adaptive interaction weights; an SVD collaborative filter; a Neural "
  "Collaborative Filtering (NeuMF) model; and a survey-based model in which a new user's answers "
  "are written out as a sentence and matched against products using sentence embeddings. A "
  "gateway blends these signals and explains each suggestion. On the language side, the platform "
  "offers semantic search with MiniLM embeddings and a FAISS index, review analysis with VADER "
  "sentiment and TF-IDF theme extraction, and a chatbot that can search, recommend, compare "
  "products and summarise reviews. In our tests, semantic search answered in about 15–21 ms at "
  "the 95th percentile, the intended product appeared in the top three for all 15 "
  "natural-language test queries, and the chatbot classified all 30 labelled test messages "
  "correctly. We also discuss the limits of our evaluation, mainly the small catalogue and the "
  "synthetic review data.", abstract)
P("<i>Index Terms</i>—recommender systems, neural collaborative filtering, semantic search, "
  "sentiment analysis, conversational agents, cold start", abstract)

# ---------------------------------------------------------------- I. Introduction
section("Introduction")
P("Most of us have searched a shopping site for something like “a bottle that keeps tea hot” and "
  "got results for tea bags. Keyword search works well when you already know the product name, "
  "and much less well when you only know the problem you are trying to solve. Students are a good "
  "example of this. They are often buying a category of product for the first time, they work to "
  "tight budgets, and their needs are tied to situations such as online classes, coding "
  "assignments or living in a hostel.")
P("A second problem appears on the first visit. Recommendation engines learn from clicks and "
  "purchases, so a new user with no history usually sees a list of best-sellers, which may have "
  "little to do with what they need. This is the well-known cold-start problem [1].")
P("A third problem is reviews. Popular products can have hundreds of them, and few people read "
  "more than a handful before deciding.")
P("ShopSense AI tries to address all three. It is a full-stack web application with a React "
  "frontend, a Flask backend and separate services for recommendation and language processing. "
  "The work was split among four team members: the frontend and content-based model; the backend "
  "and collaborative filtering; the deep-learning recommender and hybrid engine; and the NLP "
  "service with the chatbot and survey. This paper describes how the pieces fit together, what "
  "each model does, and how well the system performed in our tests.")

# ---------------------------------------------------------------- II. Related work
section("Related Work")
P("Content-based recommenders describe items by their features and suggest items similar to "
  "those a user liked before [2]. They handle new items well but tend to keep suggesting more of "
  "the same. Collaborative filtering instead learns from the behaviour of many users. Matrix "
  "factorisation methods such as SVD became widely used after the Netflix Prize [3]. He <i>et "
  "al.</i> [4] showed that replacing the inner product with a neural network (Neural "
  "Collaborative Filtering) can capture non-linear user–item interactions. Hybrid systems combine "
  "several of these approaches to offset their individual weaknesses [5].")
P("For search, Sentence-BERT [6] made it practical to compare short texts by meaning, and "
  "libraries such as FAISS [7] make nearest-neighbour lookup over the resulting vectors fast. For "
  "review analysis, VADER [8] is a rule-based sentiment model that needs no training data and runs "
  "quickly, while transformer models such as DistilBERT [9] are more expressive but heavier. Fuzzy "
  "logic [10] has also been used to soften fixed thresholds and weights in recommenders. Our "
  "contribution is mostly in combining these known techniques around a student use case, and in "
  "using the same embedding space for both search and survey-based cold-start recommendations.")

# ---------------------------------------------------------------- III. Objectives
section("Objectives")
P("We set the following goals at the start of the project:", body_noindent)
for i, item in enumerate([
        "Recommend products that match a student's needs, budget and behaviour, including on "
        "their very first visit.",
        "Let users search in plain language instead of exact keywords.",
        "Summarise customer reviews into a sentiment score and a short list of what people like "
        "and dislike.",
        "Provide a chatbot that can find, recommend and compare products and answer questions "
        "about reviews.",
        "Compare the individual recommendation models and the hybrid on standard ranking "
        "metrics."], 1):
    story.append(Paragraph(item, listitem, bulletText=f"{i})"))

# ---------------------------------------------------------------- IV. Architecture
section("System Architecture")
P("Fig. 1 shows the overall design. The React single-page application talks only to the Flask "
  "backend, which acts as a gateway. The backend owns the database (users, products, reviews, "
  "interactions, cart, wishlist and survey answers) and forwards AI requests to the services "
  "behind it: the content-based and SVD service, the NCF hybrid service, and the NLP service. "
  "Every call to an AI service has a short timeout and a fallback. If the NLP service is down, "
  "for example, semantic search falls back to keyword search instead of failing.")
architecture_diagram()

# ---------------------------------------------------------------- V. Methodology
section("Methodology")
subsection("Data")
P("The catalogue has 20 real products in nine student-oriented categories: laptops, tablets, "
  "smartphones, audio, computer accessories, study essentials, hostel essentials, backpacks, and "
  "storage. Each product has a description, specifications and links to marketplaces. Since we "
  "had no real customer reviews for these exact products, we generated 240 <i>synthetic</i> "
  "reviews (12 per product) from product-specific phrases about real strengths and weaknesses, "
  "such as soldered RAM on one laptop or expensive ink on the printer. Star ratings were drawn "
  "from a per-product distribution and the text was written to match the rating, with "
  "deliberately mixed 3-star reviews. Four demo users with different personas and 16 reviewer "
  "accounts produce 502 interaction events (view, click, wishlist, cart and purchase). We state "
  "this clearly because it limits how far our sentiment results can be generalised.")
subsection("Content-Based Model with Fuzzy Weights")
P("Each product is represented by a TF-IDF vector over its name, description, category and a set "
  "of keywords. A user's profile is the weighted average of the vectors of the products they "
  "interacted with. Instead of fixed weights per event type, the weights adapt to the user: the "
  "frequency of each event type is mapped to low, medium and high fuzzy memberships, defuzzified, "
  "and used to adjust the base weight by at most 10%. The adjustment is scaled by a confidence "
  "term <i>n</i>/(<i>n</i>+10), where <i>n</i> is the number of interactions. The final score "
  "combines profile similarity (65%) with item-to-item similarity (35%), excludes items already "
  "bought or in the cart, and caps any single category at three results to keep some variety.")
subsection("Collaborative Filtering (SVD)")
P("Interactions are converted to implicit ratings from 1 to 5 (view = 1 up to purchase = 5, "
  "summed and capped) to form a user–item matrix. Our first version used a truncated NumPy SVD "
  "with <i>k</i> = 2 latent factors. The final version uses the SVD implementation in the "
  "Surprise library (10 factors, 40 epochs), which learns user and item biases and only fits the "
  "observed ratings. Unseen items are ranked by their predicted rating, and new users fall back "
  "to a popularity ranking.")
subsection("Neural Collaborative Filtering")
P("The NeuMF model [4] has two branches. The GMF branch takes the element-wise product of "
  "32-dimensional user and item embeddings. The MLP branch concatenates separate embeddings and "
  "passes them through layers of 64, 32 and 16 units with ReLU. Both outputs are concatenated and "
  "fed to a sigmoid output. Training uses binary cross-entropy, with four sampled negatives per "
  "positive and the Adam optimiser (learning rate 0.001) for 20 epochs. We keep the checkpoint "
  "with the lowest training loss.")
subsection("Hybrid Engine and Recommendation Gateway")
P("The hybrid engine min–max normalises the three model scores and combines them as",
  body_noindent)
P("s<sub>hybrid</sub> = 0.3 s<sub>SVD</sub> + 0.3 s<sub>CB</sub> + 0.4 s<sub>NCF</sub>"
  "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;(1)", equation)
P("The backend gateway then blends whichever signals exist for the current user (hybrid, "
  "content-based history, survey and popularity), weighting them 0.45, 0.30, 0.35 and 0.10 and "
  "renormalising over the sources that are available. Each recommendation keeps the source that "
  "contributed most to it, which becomes the explanation shown to the user, such as “Similar to "
  "products you've interacted with” or “Matches your interest in Laptops”.", body_noindent)
subsection("Semantic Search")
P("For every product we join the name, brand, category, description and specifications, clean "
  "the text, and encode it with all-MiniLM-L6-v2 [6] into a 384-dimensional unit vector. The "
  "vectors go into a FAISS IndexFlatIP index [7], where the inner product equals cosine "
  "similarity. A query is encoded the same way and the closest products are returned, with "
  "optional price and category filters. The index is saved with a fingerprint of the catalogue "
  "and is rebuilt only when products change.")
subsection("Sentiment Analysis and Review Summaries")
P("Each review is scored with VADER [8]. A compound score above 0.05 counts as positive, below "
  "−0.05 as negative, and anything in between as neutral. VADER was built for social media text "
  "and misses many product-specific complaint words such as “expensive”, “lags” and “leaks”, so "
  "we added a small e-commerce lexicon of about 70 words at 0.7 of their base weight. We left out "
  "context-dependent words such as “hot” (as in “keeps tea hot”). For each product we count the "
  "sentiment classes and extract themes with TF-IDF over phrases of adjacent words, ranking a "
  "phrase by how much more often it appears on one side (positive or negative) than the other. "
  "This produces themes such as “ink cartridges” for the printer and “headband cracked” for one "
  "of the headphones, along with a one-sentence verdict.")
subsection("Conversational Assistant")
P("The chatbot uses a rule-based intent router with seven intents: greeting, help, search, "
  "recommendation, comparison, review summary and product information, plus a fallback. "
  "Alongside the intent it extracts products, budgets and categories. Product names are matched "
  "by weighting each word of the name by how identifying it is: a model number unique to one "
  "product (“CH520”, “A9”) counts much more than a shared word like “headphones”. Budgets such as "
  "“under 5k” or “between 2000 and 4000” are parsed with regular expressions. The bot remembers "
  "the products from its last answer, so follow-ups like “what do people think about it?” or "
  "“compare them” work as expected. Responses are structured JSON, so the frontend can show "
  "product cards, comparison tables and sentiment bars instead of plain text. Messages travel "
  "over Flask-SocketIO, with a REST fallback.")
subsection("Preference Survey for Cold Start")
P("New users can fill in a five-step survey covering their role, categories of interest, "
  "intended use, budget, priorities, preferred brands and an optional free-text description. The "
  "answers are turned into a short need statement, for example “I am a college undergraduate "
  "student. I will use it for hostel room living…”, which is embedded in the same space as the "
  "products. Each product then receives")
P("s = 0.40 s<sub>sem</sub> + 0.25 s<sub>cat</sub> + 0.20 s<sub>budget</sub> + 0.10 "
  "s<sub>sent</sub> + 0.05 s<sub>brand</sub>&nbsp;&nbsp;&nbsp;(2)", equation)
P("where s<sub>budget</sub> falls off smoothly as (<i>B</i>/<i>p</i>)<super>2</super> for items "
  "priced <i>p</i> above the budget <i>B</i>, and s<sub>sent</sub> is the share of positive "
  "reviews. The result page shows a match percentage and the reasons behind each pick.",
  body_noindent)

# ---------------------------------------------------------------- VI. Implementation
section("Implementation")
P("The frontend uses React with Vite and Tailwind CSS. The backend uses Flask with SQLAlchemy, "
  "Flask-JWT-Extended and PostgreSQL. The recommendation models use scikit-learn, NumPy and "
  "PyTorch, and the hybrid is served with FastAPI. The NLP service uses sentence-transformers, "
  "FAISS, vaderSentiment and Flask-SocketIO. A Docker Compose file starts the whole stack. For a "
  "lightweight hosted demo we also run the backend, recommender and NLP code inside a single "
  "serverless function on Vercel; this version uses TF-IDF vectors and REST chat because the "
  "transformer model exceeds the platform's size limit. Personal recommendations are cached for "
  "an hour under the key user:{id}:recs (in Redis when available) and invalidated whenever the "
  "user changes their cart, wishlist, survey or interaction history. The schema is managed with "
  "Alembic migrations. The project has 106 automated tests across the backend and the NLP "
  "service.")

# ---------------------------------------------------------------- VII. Results
section("Results")
subsection("Search, Sentiment and Chatbot")
P("Table I summarises the NLP benchmarks, run on a laptop CPU. Search latency is far below our "
  "200 ms target. For relevance, we wrote 15 queries that describe a need rather than name a "
  "product, such as “something to keep my tea hot during lectures” and “solve matrices in the "
  "engineering exam”. In every case the intended product was among the top three results, and in "
  "most cases it was first.")
table("NLP Service Benchmarks", [
    ["Metric", "Result"],
    ["Search latency, mean / p95 (60 queries)", "13–14 / 15–21 ms"],
    ["Relevance: hit rate@3 (15 queries)", "15/15"],
    ["Intent accuracy (30 labelled messages)", "30/30"],
], [COL_W * 0.66, COL_W * 0.30])
P("Table II compares sentiment models on a random sample of 100 reviews, with star ratings as "
  "ground truth (4–5 positive, 3 neutral, 1–2 negative). Plain VADER did slightly better on this "
  "sample, and the two VADER variants tied at 81% over all 240 reviews. We kept the domain "
  "lexicon because it fixes product-level verdicts: without it, VADER labelled 8 of the "
  "printer's 12 reviews positive even though the average rating was 3 stars. DistilBERT "
  "fine-tuned on SST-2 scored poorly, mostly because it only predicts two classes and our "
  "reviews are often mixed. The neutral class is the weak spot for every model, since a 3-star "
  "review that praises one thing and criticises another rarely reads as neutral.")
table("Sentiment Accuracy Against Star Ratings (100 Reviews)", [
    ["Model", "3-class", "Pos. vs. neg.", "ms/review"],
    ["VADER", "85%", "93%", "0.1"],
    ["VADER + domain lexicon", "82%", "91%", "0.1"],
    ["DistilBERT (SST-2)", "56%", "63%", "24"],
], [COL_W * 0.42, COL_W * 0.17, COL_W * 0.22, COL_W * 0.17])
subsection("Recommendation Models")
P("For rating prediction on a timestamp split (80/20 per user), Surprise SVD reached an RMSE of "
  "0.53 and MAE of 0.17, against 2.94 and 2.64 for the first NumPy version. The NumPy version "
  "treated every unobserved entry as zero, which pulled its predictions down.")
P("To compare all five approaches on equal terms, we ran a leave-one-out evaluation over the 19 "
  "users with at least two products. Each user's most recent product was held out and ranked "
  "against the products they had not touched (7.7 candidates on average); ties counted against "
  "the model. Table III and Fig. 2 show the results. Content-based filtering gave the best "
  "NDCG@10 and MRR, and NCF the best hit rate. The hybrid came close to the best single models "
  "but did not beat them, even after we tuned its weights by grid search on a separate "
  "validation split, which moved weight from SVD to the content model. We think the reason is "
  "the data: the reviewer histories are random, so there is little collaborative signal for the "
  "hybrid to add, and with only 20 products a single position in the ranking changes the "
  "metrics noticeably. We report this as it is rather than tuning on the test set.")
table("Leave-One-Out Comparison (19 Users)", [
    ["Model", "HR@10", "NDCG@10", "MRR"],
    ["Popularity", "0.947", "0.373", "0.204"],
    ["SVD (Surprise)", "0.947", "0.412", "0.250"],
    ["Content-based (TF-IDF)", "0.947", "<b>0.576</b>", "<b>0.465</b>"],
    ["NCF (NeuMF)", "<b>1.000</b>", "0.569", "0.434"],
    ["Hybrid (0.3 / 0.3 / 0.4)", "0.895", "0.559", "0.460"],
    ["Hybrid, tuned (0.1 / 0.5 / 0.4)", "0.895", "0.557", "0.458"],
], [COL_W * 0.46, COL_W * 0.16, COL_W * 0.2, COL_W * 0.16])
figure("hr_ndcg_by_model.png", "HR@10 and NDCG@10 for each recommendation model.")
subsection("User Interface")
P("Figs. 3–6 show the system in use. The survey (Fig. 4) gave sensible results for a "
  "hostel-living persona with a Rs. 3,000 budget: backpacks, a thermos bottle, the kettle and a "
  "power extender ranked at the top, each with a reason attached.")
figure("02_semantic_search.png",
       "Semantic search for “something to keep my tea hot in class”: the insulated bottle and the "
       "kettle rank first.")
figure("03c_survey_results.png",
       "Survey results for a hostel student with a Rs. 3,000 budget, with match scores and "
       "reasons.")
figure("05_product_review_analysis.png",
       "Review analysis for the printer: sentiment split, praise and complaint themes, verdict "
       "and per-review labels.")
figure("06b_chat_compare.png", "The chatbot comparing two tablets side by side.", 0.62)

# ---------------------------------------------------------------- VIII. Limitations
section("Limitations")
P("The biggest limitation is the data. The reviews are synthetic, so the sentiment numbers show "
  "that the pipeline works rather than how accurate it would be on real customer text, and we "
  "tuned the domain lexicon on the same reviews. The catalogue of 20 products and the small "
  "number of users make the recommendation metrics fragile. The chatbot is rule-based. It is "
  "predictable and fast, but it will miss phrasings we did not anticipate. Finally, the hosted "
  "demo replaces MiniLM with TF-IDF vectors, which match meaning less well than the full "
  "version.")

# ---------------------------------------------------------------- IX. Conclusion
section("Conclusion and Future Work")
P("ShopSense AI shows that a fairly small set of well-understood techniques, combined carefully, "
  "can make online shopping noticeably easier for students. Semantic search lets people describe "
  "what they need. The survey gives useful recommendations from the first visit. Review "
  "summaries save reading time, and the chatbot brings these features together in one place. "
  "Next, we want to collect real reviews and interaction data and rerun the model comparison on "
  "it, since we expect the hybrid to benefit most from genuine collaborative signal. We would "
  "also like to replace parts of the rule-based chatbot with a learned intent classifier.")

section("Individual Contributions", numbered=False)
P("<b>Aanchal Yadav</b> built the React frontend and the content-based TF-IDF recommender. "
  "<b>Riya Aryan</b> designed the database, built the Flask REST APIs with JWT authentication, "
  "and developed the SVD model, popularity fallback and fuzzy interaction weights. "
  "<b>Susmita</b> implemented and trained the NeuMF model and built the hybrid engine served "
  "through FastAPI. <b>Sneha</b> built the NLP service (semantic search, sentiment analysis and "
  "review summaries, and the chatbot), the preference survey and its recommender, the "
  "cross-model evaluation, and the integration, testing and deployment.", body_noindent)

section("References", numbered=False)
for i, r in enumerate([
        "A. I. Schein, A. Popescul, L. H. Ungar and D. M. Pennock, “Methods and metrics for "
        "cold-start recommendations,” in <i>Proc. 25th ACM SIGIR Conf.</i>, 2002, pp. 253–260.",
        "P. Lops, M. de Gemmis and G. Semeraro, “Content-based recommender systems: State of the "
        "art and trends,” in <i>Recommender Systems Handbook</i>, Springer, 2011, pp. 73–105.",
        "Y. Koren, R. Bell and C. Volinsky, “Matrix factorization techniques for recommender "
        "systems,” <i>Computer</i>, vol. 42, no. 8, pp. 30–37, 2009.",
        "X. He, L. Liao, H. Zhang, L. Nie, X. Hu and T.-S. Chua, “Neural collaborative "
        "filtering,” in <i>Proc. 26th Int. Conf. World Wide Web</i>, 2017, pp. 173–182.",
        "R. Burke, “Hybrid recommender systems: Survey and experiments,” <i>User Modeling and "
        "User-Adapted Interaction</i>, vol. 12, no. 4, pp. 331–370, 2002.",
        "N. Reimers and I. Gurevych, “Sentence-BERT: Sentence embeddings using Siamese "
        "BERT-networks,” in <i>Proc. EMNLP-IJCNLP</i>, 2019, pp. 3982–3992.",
        "J. Johnson, M. Douze and H. Jégou, “Billion-scale similarity search with GPUs,” <i>IEEE "
        "Trans. Big Data</i>, vol. 7, no. 3, pp. 535–547, 2021.",
        "C. J. Hutto and E. Gilbert, “VADER: A parsimonious rule-based model for sentiment "
        "analysis of social media text,” in <i>Proc. 8th Int. AAAI Conf. Weblogs and Social "
        "Media</i>, 2014.",
        "V. Sanh, L. Debut, J. Chaumond and T. Wolf, “DistilBERT, a distilled version of BERT: "
        "Smaller, faster, cheaper and lighter,” arXiv:1910.01108, 2019.",
        "L. A. Zadeh, “Fuzzy sets,” <i>Information and Control</i>, vol. 8, no. 3, pp. 338–353, "
        "1965."], 1):
    story.append(Paragraph(f"[{i}]&nbsp;&nbsp;{r}", ref))

doc.build(story)
print("wrote", OUT)

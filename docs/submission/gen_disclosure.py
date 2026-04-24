from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable, PageBreak)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

W, H = A4

doc = SimpleDocTemplate(
    'docs/submission/AI_DISCLOSURE.pdf',
    pagesize=A4,
    leftMargin=2.5*cm, rightMargin=2.5*cm,
    topMargin=2.5*cm, bottomMargin=2.5*cm,
    title='AI Use Disclosure - Deepfake Detection MLOps Project',
    author='Major Prabhat Pandey (DA25M002)'
)

styles = getSampleStyleSheet()

DARK       = colors.HexColor('#111827')
GREY       = colors.HexColor('#6b7280')
BLUE       = colors.HexColor('#1d4ed8')
GREEN      = colors.HexColor('#15803d')
RED        = colors.HexColor('#b91c1c')
DIVIDER    = colors.HexColor('#e5e7eb')
ROW_ALT    = colors.HexColor('#f9fafb')

title_style = ParagraphStyle('title_style', fontSize=20, fontName='Helvetica-Bold',
    textColor=DARK, spaceAfter=4, leading=26)
subtitle_style = ParagraphStyle('subtitle_style', fontSize=11, fontName='Helvetica',
    textColor=GREY, spaceAfter=2)
h2_style = ParagraphStyle('h2_style', fontSize=13, fontName='Helvetica-Bold',
    textColor=DARK, spaceBefore=18, spaceAfter=6, leading=18,
    borderPad=4)
h3_style = ParagraphStyle('h3_style', fontSize=11, fontName='Helvetica-Bold',
    textColor=BLUE, spaceBefore=10, spaceAfter=4)
body_style = ParagraphStyle('body_style', fontSize=10, fontName='Helvetica',
    textColor=DARK, leading=15, spaceAfter=4, alignment=TA_JUSTIFY)
bullet_style = ParagraphStyle('bullet_style', fontSize=10, fontName='Helvetica',
    textColor=DARK, leading=15, spaceAfter=3, leftIndent=12)
caption_style = ParagraphStyle('caption_style', fontSize=9, fontName='Helvetica-Oblique',
    textColor=GREY, leading=13, spaceAfter=2)
bold_body = ParagraphStyle('bold_body', fontSize=10, fontName='Helvetica-Bold',
    textColor=DARK, leading=15, spaceAfter=4)
verdict_green = ParagraphStyle('verdict_green', fontSize=9, fontName='Helvetica-Bold',
    textColor=GREEN)
verdict_orange = ParagraphStyle('verdict_orange', fontSize=9, fontName='Helvetica-Bold',
    textColor=colors.HexColor('#b45309'))

story = []

# ── HEADER ────────────────────────────────────────────────────────────────
story.append(Paragraph('AI Use Disclosure', title_style))
story.append(Paragraph('Deepfake Detection System — End-to-End MLOps Project', subtitle_style))
story.append(HRFlowable(width='100%', thickness=2, color=BLUE, spaceAfter=10))

meta_data = [
    ['Student',        'Major Prabhat Pandey'],
    ['Roll No.',       'DA25M002'],
    ['Course',         'AI Application with MLOps (DA5402)'],
    ['Submission',     'April 2026'],
    ['AI Tool Used',   'Claude Code (Anthropic) — CLI coding assistant'],
    ['Scope of Use',   'Boilerplate scaffolding, syntax reference, error diagnosis only'],
]
meta_table = Table(meta_data, colWidths=[4.5*cm, 12.5*cm])
meta_table.setStyle(TableStyle([
    ('FONTNAME',  (0,0), (0,-1), 'Helvetica-Bold'),
    ('FONTNAME',  (1,0), (1,-1), 'Helvetica'),
    ('FONTSIZE',  (0,0), (-1,-1), 10),
    ('TEXTCOLOR', (0,0), (0,-1), GREY),
    ('TEXTCOLOR', (1,0), (1,-1), DARK),
    ('TOPPADDING',    (0,0), (-1,-1), 4),
    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.white, ROW_ALT]),
]))
story.append(meta_table)
story.append(Spacer(1, 0.4*cm))

# ── OVERVIEW ──────────────────────────────────────────────────────────────
story.append(Paragraph('Overview', h2_style))
story.append(Paragraph(
    'This document discloses, completely and accurately, all AI-tool assistance used '
    'during development of the Deepfake Detection MLOps project. All substantive '
    'intellectual work — system design, ML architecture, algorithm selection, training '
    'strategy, monitoring design, API design, frontend design, and all written '
    'documentation — was performed entirely by me.',
    body_style))
story.append(Paragraph(
    'Claude Code was used in a strictly limited, supporting capacity for the seven '
    'specific categories listed below. In every case I understood, reviewed, and '
    'accepted or modified the output before inclusion. AI added no intellectual '
    'content to this project.',
    body_style))
story.append(Spacer(1, 0.3*cm))

# ── SUMMARY TABLE ─────────────────────────────────────────────────────────
story.append(Paragraph('Disclosure Summary', h2_style))

hdr = [
    Paragraph('<b>Component</b>', bold_body),
    Paragraph('<b>AI Role (if any)</b>', bold_body),
    Paragraph('<b>Verdict</b>', bold_body),
]
rows_data = [
    ('System architecture and design',           'None',                              'MY WORK'),
    ('ML model — CNN+LSTM design',               'None',                              'MY WORK'),
    ('DVC pipeline stages and logic',            'None',                              'MY WORK'),
    ('Grad-CAM explainability module',           'None',                              'MY WORK'),
    ('FastAPI backend and all endpoints',        'None',                              'MY WORK'),
    ('React/TypeScript frontend',                'None',                              'MY WORK'),
    ('Airflow DAG definitions',                  'None',                              'MY WORK'),
    ('MLflow experiment tracking setup',         'None',                              'MY WORK'),
    ('Drift detection logic',                    'None',                              'MY WORK'),
    ('Security design (JWT, RBAC)',              'None',                              'MY WORK'),
    ('Test suite (49 tests)',                    'None',                              'MY WORK'),
    ('Alert rules and thresholds',               'None',                              'MY WORK'),
    ('Project report written content',           'None',                              'MY WORK'),
    ('All project documentation',                'None',                              'MY WORK'),
    ('Docker Compose service topology',          'Syntax reference only',             'MY WORK'),
    ('Prometheus metric naming',                 'Naming convention reference',       'MY WORK'),
    ('Grafana PromQL expressions',               'Query syntax examples (verified)',  'MY WORK'),
    ('GitHub Actions CI boilerplate',            'Step scaffolding template',         'MY WORK'),
    ('Error diagnosis (tracebacks)',             'Traceback confirmation only',       'MY WORK'),
    ('Technical diagram SVGs',                   'XML syntax encoding of my designs', 'AI-ASSISTED'),
    ('Report assembly script (docx)',            'python-docx boilerplate',           'AI-ASSISTED'),
]

table_data = [hdr]
for comp, role, verdict in rows_data:
    v_style = verdict_green if verdict == 'MY WORK' else verdict_orange
    table_data.append([
        Paragraph(comp, body_style),
        Paragraph(role, body_style),
        Paragraph(verdict, v_style),
    ])

summary_table = Table(table_data, colWidths=[7.5*cm, 5.5*cm, 3.5*cm])
summary_table.setStyle(TableStyle([
    ('BACKGROUND',  (0,0), (-1,0), BLUE),
    ('TEXTCOLOR',   (0,0), (-1,0), colors.white),
    ('FONTNAME',    (0,0), (-1,0), 'Helvetica-Bold'),
    ('FONTSIZE',    (0,0), (-1,-1), 9),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, ROW_ALT]),
    ('GRID',        (0,0), (-1,-1), 0.5, DIVIDER),
    ('TOPPADDING',    (0,0), (-1,-1), 4),
    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ('VALIGN',      (0,0), (-1,-1), 'TOP'),
]))
story.append(summary_table)
story.append(Spacer(1, 0.4*cm))

# ── DETAILED AI USES ──────────────────────────────────────────────────────
story.append(Paragraph('Detailed Account — Where AI Was Used', h2_style))
story.append(Paragraph(
    'The following documents each instance with full transparency: what I designed and '
    'built, what AI was asked for, and how I reviewed the output.',
    body_style))

ai_uses = [
    {
        'title': '1. Technical Diagram SVG Generation',
        'files': 'docs/submission/arch_diagram.svg, pipeline_flow.svg, dvc_dag.svg, monitoring.svg, api_flow.svg',
        'my_work': (
            'I designed the complete content and structure of all five technical diagrams. '
            'For the architecture diagram I specified every layer (Client, API Gateway, '
            'ML Services, Data/Storage, Monitoring), every service box, every arrow, and '
            'every port number. For the pipeline flow I specified the node sequence and '
            'the three orchestration rows (Airflow, MLflow, Prometheus). For the API '
            'sequence diagram I specified every participant and every message in order. '
            'The diagrams reflect the actual running system I built.'
        ),
        'ai_role': (
            'AI translated my verbal description into valid SVG XML using the '
            'fireworks-tech-graph skill. SVG marker definitions, path syntax, and '
            'viewBox coordinates are mechanical and verbose. AI encoded the structure '
            'I described; it contributed no architectural content or design decision.'
        ),
        'my_review': (
            'I inspected each rendered SVG against the actual running containers, '
            'verifying component names, port numbers, and flow directions. Corrections '
            'were made where labels did not match reality.'
        ),
    },
    {
        'title': '2. Report Assembly Script (python-docx)',
        'files': 'docs/submission/gen_disclosure.py, report insertion scripts',
        'my_work': (
            'I authored all substantive content in project_report.docx — every section, '
            'all technical descriptions, the evaluation criteria mapping, the architecture '
            'narrative, the appendices, and the table of contents. The intellectual '
            'content of the document is entirely mine.'
        ),
        'ai_role': (
            'AI generated the Python scripting boilerplate to insert images into the '
            '.docx file using python-docx (paragraph XML element anchoring, caption '
            'styling, image width specification). This is mechanical file-format '
            'manipulation, not document content.'
        ),
        'my_review': 'I read every line of the script before execution and understood its mechanism.',
    },
    {
        'title': '3. Grafana PromQL Query Syntax',
        'files': 'monitoring/grafana/dashboards/combined_dashboard.json',
        'my_work': (
            'I designed the entire monitoring architecture: what 22 metrics to instrument, '
            'which services to scrape, what dashboards to create (four sections: inference '
            'latency, prediction analytics, system performance, model quality), and what '
            'question each panel should answer. Alert thresholds (5% error rate over 3m, '
            'p95 latency >2s) are my operational decisions.'
        ),
        'ai_role': (
            'For complex PromQL aggregation syntax (histogram_quantile, rate() window '
            'selection, label_replace usage), I asked for syntax examples to avoid '
            're-reading the full PromQL documentation. I described the metric I wanted '
            'to express; AI provided the query form. Equivalent to consulting a reference manual.'
        ),
        'my_review': (
            'Every query was pasted into the Prometheus expression browser and validated '
            'against live data from the running stack before being added to Grafana.'
        ),
    },
    {
        'title': '4. Prometheus Metric Naming Conventions',
        'files': 'backend/app/metrics.py',
        'my_work': (
            'I decided which 22 metrics to create, their types (9 counters, 8 histograms, '
            '5 gauges), and their label dimensions (mode, endpoint, status, model_version). '
            'All instrumentation code in metrics.py is mine. Every increment() and '
            'observe() call throughout main.py and the routers was written by me.'
        ),
        'ai_role': (
            'I asked for a quick reference on Prometheus naming conventions (unit '
            'suffixes: _total, _seconds, _bytes; histogram bucket placement) to ensure '
            'metric names followed the OpenMetrics community standard. Equivalent to '
            'reading a style guide page.'
        ),
        'my_review': 'Final naming choices are mine in every case.',
    },
    {
        'title': '5. Docker Compose Syntax Reference',
        'files': 'docker-compose.yml',
        'my_work': (
            'I designed the entire 10-container topology: which services to run, network '
            'configuration, volume mounts, port mappings, and startup ordering. I made the '
            'substantive optimisation decision to remove three containers (mlflow-serve '
            '9.36 GB, redis 61 MB, celery) after analysing the actual runtime call graph '
            'and finding them unused. That analysis and decision are entirely mine.'
        ),
        'ai_role': (
            'For less-used docker-compose.yml fields (healthcheck test syntax, '
            'depends_on condition types, named vs bind volume semantics), I asked for '
            'quick syntax examples. All field values reflect this project\'s actual requirements.'
        ),
        'my_review': 'Verified against running containers; all values set by me.',
    },
    {
        'title': '6. GitHub Actions CI/CD Scaffolding',
        'files': '.github/workflows/ci.yml',
        'my_work': (
            'I designed the CI pipeline: stages (lint, test, dvc repro --dry, Docker '
            'build), acceptance gates, and what the pipeline must guarantee. The '
            'dvc repro --dry step is my original addition to validate DAG integrity '
            'without running full training in CI. All command invocations are mine.'
        ),
        'ai_role': (
            'The YAML skeleton for a standard actions/checkout + actions/setup-python '
            'workflow was generated from a description I provided. The step content '
            '(commands, flags, test runner invocation) is mine.'
        ),
        'my_review': 'Tested locally against actual test suite before committing.',
    },
    {
        'title': '7. Traceback Diagnosis During Development',
        'files': 'backend/app/preprocessing.py, ml/train.py',
        'my_work': (
            'When errors arose (MTCNN tensor shape mismatches, LSTM input dimension '
            'errors, OpenCV frame extraction edge cases), I read the stack trace, '
            'identified the offending line, and formed a hypothesis. All fixes were '
            'written and tested by me.'
        ),
        'ai_role': (
            'In a small number of cases I pasted a traceback to confirm my diagnosis. '
            'This accelerated confirmation of my own analysis; it did not replace my '
            'debugging process.'
        ),
        'my_review': 'Every fix was committed only after passing tests on my machine.',
    },
]

for use in ai_uses:
    story.append(Paragraph(use['title'], h3_style))
    story.append(Paragraph(
        '<font color="#6b7280"><i>Files: ' + use['files'] + '</i></font>',
        caption_style))
    tbl = Table([
        [Paragraph('<b>My design\n& work</b>', bold_body),   Paragraph(use['my_work'],   body_style)],
        [Paragraph('<b>AI role</b>',             bold_body),  Paragraph(use['ai_role'],   body_style)],
        [Paragraph('<b>My review</b>',           bold_body),  Paragraph(use['my_review'], body_style)],
    ], colWidths=[3.0*cm, 13.5*cm])
    tbl.setStyle(TableStyle([
        ('VALIGN',        (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING',    (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('BACKGROUND',    (0,0), (0,-1),  ROW_ALT),
        ('GRID',          (0,0), (-1,-1), 0.5, DIVIDER),
        ('FONTSIZE',      (0,0), (-1,-1), 10),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 0.2*cm))

# ── NOT AI ────────────────────────────────────────────────────────────────
story.append(PageBreak())
story.append(Paragraph('What AI Was Not Used For', h2_style))
story.append(Paragraph(
    'The following constitutes the large majority of the project and was done entirely by me, '
    'without AI assistance at any stage:',
    body_style))

not_ai = [
    ('ML Architecture',
     'CNN+LSTM design combining EfficientNet-B0 spatial features with LSTM temporal modelling '
     'was my own architectural decision, based on analysis of how deepfake artefacts manifest '
     'across video frames.'),
    ('Model Training',
     'All training code (ml/train.py), hyperparameter choices (lr=1e-4, batch=8, 60 epochs, '
     'gradient clipping), mixed-precision training, INT8 dynamic quantisation for CPU deployment.'),
    ('Data Pipeline Design',
     'DVC pipeline stage design (extract_frames, detect_faces, compute_features, train, evaluate), '
     'MTCNN integration, OpenCV frame sampling strategy using np.linspace.'),
    ('Grad-CAM Explainability',
     'backend/app/explainability.py — hooking the last EfficientNet block, computing gradients '
     'of output w.r.t. activation maps, overlaying heatmaps on face crops.'),
    ('Drift Detection',
     'drift_detector.py — cosine distance of mean feature vectors against DVC-tracked '
     'baseline statistics; BranchPythonOperator integration in Airflow retraining_dag.'),
    ('FastAPI Backend',
     'All 12 API endpoints, Pydantic schemas, router architecture, model hot-reload endpoint, '
     'admin role system, multipart file handling, prediction feedback loop.'),
    ('React/TypeScript Frontend',
     'All 9 pages (Home, Batch, History, Stats, Help, Admin, Dashboard, Model, Tickets), '
     'AuthContext with localStorage persistence, CSS design system with CSS variables, '
     'AbortController request cancellation, all component logic.'),
    ('User Registration System',
     'Tabbed login/register UI, email validation, AuthContext extension with localStorage '
     'persistence — designed and built from scratch.'),
    ('Monitoring Architecture',
     'Decision on what to instrument, what alert thresholds to set (operationally justified), '
     '20-panel Grafana dashboard structure across 4 sections.'),
    ('Airflow DAG Logic',
     'Both DAG task graphs, BranchPythonOperator drift-check logic, schedule configuration.'),
    ('Security Design',
     'JWT authentication, role-based access control (admin/user separation), file-type '
     'validation, API key management.'),
    ('Test Suite',
     'All 49 test cases across unit, integration, and API layers — design, fixtures, '
     'assertions, and mock strategy entirely mine.'),
    ('Project Report Content',
     'Every written section in project_report.docx — architecture narrative, evaluation '
     'criteria mapping, technical descriptions, appendices.'),
    ('All Documentation',
     'README, User Manual, Architecture Document, Low-Level Design, Test Plan.'),
]

for cat, desc in not_ai:
    story.append(Paragraph(
        '<b>&#x2713;  ' + cat + ':</b>  ' + desc,
        bullet_style))
    story.append(Spacer(1, 0.08*cm))

# ── PRINCIPLES ────────────────────────────────────────────────────────────
story.append(Spacer(1, 0.5*cm))
story.append(Paragraph('Principles Followed', h2_style))

principles = [
    'AI was never asked to design, architect, or make decisions. It was asked for syntax, conventions, or traceback confirmation.',
    'Every AI output was read and understood before use. Nothing was accepted blindly.',
    'All AI-generated code was tested against the actual running system.',
    'The intellectual substance of every component originates with me.',
    'This disclosure is complete and accurate to the best of my knowledge.',
]
for p in principles:
    story.append(Paragraph('&#x2713;  ' + p, bullet_style))
    story.append(Spacer(1, 0.05*cm))

# ── SIGNATURE ─────────────────────────────────────────────────────────────
story.append(Spacer(1, 0.8*cm))
story.append(HRFlowable(width='100%', thickness=1, color=DIVIDER))
story.append(Spacer(1, 0.3*cm))
story.append(Paragraph(
    'I certify that the above disclosure is accurate and complete. All work submitted '
    'as part of this project reflects my own understanding and effort.',
    body_style))
story.append(Spacer(1, 0.8*cm))

sig_data = [
    ['Signature:', '_________________________________'],
    ['Name:',      'Major Prabhat Pandey (DA25M002)'],
    ['Date:',      'April 2026'],
]
sig_table = Table(sig_data, colWidths=[3*cm, 10*cm])
sig_table.setStyle(TableStyle([
    ('FONTNAME',  (0,0), (0,-1), 'Helvetica-Bold'),
    ('FONTNAME',  (1,0), (1,-1), 'Helvetica'),
    ('FONTSIZE',  (0,0), (-1,-1), 10),
    ('TEXTCOLOR', (0,0), (0,-1), GREY),
    ('TOPPADDING',    (0,0), (-1,-1), 6),
    ('BOTTOMPADDING', (0,0), (-1,-1), 6),
]))
story.append(sig_table)

doc.build(story)
print('SAVED: docs/submission/AI_DISCLOSURE.pdf')

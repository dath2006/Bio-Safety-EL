import os
from io import BytesIO
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

def generate_haccp_pdf(state: dict) -> bytes:
    """
    Generate a complete, professional PDF report for the HACCP plan.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom Palette
    primary_color = colors.HexColor('#1E3A8A')    # Deep Blue
    secondary_color = colors.HexColor('#0D9488')  # Teal
    neutral_dark = colors.HexColor('#1F2937')     # Dark gray/black
    bg_light = colors.HexColor('#F3F4F6')         # Light gray for table alt rows
    border_color = colors.HexColor('#E5E7EB')
    
    # Custom Styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=28,
        leading=34,
        textColor=primary_color,
        alignment=TA_CENTER,
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=14,
        leading=18,
        textColor=secondary_color,
        alignment=TA_CENTER,
        spaceAfter=40
    )
    
    meta_style = ParagraphStyle(
        'CoverMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=16,
        textColor=neutral_dark,
        alignment=TA_CENTER,
        spaceAfter=6
    )
    
    h1_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=primary_color,
        spaceBefore=15,
        spaceAfter=10,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'SubSectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=secondary_color,
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=neutral_dark,
        spaceAfter=8
    )
    
    table_header_style = ParagraphStyle(
        'TableHeaderText',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.white
    )
    
    table_cell_style = ParagraphStyle(
        'TableCellText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=neutral_dark
    )

    # 1. COVER PAGE
    story.append(Spacer(1, 100))
    story.append(Paragraph("HACCP SYSTEM PLAN", title_style))
    story.append(Paragraph("Hazard Analysis & Critical Control Point Documentation", subtitle_style))
    story.append(Spacer(1, 40))
    
    business_name = state.get("business_name") or "Unnamed Facility"
    category = state.get("product_category") or "General Food Category"
    plan_id = state.get("plan_id") or "N/A"
    fssai_license = state.get("fssai_license_number") or "Not Provided"
    
    story.append(Paragraph(f"<b>Food Business Operator:</b> {business_name}", meta_style))
    story.append(Paragraph(f"<b>FSSAI License No:</b> {fssai_license}", meta_style))
    story.append(Paragraph(f"<b>Product Category:</b> {category}", meta_style))
    story.append(Paragraph(f"<b>Plan ID:</b> {plan_id}", meta_style))
    story.append(Paragraph(f"<b>Generated Date:</b> {datetime.now().strftime('%B %d, %Y')}", meta_style))
    story.append(Paragraph(f"<b>Plan Version:</b> 1.0 (Draft)", meta_style))
    story.append(Spacer(1, 150))
    story.append(Paragraph("CONFIDENTIAL — FOR INTERNAL USE AND REGULATORY AUDIT ONLY", ParagraphStyle('Conf', parent=meta_style, fontSize=9, textColor=colors.gray)))
    story.append(PageBreak())
    
    # 2. SECTION 1: PROCESS FLOW DIAGRAM STEPS
    story.append(Paragraph("1. Process Flow Description", h1_style))
    story.append(Paragraph(
        "The following sequence of steps represents the operational flow for this product category. "
        "Each step is analyzed systematically for hazards in the subsequent section.",
        body_style
    ))
    
    steps = state.get("process_steps", [])
    if steps:
        flow_data = []
        for idx, step in enumerate(steps):
            flow_data.append([
                Paragraph(f"<b>Step {idx + 1}</b>", table_cell_style),
                Paragraph(step, table_cell_style)
            ])
        
        t = Table(flow_data, colWidths=[60, 440])
        t.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, border_color),
            ('BACKGROUND', (0,0), (0,-1), bg_light),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t)
    else:
        story.append(Paragraph("No process steps defined.", body_style))
        
    story.append(Spacer(1, 15))
    
    # 3. SECTION 2: HAZARD ANALYSIS
    story.append(Paragraph("2. Hazard Analysis Table", h1_style))
    story.append(Paragraph(
        "Systematic identification of biological, chemical, and physical hazards. "
        "Significant hazards (RPN &gt;= 9) require a critical control point determination.",
        body_style
    ))
    
    hazards = state.get("hazards_identified", [])
    if hazards:
        # Columns: Step, Hazard Name, Cat, RPN, Control Measure, CCP?
        header_row = [
            Paragraph("Process Step", table_header_style),
            Paragraph("Hazard details", table_header_style),
            Paragraph("Cat", table_header_style),
            Paragraph("RPN", table_header_style),
            Paragraph("Recommended Control", table_header_style)
        ]
        
        table_data = [header_row]
        for h in hazards:
            step = h.get("process_step", "N/A")
            name = h.get("name", "N/A")
            cat = h.get("category", "N/A").capitalize()
            l = h.get("likelihood", 3)
            s = h.get("severity", 3)
            rpn = l * s
            control = h.get("recommended_control", "")
            
            table_data.append([
                Paragraph(step, table_cell_style),
                Paragraph(name, table_cell_style),
                Paragraph(cat, table_cell_style),
                Paragraph(f"{rpn} ({l}x{s})", table_cell_style),
                Paragraph(control, table_cell_style)
            ])
            
        t = Table(table_data, colWidths=[100, 110, 50, 45, 195])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), primary_color),
            ('GRID', (0,0), (-1,-1), 0.5, border_color),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, bg_light]),
        ]))
        story.append(t)
    else:
        story.append(Paragraph("No hazards identified.", body_style))
        
    story.append(Spacer(1, 15))
    story.append(PageBreak())
    
    # 4. SECTION 3: CRITICAL CONTROL POINTS (CCPs)
    story.append(Paragraph("3. Approved Critical Control Points", h1_style))
    story.append(Paragraph(
        "Critical Control Points (CCPs) established based on the Codex Decision Tree. "
        "These steps require strict process monitoring and validated critical limits.",
        body_style
    ))
    
    ccps = state.get("ccps_approved", [])
    if ccps:
        header_row = [
            Paragraph("CCP No.", table_header_style),
            Paragraph("Process Step", table_header_style),
            Paragraph("Identified Hazard", table_header_style),
            Paragraph("Decision Tree Path / Override", table_header_style)
        ]
        table_data = [header_row]
        for idx, c in enumerate(ccps):
            step = c.get("process_step", "")
            hazard = c.get("hazard_name", "")
            override = c.get("user_override", False)
            path = ", ".join(c.get("decision_tree_path", []))
            
            path_desc = path
            if override:
                path_desc = f"<b>[USER OVERRIDE]</b>: {c.get('override_justification') or 'No justification provided'}"
                
            table_data.append([
                Paragraph(f"CCP {idx + 1}", table_cell_style),
                Paragraph(step, table_cell_style),
                Paragraph(hazard, table_cell_style),
                Paragraph(path_desc, table_cell_style)
            ])
            
        t = Table(table_data, colWidths=[50, 120, 130, 200])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), primary_color),
            ('GRID', (0,0), (-1,-1), 0.5, border_color),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, bg_light]),
        ]))
        story.append(t)
    else:
        story.append(Paragraph("No Critical Control Points identified or approved.", body_style))
        
    story.append(Spacer(1, 20))
    
    # 5. SECTION 4: PROCESS CONTROLS (CRITICAL LIMITS, MONITORING, CORRECTIVE ACTIONS)
    story.append(Paragraph("4. Process Control Specifications", h1_style))
    story.append(Paragraph(
        "Validated critical limits, monitoring procedures, and corrective action protocols for each approved CCP.",
        body_style
    ))
    
    limits = state.get("critical_limits", {})
    monitoring = state.get("monitoring_procedures", [])
    actions = state.get("corrective_actions", [])
    
    for idx, c in enumerate(ccps):
        h_name = c.get("hazard_name", "")
        p_step = c.get("process_step", "")
        ccp_key = f"{p_step} - {h_name}"
        
        ccp_section = []
        ccp_section.append(Paragraph(f"<b>CCP {idx + 1} — {p_step} ({h_name})</b>", h2_style))
        
        # Critical Limit
        cl_text = "Not established."
        cl_src = ""
        if ccp_key in limits:
            cl = limits[ccp_key]
            min_v = cl.get("min_value")
            max_v = cl.get("max_value")
            unit = cl.get("unit", "")
            param = cl.get("parameter", "Parameter")
            
            limits_strs = []
            if min_v is not None:
                limits_strs.append(f"Min: {min_v} {unit}")
            if max_v is not None:
                limits_strs.append(f"Max: {max_v} {unit}")
            
            cl_text = f"<b>{param}:</b> " + (" and ".join(limits_strs) if limits_strs else "No value set")
            cl_src = cl.get("source_citation", "")
            
        ccp_section.append(Paragraph(f"<b>Critical Limits:</b> {cl_text}", body_style))
        if cl_src:
            ccp_section.append(Paragraph(f"<i>Source Citation:</i> {cl_src}", ParagraphStyle('Src', parent=body_style, fontSize=8, textColor=colors.gray)))
            
        # Monitoring
        m_proc = next((m for m in monitoring if m.get("ccp_hazard") == ccp_key), None)
        if m_proc:
            m_text = (
                f"<b>Method:</b> {m_proc.get('method', '')}<br/>"
                f"<b>Frequency:</b> {m_proc.get('frequency', '')}<br/>"
                f"<b>Responsible:</b> {m_proc.get('responsible_person', '')}<br/>"
                f"<b>Record:</b> {m_proc.get('record_format', '')}"
            )
        else:
            m_text = "No monitoring procedures defined."
        ccp_section.append(Paragraph(f"<b>Monitoring Procedures:</b><br/>{m_text}", body_style))
        
        # Corrective Actions
        c_action = next((a for a in actions if a.get("ccp_hazard") == ccp_key), None)
        if c_action:
            ca_text = (
                f"<b>Trigger:</b> {c_action.get('trigger_condition', '')}<br/>"
                f"<b>Immediate Action:</b> {c_action.get('immediate_action', '')}<br/>"
                f"<b>Root Cause Action:</b> {c_action.get('root_cause_procedure', '')}<br/>"
                f"<b>Personnel:</b> {c_action.get('personnel', '')}"
            )
        else:
            ca_text = "No corrective action procedures defined."
        ccp_section.append(Paragraph(f"<b>Corrective Actions:</b><br/>{ca_text}", body_style))
        ccp_section.append(Spacer(1, 10))
        
        story.append(KeepTogether(ccp_section))
        
    story.append(Spacer(1, 15))
    story.append(PageBreak())
    
    # 6. SECTION 5: VERIFICATION SCHEDULE
    story.append(Paragraph("5. Verification Schedule", h1_style))
    story.append(Paragraph(
        "Verification procedures to ensure the HACCP system is working effectively and complied with.",
        body_style
    ))
    
    v_schedule = state.get("verification_schedule") or {}
    if v_schedule:
        v_data = [
            [Paragraph("Verification Activity", table_header_style), Paragraph("Schedule / Frequency", table_header_style)]
        ]
        for key, val in v_schedule.items():
            title = key.replace("_", " ").title()
            v_data.append([
                Paragraph(f"<b>{title}</b>", table_cell_style),
                Paragraph(str(val), table_cell_style)
            ])
            
        t = Table(v_data, colWidths=[150, 350])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), primary_color),
            ('GRID', (0,0), (-1,-1), 0.5, border_color),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, bg_light]),
        ]))
        story.append(t)
    else:
        story.append(Paragraph("No verification schedule defined.", body_style))
        
    story.append(Spacer(1, 30))

    # 7. APPENDIX: RECORD TEMPLATES
    records = state.get("records_generated", [])
    if records:
        story.append(Paragraph("Appendix A: Required FSMS Records", h1_style))
        story.append(Paragraph(
            "The following records must be maintained to demonstrate compliance with this HACCP plan:",
            body_style
        ))
        
        record_list = []
        for r in records:
            record_list.append([Paragraph(f"• {r}", table_cell_style)])
            
        t = Table(record_list, colWidths=[500])
        t.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('TOPPADDING', (0,0), (-1,-1), 3),
        ]))
        story.append(t)
        
    story.append(Spacer(1, 50))
    
    # 8. SIGNATURE BLOCK
    story.append(KeepTogether([
        Paragraph("Approval Signatures", h1_style),
        Paragraph("By signing below, the undersigned acknowledge that this HACCP plan has been reviewed, validated, and approved for implementation.", body_style),
        Spacer(1, 30),
        Table([
            [Paragraph("________________________________", table_cell_style), Paragraph("________________________________", table_cell_style)],
            [Paragraph("<b>Food Safety Team Leader / QA Manager</b>", table_cell_style), Paragraph("<b>Facility Director / Plant Manager</b>", table_cell_style)],
            [Paragraph("Name:", table_cell_style), Paragraph("Name:", table_cell_style)],
            [Paragraph("Date:", table_cell_style), Paragraph("Date:", table_cell_style)],
        ], colWidths=[250, 250], style=TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
    ]))
        
    # Build Document
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


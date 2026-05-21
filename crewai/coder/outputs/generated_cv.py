from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak,
                                Frame, KeepInFrame, Table, TableStyle)
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import os


def create_cv_pdf():
    # Output directory and file
    output_dir = "outputs"
    output_file = os.path.join(output_dir, "generated_cv.pdf")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Page setup
    PAGE_WIDTH, PAGE_HEIGHT = A4
    MARGIN = 0.55 * inch
    USABLE_WIDTH = PAGE_WIDTH - 2 * MARGIN

    # Color palette
    COLOR_HEADER = HexColor("#1a1a1a")
    COLOR_BODY = HexColor("#333333")
    COLOR_META = HexColor("#555555")
    COLOR_RULE = HexColor("#cccccc")
    COLOR_WHITE = HexColor("#ffffff")

    # Base font sizes (will be adjusted for fit)
    base_name_font_size = 17
    base_contact_font_size = 8.5
    base_section_heading_font_size = 9
    base_body_font_size = 8.5
    base_body_leading = 11
    base_meta_font_size = 8
    base_bullet_leading = 11
    base_job_meta_font_size = 8

    # Define styles (unique style names)
    styles = {
        "CVName": ParagraphStyle(
            "CVName",
            fontName="Helvetica-Bold",
            fontSize=base_name_font_size,
            leading=base_name_font_size * 1.1,
            alignment=TA_CENTER,
            textColor=COLOR_HEADER,
            uppercase=True,
            spaceAfter=3,
        ),
        "CVContact": ParagraphStyle(
            "CVContact",
            fontName="Helvetica",
            fontSize=base_contact_font_size,
            leading=base_contact_font_size * 1.1,
            alignment=TA_CENTER,
            textColor=black,
        ),
        "CVSectionHeading": ParagraphStyle(
            "CVSectionHeading",
            fontName="Helvetica-Bold",
            fontSize=base_section_heading_font_size,
            leading=base_section_heading_font_size * 1.1,
            alignment=TA_LEFT,
            textColor=COLOR_HEADER,
            spaceBefore=4,
            spaceAfter=3,
            uppercase=True,
        ),
        "CVBody": ParagraphStyle(
            "CVBody",
            fontName="Helvetica",
            fontSize=base_body_font_size,
            leading=base_body_leading,
            alignment=TA_JUSTIFY,
            textColor=COLOR_BODY,
        ),
        "CVSkillLine": ParagraphStyle(
            "CVSkillLine",
            fontName="Helvetica",
            fontSize=base_body_font_size,
            leading=base_body_leading,
            alignment=TA_LEFT,
            textColor=COLOR_BODY,
        ),
        "CVSkillLabel": ParagraphStyle(
            "CVSkillLabel",
            fontName="Helvetica-Bold",
            fontSize=base_body_font_size,
            leading=base_body_leading,
            alignment=TA_LEFT,
            textColor=COLOR_BODY,
        ),
        "CVSoftSkills": ParagraphStyle(
            "CVSoftSkills",
            fontName="Helvetica",
            fontSize=base_body_font_size,
            leading=base_body_leading,
            alignment=TA_LEFT,
            textColor=COLOR_BODY,
        ),
        "CVJobTitle": ParagraphStyle(
            "CVJobTitle",
            fontName="Helvetica-Bold",
            fontSize=base_body_font_size,
            leading=base_body_leading,
            alignment=TA_LEFT,
            textColor=COLOR_BODY,
        ),
        "CVJobMeta": ParagraphStyle(
            "CVJobMeta",
            fontName="Helvetica",
            fontSize=base_job_meta_font_size,
            leading=base_job_meta_font_size * 1.15,
            alignment=TA_LEFT,
            textColor=COLOR_META,
            spaceBefore=1,
            spaceAfter=2,
        ),
        "CVBullet": ParagraphStyle(
            "CVBullet",
            fontName="Helvetica",
            fontSize=base_body_font_size,
            leading=base_bullet_leading,
            leftIndent=10,
            bulletIndent=0,
            bulletFontName="Helvetica",
            bulletFontSize=base_body_font_size,
            textColor=COLOR_BODY,
            alignment=TA_LEFT,
            spaceBefore=0,
            spaceAfter=0,
        ),
        "CVProjectHeading": ParagraphStyle(
            "CVProjectHeading",
            fontName="Helvetica-Bold",
            fontSize=base_body_font_size,
            leading=base_body_leading,
            alignment=TA_LEFT,
            textColor=COLOR_BODY,
        ),
        "CVEducationDegree": ParagraphStyle(
            "CVEducationDegree",
            fontName="Helvetica-Bold",
            fontSize=base_body_font_size,
            leading=base_body_leading,
            alignment=TA_LEFT,
            textColor=COLOR_BODY,
        ),
        "CVEducationSchool": ParagraphStyle(
            "CVEducationSchool",
            fontName="Helvetica",
            fontSize=base_body_font_size,
            leading=base_body_leading,
            alignment=TA_LEFT,
            textColor=COLOR_BODY,
        ),
        "CVEducationDate": ParagraphStyle(
            "CVEducationDate",
            fontName="Helvetica",
            fontSize=base_meta_font_size,
            leading=base_meta_font_size * 1.15,
            alignment=TA_LEFT,
            textColor=COLOR_META,
            spaceBefore=0,
        ),
    }

    # CV Content (formatted as per context)
    full_name = "NASIR SHAHZAD"

    contact_info = {
        "email": "nasirbhotta@gmail.com",
        "phone": "0313-7576531",
        "linkedin": "https://www.linkedin.com/in/me-bhotta",
        "github": "https://github.com/NasirBhotta",
        "location": "Hostel City, Islamabad"
    }

    profile_text = (
        "Flutter Developer with 1.5 years of experience building scalable, high-performance cross-platform apps. "
        "Skilled in Flutter, Dart, Firebase, REST APIs, and clean architecture (MVVM, BLoC). Proven record delivering "
        "production-ready apps featuring offline-first design, real-time sync, notifications, and secure backups. "
        "Experienced in full-stack development with Node.js, Express.js, and MongoDB for seamless backend integration. "
        "Passionate about clean UI, efficient code, teamwork, and impactful mobile solutions."
    )

    technical_skills = {
        "Languages & Frameworks:": "Flutter, Dart, JavaScript, Node.js, Express.js",
        "Databases:": "MongoDB, MySQL, Firebase",
        "Core CS Concepts:": "Clean Architecture (MVVM, BLoC), REST APIs, Agile Methodology",
        "Tools & Platforms:": "Git, Linux, AWS, Docker",
    }

    soft_skills = [
        "Teamwork",
        "Efficient Coding",
        "Clean UI Design",
        "Problem Solving",
        "Continuous Learning",
        "Communication"
    ]

    professional_experience = [
        {
            "job_title": "Flutter App Developer",
            "company": "Various Projects",
            "date_range": "01/2022 – Present",
            "bullets": [
                "Developed BrainBee, an AI-powered personalized learning app with adaptive study plans, AI-generated flashcards, quizzes, RAG chatbot, and gamification (peer battles, leaderboards, badges) using Flutter, Node.js/Express.js, and MongoDB implementing scalable architecture.",
                "Built scalable Flutter e-commerce platform with separate customer and admin apps using Firebase, Stripe, GetX architecture; implemented full shopping flow with authentication, catalog, wishlist, cart, coupons, checkout, orders, notifications, and profile management with local caching (Hive, GetStorage). Integrated secure Stripe payments via Firebase Cloud Functions including PaymentSheet, saved cards, wallet funding, and webhook transaction handling. Created admin dashboard for order/product management, analytics, withdrawal approvals, notifications, risk alerts, exports, and audit logging.",
                "Created full-stack ride-sharing mobile app with Flutter, Firebase, Google Maps API supporting rider, driver, and admin roles. Features include real-time ride tracking with live GPS, polyline route visualization, turn-by-turn voice navigation (Google Directions API, Flutter TTS), admin dashboard with live Firestore metrics, revenue charts, ride/user management, and smart ride-matching with radius-based search, rerouting, and in-app messaging."
            ],
        }
    ]

    personal_projects = [
        {
            "name": "BrainBee",
            "tech_stack": "Flutter, Node.js, Express.js, MongoDB",
            "bullets": [
                "AI-driven adaptive learning with flashcards, quizzes, chatbot and gamification features.",
                "Designed scalable cross-platform architecture supporting real-time sync and offline support."
            ],
        },
        {
            "name": "Ecommerce App",
            "tech_stack": "Flutter, Firebase, Stripe, GetX",
            "bullets": [
                "Developed end-to-end shopping platform with customer and admin apps.",
                "Integrated secure payments and admin analytics dashboard with audit features."
            ],
        },
        {
            "name": "Ride Sharing App",
            "tech_stack": "Flutter, Firebase, Google Maps API",
            "bullets": [
                "Built multi-role ride-sharing platform with real-time tracking, navigation, admin controls.",
                "Implemented smart ride-matching, off-route rerouting, and in-app rider-driver communication."
            ],
        }
    ]

    education_entries = [
        {
            "degree": "FSc Pre Engineering",
            "institution": "Punjab Group of Colleges Phalia Campus",
            "date_range": "04/2019 - 02/2021 | Phalia, Punjab"
        },
        {
            "degree": "Bachelor of Science in Computer Science",
            "institution": "COMSATS University Islamabad",
            "date_range": "02/2022 - 01/2026 | Islamabad, Pakistan"
        }
    ]

    # Function to create a horizontal rule line (Rule) spanning usable width
    from reportlab.platypus import Flowable

    class HRLine(Flowable):
        def __init__(self, width, thickness, color):
            Flowable.__init__(self)
            self.width = width
            self.thickness = thickness
            self.color = color
            self.height = thickness

        def draw(self):
            self.canv.setStrokeColor(self.color)
            self.canv.setLineWidth(self.thickness)
            self.canv.line(0, self.height / 2.0, self.width, self.height / 2.0)

        def wrap(self, availWidth, availHeight):
            return self.width, self.height

    # Prepare contact line (omit missing and separators)
    contact_parts = []
    if contact_info.get("email"):
        contact_parts.append(contact_info["email"])
    if contact_info.get("phone"):
        contact_parts.append(contact_info["phone"])
    if contact_info.get("linkedin"):
        contact_parts.append(contact_info["linkedin"])
    if contact_info.get("github"):
        contact_parts.append(contact_info["github"])
    if contact_info.get("location"):
        contact_parts.append(contact_info["location"])
    contact_line_text = " | ".join(contact_parts)

    # Function to uppercase text for section headings enforcing uppercase per spec
    def make_uppercase(text):
        return text.upper()

    # The main story building function for one run (to be re-built for fit)
    def build_story():
        story = []

        # Header block
        # 1. Full name centered, ALL CAPS, Helvetica-Bold 17pt, color #1a1a1a
        story.append(Paragraph(full_name.upper(), styles["CVName"]))
        story.append(Spacer(1, 3))

        # 2. One centered contact line beneath
        if contact_line_text.strip():
            story.append(Paragraph(contact_line_text, styles["CVContact"]))

        # 3. Thin horizontal rule (0.6pt) below contact line, 5pt below contact line
        story.append(Spacer(1, 5))
        story.append(HRLine(USABLE_WIDTH, 0.6, COLOR_RULE))
        story.append(Spacer(1, 5))

        # Section order and rendering

        def add_section_heading(title):
            heading_text = make_uppercase(title)
            story.append(Spacer(1, 4))  # 4pt above heading
            story.append(Paragraph(heading_text, styles["CVSectionHeading"]))
            story.append(HRLine(USABLE_WIDTH, 1, COLOR_RULE))
            story.append(Spacer(1, 3))  # 3pt below horizontal rule

        # PROFILE
        if profile_text.strip():
            add_section_heading("Profile")
            story.append(Paragraph(profile_text, styles["CVBody"]))

        # TECHNICAL SKILLS
        if technical_skills:
            add_section_heading("Technical Skills")
            # Each skill group on its own line: "<b>Label:</b> values"
            for label, values in technical_skills.items():
                line_html = f"<b>{label}</b> {values}"
                story.append(Paragraph(line_html, styles["CVSkillLine"]))

        # SOFT SKILLS
        if soft_skills:
            add_section_heading("Soft Skills")
            # Single compact line or two if needed.
            # Items separated by "  -  "
            # Join items with "  -  "
            soft_skills_line = " \u2022 ".join(soft_skills)  # Unicode bullet for separator
            # Because Unicode bullets can be misread, use "  -  " per spec safer.
            soft_skills_line = "  -  ".join(soft_skills)
            # Use bullet style paragraph without actual bullets
            # Break if too long automatically by ReportLab
            story.append(Paragraph(soft_skills_line, styles["CVSoftSkills"]))

        # PROFESSIONAL EXPERIENCE
        if professional_experience:
            add_section_heading("Professional Experience")
            for role in professional_experience:
                # Job and company on one line
                job_comp_line = f"<b>{role['job_title']}</b>  |  <b>{role['company']}</b>"
                story.append(Paragraph(job_comp_line, styles["CVJobTitle"]))
                # Dates below with 1pt space
                story.append(Paragraph(role["date_range"], styles["CVJobMeta"]))
                # Bullets with 6pt gap between roles (we add after last bullet)
                for bullet in role["bullets"]:
                    # Use bulletText param with safe plain bullet character
                    story.append(Paragraph(bullet, styles["CVBullet"], bulletText="•"))
                story.append(Spacer(1, 6))

        # PERSONAL PROJECTS
        if personal_projects:
            add_section_heading("Personal Projects")
            for project in personal_projects:
                # Heading line: "<b>Project Name</b> - Tech Stack" or just project name if no tech stack
                if project.get("tech_stack","").strip():
                    heading_line = f"<b>{project['name']}</b> - {project['tech_stack']}"
                else:
                    heading_line = f"<b>{project['name']}</b>"
                story.append(Paragraph(heading_line, styles["CVProjectHeading"]))
                # Bullets with 5pt gap between projects (add after last bullet)
                for bullet in project["bullets"]:
                    story.append(Paragraph(bullet, styles["CVBullet"], bulletText="•"))
                story.append(Spacer(1, 5))

        # EDUCATION
        if education_entries:
            add_section_heading("Education")
            for entry in education_entries:
                story.append(Paragraph(entry["degree"], styles["CVEducationDegree"]))
                story.append(Paragraph(entry["institution"], styles["CVEducationSchool"]))
                story.append(Paragraph(entry["date_range"], styles["CVEducationDate"]))
                story.append(Spacer(1, 4))

        return story

    def story_height(story, doc):
        """Calculate total height of story flowables on the page (for fitting check)"""
        total_h = 0
        for flowable in story:
            w, h = flowable.wrap(doc.width, doc.height)
            total_h += h
        return total_h

    # Generate document and try to fit on one page by adjusting font sizes and spacing
    def try_fit_and_build():
        # Adjust font sizes and spacings in decrements if needed until fits or minimum sizes
        # Minimal limits:
        min_body_font_size = 7.5
        min_section_heading_font_size = 7.5
        min_contact_font_size = 7.5
        min_name_font_size = 14
        min_bullet_leading = 9
        current_body_font_size = base_body_font_size
        current_body_leading = base_body_leading
        current_section_heading_font_size = base_section_heading_font_size
        current_contact_font_size = base_contact_font_size
        current_name_font_size = base_name_font_size
        current_bullet_leading = base_bullet_leading

        # Maximum available height for content (page height - top margin - bottom margin)
        max_height = PAGE_HEIGHT - 2 * MARGIN

        # Update styles helper
        def update_styles():
            styles["CVName"].fontSize = current_name_font_size
            styles["CVName"].leading = current_name_font_size * 1.1
            styles["CVContact"].fontSize = current_contact_font_size
            styles["CVContact"].leading = current_contact_font_size * 1.1
            styles["CVSectionHeading"].fontSize = current_section_heading_font_size
            styles["CVSectionHeading"].leading = current_section_heading_font_size * 1.1
            styles["CVBody"].fontSize = current_body_font_size
            styles["CVBody"].leading = current_body_leading
            styles["CVSkillLine"].fontSize = current_body_font_size
            styles["CVSkillLine"].leading = current_body_leading
            styles["CVSkillLabel"].fontSize = current_body_font_size
            styles["CVSkillLabel"].leading = current_body_leading
            styles["CVSoftSkills"].fontSize = current_body_font_size
            styles["CVSoftSkills"].leading = current_body_leading
            styles["CVJobTitle"].fontSize = current_body_font_size
            styles["CVJobTitle"].leading = current_body_leading
            styles["CVBullet"].fontSize = current_body_font_size
            styles["CVBullet"].leading = current_bullet_leading
            styles["CVJobMeta"].fontSize = base_job_meta_font_size
            styles["CVJobMeta"].leading = base_job_meta_font_size * 1.15
            styles["CVProjectHeading"].fontSize = current_body_font_size
            styles["CVProjectHeading"].leading = current_body_leading
            styles["CVEducationDegree"].fontSize = current_body_font_size
            styles["CVEducationDegree"].leading = current_body_leading
            styles["CVEducationSchool"].fontSize = current_body_font_size
            styles["CVEducationSchool"].leading = current_body_leading
            styles["CVEducationDate"].fontSize = base_meta_font_size
            styles["CVEducationDate"].leading = base_meta_font_size * 1.15

        update_styles()

        # Build a temporary doc to check size
        from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate

        def dummy_page(canvas, doc):
            pass

        while True:
            update_styles()
            doc = BaseDocTemplate(
                "dummy.pdf",
                pagesize=A4,
                leftMargin=MARGIN,
                rightMargin=MARGIN,
                topMargin=MARGIN,
                bottomMargin=MARGIN,
            )
            frame = Frame(
                MARGIN,
                MARGIN,
                PAGE_WIDTH - 2 * MARGIN,
                PAGE_HEIGHT - 2 * MARGIN,
                id="normal",
            )
            template = PageTemplate(id="test", frames=frame, onPage=dummy_page)
            doc.addPageTemplates([template])

            story = build_story()
            try:
                # try build to measure if fit
                doc.build(story)
            except Exception:
                # ignore build errors in dummy build
                pass
            # We do a rough check by counting total height (wrap sum)
            total_height = story_height(story, doc)
            if total_height <= max_height:
                break
            # If font sizes can be reduced, reduce in order body font, heading font, contact font, name font, bullet leading
            if current_body_font_size > min_body_font_size:
                current_body_font_size -= 0.5
                current_body_leading = max(current_body_font_size * 1.1, current_body_font_size + 2)
                current_bullet_leading = max(current_bullet_leading - 1, min_bullet_leading)
                continue
            if current_section_heading_font_size > min_section_heading_font_size:
                current_section_heading_font_size -= 0.5
                continue
            if current_contact_font_size > min_contact_font_size:
                current_contact_font_size -= 0.5
                continue
            if current_name_font_size > min_name_font_size:
                current_name_font_size -= 0.5
                continue
            # If cannot reduce more sizes, break anyway to avoid infinite loop
            break

        # Final build with adjusted styles on real output file
        update_styles()
        doc_final = SimpleDocTemplate(
            output_file,
            pagesize=A4,
            leftMargin=MARGIN,
            rightMargin=MARGIN,
            topMargin=MARGIN,
            bottomMargin=MARGIN,
        )
        story_final = build_story()
        doc_final.build(story_final)

    try_fit_and_build()


if __name__ == "__main__":
    create_cv_pdf()
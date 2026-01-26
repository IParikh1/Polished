#!/usr/bin/env python3
"""
Generate test resumes for scoring validation.
Creates impressive and unimpressive versions for each sales role.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# Resume data for each role type
RESUMES = {
    # ============================================================
    # ENTRY LEVEL SDR
    # ============================================================
    "01_Entry_SDR_IMPRESSIVE": {
        "name": "Alex Chen",
        "email": "alex.chen@email.com",
        "phone": "(415) 555-0123",
        "location": "San Francisco, CA",
        "linkedin": "linkedin.com/in/alexchen-sales",
        "summary": "Recent Business graduate with proven sales aptitude demonstrated through internship experience. Completed HubSpot Sales certification and Salesforce Administrator training. Passionate about SaaS technology with strong cold calling skills developed through 500+ outreach calls during internship.",
        "experience": [
            {
                "title": "Sales Development Intern",
                "company": "TechStart SaaS",
                "dates": "June 2025 - December 2025",
                "bullets": [
                    "Completed 500+ cold calls over 6 months, achieving 12% connection rate (team avg: 8%)",
                    "Booked 45 qualified meetings for Account Executives, contributing $180K to pipeline",
                    "Achieved 115% of internship quota for meetings booked in final month",
                    "Mastered Salesforce CRM and Outreach.io for prospecting workflows",
                    "Created personalized email sequences achieving 28% open rate and 5% response rate",
                ]
            },
            {
                "title": "Campus Brand Ambassador",
                "company": "SaaS Company X",
                "dates": "September 2024 - May 2025",
                "bullets": [
                    "Generated 200+ student sign-ups for product trial through campus events",
                    "Ranked #2 out of 15 ambassadors nationwide for lead generation",
                    "Developed presentation skills through 20+ product demos to student organizations",
                ]
            }
        ],
        "education": [
            "Bachelor of Science in Business Administration, UC Berkeley, 2025",
            "GPA: 3.7 | Sales Club President | Dean's List"
        ],
        "skills": [
            "Tools: Salesforce, HubSpot, Outreach.io, LinkedIn Sales Navigator, ZoomInfo",
            "Skills: Cold Calling, Email Prospecting, Discovery Calls, CRM Management, Lead Qualification",
            "Certifications: HubSpot Sales Software Certified, Salesforce Administrator (in progress)"
        ]
    },

    "02_Entry_SDR_UNIMPRESSIVE": {
        "name": "Jordan Smith",
        "email": "jsmith123@gmail.com",
        "phone": "555-1234",
        "location": "Chicago, IL",
        "linkedin": "",
        "summary": "Recent graduate looking for entry-level sales position. Hard worker with good communication skills. Eager to learn and grow in a sales environment.",
        "experience": [
            {
                "title": "Retail Sales Associate",
                "company": "Best Buy",
                "dates": "2024 - 2025",
                "bullets": [
                    "Helped customers find products they needed",
                    "Worked cash register and processed transactions",
                    "Maintained store displays and inventory",
                    "Answered customer questions about electronics",
                ]
            },
            {
                "title": "Server",
                "company": "Applebee's Restaurant",
                "dates": "2023 - 2024",
                "bullets": [
                    "Took customer orders and delivered food",
                    "Provided good customer service",
                    "Worked well with team members",
                ]
            }
        ],
        "education": [
            "Bachelor's Degree, State University, 2025",
            "Major: Communications"
        ],
        "skills": [
            "Microsoft Office, Good communication, Team player, Quick learner, Motivated"
        ]
    },

    # ============================================================
    # SDR / BDR
    # ============================================================
    "03_SDR_BDR_IMPRESSIVE": {
        "name": "Maya Rodriguez",
        "email": "maya.rodriguez@email.com",
        "phone": "(512) 555-0456",
        "location": "Austin, TX",
        "linkedin": "linkedin.com/in/mayarodriguez-sdr",
        "summary": "High-performing SDR with 2 years experience in B2B SaaS. Consistently exceeded quota by 130%+ and ranked Top 3 SDR for 6 consecutive quarters. MEDDIC certified with expertise in multi-threaded prospecting using Outreach, Gong, and 6sense intent data.",
        "experience": [
            {
                "title": "Senior Sales Development Representative",
                "company": "CloudScale Technologies",
                "dates": "January 2024 - Present",
                "bullets": [
                    "Achieved 145% of quota in 2024, generating $2.8M in qualified pipeline",
                    "Booked 180+ meetings with enterprise prospects (avg deal size $85K ACV)",
                    "Ranked #1 SDR out of 25 reps for Q3 2024 - won President's Club trip",
                    "Maintained 65+ daily activities (calls, emails, LinkedIn touches) with 15% meeting conversion",
                    "Leveraged 6sense intent data to prioritize accounts, improving connect rate by 40%",
                    "Mentored 3 new SDRs, all achieved quota within first 90 days",
                ]
            },
            {
                "title": "Sales Development Representative",
                "company": "StartupXYZ",
                "dates": "June 2023 - December 2023",
                "bullets": [
                    "Exceeded quota by 125% in first 6 months, booking 95 qualified meetings",
                    "Generated $1.2M pipeline through cold outreach and inbound follow-up",
                    "Developed custom Outreach sequences achieving 32% reply rate (team avg: 18%)",
                    "Promoted to Senior SDR within 8 months based on performance",
                ]
            }
        ],
        "education": [
            "Bachelor of Arts in Marketing, University of Texas at Austin, 2023",
            "Minor in Computer Science | Sales Competition Winner 2022"
        ],
        "skills": [
            "Tools: Salesforce, Outreach, Gong, 6sense, ZoomInfo, LinkedIn Sales Navigator, Chorus",
            "Methodologies: MEDDIC, BANT, Challenger Sale, Solution Selling",
            "Skills: Cold Calling, Multi-threading, Account Research, Pipeline Generation, Discovery",
            "Certifications: MEDDIC Certified, Salesforce Sales Cloud Certified, Gong Certified"
        ]
    },

    "04_SDR_BDR_UNIMPRESSIVE": {
        "name": "Chris Johnson",
        "email": "chrisjohnson@yahoo.com",
        "phone": "(555) 987-6543",
        "location": "Phoenix, AZ",
        "linkedin": "",
        "summary": "SDR with some experience in sales. Looking for new opportunities to advance my career. I make calls and send emails to potential customers.",
        "experience": [
            {
                "title": "Sales Development Rep",
                "company": "ABC Software",
                "dates": "2023 - Present",
                "bullets": [
                    "Make outbound calls to prospects daily",
                    "Send emails to potential customers",
                    "Update CRM with call notes",
                    "Attend weekly team meetings",
                    "Work with account executives on deals",
                ]
            },
            {
                "title": "Telemarketer",
                "company": "Call Center Inc",
                "dates": "2022 - 2023",
                "bullets": [
                    "Made cold calls to residential customers",
                    "Read scripts to potential buyers",
                    "Transferred interested calls to closers",
                ]
            }
        ],
        "education": [
            "Some college, Community College, 2022"
        ],
        "skills": [
            "Phone skills, Email, Microsoft Word, Excel basics, Communication"
        ]
    },

    # ============================================================
    # ACCOUNT EXECUTIVE
    # ============================================================
    "05_Account_Executive_IMPRESSIVE": {
        "name": "David Park",
        "email": "david.park@email.com",
        "phone": "(206) 555-0789",
        "location": "Seattle, WA",
        "linkedin": "linkedin.com/in/davidpark-ae",
        "summary": "Top-performing Account Executive with 4 years of full-cycle B2B SaaS sales experience. Closed $3.2M ARR in 2024, achieving 142% of quota. Specializes in mid-market deals ($50K-$200K ACV) using MEDDPICC methodology. Former SDR who was promoted in 12 months.",
        "experience": [
            {
                "title": "Account Executive",
                "company": "DataCloud Solutions",
                "dates": "March 2022 - Present",
                "bullets": [
                    "Closed $3.2M in new ARR in 2024, achieving 142% of $2.25M quota",
                    "Maintained average deal size of $95K ACV across 34 closed deals",
                    "Achieved 85% win rate on deals reaching proposal stage",
                    "Shortened average sales cycle from 75 to 52 days through improved discovery",
                    "President's Club winner 2023 and 2024 - Top 5% of global sales org",
                    "Built $4.5M qualified pipeline through strategic prospecting and referrals",
                    "Managed complex multi-stakeholder deals with 6+ decision makers using MEDDPICC",
                ]
            },
            {
                "title": "Sales Development Representative",
                "company": "DataCloud Solutions",
                "dates": "January 2021 - February 2022",
                "bullets": [
                    "Exceeded quota by 135% in first year, generating $2.1M pipeline",
                    "Promoted to AE within 12 months - fastest promotion in company history",
                    "Booked 145 qualified meetings with mid-market prospects",
                ]
            }
        ],
        "education": [
            "Bachelor of Science in Finance, University of Washington, 2020",
            "Cum Laude | Business Honors Program"
        ],
        "skills": [
            "Tools: Salesforce, Gong, Clari, Outreach, LinkedIn Sales Navigator, DocuSign",
            "Methodologies: MEDDPICC, Challenger Sale, Command of the Message, Gap Selling",
            "Skills: Discovery, Negotiation, Multi-threading, Executive Presentations, Forecasting",
            "Certifications: Salesforce Sales Cloud Certified, MEDDPICC Certified, Gong Certified"
        ]
    },

    "06_Account_Executive_UNIMPRESSIVE": {
        "name": "Ashley Williams",
        "email": "awilliams@email.com",
        "phone": "(555) 246-8135",
        "location": "Dallas, TX",
        "linkedin": "linkedin.com/in/ashleyw",
        "summary": "Account Executive with experience selling software solutions. Looking for a new role where I can use my sales skills to help a company grow.",
        "experience": [
            {
                "title": "Account Executive",
                "company": "Software Solutions LLC",
                "dates": "2022 - Present",
                "bullets": [
                    "Manage a territory of accounts in the Southwest region",
                    "Conduct product demonstrations for interested prospects",
                    "Work with customers to understand their needs",
                    "Prepare and send proposals to potential clients",
                    "Collaborate with customer success team on implementations",
                    "Attend trade shows and networking events",
                ]
            },
            {
                "title": "Inside Sales Representative",
                "company": "Tech Company",
                "dates": "2020 - 2022",
                "bullets": [
                    "Handled inbound sales inquiries",
                    "Qualified leads and passed to senior reps",
                    "Maintained customer database",
                ]
            }
        ],
        "education": [
            "Bachelor's Degree in Business, University of Texas at Dallas, 2020"
        ],
        "skills": [
            "Salesforce, PowerPoint, Demo skills, Customer relationships, Teamwork"
        ]
    },

    # ============================================================
    # SENIOR / ENTERPRISE ACCOUNT EXECUTIVE
    # ============================================================
    "07_Senior_Enterprise_AE_IMPRESSIVE": {
        "name": "Jennifer Morrison",
        "email": "jennifer.morrison@email.com",
        "phone": "(415) 555-0321",
        "location": "San Francisco, CA",
        "linkedin": "linkedin.com/in/jennifermorrison-enterprise",
        "summary": "Elite Enterprise Account Executive with 8 years of SaaS sales experience closing complex, multi-million dollar deals. Closed $8.7M ARR in 2024 at 165% of quota. Expertise in selling to C-suite executives at Fortune 500 companies. 5x President's Club winner with proven track record of landing and expanding strategic accounts.",
        "experience": [
            {
                "title": "Senior Enterprise Account Executive",
                "company": "Snowflake",
                "dates": "January 2022 - Present",
                "bullets": [
                    "Closed $8.7M in new ARR in 2024, achieving 165% of $5.3M quota",
                    "Landed 3 Fortune 100 logos with average deal size of $1.2M ACV",
                    "Expanded existing accounts by $2.4M through strategic upsells and cross-sells",
                    "Achieved 145% NRR across portfolio of 12 strategic enterprise accounts",
                    "5x consecutive President's Club winner (2020-2024)",
                    "Navigated 18-month sales cycles with 15+ stakeholder buying committees",
                    "Built relationships with CIOs, CTOs, and CFOs at target accounts",
                    "Mentored 4 AEs who were all promoted within 18 months",
                ]
            },
            {
                "title": "Enterprise Account Executive",
                "company": "Salesforce",
                "dates": "June 2018 - December 2021",
                "bullets": [
                    "Closed $12.5M total contract value over 3.5 years",
                    "Consistently achieved 120%+ of annual quota",
                    "Named Rookie of the Year 2018 for fastest ramp to quota",
                    "Specialized in Financial Services vertical, closing 8 major banks",
                ]
            },
            {
                "title": "Account Executive",
                "company": "Box",
                "dates": "March 2016 - May 2018",
                "bullets": [
                    "Promoted from Commercial to Enterprise within 18 months",
                    "Closed $2.8M in new ARR across mid-market accounts",
                ]
            }
        ],
        "education": [
            "MBA, Stanford Graduate School of Business, 2016",
            "BS in Economics, UCLA, 2012 | Magna Cum Laude"
        ],
        "skills": [
            "Tools: Salesforce, Gong, Clari, LinkedIn Sales Navigator, Tableau, Seismic",
            "Methodologies: MEDDPICC, Command of the Message, Challenger Sale, Value Selling",
            "Skills: C-Suite Selling, Contract Negotiation, Strategic Account Planning, Forecasting",
            "Certifications: Salesforce Certified, Sandler Enterprise Selling, MEDDPICC Master"
        ]
    },

    "08_Senior_Enterprise_AE_UNIMPRESSIVE": {
        "name": "Robert Thompson",
        "email": "rthompson55@gmail.com",
        "phone": "(555) 789-0123",
        "location": "New York, NY",
        "linkedin": "",
        "summary": "Experienced sales professional with background in enterprise software sales. Have worked with large companies and understand complex sales processes. Looking for senior sales role.",
        "experience": [
            {
                "title": "Senior Account Executive",
                "company": "Enterprise Software Co",
                "dates": "2019 - Present",
                "bullets": [
                    "Manage relationships with enterprise accounts",
                    "Work on large deals with multiple stakeholders",
                    "Present to senior executives at client companies",
                    "Coordinate with internal teams on proposals",
                    "Travel to client sites for important meetings",
                    "Participate in QBRs with leadership",
                ]
            },
            {
                "title": "Account Executive",
                "company": "Tech Vendor",
                "dates": "2016 - 2019",
                "bullets": [
                    "Sold software to mid-size companies",
                    "Met with prospects to discuss solutions",
                    "Worked deals through the sales process",
                ]
            },
            {
                "title": "Sales Representative",
                "company": "Software Inc",
                "dates": "2014 - 2016",
                "bullets": [
                    "Made calls to potential customers",
                    "Learned about the software industry",
                ]
            }
        ],
        "education": [
            "BA in Communications, State University, 2014"
        ],
        "skills": [
            "Enterprise sales, Relationship building, Presentations, Microsoft Office, Travel"
        ]
    },

    # ============================================================
    # ACCOUNT MANAGER
    # ============================================================
    "09_Account_Manager_IMPRESSIVE": {
        "name": "Sarah Kim",
        "email": "sarah.kim@email.com",
        "phone": "(312) 555-0654",
        "location": "Chicago, IL",
        "linkedin": "linkedin.com/in/sarahkim-csm",
        "summary": "Strategic Account Manager with 5 years experience driving expansion revenue and retention in B2B SaaS. Achieved 152% NRR across $8M book of business in 2024. Expertise in identifying upsell opportunities and reducing churn through proactive customer success strategies. Salesforce and Gainsight certified.",
        "experience": [
            {
                "title": "Senior Account Manager",
                "company": "Zendesk",
                "dates": "April 2022 - Present",
                "bullets": [
                    "Manage $8M ARR book of business across 45 mid-market accounts",
                    "Achieved 152% Net Revenue Retention in 2024 through strategic upsells",
                    "Closed $2.1M in expansion revenue, exceeding target by 135%",
                    "Reduced churn rate from 12% to 4% through proactive health monitoring",
                    "Increased average contract value by 45% through multi-product adoption",
                    "Built executive relationships resulting in 8 customer references and case studies",
                    "Implemented Gainsight health scoring, improving at-risk identification by 60%",
                ]
            },
            {
                "title": "Account Manager",
                "company": "HubSpot",
                "dates": "June 2020 - March 2022",
                "bullets": [
                    "Managed 60+ SMB accounts totaling $3.5M ARR",
                    "Achieved 125% of expansion quota through Marketing Hub upsells",
                    "Maintained 95% gross retention rate across portfolio",
                    "Promoted to Senior AM within 18 months based on performance",
                ]
            },
            {
                "title": "Customer Success Manager",
                "company": "SaaS Startup",
                "dates": "January 2019 - May 2020",
                "bullets": [
                    "Onboarded 100+ customers with 90% activation rate",
                    "Transitioned to Account Manager role to focus on renewals and expansion",
                ]
            }
        ],
        "education": [
            "Bachelor of Business Administration, Northwestern University, 2018",
            "Kellogg Sales Institute Certificate"
        ],
        "skills": [
            "Tools: Salesforce, Gainsight, ChurnZero, Gong, Tableau, Intercom",
            "Skills: Renewal Management, Upselling, Customer Health Scoring, QBRs, Churn Prevention",
            "Certifications: Gainsight Admin Certified, Salesforce Certified, HubSpot Revenue Operations"
        ]
    },

    "10_Account_Manager_UNIMPRESSIVE": {
        "name": "Michael Davis",
        "email": "mdavis@email.com",
        "phone": "(555) 456-7890",
        "location": "Atlanta, GA",
        "linkedin": "",
        "summary": "Account Manager with experience managing customer relationships. Good at building rapport with clients and ensuring customer satisfaction. Looking for account management opportunities.",
        "experience": [
            {
                "title": "Account Manager",
                "company": "Software Company",
                "dates": "2021 - Present",
                "bullets": [
                    "Manage a portfolio of customer accounts",
                    "Conduct regular check-in calls with customers",
                    "Handle customer questions and concerns",
                    "Work with support team on customer issues",
                    "Prepare renewal quotes for customers",
                    "Attend customer meetings as needed",
                ]
            },
            {
                "title": "Customer Service Representative",
                "company": "Tech Support Co",
                "dates": "2019 - 2021",
                "bullets": [
                    "Answered customer phone calls and emails",
                    "Resolved customer complaints",
                    "Documented interactions in ticketing system",
                ]
            }
        ],
        "education": [
            "Associate's Degree, Community College, 2019"
        ],
        "skills": [
            "Customer service, Communication, Problem solving, Microsoft Office, Friendly attitude"
        ]
    },

    # ============================================================
    # SALES MANAGER / DIRECTOR
    # ============================================================
    "11_Sales_Manager_Director_IMPRESSIVE": {
        "name": "Marcus Johnson",
        "email": "marcus.johnson@email.com",
        "phone": "(617) 555-0987",
        "location": "Boston, MA",
        "linkedin": "linkedin.com/in/marcusjohnson-salesleader",
        "summary": "Results-driven Sales Director with 10+ years of experience building and scaling high-performing SaaS sales teams. Led team of 25 reps to $42M ARR in 2024, achieving 138% of target. Proven ability to recruit, coach, and develop top talent - promoted 8 reps to leadership roles. Expertise in MEDDPICC, Challenger Sale, and data-driven sales management.",
        "experience": [
            {
                "title": "Director of Sales",
                "company": "Datadog",
                "dates": "January 2021 - Present",
                "bullets": [
                    "Lead team of 25 (4 managers, 21 AEs) responsible for $42M ARR target",
                    "Achieved 138% of team quota in 2024, driving $58M in new ARR",
                    "Grew team from 8 to 25 reps while maintaining 120%+ attainment",
                    "Reduced average ramp time from 6 months to 4.3 months through improved onboarding",
                    "Implemented MEDDPICC methodology, increasing win rates from 22% to 35%",
                    "Promoted 8 individual contributors to management or senior roles",
                    "Achieved 85% rep retention rate (industry avg: 65%)",
                    "Built forecasting model achieving 95% accuracy within 5% variance",
                ]
            },
            {
                "title": "Sales Manager",
                "company": "Twilio",
                "dates": "March 2018 - December 2020",
                "bullets": [
                    "Managed team of 10 AEs exceeding quota by 125% for 3 consecutive years",
                    "Team generated $18M in new ARR in 2020",
                    "Hired and developed 15 AEs, 6 of whom were promoted",
                    "Implemented Gong for call coaching, improving close rates by 20%",
                ]
            },
            {
                "title": "Senior Account Executive",
                "company": "Twilio",
                "dates": "June 2015 - February 2018",
                "bullets": [
                    "Top performing AE for 2 consecutive years, closing $4.5M annually",
                    "3x President's Club winner, promoted to management",
                ]
            }
        ],
        "education": [
            "MBA, Harvard Business School, 2015",
            "BS in Computer Science, MIT, 2011"
        ],
        "skills": [
            "Leadership: Team Building, Coaching, Performance Management, Hiring, Forecasting",
            "Tools: Salesforce, Gong, Clari, Tableau, Outreach, LinkedIn Recruiter",
            "Methodologies: MEDDPICC, Challenger Sale, Force Management, Sandler",
            "Certifications: Certified Sales Leader (CSL), MEDDPICC Certified Trainer"
        ]
    },

    "12_Sales_Manager_Director_UNIMPRESSIVE": {
        "name": "Linda Martinez",
        "email": "lmartinez@yahoo.com",
        "phone": "(555) 321-6547",
        "location": "Denver, CO",
        "linkedin": "",
        "summary": "Sales manager with experience leading sales teams. Have managed reps and helped them improve their performance. Good at motivating people and building team culture.",
        "experience": [
            {
                "title": "Sales Manager",
                "company": "Tech Sales Company",
                "dates": "2020 - Present",
                "bullets": [
                    "Manage a team of sales representatives",
                    "Conduct weekly one-on-one meetings with reps",
                    "Review deals in pipeline and provide guidance",
                    "Participate in hiring interviews for new reps",
                    "Report on team performance to leadership",
                    "Handle escalated customer situations",
                    "Organize team meetings and training sessions",
                ]
            },
            {
                "title": "Senior Sales Representative",
                "company": "Another Tech Company",
                "dates": "2017 - 2020",
                "bullets": [
                    "Was a top performer on the sales team",
                    "Helped train new sales reps",
                    "Promoted to manager based on tenure",
                ]
            },
            {
                "title": "Sales Representative",
                "company": "Sales Corp",
                "dates": "2014 - 2017",
                "bullets": [
                    "Made sales calls and closed deals",
                    "Worked with various customers",
                ]
            }
        ],
        "education": [
            "Bachelor's Degree, Colorado State University, 2014"
        ],
        "skills": [
            "Team management, Sales experience, Communication, Leadership, Microsoft Office"
        ]
    },
}


def create_pdf(filename, data):
    """Create a PDF resume from the given data."""
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )

    styles = getSampleStyleSheet()

    # Custom styles
    name_style = ParagraphStyle(
        'NameStyle',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=6
    )

    contact_style = ParagraphStyle(
        'ContactStyle',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        spaceAfter=12
    )

    section_style = ParagraphStyle(
        'SectionStyle',
        parent=styles['Heading2'],
        fontSize=12,
        spaceBefore=12,
        spaceAfter=6,
        borderWidth=0,
        borderPadding=0,
        textColor='#1a365d'
    )

    job_title_style = ParagraphStyle(
        'JobTitleStyle',
        parent=styles['Normal'],
        fontSize=11,
        fontName='Helvetica-Bold',
        spaceAfter=2
    )

    company_style = ParagraphStyle(
        'CompanyStyle',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica-Oblique',
        spaceAfter=4
    )

    bullet_style = ParagraphStyle(
        'BulletStyle',
        parent=styles['Normal'],
        fontSize=10,
        leftIndent=20,
        spaceAfter=3
    )

    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=4
    )

    story = []

    # Name
    story.append(Paragraph(data['name'], name_style))

    # Contact info
    contact_parts = [data['email'], data['phone'], data['location']]
    if data.get('linkedin'):
        contact_parts.append(data['linkedin'])
    contact_line = " | ".join(contact_parts)
    story.append(Paragraph(contact_line, contact_style))

    # Summary
    story.append(Paragraph("PROFESSIONAL SUMMARY", section_style))
    story.append(Paragraph(data['summary'], normal_style))

    # Experience
    story.append(Paragraph("PROFESSIONAL EXPERIENCE", section_style))
    for exp in data['experience']:
        story.append(Paragraph(exp['title'], job_title_style))
        story.append(Paragraph(f"{exp['company']} | {exp['dates']}", company_style))
        for bullet in exp['bullets']:
            story.append(Paragraph(f"• {bullet}", bullet_style))
        story.append(Spacer(1, 6))

    # Education
    story.append(Paragraph("EDUCATION", section_style))
    for edu in data['education']:
        story.append(Paragraph(edu, normal_style))

    # Skills
    story.append(Paragraph("SKILLS & CERTIFICATIONS", section_style))
    for skill in data['skills']:
        story.append(Paragraph(skill, normal_style))

    doc.build(story)
    print(f"Created: {filename}")


def main():
    """Generate all test resumes."""
    import os

    output_dir = os.path.dirname(os.path.abspath(__file__))

    for name, data in RESUMES.items():
        filename = os.path.join(output_dir, f"{name}.pdf")
        create_pdf(filename, data)

    print(f"\nGenerated {len(RESUMES)} test resumes in {output_dir}")


if __name__ == "__main__":
    main()

# recommender.py
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

# very small mapping of interest -> career & required skills
CAREER_MAP = {
    'programming': {'career': 'Software Engineer', 'skills': ['python', 'data-structures', 'algorithms']},
    'biology': {'career': 'Biotech Researcher', 'skills': ['molecular-bio', 'lab-techniques', 'statistics']},
    'data': {'career': 'Data Analyst', 'skills': ['python', 'sql', 'statistics']},
    'design': {'career': 'UI/UX Designer', 'skills': ['design-principles', 'figma', 'portfolio']}
}

def get_recommendations(interests, skills):
    recs = []
    for it in interests:
        key = it.lower().strip()
        for k in CAREER_MAP:
            if k in key or key in k:
                recs.append(CAREER_MAP[k])
    # dedupe
    seen = set()
    out = []
    for r in recs:
        if r['career'] not in seen:
            out.append(r)
            seen.add(r['career'])
    # fallback if empty
    if not out:
        out = [{'career': 'General Counseling',
                'skills': ['communication', 'career-planning']}]
    return out

def skill_gap(recs, user_skills):
    user = set([s.lower().strip() for s in user_skills])
    gaps = {}
    for r in recs:
        required = set(r['skills'])
        missing = list(required - user)
        gaps[r['career']] = missing
    return gaps

# Pretty console output if run directly
if __name__ == "__main__":
    console = Console()

    console.print(Panel.fit("[bold cyan]Career Adviser Recommender[/bold cyan]", border_style="blue"))

    # Example input
    user_interests = ["Programming", "Data"]
    user_skills = ["python", "sql"]

    recs = get_recommendations(user_interests, user_skills)
    gaps = skill_gap(recs, user_skills)

    table = Table(title="Recommended Careers", title_style="bold green")
    table.add_column("Career", style="bold yellow")
    table.add_column("Required Skills", style="cyan")
    table.add_column("Skill Gaps", style="red")

    for r in recs:
        career = r['career']
        req = ", ".join(r['skills'])
        gap = ", ".join(gaps[career]) if gaps[career] else "None 🎉"
        table.add_row(career, req, gap)

    console.print(table)
    console.print(Panel("[bold magenta]Tip:[/bold magenta] Keep learning to close your gaps and grow your career!", style="green"))

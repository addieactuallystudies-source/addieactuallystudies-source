from pathlib import Path
from datetime import datetime, timedelta, timezone
import urllib.request
import json
import os

# Locate the garden SVG file
ROOT = Path(__file__).resolve().parent.parent
GARDEN = ROOT / "assets" / "garden.svg"
# Decide which plant to grow
def choose_plant(count):
    if count == 0:
        return None
    elif count <= 3:
        return "seedling"
    elif count <= 9:
        return "rose"
    else:
        return "goldflower"

# GitHub configuration
USERNAME = "addieactuallystudies-source"
TOKEN = os.environ.get("GITHUB_TOKEN")


def get_contributions():

    if not TOKEN:
        raise RuntimeError("GitHub token is missing!")

    now = datetime.now(timezone.utc)
    start = now - timedelta(days=20)

    query = """
    query($username: String!, $from: DateTime!, $to: DateTime!) {
        user(login: $username) {
            contributionsCollection(from: $from, to: $to) {
                contributionCalendar {
                    weeks {
                        contributionDays {
                            date
                            contributionCount
                        }
                    }
                }
            }
        }
    }
    """

    payload = {
        "query": query,
        "variables": {
            "username": USERNAME,
            "from": start.isoformat(),
            "to": now.isoformat()
        }
    }

    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "Enchanted-Garden"
        },
        method="POST"
    )

    with urllib.request.urlopen(request) as response:
        result = json.load(response)

    if result.get("errors"):
        raise RuntimeError(result["errors"])

    weeks = result["data"]["user"][
        "contributionsCollection"
    ]["contributionCalendar"]["weeks"]

    days = []

    for week in weeks:
        days.extend(week["contributionDays"])

    days.sort(key=lambda day: day["date"])

    return [
        day["contributionCount"]
        for day in days[-20:]
    ]


contributions = get_contributions()
# Positions of plants in the garden
positions = []

for y in [185, 290]:
    for x in [120, 160, 200, 240, 280,
              500, 540, 580, 620, 660]:
        positions.append((x, y))


# Generate SVG plants
plants = []

for count, (x, y) in zip(contributions, positions):
    plant = choose_plant(count)

    if plant:
        plants.append(
            f'<use href="#{plant}" x="{x}" y="{y}"/>'
        )


# Read the existing garden
svg = GARDEN.read_text(encoding="utf-8")

start = "<!-- PLANTS_START -->"
end = "<!-- PLANTS_END -->"

# Replace the old plants
before = svg.split(start)[0]
after = svg.split(end)[1]

updated_svg = (
    before
    + start + "\n"
    + "\n".join(plants) + "\n"
    + end
    + after
)

# Save the updated garden
GARDEN.write_text(updated_svg, encoding="utf-8")

print("Your enchanted garden has been updated!")
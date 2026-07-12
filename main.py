import requests
import pandas as pd
import plotly.graph_objects as go
import dotenv
import os
import plotly.subplots as sp

dotenv.load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def fetch_notion_data():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"

    payload = {"page_size": 100}

    print("Fetching data from Notion...")
    response = requests.post(url, json=payload, headers=HEADERS)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch data from Notion. Status code: {response.status_code}, Response: {response.text}")
    
    data = response.json()
    rows = []

    for page in data.get("results", []):
        props = page.get("properties", {})

        date_property = props.get("Date", {}).get("date", {})
        if not date_property:
            continue
        date_val = date_property.get("start")

        row_data = {
            "Date": date_val,
            "Make Bed": props.get("🛏️ Make Bed", {}).get("checkbox", False),
            "Exercise": props.get("💪 Exercise", {}).get("checkbox", False),
            "Study": props.get("🖊️ Study", {}).get("checkbox", False),
            "Protein": props.get("💪 Protein", {}).get("checkbox", False),
            "Reading": props.get("📖 Reading", {}).get("checkbox", False),
            "Wash Face": props.get("🧼 Wash Face", {}).get("checkbox", False),
        }
        rows.append(row_data)

    if not rows:
        print("No data found in the Notion database.")

    return pd.DataFrame(rows)

def generate_dashboard():

    df = fetch_notion_data()

    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date")

    core_habits = ["Make Bed", "Exercise", "Study", "Protein", "Reading", "Wash Face"]

    for habit in core_habits:
        df[habit] = df[habit].astype(int)

    fig = sp.make_subplots(
        rows=3, cols=2, 
        specs=[
            [{"type": "pie"}, {"type": "pie"}, {"type": "pie"}],
            [{"type": "pie"}, {"type": "pie"}, {"type": "pie"}]
        ],
        subplot_titles=core_habits
    )

    color_palette = {
        "Make Bed": "blue",
        "Exercise": "green",
        "Study": "orange",
        "Protein": "red",
        "Reading": "purple",
        "Wash Face": "cyan"
    }

    grid_positions = [(1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3)]

    for idx, habit in enumerate(core_habits):
        row, col = grid_positions[idx]

        completed_count = df[habit].sum()
        missed_count = len(df) - completed_count

        fig.add_trace(
            go.Pie(
                labels=["Done", "Missed"],
                values=[completed_count, missed_count],
                hole=0.5,
                marker=dict(colors=[color_palette[habit], "lightgray"]),
                textinfo="percent",
                hoverinfo="label+value",
                name=habit
            ),
            row=row, col=col
        )

    fig.update_layout(
        title=dict(
            text="Overall Habit Completion Breakdown", 
            font=dict(size=22, color="#ffffff"),
            x=0.05, y=0.98
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        margin=dict(l=20, r=20, t=80, b=20)
    )

    for annotation in fig['layout']['annotations']:
        annotation['font'] = dict(size=14, color='#ffffff')

    fig.write_html("index.html", include_plotlyjs="cdn")
    print("🚀 Success! Interactive multi-donut 'index.html' dashboard successfully updated.")

if __name__ == "__main__":
    generate_dashboard()
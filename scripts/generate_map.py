import os

import folium
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from folium.plugins import Fullscreen, HeatMap

load_dotenv()

OUTPUT_PATH = "docs/index.html"

QUERY = """
select
    cluster_id, n_accidents, centroid_lat, centroid_lng,
    dead_total, injured_severe_total, injured_light_total,
    first_accident_date, last_accident_date,
    n_arms_json, n_arms_csv, n_exat,
    is_geocoded, severity_score, rank
from mart_blackspot_severity
order by is_geocoded, severity_score desc
"""

SOURCE_COLOR = {False: "red", True: "orange"}
SOURCE_LABEL = {False: "จุดเสี่ยง ARMS (พิกัดจริง)", True: "จุดเสี่ยง EXAT (พิกัดประมาณ)"}


def get_connection():
    return psycopg2.connect(
        host=os.environ["POSTGRES_HOST"],
        port=os.environ["POSTGRES_PORT"],
        dbname=os.environ["WAREHOUSE_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )


def fetch_blackspots():
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(QUERY)
            return cur.fetchall()
    finally:
        conn.close()


def build_popup(row):
    return folium.Popup(
        f"""
        <b>Cluster #{row['cluster_id']}</b> (rank {row['rank']}{' - geocoded' if row['is_geocoded'] else ''})<br>
        จำนวนอุบัติเหตุ: {row['n_accidents']}<br>
        เสียชีวิต: {row['dead_total']}, บาดเจ็บสาหัส: {row['injured_severe_total']}, บาดเจ็บเล็กน้อย: {row['injured_light_total']}<br>
        severity score: {row['severity_score']}<br>
        ช่วงวันที่: {row['first_accident_date']} ถึง {row['last_accident_date']}<br>
        source: arms_json={row['n_arms_json']}, arms_csv={row['n_arms_csv']}, exat={row['n_exat']}
        """,
        max_width=300,
    )


def marker_radius(severity_score, max_score):
    if not max_score:
        return 8
    return 5 + 15 * (severity_score / max_score)


def build_source_groups(rows):
    max_score = {
        geocoded: max((r["severity_score"] for r in rows if r["is_geocoded"] == geocoded), default=0)
        for geocoded in (False, True)
    }
    groups = {
        geocoded: folium.FeatureGroup(name=SOURCE_LABEL[geocoded]) for geocoded in (False, True)
    }
    for row in rows:
        geocoded = row["is_geocoded"]
        folium.CircleMarker(
            location=[row["centroid_lat"], row["centroid_lng"]],
            radius=marker_radius(row["severity_score"], max_score[geocoded]),
            color=SOURCE_COLOR[geocoded],
            fill=True,
            fill_color=SOURCE_COLOR[geocoded],
            fill_opacity=0.8,
            popup=build_popup(row),
        ).add_to(groups[geocoded])
    return groups


def build_top10_group(rows):
    group = folium.FeatureGroup(name="Top 10 ต่อกลุ่ม (ขอบดำ)", show=False)
    for row in rows:
        if row["rank"] <= 10:
            folium.CircleMarker(
                location=[row["centroid_lat"], row["centroid_lng"]],
                radius=12,
                color="black",
                weight=2,
                fill=False,
                popup=build_popup(row),
            ).add_to(group)
    return group


def build_map(rows):
    m = folium.Map(location=[13.75, 100.5], zoom_start=6, tiles=None)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri",
        name="Esri World Street Map",
    ).add_to(m)

    heat_data = [
        [row["centroid_lat"], row["centroid_lng"], row["severity_score"]] for row in rows
    ]
    HeatMap(heat_data, name="Heatmap").add_to(m)

    for group in build_source_groups(rows).values():
        group.add_to(m)

    build_top10_group(rows).add_to(m)

    Fullscreen().add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)

    total_accidents = sum(row["n_accidents"] for row in rows)
    total_dead = sum(row["dead_total"] for row in rows)
    title_html = f"""
    <div style="position: fixed; top: 10px; left: 50px; z-index: 9999;
                background-color: white; padding: 8px 16px; border-radius: 5px;
                font-size: 16px; font-weight: bold; box-shadow: 0 1px 4px rgba(0,0,0,0.3);">
        Road Accident Blackspot Map — จุดเสี่ยงอุบัติเหตุ (ARMS + EXAT)<br>
        <span style="font-size: 12px; font-weight: normal;">
            {len(rows)} จุดเสี่ยง | อุบัติเหตุรวม {total_accidents} ครั้ง | เสียชีวิตรวม {total_dead} คน
        </span>
    </div>
    """
    m.get_root().html.add_child(folium.Element(title_html))

    legend_html = """
    <div style="position: fixed; bottom: 30px; left: 30px; z-index: 9999;
                background-color: white; padding: 10px 14px; border-radius: 5px;
                font-size: 14px; box-shadow: 0 1px 4px rgba(0,0,0,0.3);">
        <b>ประเภทจุดเสี่ยง</b><br>
        <span style="color: red;">&#9679;</span> พิกัดจริง (ARMS)<br>
        <span style="color: orange;">&#9679;</span> พิกัดประมาณ (EXAT)<br>
        <span style="color: black;">&#9675;</span> Top 10 ต่อกลุ่ม
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    return m


def main():
    rows = fetch_blackspots()
    m = build_map(rows)
    m.save(OUTPUT_PATH)
    print(f"Generated {OUTPUT_PATH} with {len(rows)} blackspots")


if __name__ == "__main__":
    main()

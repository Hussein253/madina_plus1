# 05_main_map.py
# ═══════════════════════════════════════════
# الخريطة الرئيسية المتكاملة لـ مدينة+ v1.2
# التغيير: الأزرار أصبحت تفاعلية بنوافذ منبثقة مع تفعيل كامل لـ Leaflet Event Handling
# ═══════════════════════════════════════════

import json
import os
import folium
import pandas as pd
import geopandas as gpd
from folium.plugins import (
    HeatMap, MiniMap, Fullscreen, LocateControl, MarkerCluster, MeasureControl
)
from datetime import datetime
from config import PATHS, BAGHDAD_CENTER, MAP_CONFIG

def build_madina_plus_map():
    print("🏛️ بناء خريطة مدينة+ المتكاملة v1.2...")

    # ══════════════════════════════════════
    # تحميل البيانات
    # ══════════════════════════════════════
    districts = gpd.read_file(PATHS["data_processed"] + "baghdad_districts.geojson")
    complexes = gpd.read_file(PATHS["data_processed"] + "complexes_with_ai.geojson")
    flood_grid = gpd.read_file(PATHS["data_processed"] + "flood_risk_grid.geojson")

    energy_forecast = None
    energy_path = PATHS["data_processed"] + "energy_forecast.json"
    if os.path.exists(energy_path):
        with open(energy_path, "r", encoding="utf-8") as f:
            energy_forecast = json.load(f)
        print(" ⚡ تنبؤ الطاقة محمّل")
    else:
        print(" ⚠️ energy_forecast.json غير موجود — شغّل 04 أولاً")

    # ══════════════════════════════════════
    # إحصائيات الـ Dashboard
    # ══════════════════════════════════════
    total_complexes = len(complexes)
    connected = int(complexes["complex_plus_connected"].sum())
    critical_flood = len(flood_grid[flood_grid["flood_risk"] > 0.75])
    total_revenue = int(complexes["monthly_revenue"].sum())
    avg_risk = float(complexes["risk_score"].mean())
    city_health = int((1 - avg_risk) * 100)

    avg_price = 0
    if "predicted_unit_price" in complexes.columns:
        avg_price = int(complexes["predicted_unit_price"].mean())

    health_color = (
        "#FF2200" if city_health < 40 else
        "#FF8800" if city_health < 60 else
        "#FFD700" if city_health < 75 else "#00FF88"
    )
    health_label = (
        "حرجة" if city_health < 40 else
        "تحتاج تدخل" if city_health < 60 else
        "متوسطة" if city_health < 75 else "جيدة"
    )

    # ══════════════════════════════════════
    # بيانات النوافذ التفاعلية
    # ══════════════════════════════════════
    # Property AI
    top5 = ""
    worst5 = ""
    if "predicted_unit_price" in complexes.columns:
        for _, r in complexes.nlargest(5, "predicted_unit_price").iterrows():
            top5 += (
                f"<tr>"
                f"<td style='padding:5px;color:#aaa'>{str(r['name'])[:22]}</td>"
                f"<td style='padding:5px;color:#00FF88;text-align:right;font-weight:bold'>"
                f"{int(r['predicted_unit_price']):,} د.ع</td>"
                f"</tr>"
            )
        for _, r in complexes.nsmallest(5, "predicted_unit_price").iterrows():
            worst5 += (
                f"<tr>"
                f"<td style='padding:5px;color:#aaa'>{str(r['name'])[:22]}</td>"
                f"<td style='padding:5px;color:#FF8800;text-align:right;font-weight:bold'>"
                f"{int(r['predicted_unit_price']):,} د.ع</td>"
                f"</tr>"
            )

    # Flood AI
    top_flood = ""
    for _, r in districts.nlargest(5, "flood_risk").iterrows():
        rc = (
            "#FF2200" if r["flood_risk"] > 0.75 else
            "#FF8800" if r["flood_risk"] > 0.55 else "#FFD700"
        )
        top_flood += (
            f"<tr>"
            f"<td style='padding:5px;color:#aaa'>{r['name']}</td>"
            f"<td style='padding:5px;color:{rc};text-align:right;font-weight:bold'>"
            f"{int(r['flood_risk']*100)}%</td>"
            f"</tr>"
        )

    # Complex+ Stats
    complex_stats = ""
    for level, label, color in [
        ("CRITICAL", "حرج", "#FF2200"),
        ("HIGH", "مرتفع", "#FF8800"),
        ("MEDIUM", "متوسط", "#FFD700"),
        ("LOW", "منخفض", "#00FF88")
    ]:
        count = len(complexes[complexes["risk_level"] == level])
        pct = int(count / total_complexes * 100) if total_complexes else 0
        complex_stats += (
            f"<tr>"
            f"<td style='padding:5px;color:#aaa'>{label}</td>"
            f"<td style='padding:5px;text-align:center'>"
            f"<span style='color:{color};font-weight:bold'>{count}</span></td>"
            f"<td style='padding:5px;text-align:right;color:#555'>{pct}%</td>"
            f"</tr>"
        )
    connected_pct = int(connected / total_complexes * 100) if total_complexes else 0

    # Energy Pred
    energy_table = ""
    energy_summary_html = ""
    if energy_forecast:
        for p in energy_forecast["predictions"]:
            ec = {
                "CRITICAL": "#FF2200", "HIGH": "#FF8800",
                "MEDIUM": "#FFD700", "LOW": "#00FF88"
            }.get(p["risk_level"], "#888")
            energy_table += (
                f"<tr>"
                f"<td style='padding:4px;color:#aaa'>{p['date']}</td>"
                f"<td style='padding:4px;text-align:center;font-weight:bold;color:#fff'>"
                f"{p['predicted_mw']} MW</td>"
                f"<td style='padding:4px;text-align:right;color:{ec}'>"
                f"{p['risk_level']}</td>"
                f"</tr>"
            )
        nd = energy_forecast["predictions"][0]
        peak = energy_forecast["predictions"][4]
        ec = { "CRITICAL": "#FF2200", "HIGH": "#FF8800", "MEDIUM": "#FFD700", "LOW": "#00FF88" }.get(nd["risk_level"], "#888")
        energy_summary_html = f"""
        <div style="background:#050a05;border:1px solid #006600; border-radius:8px;padding:10px;margin-bottom:10px">
          <div style="font-size:9px;color:#00AA44;letter-spacing:2px; margin-bottom:6px">⚡ تنبؤ الطاقة — الأيام القادمة</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px">
            <div style="text-align:center">
              <div style="font-size:16px;font-weight:bold;color:{ec}"> {nd['predicted_mw']} MW</div>
              <div style="font-size:8px;color:#555">غداً</div>
            </div>
            <div style="text-align:center">
              <div style="font-size:11px;font-weight:bold; color:{ec};padding-top:4px">{nd['risk_level']}</div>
              <div style="font-size:8px;color:#555">مستوى الخطر</div>
            </div>
          </div>
          <div style="margin-top:6px;font-size:9px;color:#444">
            ذروة الأسبوع: {peak['date']} — {peak['predicted_mw']} MW
          </div>
        </div>
        """

    # Analytics
    analytics_rows = f"""
    <tr><td style='padding:5px;color:#aaa'>إجمالي المجمعات</td> <td style='padding:5px;color:#FF6600;text-align:right;font-weight:bold'>{total_complexes}</td></tr>
    <tr><td style='padding:5px;color:#aaa'>مرتبطة بـ Complex+</td> <td style='padding:5px;color:#00FF88;text-align:right;font-weight:bold'>{connected}</td></tr>
    <tr><td style='padding:5px;color:#aaa'>مناطق خطر فيضان</td> <td style='padding:5px;color:#FF2200;text-align:right;font-weight:bold'>{critical_flood}</td></tr>
    <tr><td style='padding:5px;color:#aaa'>أحياء مراقبة</td> <td style='padding:5px;color:#FFD700;text-align:right;font-weight:bold'>{len(districts)}</td></tr>
    <tr><td style='padding:5px;color:#aaa'>صحة المدينة</td> <td style='padding:5px;color:{health_color};text-align:right;font-weight:bold'> {city_health}% — {health_label}</td></tr>
    <tr><td style='padding:5px;color:#aaa'>الإيراد الشهري</td> <td style='padding:5px;color:#00FF88;text-align:right;font-weight:bold'> {total_revenue:,} د.ع</td></tr>
    <tr><td style='padding:5px;color:#aaa'>متوسط سعر الوحدة (AI)</td> <td style='padding:5px;color:#FFD700;text-align:right;font-weight:bold'> {avg_price:,} د.ع</td></tr>
    """

    # ══════════════════════════════════════
    # بناء الخريطة
    # ══════════════════════════════════════
    m = folium.Map(
        location=[BAGHDAD_CENTER["lat"], BAGHDAD_CENTER["lon"]],
        zoom_start=MAP_CONFIG["zoom_start"],
        tiles=None
    )
    folium.TileLayer("CartoDB dark_matter", name="🌑 مظلمة").add_to(m)
    folium.TileLayer("OpenStreetMap", name="🗺️ عادية", show=False).add_to(m)
    folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        attr="Google", name="🛰️ قمر صناعي", show=False
    ).add_to(m)

    # طبقة الفيضانات
    flood_group = folium.FeatureGroup(name="🌊 خطر الفيضانات", show=True)
    flood_points = [
        [r.lat, r.lon, r.flood_risk]
        for r in flood_grid[flood_grid["flood_risk"] > 0.3].itertuples()
    ]
    HeatMap(
        flood_points, min_opacity=0.3, radius=18, blur=14,
        gradient={ 0.3: "#0000FF", 0.5: "#00FFFF", 0.7: "#FFFF00", 0.85: "#FF4400", 1.0: "#FF0000" }
    ).add_to(flood_group)
    flood_group.add_to(m)

    # طبقة الأحياء
    risk_colors = { "CRITICAL": "#FF2200", "HIGH": "#FF8800", "MEDIUM": "#FFD700", "LOW": "#00FF88" }
    district_group = folium.FeatureGroup(name="🏙️ أحياء بغداد", show=True)
    for _, d in districts.iterrows():
        infra = d["infrastructure_score"]
        risk = (
            "CRITICAL" if infra < 0.3 else
            "HIGH"     if infra < 0.5 else
            "MEDIUM"   if infra < 0.7 else "LOW"
        )
        color = risk_colors[risk]
        popup_html = f"""
        <div style='font-family:monospace;background:#0d0d0d;color:#e0e0e0; padding:12px;border-radius:8px;min-width:230px; border:1px solid {color}'>
          <b style='color:{color};font-size:14px'>{d['name']}</b>
          <hr style='border-color:#333;margin:6px 0'>
          👥 السكان: <b>{d['population']:,}</b><br>
          🏗️ عمر البنية: <b>{d['infrastructure_age']} سنة</b><br>
          🌊 خطر الفيضان: <b>{int(d['flood_risk']*100)}%</b><br>
          💰 متوسط العقار: <b>{d['avg_property_price']:,} د.ع</b><br>
          🔧 نقاط البنية: <b>{int(d['infrastructure_score']*100)}%</b><br>
          📊 الحالة: <b style='color:{color}'>{risk}</b>
        </div>
        """
        folium.CircleMarker(
            location=[d["lat"], d["lon"]],
            radius=14, color=color, fill=True, fill_color=color, fill_opacity=0.25,
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=f"🏙️ {d['name']} — انقر للتفاصيل"
        ).add_to(district_group)
    district_group.add_to(m)

    # طبقة المجمعات
    cluster = MarkerCluster(
        name="🏗️ المجمعات السكنية", overlay=True, control=True,
        options={ "maxClusterRadius": 50, "spiderfyOnMaxZoom": True, "showCoverageOnHover": True }
    )
    for _, c in complexes.iterrows():
        risk_c = c.get("risk_level", "LOW")
        color = risk_colors.get(risk_c, "#888")
        price = int(c.get("predicted_unit_price", 0) or 0)
        grade = c.get("investment_grade", "—") or "—"
        icon_color = { "CRITICAL": "red", "HIGH": "orange", "MEDIUM": "beige", "LOW": "green" }.get(risk_c, "blue")
        popup_html = f"""
        <div style='font-family:monospace;background:#0d0d0d;color:#e0e0e0; padding:12px;border-radius:8px;min-width:240px; border:1px solid {color}'>
          <b style='color:{color}'>{c['name']}</b>
          <hr style='border-color:#333;margin:6px 0'>
          🏠 الوحدات: <b>{c['total_units']}</b><br>
          👤 الإشغال: <b>{int(c['occupancy_rate']*100)}%</b><br>
          💰 سعر الوحدة: <b>{price:,} د.ع</b><br>
          📊 تقييم: <b style='color:{color}'>{grade}</b><br>
          ⚠️ درجة الخطر: <b>{int(c['risk_score']*100)}%</b><br>
          🔗 Complex+: <b>{'✅' if c['complex_plus_connected'] else '❌'}</b><br>
          📅 آخر فحص: <b>{c['last_inspection']}</b>
        </div>
        """
        folium.Marker(
            location=[c["lat"], c["lon"]],
            popup=folium.Popup(popup_html, max_width=270),
            tooltip=f"🏗️ {c['name']}",
            icon=folium.Icon(color=icon_color, icon="building", prefix="fa")
        ).add_to(cluster)
    cluster.add_to(m)

    # إضافات احترافية
    Fullscreen(position="topleft", title="ملء الشاشة", title_cancel="تصغير").add_to(m)
    LocateControl(position="topleft", strings={"title": "موقعي الحالي"}, flyTo=True).add_to(m)
    MeasureControl(
        position="topleft", primary_length_unit="kilometers",
        secondary_length_unit="meters", primary_area_unit="sqkilometers"
    ).add_to(m)
    MiniMap(
        position="bottomright", width=160, height=160,
        toggle_display=True, tile_layer="CartoDB dark_matter"
    ).add_to(m)
    folium.LayerControl(position="topright", collapsed=False).add_to(m)

    # ══════════════════════════════════════
    # HTML الكامل: النوافذ + لوحة التحكم
    # ══════════════════════════════════════
    full_ui = f"""

    <div id="etc-overlay" onclick="etcCloseAll()" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%; background:rgba(0,0,0,0.75);z-index:99998"></div>

    <div id="panel-complex" style="display:none;position:fixed;top:50%;left:50%; transform:translate(-50%,-50%);z-index:99999;width:380px; background:rgba(5,5,10,0.99);border-radius:12px;overflow:hidden; border:1px solid #FF6600;box-shadow:0 20px 60px rgba(0,0,0,0.95)">
        <div style="background:linear-gradient(135deg,#1a0800,#0d0d0d);padding:12px 15px; display:flex;justify-content:space-between;align-items:center; border-bottom:1px solid #1a1a1a">
            <span style="color:#FF6600;font-weight:bold;font-family:monospace;font-size:13px"> 🏗️ Complex+ Link</span>
            <button class="etc-close-btn" data-panel="panel-complex" style="background:none;border:1px solid #444;color:#888;border-radius:4px; padding:2px 9px;cursor:pointer;font-size:15px;line-height:1">✕</button>
        </div>
        <div style="padding:15px;font-family:monospace">
            <table style="width:100%;border-collapse:collapse;font-size:11px;margin-bottom:12px"> {complex_stats} </table>
        </div>
    </div>
    
    <div id="panel-flood" style="display:none;position:fixed;top:50%;left:50%; transform:translate(-50%,-50%);z-index:99999;width:380px; background:rgba(5,5,10,0.99);border-radius:12px;overflow:hidden; border:1px solid #0066FF;box-shadow:0 20px 60px rgba(0,0,0,0.95)">
        <div style="background:linear-gradient(135deg,#000820,#0d0d0d);padding:12px 15px; display:flex;justify-content:space-between;align-items:center; border-bottom:1px solid #1a1a1a">
            <span style="color:#00AAFF;font-weight:bold;font-family:monospace;font-size:13px"> 🌊 Flood AI</span>
            <button class="etc-close-btn" data-panel="panel-flood" style="background:none;border:1px solid #444;color:#888;border-radius:4px; padding:2px 9px;cursor:pointer;font-size:15px;line-height:1">✕</button>
        </div>
        <div style="padding:15px;font-family:monospace">
             <table style="width:100%;border-collapse:collapse;font-size:11px;margin-bottom:12px"> {top_flood} </table>
        </div>
    </div>

    <div id="panel-property" style="display:none;position:fixed;top:50%;left:50%; transform:translate(-50%,-50%);z-index:99999;width:400px; background:rgba(5,5,10,0.99);border-radius:12px;overflow:hidden; border:1px solid #FFD700;box-shadow:0 20px 60px rgba(0,0,0,0.95)">
        <div style="background:linear-gradient(135deg,#1a1400,#0d0d0d);padding:12px 15px; display:flex;justify-content:space-between;align-items:center; border-bottom:1px solid #1a1a1a">
            <span style="color:#FFD700;font-weight:bold;font-family:monospace;font-size:13px"> 💰 Property AI</span>
            <button class="etc-close-btn" data-panel="panel-property" style="background:none;border:1px solid #444;color:#888;border-radius:4px; padding:2px 9px;cursor:pointer;font-size:15px;line-height:1">✕</button>
        </div>
        <div style="padding:15px;font-family:monospace">
            <table style="width:100%;border-collapse:collapse;font-size:10px;margin-bottom:12px"> {top5} </table>
        </div>
    </div>

    <div id="panel-energy" style="display:none;position:fixed;top:50%;left:50%; transform:translate(-50%,-50%);z-index:99999;width:380px; background:rgba(5,5,10,0.99);border-radius:12px;overflow:hidden; border:1px solid #00FF88;box-shadow:0 20px 60px rgba(0,0,0,0.95)">
        <div style="background:linear-gradient(135deg,#001a05,#0d0d0d);padding:12px 15px; display:flex;justify-content:space-between;align-items:center; border-bottom:1px solid #1a1a1a">
            <span style="color:#00FF88;font-weight:bold;font-family:monospace;font-size:13px"> ⚡ Energy Pred</span>
            <button class="etc-close-btn" data-panel="panel-energy" style="background:none;border:1px solid #444;color:#888;border-radius:4px; padding:2px 9px;cursor:pointer;font-size:15px;line-height:1">✕</button>
        </div>
        <div style="padding:15px;font-family:monospace">
            {energy_table}
        </div>
    </div>

    <div id="panel-satellite" style="display:none;position:fixed;top:50%;left:50%; transform:translate(-50%,-50%);z-index:99999;width:360px; background:rgba(5,5,10,0.99);border-radius:12px;overflow:hidden; border:1px solid #9370DB;box-shadow:0 20px 60px rgba(0,0,0,0.95)">
        <div style="background:linear-gradient(135deg,#0d0020,#0d0d0d);padding:12px 15px; display:flex;justify-content:space-between;align-items:center; border-bottom:1px solid #1a1a1a">
            <span style="color:#9370DB;font-weight:bold;font-family:monospace;font-size:13px"> 🛰️ Satellite</span>
            <button class="etc-close-btn" data-panel="panel-satellite" style="background:none;border:1px solid #444;color:#888;border-radius:4px; padding:2px 9px;cursor:pointer;font-size:15px;line-height:1">✕</button>
        </div>
        <div style="padding:15px;font-family:monospace">
            <div style="color:#888;font-size:11px">الطبقات متاحة من القائمة العلوية</div>
        </div>
    </div>

    <div id="panel-analytics" style="display:none;position:fixed;top:50%;left:50%; transform:translate(-50%,-50%);z-index:99999;width:380px; background:rgba(5,5,10,0.99);border-radius:12px;overflow:hidden; border:1px solid #00BFFF;box-shadow:0 20px 60px rgba(0,0,0,0.95)">
        <div style="background:linear-gradient(135deg,#001520,#0d0d0d);padding:12px 15px; display:flex;justify-content:space-between;align-items:center; border-bottom:1px solid #1a1a1a">
            <span style="color:#00BFFF;font-weight:bold;font-family:monospace;font-size:13px"> 📊 Analytics</span>
            <button class="etc-close-btn" data-panel="panel-analytics" style="background:none;border:1px solid #444;color:#888;border-radius:4px; padding:2px 9px;cursor:pointer;font-size:15px;line-height:1">✕</button>
        </div>
        <div style="padding:15px;font-family:monospace">
            <table style="width:100%;border-collapse:collapse;font-size:11px"> {analytics_rows} </table>
        </div>
    </div>

    <div id="madina-dashboard" style="position:fixed; top:15px; right:15px; width:310px; z-index:9999; font-family:'Consolas','Courier New',monospace; background:rgba(5,5,10,0.97); color:#d0d0d0; border-radius:12px; overflow:hidden; box-shadow:0 20px 60px rgba(0,0,0,0.95); border:1px solid rgba(255,100,0,0.4)">
        <div style="background:linear-gradient(135deg,#1a0800,#0a0a0f); padding:13px 15px;border-bottom:1px solid #1a1a1a">
            <div style="font-size:9px;color:#FF4400;letter-spacing:3px;margin-bottom:3px"> ETC — ENGINEERED TRANSFORMATION CO.</div>
            <div style="font-size:17px;color:#fff;font-weight:bold;letter-spacing:1px"> 🏛️ مدينة+</div>
        </div>
        <div style="padding:13px">
            <div style="font-size:9px;color:#444;letter-spacing:2px;margin-bottom:8px"> ACTIVE MODULES — اضغط للتفاصيل ↓</div>
            <div id="button-container" style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:12px">
                <button class="etc-panel-btn" data-target="panel-complex" onclick="etcOpen('panel-complex')" style="background:#0a0a0a;border:1px solid #FF6600;border-radius:6px; padding:9px 7px;cursor:pointer;text-align:left;font-family:monospace; color:inherit;">
                    <div style="font-size:14px">🏗️</div> <div style="font-size:10px;color:#ddd">Complex+</div>
                </button>
                <button class="etc-panel-btn" data-target="panel-flood" onclick="etcOpen('panel-flood')" style="background:#0a0a0a;border:1px solid #0066FF;border-radius:6px; padding:9px 7px;cursor:pointer;text-align:left;font-family:monospace; color:inherit;">
                    <div style="font-size:14px">🌊</div> <div style="font-size:10px;color:#ddd">Flood AI</div>
                </button>
                <button class="etc-panel-btn" data-target="panel-property" onclick="etcOpen('panel-property')" style="background:#0a0a0a;border:1px solid #FFD700;border-radius:6px; padding:9px 7px;cursor:pointer;text-align:left;font-family:monospace; color:inherit;">
                    <div style="font-size:14px">💰</div> <div style="font-size:10px;color:#ddd">Property AI</div>
                </button>
                <button class="etc-panel-btn" data-target="panel-energy" onclick="etcOpen('panel-energy')" style="background:#0a0a0a;border:1px solid #00FF88;border-radius:6px; padding:9px 7px;cursor:pointer;text-align:left;font-family:monospace; color:inherit;">
                    <div style="font-size:14px">⚡</div> <div style="font-size:10px;color:#ddd">Energy</div>
                </button>
                <button class="etc-panel-btn" data-target="panel-satellite" onclick="etcOpen('panel-satellite')" style="background:#0a0a0a;border:1px solid #9370DB;border-radius:6px; padding:9px 7px;cursor:pointer;text-align:left;font-family:monospace; color:inherit;">
                    <div style="font-size:14px">🛰️</div> <div style="font-size:10px;color:#ddd">Satellite</div>
                </button>
                <button class="etc-panel-btn" data-target="panel-analytics" onclick="etcOpen('panel-analytics')" style="background:#0a0a0a;border:1px solid #00BFFF;border-radius:6px; padding:9px 7px;cursor:pointer;text-align:left;font-family:monospace; color:inherit;">
                    <div style="font-size:14px">📊</div> <div style="font-size:10px;color:#ddd">Analytics</div>
                </button>
            </div>
        </div>
    </div>

    <script>
var ETC_PANELS = ['panel-complex','panel-flood','panel-property','panel-energy','panel-satellite','panel-analytics'];

document.addEventListener('DOMContentLoaded', function() {{
    var panelBtns = document.querySelectorAll('.etc-panel-btn');
    panelBtns.forEach(function(btn) {{
        btn.addEventListener('click', function() {{
            var target = btn.getAttribute('data-target');
            ETC_PANELS.forEach(function(pid) {{
                var p = document.getElementById(pid);
                if (p) p.style.display = 'none';
            }});
            var overlay = document.getElementById('etc-overlay');
            var panel = document.getElementById(target);
            if (overlay) overlay.style.display = 'block';
            if (panel) panel.style.display = 'block';
        }});
    }});

    var closeBtns = document.querySelectorAll('.etc-close-btn');
    closeBtns.forEach(function(btn) {{
        btn.addEventListener('click', function(e) {{
            var closeId = btn.getAttribute('data-panel');
            var panel = document.getElementById(closeId);
            if (panel) panel.style.display = 'none';
            var overlay = document.getElementById('etc-overlay');
            if (overlay) overlay.style.display = 'none';
            e.stopPropagation();
        }});
    }});

    var overlay = document.getElementById('etc-overlay');
    if (overlay) {{
        overlay.addEventListener('click', function() {{
            ETC_PANELS.forEach(function(pid) {{
                var p = document.getElementById(pid);
                if (p) p.style.display = 'none';
            }});
            overlay.style.display = 'none';
        }});
    }}

    setTimeout(function() {{
        var dashboard = document.getElementById('madina-dashboard');
        if (dashboard && window.L && L.DomEvent) {{
            L.DomEvent.disableClickPropagation(dashboard);
            L.DomEvent.disableScrollPropagation(dashboard);
            ['mousedown', 'touchstart', 'dblclick'].forEach(function(event) {{
                dashboard.addEventListener(event, function(e) {{
                    e.stopPropagation();
                }});
            }});
        }}
    }}, 500);
}});

function etcOpen(id) {{
    document.getElementById('etc-overlay').style.display = 'block';
    document.getElementById(id).style.display = 'block';
}}
function etcClose(id) {{
    document.getElementById(id).style.display = 'none';
    document.getElementById('etc-overlay').style.display = 'none';
}}
function etcCloseAll() {{
    ETC_PANELS.forEach(function(id) {{
        var panel = document.getElementById(id);
        if (panel) panel.style.display = 'none';
    }});
    var overlay = document.getElementById('etc-overlay');
    if (overlay) overlay.style.display = 'none';
}}
</script>

    <div style="text-align:center;font-size:9px;color:#2a2a2a;border-top:1px solid #111;padding:10px 15px;letter-spacing:1px">
      {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} — ETC GeoAI Platform
    </div>
    """

    dashboard_html = full_ui


    m.get_root().html.add_child(folium.Element(dashboard_html))

    output_path = PATHS["outputs"] + "madina_plus.html"
    m.save(output_path)
    print(f"  ✅ الخريطة محفوظة: {output_path}")
    return output_path


if __name__ == "__main__":
    print("═" * 55)
    print("  مدينة+ — الخريطة الرئيسية v1.2")
    print("═" * 55)
    build_madina_plus_map()

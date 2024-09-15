import folium
import matplotlib
from matplotlib.patches import Rectangle
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
import pointpats as pp
import contextily as cx

matplotlib.use("TkAgg")

# Reading shooting GeoDataFrame
gdf_shootings = gpd.read_parquet("./data/gdf_shootings.parquet")
# Projecting CRS to UTM 24S
gdf_shootings.to_crs(31984, inplace=True)

# reading cities GeoDataFrame
gdf_rm_salvador = gpd.read_file("./data/dados_BA.gpkg", layer="gdf_rm_salvador")
gdf_rm_salvador.to_crs(31984, inplace=True)

# Reproduce table 1:
# Cities in the metropolitan region of Salvador with their total shootings recorded from July 1, 2022, to June 30, 2024..
gdf_shootings.groupby(gdf_shootings.city_name).size().sort_values(
    ascending=False
).to_frame("shootings")

# running global Knox test for each city
results = []
for city in gdf_shootings["city_name"].unique():
    gdf_tiroteios_city = gdf_shootings[gdf_shootings["city_name"] == city].copy()
    min_date = gdf_shootings.date.min()

    # Calculos de dias passados em função do primeiro registro de 2023
    gdf_tiroteios_city["time_in_days"] = gdf_tiroteios_city.date.apply(
        lambda x: x - min_date
    ).dt.days

    tiros_knox = pp.Knox.from_dataframe(
        gdf_tiroteios_city, time_col="time_in_days", delta=300, tau=5
    )

    results.append(
        {
            "city": city,
            "n_tiros": gdf_tiroteios_city.shape[0],
            "p_poisson": tiros_knox.p_poisson,
            "p_sim": tiros_knox.p_sim,
            "mean_tau": gdf_tiroteios_city["time_in_days"].mean(),
        }
    )

results = pd.DataFrame(results)

# filtering cities with p-value lower or equals to 0.05
# Reproduce table 2:
# Cities in the metropolitan region of Salvador with a deviation from the null hypothesis,
# indicating a systematic spatiotemporal correlation in the Knox Global Test.
results.loc[(results.p_poisson <= 0.05) | (results.p_sim <= 0.05)].reset_index(
    drop=True
)[["city", "n_tiros", "p_sim"]]

# Preparing data to test spatio-temporal [local] clustering
# Creating date sequence
min_date = gdf_shootings.date.min()

# Caculating days passed since the first shooting in 2023
gdf_shootings["time_in_days"] = gdf_shootings.date.apply(lambda x: x - min_date).dt.days

# Local Knox Local Spatio-temporal test
tiros_knox_local = pp.KnoxLocal.from_dataframe(
    gdf_shootings,
    time_col="time_in_days",
    delta=300,
    tau=5,
    permutations=99,
    keep=False,
)

tiros_knox_local_ = tiros_knox_local.hotspots()
# joining result with cities GeoDataFrame to identify the city of each shooting
shootings_spatemp_hotspot = tiros_knox_local_.sjoin(gdf_rm_salvador)

# saving shootings_spatemp_hotspot as GeoPackage
shootings_spatemp_hotspot.to_file(
    "./data/dados_BA.gpkg", layer="shootings_spatemp_hotspot"
)

# filtering spatio-temporal hotspots with p-value lower or equals to 0.05
shootings_spatemp_hotspot = shootings_spatemp_hotspot.loc[
    shootings_spatemp_hotspot.pvalue <= 0.05
]

# Reproduce table 3:
# Knox local statistics showing the number of lead, lag, and coincident shooting observations for each city.
shootings_spatemp_hotspot.groupby(
    [shootings_spatemp_hotspot.name_muni, shootings_spatemp_hotspot.orientation]
).size().to_frame("value").sort_values(by="value", ascending=False)

# Create map with Knox Local results
# Create fig with gridspec
fig = plt.figure(figsize=(15, 10))
gs = fig.add_gridspec(2, 2, height_ratios=[1, 1])  # Define uma grid de 2 linhas e 2 colunas

# First map: Reference Map: first line, first column
ax1 = fig.add_subplot(gs[0, 0])
gdf_rm_salvador.plot(ax=ax1, facecolor="none", edgecolor="black")
tiros_knox_local.plot(
    ax=ax1, colors={"focal": "red", "neighbor": "yellow", "nonsig": "none"}
)
cx.add_basemap(ax1, crs=gdf_rm_salvador.to_crs(31984).crs)
ax1.set_title("Metropolitan Region of Salvador")

# Define the Salvador area
salvador_xmin_zoom, salvador_ymin_zoom, salvador_xmax_zoom, salvador_ymax_zoom = (
    550667,
    8560768,
    558163,
    8566284)
# Add Salvador Area as a rectangle in the reference map
salvador_rect = Rectangle(
    (salvador_xmin_zoom,
     salvador_ymin_zoom),
    salvador_xmax_zoom - salvador_xmin_zoom,
    salvador_ymax_zoom - salvador_ymin_zoom,
    linewidth=2,
    edgecolor="black",
    facecolor="none",
    linestyle='dotted'
)
ax1.add_patch(salvador_rect)

# Second map: Salvador area map
ax2 = fig.add_subplot(gs[0, 1])
gdf_rm_salvador.plot(ax=ax2, facecolor="none", edgecolor="black")
tiros_knox_local.plot(
    ax=ax2, colors={"focal": "red", "neighbor": "yellow", "nonsig": "none"}
)
cx.add_basemap(
    ax2,
    crs=gdf_rm_salvador.to_crs(31984).crs,
    # source=cx.providers.Esri.WorldImagery,
    zoom=12,
)
ax2.set_xlim(salvador_xmin_zoom, salvador_xmax_zoom)
ax2.set_ylim(salvador_ymin_zoom, salvador_ymax_zoom)
ax2.set_title("Salvador area")

# Define a zoom to a specific example of Knox local hotspot
example_xmin_zoom, example_ymin_zoom, example_xmax_zoom, example_ymax_zoom = (
    551933,
    8563034,
    553259,
    8561993
    # 556116,
    # 8562535,
    # 558210,
    # 8561240
)
# Add example area as a rectangle to the Salvador map
example_rect = Rectangle(
    (example_xmin_zoom,
     example_ymin_zoom),
    example_xmax_zoom - example_xmin_zoom,
    example_ymax_zoom - example_ymin_zoom,
    linewidth=2,
    edgecolor="black",
    facecolor="none",
    linestyle='dotted'
)
ax2.add_patch(example_rect)

# Third map: specific Knox local hotspot
ax3 = fig.add_subplot(gs[1, :])
gdf_rm_salvador.plot(ax=ax3, facecolor="none", edgecolor="black")
tiros_knox_local.plot(ax=ax3, colors={"focal": "red", "neighbor": "yellow", "nonsig": "none"})
ax3.set_xlim(example_xmin_zoom, example_xmax_zoom)
ax3.set_ylim(example_ymax_zoom, example_ymin_zoom)
ax3.set_title('Knox local spatio-temporal example')
# Add annotations to the map
for idx, row in shootings_spatemp_hotspot.iterrows():
    point_x, point_y = row.geometry.x, row.geometry.y
    ax3.annotate(text=row['focal_time'], xy=(point_x, point_y), fontsize=8, color='red',
                xytext=(3, 3), textcoords="offset points")

cx.add_basemap(ax3, crs=gdf_rm_salvador.to_crs("EPSG:31984").crs, source=cx.providers.Esri.WorldImagery,
               #zoom=15
               )

plt.tight_layout()
# Save map
plt.savefig('mapa_1.png', dpi=300, bbox_inches='tight')

# Mostrar o gráfico
plt.show()

# Create and save a webmap with Knox Local results
e = tiros_knox_local.explore()
folium.GeoJson(gdf_rm_salvador).add_to(e)
e.add_child(folium.map.LayerControl())
e.save("Knox_local_test_result.html")

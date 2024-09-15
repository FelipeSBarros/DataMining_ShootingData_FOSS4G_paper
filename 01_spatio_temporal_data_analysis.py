import folium

import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
import pointpats as pp
import contextily as cx


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


ax = gdf_rm_salvador.plot(facecolor="none", edgecolor="black")
tiros_knox_local.plot(
    ax=ax, colors={"focal": "red", "neighbor": "yellow", "nonsig": "none"}
)
cx.add_basemap(
    ax,
    crs=gdf_rm_salvador.to_crs(31984).crs,
    # source=cx.providers.HERE.satelliteDay
)
# Obter os limites do GeoDataFrame tiros_knox_local
xmin, ymin, xmax, ymax = gdf_rm_salvador.total_bounds

# Ajustar os limites do gráfico para os limites de salva
ax.set_xlim(xmin, xmax)
ax.set_ylim(ymin, ymax)
matplotlib.use('TkAgg')
plt.show()




# Criar a figura e os eixos para os subplots
fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(15, 7))

# Mapa de Referência
gdf_rm_salvador.plot(ax=ax1, facecolor="none", edgecolor="black")
tiros_knox_local.plot(ax=ax1, colors={"focal": "red", "neighbor": "yellow", "nonsig": "none"})
cx.add_basemap(ax1, crs=gdf_rm_salvador.to_crs(31984).crs)
ax1.set_title('Mapa de Referência')

# Definir limites para o zoom (substitua com suas coordenadas)
# xmin_zoom, ymin_zoom, xmax_zoom, ymax_zoom = (-38.5, -12.5, -37.5, -11.5)
xmin_zoom, ymin_zoom, xmax_zoom, ymax_zoom = (-38.51886, -12.99604, -38.50775, -11.00704)

# Mapa com Zoom
gdf_rm_salvador.plot(ax=ax2, facecolor="none", edgecolor="black")
tiros_knox_local.plot(ax=ax2, colors={"focal": "red", "neighbor": "yellow", "nonsig": "none"})
cx.add_basemap(ax2, crs=gdf_rm_salvador.to_crs(31984).crs)
ax2.set_xlim(xmin_zoom, xmax_zoom)
ax2.set_ylim(ymin_zoom, ymax_zoom)
ax2.set_title('Mapa com Zoom')

# Ajustar layout
plt.tight_layout()

# Mostrar o gráfico
plt.show()



















e = tiros_knox_local.explore()
folium.GeoJson(gdf_rm_salvador).add_to(e)
e.add_child(folium.map.LayerControl())
e.save("Knox_local_test_result.html")

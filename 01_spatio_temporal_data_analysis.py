import folium

import pandas as pd
import geopandas as gpd
import pointpats as pp
import contextily as cx


# Reading shooting GeoDataFrame
gdf_shootings = gpd.read_parquet(
    "./data/gdf_shootings.parquet"
)
# reading cities GeoDataFrame
gdf_rm_salvador = gpd.read_file(
    "./data/dados_BA.gpkg",
    layer="gdf_rm_salvador")
gdf_rm_salvador.to_crs(31984, inplace=True)

# cria coluna datetime convertendo dado de data e hora como tal
# gdf_shootings["datetime"] = pd.to_datetime(gdf_shootings["datetime"])
# cria coluna de data e hora separando tais informacoes
# gdf_tiroteios["date"] = gdf_tiroteios.datetime.dt.date
# gdf_tiroteios["time"] = gdf_tiroteios.datetime.dt.time

# Table with the number of shootings per city
gdf_shootings.groupby(gdf_shootings.city_name).size().sort_values(
    ascending=False
).to_frame('shootings')

# Projecting CRS to UTM 24S
gdf_shootings.to_crs(31984, inplace=True)
# gdf_shootings_salvador = gdf_shootings[gdf_shootings["city_name"] == "SALVADOR"].copy()

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

# Organizing data to test spatio-temporal clustering
# filtering cities with p-value lower or equals to 0.05
results.loc[(results.p_poisson <= 0.05) | (results.p_sim <= 0.05)].reset_index(
    drop=True
)

# Creating date sequence
min_date = gdf_shootings.date.min()

# Caculating days passed since the first shooting in 2023
gdf_shootings["time_in_days"] = gdf_shootings.date.apply(lambda x: x - min_date).dt.days

# Global Knox Spatio-temporal test
tiros_knox = pp.Knox.from_dataframe(
    gdf_shootings,
    time_col="time_in_days",
    delta=300,
    tau=5
)
print("p_poisson: ", tiros_knox.p_poisson)
print("p_sim: ", tiros_knox.p_sim)

# Local Knox Spatio-temporal test
tiros_knox_local = pp.KnoxLocal.from_dataframe(
    gdf_shootings,
    time_col="time_in_days",
    delta=300,
    tau=5,
    permutations=99,
    keep=False,
)


tiros_knox_local.hotspots()

tiros_knox_local._gdfhs()

tiros_knox_local_ = tiros_knox_local.hotspots()
print(tiros_knox_local_.shape)
shootings_spatemp_hotspot = tiros_knox_local_.sjoin(gdf_rm_salvador)

shootings_spatemp_hotspot.to_file(
    "./data/dados_BA.gpkg",
    layer="shootings_spatemp_hotspot"
)

# filtering spatio-temporal hotspots with p-value lower or equals to 0.05
shootings_spatemp_hotspot = shootings_spatemp_hotspot.loc[shootings_spatemp_hotspot.pvalue <= 0.05]
print(tiros_knox_local_.shape)
shootings_spatemp_hotspot_orientation = (
    shootings_spatemp_hotspot.groupby(shootings_spatemp_hotspot.orientation).size().to_frame()
)

shootings_spatemp_hotspot_orientation

# table with the number of shootings per city and orientation
shootings_spatemp_hotspot.groupby(
    [shootings_spatemp_hotspot.name_muni, shootings_spatemp_hotspot.orientation]
).size().to_frame("value").sort_values(by="value", ascending=False)


ax = gdf_rm_salvador.plot(facecolor="none", edgecolor="black")
tiros_knox_local.plot(
    ax=ax, colors={"focal": "red", "neighbor": "yellow", "nonsig": "none"}
)
cx.add_basemap(
    ax, crs=gdf_rm_salvador.to_crs(31984).crs,
    #source=cx.providers.HERE.satelliteDay
)
# Obter os limites do GeoDataFrame tiros_knox_local
xmin, ymin, xmax, ymax = shootings_spatemp_hotspot.total_bounds

# Ajustar os limites do gráfico para os limites de salva
ax.set_xlim(xmin, xmax)
ax.set_ylim(ymin, ymax)


e = tiros_knox_local.explore()
folium.GeoJson(gdf_rm_salvador).add_to(e)
e.add_child(folium.map.LayerControl())
e

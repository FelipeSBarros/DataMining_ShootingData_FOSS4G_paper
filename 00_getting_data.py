import pandas as pd

from crossfire import AsyncClient

from decouple import config

EMAIL = config("EMAIL")
PASSWORD = config("PASSWORD")

client = AsyncClient(email=EMAIL, password=PASSWORD)

# identifying states ids
states, _ = await client.states(format="df")
states

# downloading shooting data
shootings = await client.occurrences(
    id_state=states.iloc[2].id,
    initial_date="2000/01/01",
    final_date="2024/06/30",
    format="geodf",
    flat=True,
)
shootings.head()

# updating columns names and data types
shootings["datetime"] = shootings.date
shootings.date = pd.to_datetime(shootings.date)

# saving as .parquet
shootings.to_parquet("./data/gdf_shootings.parquet")

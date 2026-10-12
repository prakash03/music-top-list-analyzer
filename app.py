from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


DATA_PATH = Path(__file__).with_name("music_visualizer_songs.csv")


st.set_page_config(
    page_title="My Global Music Atlas",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    numeric_columns = [
        "rank",
        "release_year",
        "duration_seconds",
        "bpm",
        "energy",
        "danceability",
        "valence",
        "acousticness",
        "my_listens",
        "youtube_views_estimate",
        "spotify_streams_estimate",
        "favorite_score",
        "skip_rate",
    ]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df["explicit"] = df["explicit"].astype(str).str.upper().eq("TRUE")
    df["first_added_date"] = pd.to_datetime(df["first_added_date"], errors="coerce")
    df["duration_minutes"] = df["duration_seconds"] / 60
    df["youtube_views_millions"] = df["youtube_views_estimate"] / 1_000_000
    df["spotify_streams_millions"] = df["spotify_streams_estimate"] / 1_000_000
    return df


def format_number(value: float) -> str:
    if pd.isna(value):
        return "—"
    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f}B"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:,.0f}"


def show_empty_state() -> None:
    st.warning("No songs match the current filters. Try widening the selection.")
    st.stop()


if not DATA_PATH.exists():
    st.error(f"Could not find the data file at {DATA_PATH}")
    st.stop()


df = load_data(DATA_PATH)

st.title("My Global Music Atlas")
st.caption(
    "Explore your songs by language, era, genre, mood, popularity, and personal affinity."
)

with st.sidebar:
    st.header("Explore the collection")

    languages = sorted(df["language"].dropna().unique())
    selected_languages = st.multiselect(
        "Language",
        languages,
        default=languages,
    )

    countries = sorted(df["artist_country"].dropna().unique())
    selected_countries = st.multiselect(
        "Artist country",
        countries,
        default=countries,
    )

    year_min = int(df["release_year"].min())
    year_max = int(df["release_year"].max())
    selected_years = st.slider(
        "Release year",
        min_value=year_min,
        max_value=year_max,
        value=(year_min, year_max),
    )

    genres = sorted(df["genre"].dropna().unique())
    selected_genres = st.multiselect("Genre", genres, default=genres)

    metric = st.selectbox(
        "Primary metric",
        options=[
            "my_listens",
            "favorite_score",
            "youtube_views_millions",
            "spotify_streams_millions",
        ],
        format_func=lambda value: {
            "my_listens": "My listens",
            "favorite_score": "Favorite score",
            "youtube_views_millions": "YouTube views",
            "spotify_streams_millions": "Spotify streams",
        }[value],
    )

    include_explicit = st.checkbox("Include explicit songs", value=True)

    st.divider()
    st.caption("The dataset contains exploratory and estimated metrics.")


filtered = df[
    df["language"].isin(selected_languages)
    & df["artist_country"].isin(selected_countries)
    & df["genre"].isin(selected_genres)
    & df["release_year"].between(selected_years[0], selected_years[1])
]

if not include_explicit:
    filtered = filtered[~filtered["explicit"]]

if filtered.empty:
    show_empty_state()


metric_labels = {
    "my_listens": "My listens",
    "favorite_score": "Favorite score",
    "youtube_views_millions": "YouTube views",
    "spotify_streams_millions": "Spotify streams",
}

top_artist = (
    filtered.groupby("artist", as_index=False)["my_listens"]
    .sum()
    .sort_values("my_listens", ascending=False)
    .iloc[0]["artist"]
)
top_language = filtered["language"].value_counts().index[0]
top_genre = filtered["genre"].value_counts().index[0]

card_columns = st.columns(5)
card_columns[0].metric("Songs in view", f"{len(filtered):,}")
card_columns[1].metric("My listens", format_number(filtered["my_listens"].sum()))
card_columns[2].metric("Top language", top_language)
card_columns[3].metric("Top artist", top_artist)
card_columns[4].metric("Top genre", top_genre)

st.caption(
    f"Showing {len(filtered):,} of {len(df):,} songs · "
    f"Metric focus: {metric_labels[metric]}"
)

overview_tab, taste_tab, artists_tab, library_tab = st.tabs(
    ["Overview", "Taste explorer", "Artists & geography", "Song library"]
)

with overview_tab:
    st.subheader("Your music universe")
    st.caption(
        "Each point is a song. Position describes its musical profile; size reflects your selected metric."
    )

    universe = filtered.copy()
    universe["metric_size"] = universe[metric].fillna(0)
    if metric == "favorite_score":
        universe["metric_size"] = universe["metric_size"] * 10
    elif metric in {"youtube_views_millions", "spotify_streams_millions"}:
        universe["metric_size"] = universe["metric_size"].clip(lower=1)

    fig = px.scatter(
        universe,
        x="danceability",
        y="energy",
        color="language",
        size="metric_size",
        size_max=28,
        hover_name="song",
        hover_data={
            "artist": True,
            "album": True,
            "genre": True,
            "release_year": True,
            "bpm": True,
            "danceability": ":.2f",
            "energy": ":.2f",
            "metric_size": False,
        },
        labels={
            "danceability": "Danceability",
            "energy": "Energy",
            "language": "Language",
        },
        template="plotly_dark",
        height=560,
    )
    fig.update_layout(legend_title_text="Language")
    st.plotly_chart(fig, use_container_width=True)

    left, right = st.columns(2)
    with left:
        language_summary = (
            filtered.groupby("language", as_index=False)
            .agg(songs=("song", "count"), listens=("my_listens", "sum"))
            .sort_values("listens", ascending=False)
        )
        language_fig = px.bar(
            language_summary,
            x="language",
            y="listens",
            color="language",
            text_auto=".2s",
            title="Personal listening by language",
            labels={"listens": "My listens", "language": ""},
            template="plotly_dark",
        )
        st.plotly_chart(language_fig, use_container_width=True)

    with right:
        decade_summary = (
            filtered.groupby(["decade", "language"], as_index=False)
            .size()
            .rename(columns={"size": "songs"})
        )
        decade_fig = px.bar(
            decade_summary,
            x="decade",
            y="songs",
            color="language",
            barmode="stack",
            title="Languages across the decades",
            labels={"songs": "Songs", "decade": ""},
            template="plotly_dark",
        )
        st.plotly_chart(decade_fig, use_container_width=True)

with taste_tab:
    st.subheader("Taste explorer")

    timeline = (
        filtered.groupby(["release_year", "language"], as_index=False)
        .agg(
            songs=("song", "count"),
            listens=("my_listens", "sum"),
            favorite_score=("favorite_score", "mean"),
        )
        .sort_values("release_year")
    )
    timeline_fig = px.line(
        timeline,
        x="release_year",
        y="listens",
        color="language",
        markers=True,
        hover_data={"songs": True, "favorite_score": ":.1f"},
        title="How your collection spans release years",
        labels={"release_year": "Release year", "listens": "My listens"},
        template="plotly_dark",
    )
    st.plotly_chart(timeline_fig, use_container_width=True)

    left, right = st.columns(2)
    with left:
        genre_summary = (
            filtered.groupby("genre", as_index=False)
            .agg(songs=("song", "count"), listens=("my_listens", "sum"))
            .sort_values("listens", ascending=False)
            .head(15)
        )
        genre_fig = px.bar(
            genre_summary.sort_values("listens"),
            x="listens",
            y="genre",
            orientation="h",
            color="listens",
            title="Genres by personal listens",
            labels={"listens": "My listens", "genre": ""},
            template="plotly_dark",
        )
        st.plotly_chart(genre_fig, use_container_width=True)

    with right:
        popularity_fig = px.scatter(
            filtered,
            x="spotify_streams_millions",
            y="my_listens",
            color="language",
            size="favorite_score",
            hover_name="song",
            hover_data={"artist": True, "genre": True, "spotify_streams_millions": ":.1f"},
            title="Global popularity versus personal affinity",
            labels={
                "spotify_streams_millions": "Estimated Spotify streams (millions)",
                "my_listens": "My listens",
            },
            template="plotly_dark",
        )
        st.plotly_chart(popularity_fig, use_container_width=True)

    st.subheader("Compare song DNA")
    comparison_options = (
        filtered.assign(label=filtered["song"] + " — " + filtered["artist"])
        .sort_values("my_listens", ascending=False)["label"]
        .tolist()
    )
    selected_songs = st.multiselect(
        "Choose up to five songs",
        comparison_options,
        default=comparison_options[:2],
        max_selections=5,
    )

    if selected_songs:
        compare = filtered.assign(label=filtered["song"] + " — " + filtered["artist"])
        compare = compare[compare["label"].isin(selected_songs)]
        dimensions = ["energy", "danceability", "valence", "acousticness"]
        radar_rows = []
        for _, row in compare.iterrows():
            for dimension in dimensions:
                radar_rows.append(
                    {
                        "song": row["label"],
                        "dimension": dimension.title(),
                        "value": row[dimension],
                    }
                )
        radar_fig = px.line_polar(
            pd.DataFrame(radar_rows),
            r="value",
            theta="dimension",
            color="song",
            line_close=True,
            range_r=[0, 1],
            title="Selected songs' musical profiles",
            template="plotly_dark",
        )
        st.plotly_chart(radar_fig, use_container_width=True)

with artists_tab:
    st.subheader("Artists and geography")

    artist_summary = (
        filtered.groupby("artist", as_index=False)
        .agg(
            songs=("song", "count"),
            listens=("my_listens", "sum"),
            favorite_score=("favorite_score", "mean"),
            country=("artist_country", "first"),
        )
        .sort_values("listens", ascending=False)
        .head(20)
    )
    artist_fig = px.bar(
        artist_summary.sort_values("listens"),
        x="listens",
        y="artist",
        orientation="h",
        color="country",
        title="Artists with the most personal listens",
        labels={"listens": "My listens", "artist": ""},
        template="plotly_dark",
        height=620,
    )
    st.plotly_chart(artist_fig, use_container_width=True)

    country_summary = (
        filtered.groupby("artist_country", as_index=False)
        .agg(songs=("song", "count"), listens=("my_listens", "sum"))
        .sort_values("songs", ascending=False)
    )
    country_fig = px.bar(
        country_summary,
        x="artist_country",
        y="songs",
        color="listens",
        text_auto=True,
        title="Artist countries in the current selection",
        labels={"artist_country": "Country", "songs": "Songs"},
        template="plotly_dark",
    )
    st.plotly_chart(country_fig, use_container_width=True)

    st.subheader("Selected artist")
    chosen_artist = st.selectbox(
        "Inspect an artist",
        sorted(filtered["artist"].unique()),
    )
    artist_songs = (
        filtered[filtered["artist"] == chosen_artist]
        .sort_values(["my_listens", "favorite_score"], ascending=False)
        .loc[
            :,
            [
                "song",
                "album",
                "language",
                "release_year",
                "genre",
                "my_listens",
                "favorite_score",
            ],
        ]
    )
    st.dataframe(artist_songs, use_container_width=True, hide_index=True)

with library_tab:
    st.subheader("Song library")

    search_term = st.text_input(
        "Search songs, artists, albums, or genres",
        placeholder="Try “Arijit”, “rock”, or “Vaaranam Aayiram”",
    )
    library = filtered.copy()
    if search_term:
        searchable = library[
            ["song", "artist", "album", "genre", "language"]
        ].astype(str).agg(" ".join, axis=1)
        library = library[searchable.str.contains(search_term, case=False, na=False)]

    sort_column = st.selectbox(
        "Sort table by",
        ["my_listens", "favorite_score", "release_year", "skip_rate", "song"],
        format_func=lambda value: {
            "my_listens": "My listens",
            "favorite_score": "Favorite score",
            "release_year": "Release year",
            "skip_rate": "Skip rate",
            "song": "Song title",
        }[value],
    )
    library = library.sort_values(
        sort_column,
        ascending=sort_column == "song",
    )

    display_columns = [
        "song",
        "artist",
        "language",
        "artist_country",
        "release_year",
        "genre",
        "album",
        "bpm",
        "my_listens",
        "favorite_score",
        "skip_rate",
    ]
    st.dataframe(
        library[display_columns],
        use_container_width=True,
        hide_index=True,
        height=560,
        column_config={
            "favorite_score": st.column_config.NumberColumn(
                "Favorite score", format="%.1f"
            ),
            "skip_rate": st.column_config.NumberColumn(
                "Skip rate", format="%.0%%"
            ),
        },
    )
    st.download_button(
        "Download filtered songs",
        data=library.to_csv(index=False).encode("utf-8"),
        file_name="filtered_music_visualizer_songs.csv",
        mime="text/csv",
    )

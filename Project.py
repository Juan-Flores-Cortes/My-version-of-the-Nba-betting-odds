# ============================================================
# IMPORTS
# ============================================================
# streamlit:
#   Builds the website.
#
# pandas:
#   Handles NBA game-log data.
#
# matplotlib:
#   Creates the recent-games bar chart.
#
# nba_api:
#   Finds NBA players and gets their game logs.
# ============================================================

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from nba_api.stats.endpoints import playergamelogs
from nba_api.stats.static import players


# ============================================================
# PAGE CONFIGURATION
# ============================================================
# This controls the browser tab and general page layout.
#
# layout="wide":
#   Gives us more horizontal room like a dashboard.
# ============================================================

st.set_page_config(
    page_title="NBA Prop Research",
    page_icon="🏀",
    layout="wide"
)


# ============================================================
# CUSTOM WEBSITE STYLE
# ============================================================
# Streamlit normally has a very plain look.
# This CSS gives it more of a sportsbook / analytics style.
#
# FUTURE CHANGES:
# You can modify:
#   background colors
#   card colors
#   border radius
#   spacing
#   font sizes
#
# IMPORTANT:
# This is only visual styling. It does not affect calculations.
# ============================================================

st.markdown(
    """
    <style>

    /* Main page background */
    .stApp {
        background: #0b1020;
        color: white;
    }

    /* Main content width */
    .block-container {
        max-width: 1450px;
        padding-top: 1rem;
        padding-bottom: 3rem;
    }

    /* Player header */
    .player-card {
        background: linear-gradient(
            90deg,
            #11172a,
            #171d35
        );
        border: 1px solid #252d46;
        border-radius: 16px;
        padding: 22px;
        margin-bottom: 18px;
    }

    .player-name {
        font-size: 28px;
        font-weight: 800;
        margin-bottom: 4px;
    }

    .player-subtitle {
        color: #aab2c8;
        font-size: 15px;
    }

    /* Generic stat card */
    .research-card {
        background: #141a2d;
        border: 1px solid #252d46;
        border-radius: 14px;
        padding: 16px;
        text-align: center;
        min-height: 115px;
    }

    .research-label {
        color: #9da6bd;
        font-size: 14px;
        margin-bottom: 4px;
    }

    .research-value {
        font-size: 28px;
        font-weight: 800;
        margin-bottom: 4px;
    }

    .research-small {
        font-size: 13px;
        color: #b9c1d5;
    }

    /* Green / Red result text */
    .good {
        color: #38d996;
        font-weight: 700;
    }

    .bad {
        color: #ff5b6e;
        font-weight: 700;
    }

    /* Section headers */
    .section-title {
        font-size: 20px;
        font-weight: 750;
        margin-top: 12px;
        margin-bottom: 10px;
    }

    /* Make Streamlit widgets fit the dark theme */
    div[data-baseweb="select"] > div {
        background-color: #141a2d;
    }

    input {
        background-color: #141a2d !important;
        color: white !important;
    }

    /* Buttons */
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        font-weight: 700;
        height: 44px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# PLAYER LOOKUP
# ============================================================
# nba_api uses numeric IDs.
#
# This converts:
#   "Stephen Curry"
#
# into:
#   201939
#
# FUTURE CHANGE:
# This can later become a searchable dropdown of active players.
# ============================================================

def get_player_info(player_name):

    matches = players.find_players_by_full_name(player_name)

    if len(matches) == 0:
        return None

    # For now, use first matching result.
    return matches[0]


# ============================================================
# GET PLAYER GAME LOGS
# ============================================================
# Retrieves all available player game logs for the selected
# NBA season.
#
# FUTURE CHANGE:
# Instead of hard-coding "2025-26", we can let the user choose
# a season from a dropdown.
# ============================================================

def get_player_games(player_id):

    data = playergamelogs.PlayerGameLogs(
        season_nullable="2025-26",
        player_id_nullable=player_id
    )

    df = data.get_data_frames()[0]

    if df.empty:
        return None

    # Convert date strings into real date objects.
    df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])

    # Newest games first.
    df = df.sort_values(
        "GAME_DATE",
        ascending=False
    )

    # ========================================================
    # CREATE COMBINATION PROP STATS
    # ========================================================
    # These let us research sportsbook combination props.
    #
    # PRA = Points + Rebounds + Assists
    # PR  = Points + Rebounds
    # PA  = Points + Assists
    # RA  = Rebounds + Assists
    # ========================================================

    df["PRA"] = (
        df["PTS"]
        + df["REB"]
        + df["AST"]
    )

    df["PR"] = (
        df["PTS"]
        + df["REB"]
    )

    df["PA"] = (
        df["PTS"]
        + df["AST"]
    )

    df["RA"] = (
        df["REB"]
        + df["AST"]
    )

    return df


# ============================================================
# HIT RATE CALCULATION
# ============================================================
# Determines how many games hit a selected prop.
#
# Example:
#
# stat = "PTS"
# line = 25.5
# direction = "Over"
#
# For every game:
#   PTS > 25.5
#
# Then count how many were True.
# ============================================================

def calculate_hit_rate(games, stat, line, direction):

    if direction == "Over":
        results = games[stat] > line

    else:
        results = games[stat] < line

    hits = results.sum()
    total = len(games)

    if total == 0:
        return 0, 0

    hit_rate = (hits / total) * 100

    return hits, hit_rate


# ============================================================
# RESULT CARD
# ============================================================
# Creates the L5 / L10 / L15 / Season-style cards.
# ============================================================

def result_card(label, games, stat, line, direction):

    hits, rate = calculate_hit_rate(
        games,
        stat,
        line,
        direction
    )

    average = games[stat].mean()

    # Green if hit rate is at least 60%.
    # You can change this threshold later.
    css_class = "good" if rate >= 60 else "bad"

    st.markdown(
        f"""
        <div class="research-card">
            <div class="research-label">{label}</div>

            <div class="research-value {css_class}">
                {rate:.0f}%
            </div>

            <div class="research-small">
                {hits}/{len(games)} hits
            </div>

            <div class="research-small">
                Avg {average:.1f}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# PAGE TITLE
# ============================================================

st.title("🏀 NBA Prop Research Dashboard")

st.caption(
    "Analyze recent player performance against custom prop lines."
)


# ============================================================
# PLAYER SEARCH AREA
# ============================================================

search_col1, search_col2 = st.columns(
    [4, 1]
)

with search_col1:

    player_name = st.text_input(
        "Player",
        placeholder="Example: Stephen Curry"
    )

with search_col2:

    st.write("")
    st.write("")

    search_clicked = st.button(
        "Load Player"
    )


# ============================================================
# ONLY RUN DASHBOARD AFTER PLAYER IS ENTERED
# ============================================================

if player_name:

    player_info = get_player_info(player_name)

    # --------------------------------------------------------
    # PLAYER NOT FOUND
    # --------------------------------------------------------

    if player_info is None:

        st.error(
            "Player not found. Check the spelling and try again."
        )

    else:

        player_id = player_info["id"]
        full_name = player_info["full_name"]

        games = get_player_games(player_id)

        # ----------------------------------------------------
        # NO GAME DATA
        # ----------------------------------------------------

        if games is None:

            st.error(
                "No game logs were found for this player."
            )

        else:

            # =================================================
            # PLAYER HEADER
            # =================================================

            st.markdown(
                f"""
                <div class="player-card">

                    <div class="player-name">
                        {full_name}
                    </div>

                    <div class="player-subtitle">
                        NBA Player ID: {player_id}
                        &nbsp;&nbsp;•&nbsp;&nbsp;
                        Season: 2025-26
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )


            # =================================================
            # STAT TABS
            # =================================================
            # These resemble the stat categories in your
            # reference screenshots.
            #
            # FUTURE CHANGE:
            # Add:
            #   STL
            #   BLK
            #   3PM
            #   fantasy points
            # =================================================

            tabs = st.tabs(
                [
                    "PTS",
                    "REB",
                    "AST",
                    "PRA",
                    "PR",
                    "PA",
                    "RA"
                ]
            )


            # =================================================
            # CREATE CONTENT FOR EACH TAB
            # =================================================
            # Rather than manually writing each tab separately,
            # we loop through the list of supported stats.
            # =================================================

            stat_names = [
                "PTS",
                "REB",
                "AST",
                "PRA",
                "PR",
                "PA",
                "RA"
            ]

            for tab, selected_stat in zip(
                tabs,
                stat_names
            ):

                with tab:

                    # =========================================
                    # PROP CONTROLS
                    # =========================================

                    control1, control2, control3 = st.columns(3)

                    with control1:

                        prop_line = st.number_input(
                            "Prop Line",
                            min_value=0.0,
                            value=20.5,
                            step=0.5,
                            key=f"line_{selected_stat}"
                        )

                    with control2:

                        direction = st.selectbox(
                            "Direction",
                            ["Over", "Under"],
                            key=f"direction_{selected_stat}"
                        )

                    with control3:

                        sample_size = st.selectbox(
                            "Recent Games",
                            [
                                5,
                                10,
                                15,
                                20
                            ],
                            index=1,
                            key=f"sample_{selected_stat}"
                        )


                    # =========================================
                    # OPTIONAL MATCHUP FILTERS
                    # =========================================
                    # These are placeholders for the kind of
                    # filters seen in the reference dashboard.
                    #
                    # Opponent filtering can be added later.
                    # Home/Away filtering can also be added.
                    # =========================================

                    filter1, filter2 = st.columns(2)

                    with filter1:

                        location_filter = st.selectbox(
                            "Home / Away",
                            [
                                "All",
                                "Home",
                                "Away"
                            ],
                            key=f"location_{selected_stat}"
                        )

                    with filter2:

                        season_filter = st.selectbox(
                            "Season",
                            [
                                "2025-26"
                            ],
                            key=f"season_{selected_stat}"
                        )


                    # =========================================
                    # APPLY HOME / AWAY FILTER
                    # =========================================
                    # nba_api MATCHUP looks like:
                    #
                    # LAL vs. DEN = home
                    # LAL @ DEN   = away
                    # =========================================

                    filtered_games = games.copy()

                    if location_filter == "Home":

                        filtered_games = filtered_games[
                            filtered_games["MATCHUP"].str.contains(
                                "vs."
                            )
                        ]

                    elif location_filter == "Away":

                        filtered_games = filtered_games[
                            filtered_games["MATCHUP"].str.contains(
                                "@"
                            )
                        ]


                    # =========================================
                    # HIT RATE CARDS
                    # =========================================

                    st.markdown(
                        '<div class="section-title">Hit Rates</div>',
                        unsafe_allow_html=True
                    )

                    c1, c2, c3, c4 = st.columns(4)

                    with c1:
                        result_card(
                            "L5",
                            filtered_games.head(5),
                            selected_stat,
                            prop_line,
                            direction
                        )

                    with c2:
                        result_card(
                            "L10",
                            filtered_games.head(10),
                            selected_stat,
                            prop_line,
                            direction
                        )

                    with c3:
                        result_card(
                            "L15",
                            filtered_games.head(15),
                            selected_stat,
                            prop_line,
                            direction
                        )

                    with c4:
                        result_card(
                            "Season",
                            filtered_games,
                            selected_stat,
                            prop_line,
                            direction
                        )


                    # =========================================
                    # SELECT GAMES FOR CHART
                    # =========================================

                    recent_games = filtered_games.head(
                        sample_size
                    ).copy()


                    # =========================================
                    # DETERMINE HIT / MISS
                    # =========================================

                    if direction == "Over":

                        recent_games["HIT"] = (
                            recent_games[selected_stat]
                            > prop_line
                        )

                    else:

                        recent_games["HIT"] = (
                            recent_games[selected_stat]
                            < prop_line
                        )


                    # =========================================
                    # RECENT GAME CHART
                    # =========================================
                    # We use matplotlib here because it lets us
                    # show individual game bars and the prop line.
                    # =========================================

                    st.markdown(
                        '<div class="section-title">Recent Games</div>',
                        unsafe_allow_html=True
                    )

                    if not recent_games.empty:

                        chart_data = recent_games.iloc[::-1]

                        fig, ax = plt.subplots(
                            figsize=(12, 5)
                        )

                        bars = ax.bar(
                            range(len(chart_data)),
                            chart_data[selected_stat]
                        )

                        # Prop-line reference
                        ax.axhline(
                            prop_line,
                            linestyle="--",
                            linewidth=2,
                            label=f"Prop Line: {prop_line}"
                        )

                        # Game labels
                        ax.set_xticks(
                            range(len(chart_data))
                        )

                        ax.set_xticklabels(
                            chart_data["MATCHUP"],
                            rotation=45,
                            ha="right"
                        )

                        ax.set_ylabel(
                            selected_stat
                        )

                        ax.set_title(
                            f"{full_name} — "
                            f"{selected_stat} Recent Games"
                        )

                        ax.legend()

                        # Add stat value above each bar
                        for bar, value in zip(
                            bars,
                            chart_data[selected_stat]
                        ):

                            ax.text(
                                bar.get_x()
                                + bar.get_width() / 2,
                                bar.get_height(),
                                f"{value:.0f}",
                                ha="center",
                                va="bottom"
                            )

                        plt.tight_layout()

                        st.pyplot(fig)


                    # =========================================
                    # GAME TABLE
                    # =========================================

                    st.markdown(
                        '<div class="section-title">Game Log</div>',
                        unsafe_allow_html=True
                    )

                    table = recent_games[
                        [
                            "GAME_DATE",
                            "MATCHUP",
                            "PTS",
                            "REB",
                            "AST",
                            selected_stat,
                            "HIT"
                        ]
                    ].copy()


                    # Remove duplicate column when selected stat
                    # is already PTS, REB, or AST.
                    table = table.loc[
                        :,
                        ~table.columns.duplicated()
                    ]


                    # Convert True / False into readable labels.
                    table["RESULT"] = table["HIT"].map(
                        {
                            True: "HIT",
                            False: "MISS"
                        }
                    )

                    table = table.drop(
                        columns=["HIT"]
                    )

                    st.dataframe(
                        table,
                        use_container_width=True,
                        hide_index=True
                    )
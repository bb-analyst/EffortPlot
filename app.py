import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Effort Plotter",
    page_icon="🏉",
    layout="wide"
)

# Title and description
st.title("NRL Player Efforts")

# Function to load and prepare data
@st.cache_data
def load_data():
    # Load data
    df = pd.read_csv('round_players.csv')

    # Create team name mapping
    team_name_mapping = {
        500011: "Brisbane Broncos",
        500013: "Canberra Raiders",
        500010: "Canterbury-Bankstown Bulldogs",
        500028: "Cronulla-Sutherland Sharks",
        500004: "Gold Coast Titans",
        500002: "Manly-Warringah Sea Eagles",
        500021: "Melbourne Storm",
        500003: "Newcastle Knights",
        500032: "New Zealand Warriors",
        500012: "North Queensland Cowboys",
        500031: "Parramatta Eels",
        500014: "Penrith Panthers",
        500005: "South Sydney Rabbitohs",
        500022: "St George Illawarra Dragons",
        500001: "Sydney Roosters",
        500023: "Wests Tigers",
        500723: "The Dolphins"
    }

    # Add team name column
    df['teamName'] = df['teamId'].map(team_name_mapping)

    # Calculate season totals per player
    player_totals = df.groupby(['playerName', 'teamName', 'positionName']).agg({
        'mins': 'sum',
        'roundNumber': 'count'
    }).reset_index()
    player_totals.rename(columns={'roundNumber': 'gamesPlayed', 'mins': 'totalMins'}, inplace=True)

    return df, player_totals


# Load data
df, player_totals = load_data()

# Create sidebar for filters
with st.sidebar:
    st.sidebar.header("Filters")
    # Position filter
    all_positions = sorted(df['positionName'].unique())
    st.sidebar.markdown("#### Filter by Position")
    selected_positions = st.sidebar.multiselect(
        "(empty = all)",
        options=all_positions,
        default=[],
        key="positions_multiselect"
    )

    # If nothing selected, use all positions
    if not selected_positions:
        selected_positions = all_positions

    # Team filter
    all_teams = sorted(df['teamName'].unique())
    st.sidebar.markdown("#### Filter by Team")
    selected_teams = st.sidebar.multiselect(
        "(empty = all)",
        options=all_teams,
        default=[],
        key="teams_multiselect"
    )

    # If nothing selected, use all teams
    if not selected_teams:
        selected_teams = all_teams

    # Filter dataframe based on selections
    filtered_df = df[
        (df['positionName'].isin(selected_positions)) &
        (df['teamName'].isin(selected_teams))
        ]

    # Player filter (depends on position and team filters)
    all_players = sorted(filtered_df['playerName'].unique())
    st.sidebar.markdown("#### Filter by Player")
    selected_players = st.sidebar.multiselect(
        "(empty = all)",
        options=all_players,
        default=[],
        key="players_multiselect"
    )

    # Further filter if players are selected
    if selected_players:
        filtered_df = filtered_df[filtered_df['playerName'].isin(selected_players)]

    # Stat selection
    available_stats = ['runs', 'kickPressures', 'kicksDefused', 'supports', 'decoys', 'tackles']
    st.sidebar.markdown("#### Select Effort Stats")
    selected_stats = st.multiselect(
        "Select statistics",
        options=available_stats,
        default=available_stats,
        key="stats_multiselect"
    )

# Main content area
if not selected_stats:
    st.warning("Please select at least one statistic to analyze.")
else:
    # Calculate the sum of selected stats for each player-round combination
    filtered_df['efforts'] = filtered_df[selected_stats].sum(axis=1)

    # Calculate player season totals for the selected stats
    player_season_stats = filtered_df.groupby(['playerName', 'teamName', 'positionName']).agg({
        'mins': 'sum',
        'efforts': 'sum',
        'roundNumber': 'count'
    }).reset_index()
    player_season_stats.rename(columns={'roundNumber': 'gamesPlayed', 'mins': 'totalMins'}, inplace=True)

    # Calculate the stats per minute
    player_season_stats['efforts_per_min'] = (player_season_stats['efforts'] / player_season_stats['totalMins'])

    # Display three plots in tabs
    plot_tabs = st.tabs(["Individual Games", "Season Total", "Season Efficiency"])

    # Construct a descriptive title for the plots
    selected_stats_str = ', '.join(selected_stats)
    title_stats = selected_stats_str if len(selected_stats_str) < 60 else selected_stats_str[:57] + '...'

    with plot_tabs[0]:
        st.subheader("Game Minutes vs. Efforts")

        # Create the scatter plot
        fig1 = px.scatter(
            filtered_df,
            x='mins',
            y='efforts',
            color='positionName',
            hover_name='playerName',
            hover_data=['positionName', 'teamName', 'roundNumber', 'mins'],
            labels={'mins': 'Mins', 'efforts': f'Efforts'}
        )

        # Update the layout
        fig1.update_layout(
            height=600,
            xaxis_title="Minutes Played",
            yaxis_title=f"Number of Efforts",
            legend_title="Position"
        )

        # Show the plot
        st.plotly_chart(fig1, use_container_width=True)

    with plot_tabs[1]:
        st.subheader("Total Minutes vs. Total Efforts")

        # Create the scatter plot for season totals
        fig2 = px.scatter(
            player_season_stats,
            x='totalMins',
            y='efforts',
            color='positionName',
            hover_name='playerName',
            hover_data=['teamName', 'gamesPlayed', 'totalMins', 'efforts'],
            labels={'totalMins': 'Total Mins', 'efforts': f'Total Efforts'},
            size='gamesPlayed',  # Size points by games played
            size_max=15  # Maximum marker size
        )

        # Update the layout
        fig2.update_layout(
            height=600,
            xaxis_title="Total Minutes Played",
            yaxis_title=f"Total Efforts",
            legend_title="Position"
        )

        # Show the plot
        st.plotly_chart(fig2, use_container_width=True)

    with plot_tabs[2]:
        st.subheader("Efforts Per Minute")

        # Create the scatter plot for efficiency
        fig3 = px.scatter(
            player_season_stats,
            x='totalMins',
            y='efforts_per_min',
            color='positionName',
            hover_name='playerName',
            hover_data=['teamName', 'gamesPlayed', 'totalMins', 'efforts', 'efforts_per_min'],
            labels={'totalMins': 'Total Minutes Played', 'efforts_per_min': f'Efforts per Minute'},
            size='gamesPlayed',  # Size points by games played
            size_max=15  # Maximum marker size
        )

        # Update the layout
        fig3.update_layout(
            height=600,
            xaxis_title="Total Minutes Played",
            yaxis_title=f"Efforts Per Minute",
            legend_title="Position"
        )

        # Show the plot
        st.plotly_chart(fig3, use_container_width=True)

    # Display summary statistics
    st.header("Summary Statistics")

    summary_tabs = st.tabs(["Top Players"])

    with summary_tabs[0]:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Top Players by Total Efforts")

            # Create a more detailed top players table
            top_players = player_season_stats.sort_values('efforts', ascending=False).head(10)

            # Add rank column
            top_players = top_players.reset_index(drop=True)
            top_players.index = top_players.index + 1

            # Format table for display
            top_players_table = top_players[
                ['playerName', 'teamName', 'positionName', 'gamesPlayed', 'totalMins', 'efforts']]
            st.dataframe(top_players_table, use_container_width=True)

            # Show a bar chart of top players
            fig_top = px.bar(
                top_players.head(10),
                y='playerName',
                x='efforts',
                color='positionName',
                orientation='h',
                labels={'efforts': 'Total Efforts', 'playerName': 'Player'},
                hover_data=['teamName', 'gamesPlayed', 'totalMins']
            )

            # Reverse y-axis to show highest values at the top
            fig_top.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False)

            st.plotly_chart(fig_top, use_container_width=True)

        with col2:
            st.subheader("Top Players by Efficiency")

            # Filter players with meaningful playing time (e.g., at least 80 minutes)
            min_mins = 80
            efficient_players = player_season_stats[player_season_stats['totalMins'] >= min_mins]
            efficient_players = efficient_players.sort_values('efforts_per_min', ascending=False).head(10)

            # Add rank column
            efficient_players = efficient_players.reset_index(drop=True)
            efficient_players.index = efficient_players.index + 1

            # Format table for display
            efficient_players_table = efficient_players[
                ['playerName', 'teamName', 'positionName', 'gamesPlayed', 'totalMins', 'efforts_per_min']]
            st.dataframe(efficient_players_table, use_container_width=True)

            # Show a bar chart of most efficient players
            fig_eff = px.bar(
                efficient_players.head(10),
                y='playerName',
                x='efforts_per_min',
                color='positionName',
                orientation='h',
                labels={'efforts_per_min': 'Efforts/Min', 'playerName': 'Player'},
                hover_data=['teamName', 'gamesPlayed', 'totalMins', 'efforts']
            )

            # Reverse y-axis to show highest values at the top
            fig_eff.update_layout(yaxis={'categoryorder': 'total ascending'},showlegend=False)

            st.plotly_chart(fig_eff, use_container_width=True)


    # Display raw data in an expandable section
    with st.expander("View Raw Data"):
        # Add tabs for different data views
        raw_tabs = st.tabs(["Individual Games", "Season Totals"])

        with raw_tabs[0]:
            st.subheader("Individual Games")
            # Allow searching in the dataframe
            search_term = st.text_input("Search by player name:", key="search_round_data")

            if search_term:
                filtered_display_df = filtered_df[filtered_df['playerName'].str.contains(search_term, case=False)]
            else:
                filtered_display_df = filtered_df

            st.dataframe(
                filtered_display_df[
                    ['playerName', 'teamName', 'positionName', 'roundNumber', 'mins'] + selected_stats + ['efforts']],
                use_container_width=True
            )

        with raw_tabs[1]:
            st.subheader("Season Totals")
            # Allow searching in the dataframe
            search_term_season = st.text_input("Search by player name:", key="search_season_data")

            if search_term_season:
                filtered_season_df = player_season_stats[
                    player_season_stats['playerName'].str.contains(search_term_season, case=False)]
            else:
                filtered_season_df = player_season_stats

            st.dataframe(
                filtered_season_df[['playerName', 'teamName', 'positionName', 'gamesPlayed', 'totalMins', 'efforts',
                                    'efforts_per_min']],
                use_container_width=True
            )
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Workout Analytics",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
        background-color: #0E1117;
        color: #FAFAFA;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
    }
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    </style>
""", unsafe_allow_html=True)

# Exercise mapping dictionary
EXERCISE_CLUSTERS = {
    'pushups': ['Push Up', 'Push Up (Weighted)', 'Decline Push Up'],
    'dips': ['Chest Dip', 'Chest Dip (Weighted)', 'Triceps Dip', 'Triceps Dip (Weighted)', 'Bench Dip'],
    'curls': ['Bicep Curl (Dumbbell)', 'Hammer Curl (Band)'],
    'rows': ['Bent Over Row (Dumbbell)', 'Bent Over Row (Band)'],
    'core': ['Decline Crunch', 'Decline Crunch (Weighted)', 'Plank', 'Side Plank', 
             'Bicycle Crunch', 'Russian Twist (Bodyweight)', 'Oblique Crunch', 
             'Flutter Kicks', 'Sit Up', 'Heel Taps', 'Lying Leg Raise',
             'Leg Raise Parallel Bars', 'Superman'],
    'shoulders': ['Overhead Press (Dumbbell)'],
    'legs': ['Squat (Barbell)', 'Goblet Squat']
}

def get_exercise_cluster(exercise_name):
    for cluster, exercises in EXERCISE_CLUSTERS.items():
        if exercise_name in exercises:
            return cluster
    return 'other'

def load_and_process_data(df):
    # French to English month name mapping
    MONTH_MAPPING = {
        'janv.': 'Jan', 'févr.': 'Feb', 'mars.': 'Mar', 'avr.': 'Apr',
        'mai.': 'May', 'juin.': 'Jun', 'juil.': 'Jul', 'août': 'Aug',  # Note: removed period from août
        'sept.': 'Sep', 'oct.': 'Oct', 'nov.': 'Nov', 'déc.': 'Dec',
        # Add non-abbreviated versions
        'janvier': 'Jan', 'février': 'Feb', 'mars': 'Mar', 'avril': 'Apr',
        'mai': 'May', 'juin': 'Jun', 'juillet': 'Jul', 'août': 'Aug',
        'septembre': 'Sep', 'octobre': 'Oct', 'novembre': 'Nov', 'décembre': 'Dec'
    }
    
    # Convert time columns to datetime with flexible parsing
    for col in ['start_time', 'end_time']:
        try:
            # Replace French month names with English ones
            temp_col = df[col].copy()
            
            # Convert to lowercase for case-insensitive replacement
            temp_col = temp_col.str.lower()
            
            # Remove any extra spaces
            temp_col = temp_col.str.replace(r'\s+', ' ', regex=True)
            
            # Replace French months with English ones (case-insensitive)
            for fr_month, en_month in MONTH_MAPPING.items():
                temp_col = temp_col.str.replace(
                    fr_month.lower(), 
                    en_month, 
                    case=False
                )
            
            # Capitalize the month names back
            for en_month in set(MONTH_MAPPING.values()):
                temp_col = temp_col.str.replace(
                    en_month.lower(),
                    en_month,
                    case=False
                )
            
            # First try with dayfirst=True since dates are in DD MMM YYYY format
            df[col] = pd.to_datetime(temp_col, dayfirst=True)
        except Exception as e:
            try:
                # If that fails, try with a more flexible parser
                df[col] = pd.to_datetime(temp_col, format='mixed', dayfirst=True)
            except Exception as e:
                # If both methods fail, print the problematic values for debugging
                problematic_dates = temp_col[pd.to_datetime(temp_col, errors='coerce').isna()]
                if not problematic_dates.empty:
                    st.error(f"Failed to parse these dates in {col}:\n{problematic_dates.unique()}")
                raise e
    
    # Standardize exercise names (map French to English)
    exercise_name_mapping = {
        'Pompes': 'Push Up',
        'Pompes (Lesté)': 'Push Up (Weighted)',
        'Dips Triceps': 'Triceps Dip',
        'Dips Triceps (Lesté)': 'Triceps Dip (Weighted)',
        'Crunch (Lesté)': 'Decline Crunch (Weighted)',
        'Rotation Russe (Lesté)': 'Russian Twist (Weighted)',
        'Squat (Barre)': 'Squat (Barbell)',
        'Squat (Haltère)': 'Goblet Squat'
    }
    
    # Apply the mapping, keeping original name if no mapping exists
    df['exercise_title'] = df['exercise_title'].map(lambda x: exercise_name_mapping.get(x, x))
    
    # Add exercise cluster column
    df['exercise_cluster'] = df['exercise_title'].apply(get_exercise_cluster)
    
    # Add week column
    df['week'] = df['start_time'].dt.isocalendar().week
    df['year'] = df['start_time'].dt.isocalendar().year
    df['year_week'] = df['year'].astype(str) + '-W' + df['week'].astype(str).str.zfill(2)
    
    # Create a numeric year_week for proper sorting
    df['year_week_num'] = df['year'] * 100 + df['week']
    
    # Calculate cumulative sums for each exercise and cluster
    df = df.sort_values(['exercise_title', 'year_week_num'])
    df['cumulative_reps_by_exercise'] = df.groupby('exercise_title')['reps'].cumsum()
    
    df = df.sort_values(['exercise_cluster', 'year_week_num'])
    df['cumulative_reps_by_cluster'] = df.groupby('exercise_cluster')['reps'].cumsum()
    
    return df

def main():
    # Header with icon
    st.markdown("# 💪 Workout Analytics Dashboard")
    st.markdown("---")
    
    # File upload with instructions
    st.markdown("### 📊 Data Import")
    uploaded_file = st.file_uploader(
        "Upload your workout data CSV file to begin analysis",
        type="csv",
        help="Make sure your CSV file contains workout data with exercises, sets, and reps"
    )
    
    if uploaded_file is not None:
        with st.spinner('Processing your workout data...'):
            # Read and process the data
            df = pd.read_csv(uploaded_file)
            df = load_and_process_data(df)
        
        # Sidebar configuration
        with st.sidebar:
            st.markdown("### ⚙️ Analysis Settings")
            
            # Date range selector with clear labels
            st.markdown("#### 📅 Time Period")
            min_date = df['start_time'].min().date()
            max_date = df['start_time'].max().date()
            selected_date_range = st.date_input(
                "Select date range for analysis",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                help="Filter your workout data by date range"
            )
            
            st.markdown("---")
            
            # Exercise selection
            st.markdown("#### 🎯 Exercise Selection")
            selected_clusters = st.multiselect(
                "Choose exercise categories",
                options=sorted(df['exercise_cluster'].unique()),
                default=['pushups'],
                help="Select one or more exercise categories to analyze"
            )
            
            selected_exercises = st.multiselect(
                "Choose specific exercises",
                options=df[df['exercise_cluster'].isin(selected_clusters)]['exercise_title'].unique(),
                default=df[df['exercise_cluster'] == 'pushups']['exercise_title'].unique(),
                help="Select exercises within the chosen categories"
            )
            
            st.markdown("---")
            
            # Visualization options
            st.markdown("#### 📈 Visualization Options")
            show_cumulative = st.checkbox(
                "Show cumulative progress",
                value=False,
                help="Display cumulative total of reps over time"
            )
        
        # Filter data based on selections
        if len(selected_date_range) == 2:
            start_date, end_date = selected_date_range
            mask = (df['start_time'].dt.date >= start_date) & (df['start_time'].dt.date <= end_date)
            df = df[mask]
        
        filtered_df = df[df['exercise_title'].isin(selected_exercises)]
        
        # Add KPI Cards section
        st.markdown("### 📊 Key Metrics")
        
        # Get current week's data
        current_week = datetime.now().isocalendar()[1]
        current_year = datetime.now().year
        this_week_mask = (filtered_df['week'] == current_week) & (filtered_df['year'] == current_year)
        this_week_data = filtered_df[this_week_mask]
        
        # Calculate metrics
        total_reps = int(filtered_df['reps'].sum())  # Convert to integer
        total_sessions = filtered_df['title'].nunique()
        total_days = filtered_df['start_time'].dt.date.nunique()
        
        this_week_reps = int(this_week_data['reps'].sum()) if not this_week_data.empty else 0
        avg_reps_per_session = int(total_reps / total_sessions) if total_sessions > 0 else 0
        avg_reps_per_day = int(total_reps / total_days) if total_days > 0 else 0
        
        # Style for the cards - updated for dark theme
        card_style = """
        <style>
        .metric-card {
            background-color: #262730;
            border-radius: 0.5rem;
            padding: 1rem;
            text-align: center;
            margin: 0.5rem 0;
            border: 1px solid #444444;
        }
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            margin: 0.5rem 0;
            color: #ffffff;
        }
        .metric-label {
            font-size: 1rem;
            color: #cccccc;
        }
        </style>
        """
        st.markdown(card_style, unsafe_allow_html=True)
        
        # Display KPI cards
        col1, col2, col3, col4 = st.columns(4)
        
        # Display KPI cards
        with col1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value">{this_week_reps:,}</div>
                    <div class="metric-label">Reps This Week</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with col2:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value">{avg_reps_per_session:,}</div>
                    <div class="metric-label">Avg Reps per Session</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with col3:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value">{avg_reps_per_day:,}</div>
                    <div class="metric-label">Avg Reps per Day</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with col4:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value">{total_reps:,}</div>
                    <div class="metric-label">Total Reps</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        st.markdown("---")
        
        # Progress charts
        st.markdown("### 📈 Progress Tracking")
        
        # Prepare data for charts
        exercise_progress = filtered_df.groupby(['year_week', 'exercise_title']).agg({
            'reps': 'sum'  # Remove weight_kg
        }).reset_index()
        
        # Sort by year_week to ensure chronological order
        exercise_progress = exercise_progress.sort_values('year_week')
        if show_cumulative:
            exercise_progress['cumulative_reps'] = exercise_progress.groupby('exercise_title')['reps'].cumsum()
        
        category_progress = filtered_df.groupby(['year_week', 'exercise_cluster']).agg({
            'reps': 'sum'  # Remove weight_kg
        }).reset_index()
        
        # Sort by year_week to ensure chronological order
        category_progress = category_progress.sort_values('year_week')
        if show_cumulative:
            category_progress['cumulative_reps'] = category_progress.groupby('exercise_cluster')['reps'].cumsum()
        
        # Tabs for different views
        tab1, tab2 = st.tabs(["📊 Category Totals", "🎯 Individual Exercises"])
        
        with tab1:
            if show_cumulative:
                # Show cumulative progress
                fig2 = px.bar(
                    category_progress, 
                    x='year_week', 
                    y='cumulative_reps',
                    color='exercise_cluster',
                    title='Cumulative Progress by Category',
                    template="plotly_dark"
                )
            else:
                # Show weekly progress
                fig2 = px.bar(
                    category_progress, 
                    x='year_week', 
                    y='reps',
                    color='exercise_cluster',
                    title='Weekly Category Progress',
                    template="plotly_dark"
                )
            
            fig2.update_xaxes(tickangle=45)
            for trace in fig2.data:
                trace.update(
                    text=trace.y,
                    textposition='outside',
                    texttemplate='%{text:.0f}'
                )
            st.plotly_chart(fig2, use_container_width=True)
            
        with tab2:
            if show_cumulative:
                # Show cumulative progress
                fig1 = px.bar(
                    exercise_progress, 
                    x='year_week', 
                    y='cumulative_reps',
                    color='exercise_title',
                    title='Cumulative Progress by Exercise',
                    template="plotly_dark"
                )
            else:
                # Show weekly progress
                fig1 = px.bar(
                    exercise_progress, 
                    x='year_week', 
                    y='reps',
                    color='exercise_title',
                    title='Weekly Exercise Progress',
                    template="plotly_dark"
                )
            
            fig1.update_xaxes(tickangle=45)
            for trace in fig1.data:
                trace.update(
                    text=trace.y,
                    textposition='outside',
                    texttemplate='%{text:.0f}'
                )
            st.plotly_chart(fig1, use_container_width=True)
    
    else:
        # Welcome message when no file is uploaded
        st.info("👋 Welcome! Please upload your workout data CSV file to begin analyzing your fitness progress.")

if __name__ == "__main__":
    main() 
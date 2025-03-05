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
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 0.5rem;
        padding: 1rem;
        text-align: center;
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
    # Convert time columns to datetime
    df['start_time'] = pd.to_datetime(df['start_time'], format='%d %b %Y, %H:%M')
    df['end_time'] = pd.to_datetime(df['end_time'], format='%d %b %Y, %H:%M')
    
    # Add exercise cluster column
    df['exercise_cluster'] = df['exercise_title'].apply(get_exercise_cluster)
    
    # Add week column
    df['week'] = df['start_time'].dt.isocalendar().week
    df['year'] = df['start_time'].dt.isocalendar().year
    df['year_week'] = df['year'].astype(str) + '-W' + df['week'].astype(str).str.zfill(2)
    
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
                default=sorted(df['exercise_cluster'].unique())[:2],
                help="Select one or more exercise categories to analyze"
            )
            
            selected_exercises = st.multiselect(
                "Choose specific exercises",
                options=df[df['exercise_cluster'].isin(selected_clusters)]['exercise_title'].unique(),
                default=df[df['exercise_cluster'].isin(selected_clusters)]['exercise_title'].unique()[:3],
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
        
        # Main content area
        st.markdown("### 📊 Workout Analysis")
        
        # Metrics in styled cards
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("🏋️ Total Workouts", len(filtered_df['title'].unique()))
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("🔄 Total Sets", len(filtered_df))
            st.markdown('</div>', unsafe_allow_html=True)
        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("🎯 Unique Exercises", len(filtered_df['exercise_title'].unique()))
            st.markdown('</div>', unsafe_allow_html=True)
        with col4:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("📊 Exercise Categories", len(filtered_df['exercise_cluster'].unique()))
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Progress charts
        st.markdown("### 📈 Progress Tracking")
        
        # Prepare data for charts
        exercise_progress = filtered_df.groupby(['year_week', 'exercise_title']).agg({
            'weight_kg': 'max',
            'reps': 'sum'
        }).reset_index()
        
        category_progress = filtered_df.groupby(['year_week', 'exercise_cluster']).agg({
            'reps': 'sum',
            'weight_kg': 'mean'
        }).reset_index()
        
        if show_cumulative:
            exercise_progress = exercise_progress.sort_values('year_week')
            exercise_progress['cumulative_reps'] = exercise_progress.groupby('exercise_title')['reps'].cumsum()
            
            category_progress = category_progress.sort_values('year_week')
            category_progress['cumulative_reps'] = category_progress.groupby('exercise_cluster')['reps'].cumsum()
        
        # Tabs for different views
        tab1, tab2 = st.tabs(["🎯 Individual Exercises", "📊 Category Totals"])
        
        with tab1:
            y_cols = ['weight_kg', 'reps']
            if show_cumulative:
                y_cols.append('cumulative_reps')
            
            fig1 = px.bar(
                exercise_progress, 
                x='year_week', 
                y=y_cols,
                color='exercise_title',
                title='Weekly Exercise Progress',
                barmode='group',
                template="plotly_white"
            )
            fig1.update_xaxes(tickangle=45)
            st.plotly_chart(fig1, use_container_width=True)
            
        with tab2:
            y_cols = ['weight_kg', 'reps']
            if show_cumulative:
                y_cols.append('cumulative_reps')
                
            fig2 = px.bar(
                category_progress, 
                x='year_week', 
                y=y_cols,
                color='exercise_cluster',
                title='Weekly Category Progress',
                barmode='group',
                template="plotly_white"
            )
            fig2.update_xaxes(tickangle=45)
            st.plotly_chart(fig2, use_container_width=True)
    
    else:
        # Welcome message when no file is uploaded
        st.info("👋 Welcome! Please upload your workout data CSV file to begin analyzing your fitness progress.")

if __name__ == "__main__":
    main() 
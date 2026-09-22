Flight Delay Analysis is a Streamlit dashboard backed by MySQL and MongoDB to evaluate U.S. flight disruptions. 
It processes multi-dimensional data to track seasonal weather risks, rank carrier reliability, and break down root causes across different regions. 
The platform combines predictive risk cards, regional heatmaps, comparative annual trends, and performance metrics into a single tool for better travel and operational decisions.

System Archictecture
- Frontend: Streamlit (Python)
- Relational Database (OLAP): MySQL (Handles raw data storage, multi-table joins, and multidimensional aggregation queries)
- NoSQL Database: MongoDB (Stores aggregated analytical collections to accelerate dashboard response times)
- Data Processing: Python
  
The application integrates two primary datasets:
1. U.S. Airline Delay Dataset (Kaggle): Contains flight counts, cancellation metrics, delay frequencies, and specific delay causes.
2. U.S. States to Region Dataset (Kaggle): Used for geographical mapping from state codes embedded in airport data to 4 major U.S. regions.

The ETL and OLAP pipeline aggregates data from MySQL, computes percentile-based risk distributions, and pushes structured documents into MongoDB collections (delay_time_analysis, airline_performance, delay_cause_distribution).

"""相容本機 modules/ 與 GitHub 根目錄兩種部署方式。"""

try:
    from modules.churn import render_churn_prediction
    from modules.cohort import render_cohort_analysis
    from modules.data_loader import load_and_clean_data
    from modules.data_quality import render_data_quality
    from modules.executive_summary import render_executive_summary
    from modules.filters import render_sidebar_filters
    from modules.market_basket import render_market_basket
except ModuleNotFoundError:
    from churn import render_churn_prediction
    from cohort import render_cohort_analysis
    from data_loader import load_and_clean_data
    from data_quality import render_data_quality
    from executive_summary import render_executive_summary
    from filters import render_sidebar_filters
    from market_basket import render_market_basket

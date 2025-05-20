# Streamgraph and Application Fix Strategy

## Step 1: Create a new branch from feature/streamlit-dashboard
git checkout feature/streamlit-dashboard
git checkout -b fix/integrate-streamgraph-fixes

## Step 2: Cherry-pick the simulation framework enhancements
git cherry-pick d6e716b  # Enhanced DES implementation
git cherry-pick aa0aa95  # TreatAndExtendAdapter implementation
git cherry-pick 90b2fee  # EnhancedTreatAndExtendDES integration
git cherry-pick 278dd7f  # Staggered enrollment with discontinuation

## Step 3: Apply the streamgraph fixes
# Option A: Cherry-pick
git cherry-pick 22d7a16  # Streamgraph retreatment visualization fix

# Option B: Manual copy (if cherry-pick conflicts)
cp fix/restore-app-and-streamgraph/streamlit_app/streamgraph_patient_states_fixed.py feature/streamlit-dashboard/streamlit_app/

## Step 4: Apply the app.py fix
git cherry-pick 8c4d4de  # Page configuration fix

## Step 5: Test the integrated application
streamlit run streamlit_app/app.py

## Step 6: Merge back to feature/streamlit-dashboard
git checkout feature/streamlit-dashboard
git merge fix/integrate-streamgraph-fixes

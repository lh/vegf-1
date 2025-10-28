"""
Batch Simulations - Experimental page for running multiple simulations.

This page allows running multiple protocol simulations as a batch job,
restricted to local machines only.
"""

import streamlit as st
from pathlib import Path
import subprocess
import sys
import time
import signal
import os
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Batch Simulations",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Import utilities
from ape.utils.startup_redirect import handle_page_startup
from ape.components.ui.workflow_indicator import workflow_progress_indicator
from ape.utils.environment import is_streamlit_cloud
from ape.batch.status import BatchStatus, get_batch_dir, list_batches
from ape.core.results.factory import ResultsFactory

# Check for startup redirect
handle_page_startup("batch_simulations")

# Show workflow progress
workflow_progress_indicator("batch_simulations")

st.title("🔬 Batch Simulations (Experimental)")

# Cloud guard - CRITICAL
if is_streamlit_cloud():
    st.error("""
    ❌ **Batch simulations are disabled on Streamlit Cloud**

    This feature requires significant compute resources and the ability to run
    background processes, which are only available on local machines.

    To use batch simulations:
    1. Clone the repository to your local machine
    2. Run the Streamlit app locally
    3. Return to this page
    """)
    st.stop()

st.success("✓ Local environment detected - batch simulations available")

st.markdown("""
This experimental page allows you to run multiple protocol simulations as a batch job.
All simulations in a batch will use the same parameters (patients, duration, seed).

**Important - Statistical Design:**
All protocols use the **same random seed**, implementing a "paired comparison" design.
This means each protocol is tested on identical patient populations, which:
- Reduces variance and increases statistical power
- Isolates the protocol effect from patient variation
- Enables more sensitive detection of differences
- Requires smaller sample sizes for significance

This is the standard approach for controlled protocol comparison studies.
""")

# Initialize session state
if 'batch_running' not in st.session_state:
    st.session_state.batch_running = False
if 'batch_id' not in st.session_state:
    st.session_state.batch_id = None

# Get available protocols - TIME-BASED ONLY
protocols_dir = Path(__file__).parent.parent / "protocols"
available_protocols = []

# Search for protocol files and check if they're time-based
import yaml
for pattern in ["*.yaml", "v2_time_based/*.yaml"]:
    for protocol_file in protocols_dir.glob(pattern):
        # Skip parameter files
        if protocol_file.parent.name == "parameters":
            continue
        # Skip resources
        if "resource" in protocol_file.name.lower():
            continue

        # Check if time-based by reading the file
        try:
            with open(protocol_file) as f:
                protocol_data = yaml.safe_load(f)

            # Only include time-based protocols
            if protocol_data.get('model_type') == 'time_based':
                display_name = protocol_file.stem.replace('_', ' ').title()
                available_protocols.append({
                    'name': display_name,
                    'path': str(protocol_file)
                })
        except:
            # Skip files that can't be read
            continue

# Sort by name
available_protocols.sort(key=lambda x: x['name'])

if len(available_protocols) < 2:
    st.error("Need at least 2 protocols available to run batch simulations.")
    st.stop()

st.markdown("---")
st.markdown("## Batch Configuration")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Protocol Selection")
    protocol_a_idx = st.selectbox(
        "Protocol A",
        range(len(available_protocols)),
        format_func=lambda i: available_protocols[i]['name'],
        key="protocol_a_select",
        disabled=st.session_state.batch_running
    )
    protocol_a = available_protocols[protocol_a_idx]

    # Filter out protocol A from B options
    protocol_b_options = [i for i in range(len(available_protocols)) if i != protocol_a_idx]

    protocol_b_idx = st.selectbox(
        "Protocol B",
        protocol_b_options,
        format_func=lambda i: available_protocols[i]['name'],
        key="protocol_b_select",
        disabled=st.session_state.batch_running
    )
    protocol_b = available_protocols[protocol_b_idx]

    st.info(f"""
    **Selected Protocols:**
    - A: {protocol_a['name']}
    - B: {protocol_b['name']}
    """)

with col2:
    st.markdown("### Simulation Parameters")
    st.markdown("⚠️ **All simulations will use the same parameters**")

    n_patients = st.number_input(
        "Patients per simulation",
        min_value=100,
        max_value=5000,
        value=2000,
        step=100,
        disabled=st.session_state.batch_running,
        help="Number of patients to simulate for each protocol"
    )

    duration_years = st.number_input(
        "Duration (years)",
        min_value=1.0,
        max_value=10.0,
        value=5.0,
        step=0.5,
        disabled=st.session_state.batch_running,
        help="Simulation duration in years"
    )

    seed = st.number_input(
        "Random seed",
        min_value=0,
        max_value=999999,
        value=42,
        disabled=st.session_state.batch_running,
        help="Random seed for reproducibility"
    )

    # Estimate runtime
    # Rough estimate: ~5 seconds per 1000 patient-years
    complexity = n_patients * duration_years
    estimated_runtime_per_sim = max(2.0, (complexity / 1000) * 5)
    estimated_total = estimated_runtime_per_sim * 2

    st.caption(f"Estimated runtime: ~{estimated_total:.0f}s ({estimated_total/60:.1f}m) for both simulations")

st.markdown("---")

# Start batch button
if not st.session_state.batch_running:
    if st.button("🚀 Start Batch Run", type="primary", use_container_width=True):
        # Generate batch ID
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        st.session_state.batch_id = batch_id
        st.session_state.batch_running = True

        # Create batch directory and initialize status
        batch_dir = get_batch_dir(batch_id)
        status_mgr = BatchStatus(batch_dir)
        status_mgr.initialize(
            batch_id=batch_id,
            protocols=[protocol_a['name'], protocol_b['name']],
            n_patients=n_patients,
            duration_years=duration_years,
            seed=seed
        )

        # Launch subprocess
        cmd = [
            sys.executable,
            "-m", "ape.batch.runner",
            "--protocol-a", protocol_a['path'],
            "--protocol-b", protocol_b['path'],
            "--n-patients", str(n_patients),
            "--duration-years", str(duration_years),
            "--seed", str(seed),
            "--batch-id", batch_id
        ]

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True  # Detach from parent
            )

            # Update status with PID
            status = status_mgr.read()
            status['pid'] = process.pid
            status_mgr._write_status(status)

            st.success(f"✓ Batch started with ID: {batch_id}")
            st.rerun()

        except Exception as e:
            st.error(f"Failed to start batch: {e}")
            st.session_state.batch_running = False

# Progress display
if st.session_state.batch_running:
    st.markdown("## Batch Progress")

    batch_id = st.session_state.batch_id
    batch_dir = get_batch_dir(batch_id)
    status_mgr = BatchStatus(batch_dir)

    status = status_mgr.read()

    if not status:
        st.error("Could not read batch status")
        st.session_state.batch_running = False
        st.rerun()

    # Status indicator
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        if status['status'] == 'running':
            st.info(f"🔄 **Status:** Running")
        elif status['status'] == 'completed':
            st.success(f"✅ **Status:** Completed")
        elif status['status'] == 'error':
            st.error(f"❌ **Status:** Error")
        elif status['status'] == 'cancelled':
            st.warning(f"⚠️ **Status:** Cancelled")
        else:
            st.info(f"**Status:** {status['status']}")

    with col2:
        st.markdown(f"**Progress:** {status['progress']}")

    with col3:
        if status['status'] in ['running', 'pending']:
            if st.button("❌ Cancel", type="secondary"):
                pid = status_mgr.get_pid()
                if pid:
                    try:
                        os.kill(pid, signal.SIGTERM)
                        status_mgr.mark_cancelled()
                        st.session_state.batch_running = False
                        st.success("Batch cancelled")
                        st.rerun()
                    except ProcessLookupError:
                        st.warning("Process already terminated")
                        st.session_state.batch_running = False
                        st.rerun()

    # Progress bar
    completed_count = len(status.get('completed_simulations', []))
    total_count = len(status.get('protocols', []))
    progress = completed_count / total_count if total_count > 0 else 0

    st.progress(progress, text=f"{completed_count} of {total_count} simulations complete")

    # Completed simulations
    if status.get('completed_simulations'):
        st.markdown("### Completed Simulations")
        for sim in status['completed_simulations']:
            st.markdown(f"""
            - **{sim['protocol']}**: `{sim['sim_id']}`
              - {sim['n_patients']} patients
              - Runtime: {sim['runtime']:.1f}s
              - Completed: {sim['completed_at']}
            """)

    # Check if completed
    if status['status'] == 'completed':
        st.session_state.batch_running = False

        st.markdown("---")
        st.success("✅ Batch completed successfully!")

        # Show navigation options
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 View Summary Statistics", use_container_width=True):
                st.session_state.batch_view_summary = batch_id
                st.rerun()

        with col2:
            if st.button("🔄 Start New Batch", use_container_width=True):
                st.session_state.batch_id = None
                st.rerun()

    elif status['status'] == 'error':
        st.session_state.batch_running = False
        st.error(f"Error: {status.get('error', 'Unknown error')}")

    elif status['status'] == 'cancelled':
        st.session_state.batch_running = False

    # Auto-refresh while running
    if status['status'] in ['running', 'pending']:
        time.sleep(2)
        st.rerun()

# Show previous batches
st.markdown("---")
st.markdown("## Previous Batch Runs")

batches = list_batches()

if not batches:
    st.info("No previous batch runs found.")
else:
    for batch in batches[:10]:  # Show last 10
        with st.expander(f"{batch['batch_id']} - {batch['status'].title()} ({batch['completed_count']}/{batch['total_count']})"):
            st.markdown(f"""
            - **Status:** {batch['status']}
            - **Started:** {batch.get('started_at', 'Unknown')}
            - **Protocols:** {', '.join(batch.get('protocols', []))}
            - **Completed:** {batch['completed_count']} of {batch['total_count']}
            """)

            if batch['status'] == 'completed':
                if st.button(f"View Results", key=f"view_{batch['batch_id']}"):
                    st.session_state.batch_view_summary = batch['batch_id']
                    st.rerun()

# Show summary if requested
if st.session_state.get('batch_view_summary'):
    batch_id = st.session_state.batch_view_summary
    batch_dir = get_batch_dir(batch_id)
    status_mgr = BatchStatus(batch_dir)

    st.markdown("---")
    st.markdown(f"## Summary: {batch_id}")

    summary = status_mgr.read_summary()
    if summary:
        st.markdown("### Batch Information")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            **Protocols:** {', '.join(summary['protocols'])}
            **Completed:** {summary['completed_at']}
            """)
        with col2:
            params = summary['parameters']
            st.markdown(f"""
            **Parameters:** {params['n_patients']} patients × {params['duration_years']} years
            **Random Seed:** {params['seed']}
            """)

        st.markdown("### Visual Comparison")

        try:
            from visualization.batch_comparison import create_batch_summary_figure
            import matplotlib.pyplot as plt

            # Create comprehensive summary figure
            fig = create_batch_summary_figure(batch_id)
            st.pyplot(fig)
            plt.close(fig)

        except Exception as e:
            st.error(f"Error creating visualization: {e}")
            import traceback
            st.code(traceback.format_exc())

        st.markdown("### Text Summary")

        try:
            from ape.batch.statistics import get_batch_summary_text
            summary_text = get_batch_summary_text(batch_id)
            st.code(summary_text, language=None)
        except Exception as e:
            st.error(f"Error generating text summary: {e}")

        st.markdown("### Simulation Links")
        # Quick links to simulations
        for i, sim_id in enumerate(summary['simulation_ids']):
            protocol_name = summary['protocols'][i]
            st.markdown(f"- **{protocol_name}**: `{sim_id}`")

    if st.button("Back to Batch List"):
        del st.session_state.batch_view_summary
        st.rerun()

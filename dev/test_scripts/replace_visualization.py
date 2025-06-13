#!/usr/bin/env python
"""
Script to replace the visualization in the staggered simulation page.

This script modifies the staggered_simulation_page.py file to use
Tufte-inspired visualizations instead of the default matplotlib styling.
"""

import os
import re
import shutil
from pathlib import Path

def main():
    print("Enhancing visualizations with Tufte-inspired style...")
    
    # Path to the staggered simulation page
    page_path = Path("streamlit_app/pages/staggered_simulation_page.py")
    
    # Copy tufte_viz.py functions to utils directory
    utils_dir = Path("streamlit_app/utils")
    if not utils_dir.exists():
        os.makedirs(utils_dir)
    
    # Create visualization utilities file
    viz_utils_path = utils_dir / "tufte_viz.py"
    
    # Copy relevant functions from tufte_viz.py
    with open("streamlit_app/tufte_viz.py", "r") as f:
        tufte_viz_content = f.read()
    
    # Extract the functions and style settings
    functions = re.findall(r"def ([^(]+)\([^)]+\):[^:]+:([^:]+)((?:.+?)+?)(?=\n\ndef|\n\n# |$)", 
                         tufte_viz_content, re.DOTALL)
    
    # Create the visualization utilities file
    with open(viz_utils_path, "w") as f:
        f.write('"""\nTufte-inspired visualization utilities.\n\nThis module provides clean, minimal visualizations inspired by Edward Tufte\'s principles.\n"""\n\n')
        f.write("import pandas as pd\nimport matplotlib.pyplot as plt\nimport numpy as np\nimport streamlit as st\nfrom matplotlib import rcParams\n\n")
        
        # Include the style setup function
        style_fn = re.search(r"def set_tufte_style\(\):(.*?)def", tufte_viz_content, re.DOTALL)
        if style_fn:
            f.write(style_fn.group(0).replace("def", "\ndef"))
        
        # Include the visualization functions
        for fn_name, docstring, fn_body in functions:
            if fn_name in ["create_tufte_enrollment_visualization", "create_tufte_va_over_time_plot"]:
                f.write(f"\ndef {fn_name}(")
                
                # Extract the function signature
                signature = re.search(rf"def {fn_name}\(([^)]+)\)", tufte_viz_content)
                if signature:
                    f.write(signature.group(1))
                else:
                    f.write("data")
                    
                f.write(f"):{docstring}{fn_body}\n")
    
    print(f"Created visualization utilities at {viz_utils_path}")
    
    # Backup the staggered simulation page
    backup_path = page_path.with_suffix('.py.bak')
    shutil.copy2(page_path, backup_path)
    print(f"Created backup of staggered_simulation_page.py at {backup_path}")
    
    # Read the staggered simulation page
    with open(page_path, "r") as f:
        content = f.read()
    
    # Add the import for the Tufte visualization
    import_line = "from streamlit_app.utils.tufte_viz import set_tufte_style, create_tufte_enrollment_visualization"
    if import_line not in content:
        content = content.replace(
            "import pandas as pd", 
            "import pandas as pd\n" + import_line
        )
    
    # Find the matplotlib visualization code
    viz_pattern = r"(# Use direct matplotlib visualization.*?st\.pyplot\(fig\))"
    
    # Create the replacement code
    replacement = """# Use Tufte-inspired visualization instead of default matplotlib
                            st.markdown("### Patient Enrollment Visualization")
                            
                            try:
                                # Create a Tufte-inspired visualization directly
                                import matplotlib.pyplot as plt
                                import numpy as np
                                
                                # Set tufte style if not imported
                                if 'set_tufte_style' not in locals():
                                    from matplotlib import rcParams
                                    
                                    # Set up clean style
                                    plt.style.use('seaborn-v0_8-whitegrid')
                                    rcParams['grid.color'] = '#eeeeee'
                                    rcParams['grid.linestyle'] = '-'
                                    rcParams['grid.linewidth'] = 0.5
                                    rcParams['text.color'] = '#333333'
                                    rcParams['axes.labelcolor'] = '#666666'
                                    rcParams['xtick.color'] = '#666666'
                                    rcParams['ytick.color'] = '#666666'
                                    rcParams['axes.spines.top'] = False
                                    rcParams['axes.spines.right'] = False
                                    rcParams['axes.spines.left'] = False
                                else:
                                    set_tufte_style()
                                
                                # Create visualization
                                fig = create_tufte_enrollment_visualization(enroll_df)
                                
                                # Display the plot
                                st.pyplot(fig)
                                
                            except Exception as e:
                                if debug_mode:
                                    st.error(f"Error creating Tufte visualization: {e}")
                                    import traceback
                                    st.code(traceback.format_exc())
                                    
                                # Fall back to basic matplotlib visualization
                                st.warning("Falling back to basic matplotlib visualization")
                                
                                # Group by month
                                if not pd.api.types.is_datetime64_any_dtype(enroll_df['enrollment_date']):
                                    enroll_df['enrollment_date'] = pd.to_datetime(enroll_df['enrollment_date'])
                                    
                                enroll_df['month'] = enroll_df['enrollment_date'].dt.strftime('%Y-%m')
                                monthly_counts = enroll_df.groupby('month').size()
                                
                                # Create figure
                                fig, ax = plt.subplots(figsize=(10, 5))
                                
                                # Plot data
                                x = range(len(monthly_counts))
                                ax.bar(x, monthly_counts.values, color='#4682B4')
                                ax.set_xticks(x)
                                ax.set_xticklabels(monthly_counts.index, rotation=45, ha='right')
                                ax.set_title('Patient Enrollment by Month')
                                ax.set_ylabel('Number of Patients')
                                plt.tight_layout()
                                
                                # Display plot
                                st.pyplot(fig)"""
    
    # Replace the visualization code
    updated_content = re.sub(viz_pattern, replacement, content, flags=re.DOTALL)
    
    # Write the updated file
    with open(page_path, "w") as f:
        f.write(updated_content)
    
    print(f"Updated {page_path} with Tufte-inspired visualization")
    print("\nTo try the Tufte-inspired visualizations:")
    print("1. Run the standalone demo: streamlit run streamlit_app/tufte_viz.py")
    print("2. Run the normal application: streamlit run streamlit_app/app_refactored.py")
    print("   and navigate to the Staggered Simulation page")
    print("\nIf you encounter any issues, the backup file is at:", backup_path)

if __name__ == "__main__":
    main()
"""
Quarto Utilities Module

This module provides utilities for integrating Quarto with Streamlit, including
automatic installation of Quarto in Streamlit Cloud environments and rendering
Quarto reports.

Based on the implementation by Sammi Rosser in the Project_Toy_MECC repository
(https://github.com/Bergam0t/Project_Toy_MECC).
"""

import os
import sys
import platform
import subprocess
import streamlit as st
import tempfile
import shutil
from pathlib import Path


def is_streamlit_cloud():
    """
    Detect if the application is running in Streamlit Cloud.
    
    Returns
    -------
    bool
        True if running in Streamlit Cloud, False otherwise
    """
    # Check environment variables that might be set in Streamlit Cloud
    return os.environ.get("STREAMLIT_SHARING", "") == "true" or \
           os.environ.get("IS_STREAMLIT_CLOUD", "") == "true" or \
           os.path.exists("/.dockerenv")  # Docker container (likely Streamlit Cloud)

def ensure_r_installed():
    """
    Check if R is installed and available. If not, attempt to install it
    based on the environment (Streamlit Cloud or local).
    
    Returns
    -------
    bool
        True if R is available, False otherwise
    """
    # Check if R is already installed
    result = subprocess.run(
        ["which", "R"], 
        capture_output=True, 
        text=True
    )
    
    r_path = result.stdout.strip()
    
    if r_path:
        st.toast(f"R found at {r_path}")
        return True
    
    # If not found, try to install it
    st.info("R not found. Providing installation instructions...")
    
    system = platform.system().lower()
    if is_streamlit_cloud():
        # In Streamlit Cloud (Linux)
        st.text("Detected Streamlit Cloud environment. Installing R using apt...")
        try:
            subprocess.run(
                ["apt-get", "update"],
                check=True
            )
            subprocess.run(
                ["apt-get", "install", "-y", "r-base", "r-base-dev"],
                check=True
            )
            
            # Verify installation
            result = subprocess.run(
                ["R", "--version"],
                capture_output=True,
                text=True
            )
            
            if "R version" in result.stdout:
                st.success("R installed successfully in Streamlit Cloud")
                return True
            else:
                st.error("R installation verification failed in Streamlit Cloud")
                return False
        except Exception as e:
            st.error(f"Failed to install R in Streamlit Cloud: {str(e)}")
            return False
    elif system == "darwin":
        # macOS
        st.error("""
        R not found on your Mac. Please install it using one of these methods:
        
        1. Download from CRAN: https://cran.r-project.org/bin/macosx/
        2. Using Homebrew: `brew install r`
        3. Using Conda: `conda install -c conda-forge r-base`
        
        After installing, restart this application.
        """)
        return False
    elif system == "windows":
        # Windows
        st.error("""
        R not found on Windows. Please install it from:
        https://cran.r-project.org/bin/windows/base/
        
        After installing, restart this application.
        """)
        return False
    else:
        # Other Linux
        st.error(f"""
        R not found on your {system.capitalize()} system. Please install it using your package manager.
        For example:
        
        Ubuntu/Debian: `sudo apt-get install r-base r-base-dev`
        Fedora: `sudo dnf install R`
        
        After installing, restart this application.
        """)
        return False

def get_quarto():
    """
    Check if Quarto is installed and available. If not, attempt to install it
    in the Streamlit Cloud environment.
    
    This function is adapted from the implementation by Sammi Rosser in the
    Project_Toy_MECC repository.
    
    Returns
    -------
    str or None
        Path to the Quarto executable if available, None otherwise
    """
    # First check if Quarto is already installed
    result = subprocess.run(
        ["which", "quarto"], 
        capture_output=True, 
        text=True
    )
    
    quarto_path = result.stdout.strip()
    
    if quarto_path:
        st.toast(f"Quarto found at {quarto_path}")
        return quarto_path
    
    # If not found, try to install it
    st.info("Quarto not found. Attempting to install...")
    
    try:
        # Check if R is installed, needed for Quarto
        r_available = ensure_r_installed()
        if not r_available:
            st.error("R is required for Quarto but could not be installed")
            return None
        
        # Create temporary directory for installation
        temp_dir = tempfile.mkdtemp()
        
        # Set up platform-specific details
        system = platform.system().lower()
        
        # Provide platform-specific installation instructions
        if system == "darwin":
            st.warning("""
            Quarto not found on your Mac. Please install it using one of these methods:
            
            1. Download from Quarto website: https://quarto.org/docs/get-started/
            2. Using Homebrew: `brew install quarto`
            
            After installing, restart this application.
            """)
            return None
        elif system == "windows":
            st.warning("""
            Quarto not found on Windows. Please install it from:
            https://quarto.org/docs/get-started/
            
            After installing, restart this application.
            """)
            return None
        elif not is_streamlit_cloud() and system == "linux":
            st.warning("""
            Quarto not found on your Linux system. Please install it from:
            https://quarto.org/docs/get-started/
            
            After installing, restart this application.
            """)
            return None
            
        # Only proceed with automatic installation on Streamlit Cloud
        if not is_streamlit_cloud():
            return None
        
        # Download Quarto for Linux
        st.text("Downloading Quarto...")
        quarto_version = "1.5.14"
        quarto_url = f"https://github.com/quarto-dev/quarto-cli/releases/download/v{quarto_version}/quarto-{quarto_version}-linux-amd64.tar.gz"
        
        download_path = os.path.join(temp_dir, "quarto.tar.gz")
        subprocess.run(
            ["wget", quarto_url, "-O", download_path],
            check=True
        )
        
        # Extract the archive
        st.text("Extracting Quarto...")
        extract_dir = os.path.join(temp_dir, "quarto-extract")
        os.makedirs(extract_dir, exist_ok=True)
        
        subprocess.run(
            ["tar", "-xzf", download_path, "-C", extract_dir],
            check=True
        )
        
        # Find the quarto executable
        quarto_dir = os.path.join(extract_dir, f"quarto-{quarto_version}")
        quarto_bin = os.path.join(quarto_dir, "bin", "quarto")
        
        # Make executable
        os.chmod(quarto_bin, 0o755)
        
        # Add to PATH
        os.environ["PATH"] = f"{os.path.dirname(quarto_bin)}:{os.environ['PATH']}"
        
        # Verify installation
        result = subprocess.run(
            [quarto_bin, "--version"],
            capture_output=True,
            text=True
        )
        
        if "quarto" in result.stdout.lower():
            st.success(f"Quarto {quarto_version} installed successfully")
            
            # Install required R packages
            required_packages = [
                "jsonlite", "dplyr", "ggplot2", "knitr", "kableExtra", "plotly"
            ]
            
            st.info(f"Installing required R packages for Quarto: {', '.join(required_packages)}")
            install_r_packages(required_packages)
            
            return quarto_bin
        else:
            st.error("Quarto installation verification failed")
            return None
            
    except Exception as e:
        st.error(f"Failed to install Quarto: {str(e)}")
        return None


def install_r_packages(packages):
    """
    Install required R packages for Quarto reporting.
    
    Parameters
    ----------
    packages : list
        List of R packages to install
    
    Returns
    -------
    bool
        True if successful, False otherwise
    """
    try:
        # Check if R is available
        r_check = subprocess.run(
            ["which", "R"], 
            capture_output=True, 
            text=True
        )
        
        if not r_check.stdout.strip():
            st.error("R not found in PATH. Cannot install required packages.")
            return False
        
        # Create an R script to install packages
        with tempfile.NamedTemporaryFile(mode='w', suffix='.R', delete=False) as f:
            script_path = f.name
            
            # Set different repository options based on environment
            system = platform.system().lower()
            if system == "darwin":
                # macOS specific setup
                f.write('options(repos = c(CRAN = "https://mac.r-project.org"))\n')
            else:
                # Default for other systems
                f.write('options(repos = c(CRAN = "https://cloud.r-project.org"))\n')
                
            # Include common error-handling for Mac permission issues
            if system == "darwin":
                f.write("""
# Mac-specific error handling function
handle_mac_errors <- function(expr) {
  tryCatch(
    expr,
    error = function(e) {
      if (grepl("Permission denied", e$message)) {
        message("Permission error detected. This may be because R cannot write to the library directory.")
        message("Possible solutions:")
        message("1. Run R as admin: sudo R")
        message("2. Install packages to user library: install.packages(..., lib = Sys.getenv('R_LIBS_USER'))")
        message("3. Fix permissions on R library directories")
      }
      stop(e)
    }
  )
}
""")
            
            # Package installation function with error handling
            f.write("""
install_if_missing <- function(pkg) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    message(paste("Installing package:", pkg))
    
    # Try to install the package
    tryCatch({
      install.packages(pkg)
      if (!requireNamespace(pkg, quietly = TRUE)) {
        message(paste("Package", pkg, "installation seems to have failed. Trying with lib.loc specified..."))
        # Try again with user library location
        lib_loc <- Sys.getenv("R_LIBS_USER", unset = NA)
        if (!is.na(lib_loc) && !dir.exists(lib_loc)) {
          dir.create(lib_loc, recursive = TRUE)
        }
        install.packages(pkg, lib = lib_loc)
      }
    }, error = function(e) {
      message(paste("Error installing package", pkg, ":", e$message))
      return(FALSE)
    })
    
    # Final check
    return(requireNamespace(pkg, quietly = TRUE))
  }
  return(TRUE)
}
""")
            
            # Add code to check which packages are already installed
            f.write('cat("Checking packages:", "' + '", "'.join(packages) + '")\n')
            f.write('installed <- sapply(c("' + '", "'.join(packages) + '"), function(pkg) requireNamespace(pkg, quietly = TRUE))\n')
            f.write('cat("\\nAlready installed:", paste(names(installed)[installed], collapse = ", "), "\\n")\n')
            f.write('cat("Need to install:", paste(names(installed)[!installed], collapse = ", "), "\\n\\n")\n')
            
            # Add installation commands
            for pkg in packages:
                if system == "darwin":
                    f.write(f'result <- handle_mac_errors(install_if_missing("{pkg}"))\n')
                    f.write(f'cat("Package {pkg} installation ", ifelse(result, "succeeded", "failed"), "\\n")\n')
                else:
                    f.write(f'result <- install_if_missing("{pkg}")\n')
                    f.write(f'cat("Package {pkg} installation ", ifelse(result, "succeeded", "failed"), "\\n")\n')
            
            # Add final verification
            f.write('cat("\\nFinal verification:\\n")\n')
            f.write('final_check <- sapply(c("' + '", "'.join(packages) + '"), function(pkg) requireNamespace(pkg, quietly = TRUE))\n')
            f.write('cat("Successfully installed:", paste(names(final_check)[final_check], collapse = ", "), "\\n")\n')
            f.write('cat("Failed to install:", paste(names(final_check)[!final_check], collapse = ", "), "\\n")\n')
            f.write('if (all(final_check)) { cat("SUCCESS: All packages installed successfully\\n"); quit(status = 0) } else { cat("ERROR: Some packages failed to install\\n"); quit(status = 1) }\n')
        
        # Run the R script with different approaches based on environment
        st.write(f"Installing required R packages: {', '.join(packages)}")
        
        is_cloud = is_streamlit_cloud()
        system = platform.system().lower()
        
        if is_cloud:
            # In Streamlit Cloud - can use direct sudo approach
            st.text("Using Streamlit Cloud R package installation...")
            
            # Try with sudo for permission issues
            try:
                result = subprocess.run(
                    ["sudo", "Rscript", script_path], 
                    capture_output=True, 
                    text=True,
                    timeout=300  # Longer timeout for package installation
                )
            except:
                # Fall back to regular if sudo fails
                result = subprocess.run(
                    ["Rscript", script_path], 
                    capture_output=True, 
                    text=True,
                    timeout=300
                )
        elif system == "darwin":
            # macOS-specific approach
            st.text("Using macOS R package installation...")
            
            # On Mac, try normal first, with longer timeout
            result = subprocess.run(
                ["Rscript", script_path], 
                capture_output=True, 
                text=True,
                timeout=300  # Longer timeout for package installation
            )
            
            # If it fails with a permission error, suggest solutions
            if result.returncode != 0 and "Permission denied" in result.stderr:
                st.error("""
                Permission error when installing R packages on macOS. Try one of these solutions:
                
                1. Install R packages manually with:
                   `R -e 'install.packages(c("jsonlite", "dplyr", "ggplot2", "knitr", "kableExtra", "plotly"))'`
                   
                2. Use homebrew R instead:
                   `brew install r` and then install packages
                   
                3. Run the app with elevated permissions (not recommended)
                """)
        else:
            # Default for other systems
            result = subprocess.run(
                ["Rscript", script_path], 
                capture_output=True, 
                text=True,
                timeout=300
            )
            
        # Display output for debugging
        with st.expander("R Package Installation Details"):
            st.write("Output from R package installation:")
            st.code(result.stdout)
            if result.stderr:
                st.error("Errors:")
                st.code(result.stderr)
        
        # Clean up
        try:
            os.unlink(script_path)
        except:
            pass
        
        if result.returncode != 0:
            st.error(f"Failed to install all R packages")
            return False
        
        st.success("R packages installed or already available")
        return True
    
    except Exception as e:
        st.error(f"Error installing R packages: {e}")
        return False

def render_quarto_report(quarto_path, qmd_template_path, output_dir, data_path, 
                         output_format='html', include_code=False, include_appendix=True):
    """
    Render a Quarto report from a template using simulation data.
    
    Parameters
    ----------
    quarto_path : str
        Path to the Quarto executable
    qmd_template_path : str
        Path to the Quarto template file (.qmd)
    output_dir : str
        Directory to save the rendered report
    data_path : str
        Path to the JSON data file with simulation results
    output_format : str, optional
        Output format ('html', 'pdf', 'docx'), by default 'html'
    include_code : bool, optional
        Whether to include code chunks in the output, by default False
    include_appendix : bool, optional
        Whether to include the appendix section, by default True
    
    Returns
    -------
    str or None
        Path to the rendered report if successful, None otherwise
    """
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Define required R packages
        required_packages = [
            "jsonlite", "dplyr", "ggplot2", "knitr", "kableExtra", "plotly"
        ]
        
        # Install required R packages
        with st.spinner("Checking and installing required R packages..."):
            packages_installed = install_r_packages(required_packages)
            if not packages_installed:
                pkg_list = "', '".join(required_packages)
                st.warning(
                    "Could not automatically install R packages. Reports may fail. " +
                    "You may need to install them manually with: " +
                    f"`R -e \"install.packages(c('{pkg_list}'))\"`"
                )
        
        # Create a temporary directory for the template
        with tempfile.TemporaryDirectory() as temp_dir:
            # Copy the template to the temp directory
            temp_qmd_path = os.path.join(temp_dir, "report.qmd")
            shutil.copyfile(qmd_template_path, temp_qmd_path)
            
            # Set up command line arguments
            cmd = [
                quarto_path,
                "render",
                temp_qmd_path,
                "--to", output_format,
                "--output-dir", output_dir,
                "-M", f"dataPath={data_path}",
                "-M", f"includeCode={'true' if include_code else 'false'}",
                "-M", f"includeAppendix={'true' if include_appendix else 'false'}"
            ]
            
            # Run Quarto
            st.text("Rendering report with Quarto...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                st.error(f"Error rendering report: {result.stderr}")
                return None
            
            # Determine the output file path
            output_filename = f"report.{output_format}"
            output_path = os.path.join(output_dir, output_filename)
            
            if os.path.exists(output_path):
                st.success("Report rendered successfully")
                return output_path
            else:
                st.error(f"Output file not found at {output_path}")
                return None
                
    except Exception as e:
        st.error(f"Failed to render report: {str(e)}")
        return None
# This script uses a ROBPCA library from R and runs it in Python using rpy2

import numpy as np
import pandas as pd
import rpy2.robjects as robjects
from rpy2.robjects import pandas2ri
from rpy2.robjects.packages import importr
from rpy2.robjects.conversion import localconverter
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.stats import median_abs_deviation


class RobustPCA:
    def __init__(self):
        # Activate the conversion between pandas and R dataframes
        pandas2ri.activate()

        # Check and install rospca if needed
        if not self._is_package_installed("rospca"):
            print("Installing rospca package...")
            utils = importr("utils")
            utils.install_packages("rospca")
        else:
            print("rospca package is already installed")

        # Import rospca package
        self.rospca = importr("rospca")

    def _is_package_installed(self, package_name):
        """Check if R package is installed"""
        r_code = f'is.element("{package_name}", installed.packages()[,1])'
        return robjects.r(r_code)[0]

    def fit(self, X, k=None, kmax=10, alpha=0.75, ndir="all", skew=False):
        """
        Fit Robust PCA to the data

        Parameters:
        -----------
        X : pandas DataFrame or numpy array
            Input data with observations in rows and variables in columns
        k : int, optional (default=None)
            Number of components to extract. If None, uses number of features
        alpha : float, optional (default=0.75)
            Robustness parameter
        skew : bool, optional (default=False)
            If True, uses version for skewed data

        Returns:
        --------
        self : returns an instance of self
        """
        # Convert input to DataFrame if needed
        if isinstance(X, np.ndarray):
            X = pd.DataFrame(X)

        self.n_features_ = X.shape[1]
        if k is None:
            k = self.n_features_

        # Convert pandas DataFrame to R dataframe
        with localconverter(robjects.default_converter + pandas2ri.converter):
            r_df = robjects.conversion.py2rpy(X)

        # Perform robust PCA
        self.rob_pca_ = self.rospca.robpca(
            r_df, k=k, kmax=kmax, alpha=alpha, ndir=ndir, skew=skew
        )

        # Extract results
        with localconverter(robjects.default_converter + pandas2ri.converter):
            self.components_ = pd.DataFrame(
                robjects.conversion.rpy2py(self.rob_pca_.rx2("loadings"))
            )
            self.eigenvalues_ = pd.Series(
                robjects.conversion.rpy2py(self.rob_pca_.rx2("eigenvalues"))
            )
            self.scores_ = pd.DataFrame(
                robjects.conversion.rpy2py(self.rob_pca_.rx2("scores"))
            )
            self.center_ = pd.Series(
                robjects.conversion.rpy2py(self.rob_pca_.rx2("center"))
            )
            self.n_components_ = pd.Series(
                robjects.conversion.rpy2py(self.rob_pca_.rx2("k"))
            )
            self.sd_ = pd.Series(robjects.conversion.rpy2py(self.rob_pca_.rx2("sd")))
            self.od_ = pd.Series(robjects.conversion.rpy2py(self.rob_pca_.rx2("od")))
            self.cutoff_sd_ = pd.Series(
                robjects.conversion.rpy2py(self.rob_pca_.rx2("cutoff.sd")[0])
            )
            self.cutoff_od_ = pd.Series(
                robjects.conversion.rpy2py(self.rob_pca_.rx2("cutoff.od")[0])
            )
            self.outlier_flags_ = pd.Series(
                robjects.conversion.rpy2py(self.rob_pca_.rx2("flag.all"))
            )

        # Calculate explained variance ratio
        total_variance = self.eigenvalues_.sum()
        self.explained_variance_ratio_ = self.eigenvalues_ / total_variance

        return self

    def plot_diagnostic(
        self,
        plot_folder=None,
        filename="robpca_diagnostic.png",
        n_samples=1000,
        random_state=42,
    ):
        """
        Create diagnostic plot for outlier detection

        Parameters:
        -----------
        plot_folder : str or Path, optional (default=None)
            Path to folder where plot should be saved.
            If None, displays plot instead of saving
        filename : str, optional (default="robpca_diagnostic.png")
            Name of the output file (if plot_folder is specified)
        n_samples : int, optional (default=1000)
            Number of points to plot
        random_state : int, optional (default=42)
            Random seed for reproducibility
        """
        # Set random seed
        np.random.seed(random_state)

        # Select random subset of indices
        n_total = len(self.sd_)
        n_samples = min(n_samples, n_total)
        idx = np.random.choice(n_total, size=n_samples, replace=False)

        plt.figure(figsize=(10, 8))
        plt.scatter(self.sd_[idx], self.od_[idx], alpha=0.5)
        plt.axhline(y=self.cutoff_od_[0], color="r", linestyle="--", label="OD cutoff")
        plt.axvline(x=self.cutoff_sd_[0], color="r", linestyle="--", label="SD cutoff")
        plt.xlabel("Score Distance")
        plt.ylabel("Orthogonal Distance")
        plt.title("Robust PCA Diagnostic Plot")
        plt.legend()

        if plot_folder is not None:
            # Convert to Path object and create folder if it doesn't exist
            plot_path = Path(plot_folder)
            plot_path.mkdir(parents=True, exist_ok=True)

            # Save the plot
            plt.savefig(plot_path / filename)
            plt.close()
        else:
            plt.show()


if __name__ == "__main__":

    from ucimlrepo import fetch_ucirepo

    # ==== Load dataset ====
    # fetch dataset
    computer_hardware = fetch_ucirepo(id=29)

    # data (as pandas dataframes)
    df = computer_hardware.data.features
    y = computer_hardware.data.targets

    # metadata
    print(computer_hardware.metadata)

    # variable information
    print(computer_hardware.variables)

    # Drop VendorName and ModelName
    df = df.drop(columns=["VendorName", "ModelName"])

    # # ==== Create test dataset ====
    # # Create a simple dataset with some outliers
    # np.random.seed(42)
    # n_samples = 100
    # n_features = 5

    # # Generate normal data
    # X = np.random.randn(n_samples, n_features)

    # # Add some correlation between features
    # X[:, 1] = X[:, 0] * 0.9 + np.random.randn(n_samples) * 0.1
    # X[:, 2] = X[:, 0] * 0.8 + np.random.randn(n_samples) * 0.2

    # # Add some outliers
    # X[0:5, :] = X[0:5, :] * 5  # Make first 5 samples outliers

    # # Convert to pandas DataFrame
    # df = pd.DataFrame(X, columns=[f"V{i+1}" for i in range(n_features)])

    # Calculate median and median absolute deviation (MAD)
    medians = np.median(df, axis=0)
    mads = median_abs_deviation(df, axis=0, scale=1.0)
    # Prevent division by zero
    mads[mads == 0] = 1
    # Center and scale the data
    scaled_data = (df - medians) / mads
    scaled_df = pd.DataFrame(scaled_data, columns=df.columns, index=df.index)

    # Fit Robust PCA
    rpca = RobustPCA()
    rpca.fit(scaled_df, alpha=0.75, ndir=1000, skew=True)

    # Print results
    print("Robust PCA:")
    print("\nPrincipal Components (loadings):")
    print(rpca.components_)
    print("\nOutliers detected:")
    print(f"Number of outliers detected: {sum(rpca.outlier_flags_ == 0)}")
    print(
        f"The outliers consitute {sum(rpca.outlier_flags_ == 0) / len(rpca.outlier_flags_):.2%} of the data"
    )
    print("\nEigenvalues:")
    print(rpca.eigenvalues_)
    print("\nExplained Variance Ratio:")
    print(rpca.explained_variance_ratio_)
    print("\nCumulative Explained Variance Ratio:")
    print(rpca.explained_variance_ratio_.cumsum())

    # Plot diagnostic plot
    rpca.plot_diagnostic(plot_folder="/mnt/g/SOCIAL_PAPER/plots")

    # ==== Run standard PCA for comparison ====

    pca = PCA(n_components=df.shape[1])
    X_pca = pca.fit_transform(scaled_df)

    # Print results
    print("Standard PCA:")
    print("\nPrincipal Components (loadings):")
    print(pca.components_)
    print("\nExplained Variance Ratio:")
    print(pca.explained_variance_ratio_)
    print("\nCumulative Explained Variance Ratio:")
    print(np.cumsum(pca.explained_variance_ratio_))
